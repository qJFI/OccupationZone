import streamlit as st
import sqlite3
from auth import get_current_user
import pandas as pd
import json
import tempfile
import os
from PyPDF2 import PdfReader
import base64

def get_default_labels():
    return {
        # Personal Information
        "name": "",
        "age": "",
        "national_id": "",
        "phone": "",
        "email": "",
        "location": "",
        "linkedin_profile": "",
        
        # Professional Summary
        "overview": "",
        "career_objective": "",
        
        # Core Information
        "skills": "",
        "experience": "",
        "education": "",
        "certifications": "",
        
        # Additional Information
        "languages": "",
        "projects": "",
        "achievements": "",
        "references": "",
        
        # Job Application Specific
        "salary_expectations": "",
        "availability": "",
        "preferred_work_type": "",  # remote, hybrid, on-site
        "notice_period": "",
        "visa_status": "",
    }

def convert_to_json_labels(labels):
    """Convert string labels to JSON format if needed."""
    if not labels:
        return json.dumps({})
    try:
        # Try to parse as JSON first
        json.loads(labels)
        return labels
    except json.JSONDecodeError:
        # If it's not JSON, assume it's comma-separated and convert
        label_list = [label.strip() for label in labels.split(',')]
        return json.dumps({label: "" for label in label_list})

def display_pdf(pdf_content):
    """Display PDF file in Streamlit."""
    # Create an embedded PDF viewer
    base64_pdf = base64.b64encode(pdf_content).decode('utf-8')
    pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf">'
    st.markdown(pdf_display, unsafe_allow_html=True)

def get_existing_resume_data(conn, user):
    """Get existing resume data for the user."""
    try:
        query = "SELECT filename, labels, content FROM resumes WHERE user = ? ORDER BY rowid DESC LIMIT 1"
        result = pd.read_sql_query(query, conn, params=(user,))
        if not result.empty:
            return result.iloc[0]
    except Exception as e:
        st.error(f"Error loading existing resume: {str(e)}")
    return None

def resume_manager_page():
    st.header("Resume Manager")
    user = get_current_user()
    conn = sqlite3.connect("jobs.db")

    # Get existing resume data
    existing_resume = get_existing_resume_data(conn, user)
    
    # Show current resume status
    if existing_resume is not None:
        st.info(f"Current resume on file: {existing_resume['filename']}")
    
    # Upload resume section
    uploaded_file = st.file_uploader("Upload or Update Resume", type=["pdf", "docx"])
    
    # Initialize labels dictionary
    labels_dict = get_default_labels()
    updated_labels = {}

    if uploaded_file is not None:
        resume_content = uploaded_file.read()
        st.success("Resume uploaded successfully!")

        # Display the uploaded PDF
        if uploaded_file.type == "application/pdf":
            st.subheader("Resume Preview")
            display_pdf(resume_content)
    else:
        # Display existing PDF if available
        if existing_resume is not None and existing_resume['filename'].lower().endswith('.pdf'):
            st.subheader("Current Resume")
            display_pdf(existing_resume['content'])
            # Load existing labels
            try:
                existing_labels = json.loads(convert_to_json_labels(existing_resume['labels']))
                labels_dict.update(existing_labels)
            except Exception as e:
                st.error(f"Error loading existing labels: {str(e)}")

    # Display form for labels
    st.subheader("Resume Information")
    
    # Group labels by category
    categories = {
        "Personal Information": ["name", "age", "national_id", "phone", "email", "location", "linkedin_profile"],
        "Professional Summary": ["overview", "career_objective"],
        "Core Information": ["skills", "experience", "education", "certifications"],
        "Additional Information": ["languages", "projects", "achievements", "references"],
        "Job Application Specific": ["salary_expectations", "availability", "preferred_work_type", "notice_period", "visa_status"]
    }
    
    # Create tabs for different categories
    category_tabs = st.tabs(list(categories.keys()))
    
    # Display fields in tabs
    for tab, (category, fields) in zip(category_tabs, categories.items()):
        with tab:
            col1, col2 = st.columns(2)
            for idx, field in enumerate(fields):
                with col1 if idx % 2 == 0 else col2:
                    updated_labels[field] = st.text_input(
                        field.replace('_', ' ').title(),
                        value=labels_dict.get(field, ""),
                        key=f"{category}_{field}"
                    )

    # Custom labels section
    with st.expander("Add Custom Labels"):
        custom_label_key = st.text_input("New Label Name")
        custom_label_value = st.text_input("Label Value")
        if custom_label_key and custom_label_value:
            updated_labels[custom_label_key] = custom_label_value

    # Save button
    if st.button("Save Resume and Information"):
        if uploaded_file is not None or existing_resume is not None:
            try:
                # Convert labels dictionary to JSON string
                labels_json = json.dumps(updated_labels)
                
                # Prepare content and filename
                content = resume_content if uploaded_file is not None else existing_resume['content']
                filename = uploaded_file.name if uploaded_file is not None else existing_resume['filename']
                
                # Save resume metadata to database
                conn.execute(
                    """
                    INSERT OR REPLACE INTO resumes (user, filename, labels, content) 
                    VALUES (?, ?, ?, ?)
                    """,
                    (user, filename, labels_json, content)
                )
                conn.commit()
                st.success("Resume and information saved successfully!")
            except Exception as e:
                st.error(f"Error saving resume: {str(e)}")
        else:
            st.warning("Please upload a resume first.")

    conn.close()

# Remove the function call at the bottom
# The function will be called by the main app when needed 