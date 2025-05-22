import sys
import os
import uuid
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from job_applier import apply_to_job

import streamlit as st
import sqlite3
import pandas as pd
import json
from auth import get_current_user

RESUME_DIR = "resumes"  # Directory where resume files are stored

def get_resumes(conn, user):
    df = pd.read_sql_query("SELECT filename, labels FROM resumes WHERE user = ?", conn, params=(user,))
    resumes = []
    for _, row in df.iterrows():
        try:
            labels = json.loads(row['labels'])
        except Exception:
            labels = {}
        resumes.append({"filename": row['filename'], "labels": labels})
    return resumes

def applications_page():
    st.header("Automated Job Applications")
    user = get_current_user()
    conn = sqlite3.connect("jobs.db")

    # Load jobs
    jobs_df = pd.read_sql_query("SELECT id, title, company, location, link, source FROM jobs ORDER BY timestamp DESC", conn)
    if jobs_df.empty:
        st.info("No jobs found in the database.")
        return

    # Load resumes
    resumes = get_resumes(conn, user)
    if not resumes:
        st.warning("Please upload a resume in the Resume Manager first.")
        return

    # Job selection
    st.subheader("Select Jobs to Apply To")
    jobs_df['select'] = False
    selected = st.data_editor(
        jobs_df[['select', 'title', 'company', 'location', 'source', 'link']],
        use_container_width=True,
        column_config={"select": st.column_config.CheckboxColumn("Apply?")},
        disabled=["title", "company", "location", "source", "link"],
        key="job_applications_data_editor"
    )
    selected_jobs = jobs_df[selected['select']]

    # Resume selection
    st.subheader("Select Resume/Info Set")
    resume_filenames = [r['filename'] for r in resumes]
    selected_resume_idx = st.selectbox("Choose resume/info set to use for all applications:", range(len(resume_filenames)), format_func=lambda i: resume_filenames[i])
    selected_resume = resumes[selected_resume_idx]
    resume_path = os.path.join(RESUME_DIR, selected_resume['filename'])

    # Credentials input
    st.subheader("Enter Your Login Credentials (Not stored)")
    with st.expander("LinkedIn Credentials"):
        linkedin_email = st.text_input("LinkedIn Email", type="default")
        linkedin_password = st.text_input("LinkedIn Password", type="password")
    with st.expander("Wuzzuf Credentials"):
        wuzzuf_email = st.text_input("Wuzzuf Email", type="default")
        wuzzuf_password = st.text_input("Wuzzuf Password", type="password")
    with st.expander("Freelancer Credentials"):
        freelancer_email = st.text_input("Freelancer Email", type="default")
        freelancer_password = st.text_input("Freelancer Password", type="password")

    credentials = {
        'linkedin_email': linkedin_email,
        'linkedin_password': linkedin_password,
        'wuzzuf_email': wuzzuf_email,
        'wuzzuf_password': wuzzuf_password,
        'freelancer_email': freelancer_email,
        'freelancer_password': freelancer_password,
    }

    # Application status table
    if 'application_status' not in st.session_state:
        st.session_state['application_status'] = []

    if st.button("Apply to Selected Jobs"):
        status_list = []
        for _, job in selected_jobs.iterrows():
            success, message = apply_to_job(job, resume_path, selected_resume['labels'], credentials)
            status_list.append({
                "Job Title": job['title'],
                "Company": job['company'],
                "Status": "Success" if success else "Failed",
                "Message": message
            })
        st.session_state['application_status'] = status_list
        st.success(f"Attempted to apply to {len(selected_jobs)} jobs.")

    # Show application status
    if st.session_state['application_status']:
        st.subheader("Application Status")
        st.dataframe(pd.DataFrame(st.session_state['application_status']))

    conn.close()

# # Only run if this is the main page
# applications_page()
