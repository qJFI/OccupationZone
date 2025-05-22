import streamlit as st
import pandas as pd
import sqlite3
from auth import get_current_user
from datetime import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.job_filters import create_filter_ui, apply_filters

def job_search_page():
    st.header("Job Search")
    user = get_current_user()
    conn = sqlite3.connect("jobs.db")
    df = pd.read_sql_query("SELECT * FROM jobs", conn)
    # Create saved_jobs table if not exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS saved_jobs (
            user TEXT,
            job_id TEXT,
            PRIMARY KEY (user, job_id)
        )
    """)

    # Handle save job action
    if "save_job_clicked" not in st.session_state:
        st.session_state["save_job_clicked"] = None

    # Use the shared filtering UI
    filters = create_filter_ui(df)
    
    # Apply filters
    filtered = apply_filters(df, filters)

    st.write(f"{len(filtered)} jobs found.")
    max_jobs = 20
    total_pages = (len(filtered) - 1) // max_jobs + 1 if len(filtered) > 0 else 1
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
    start_idx = (page - 1) * max_jobs
    end_idx = start_idx + max_jobs
    show_df = filtered.iloc[start_idx:end_idx]

    # Get saved jobs for this user
    saved_job_ids = set(row[0] for row in conn.execute("SELECT job_id FROM saved_jobs WHERE user = ?", (user,)))

    for idx, row in show_df.iterrows():
        with st.expander(f"{row['title']} ({row['source']})"):
            st.write(row['description'])
            st.write(f"[View Job Posting]({row['link']})")
            is_saved = row['id'] in saved_job_ids
            if is_saved:
                st.success("Saved")
            else:
                if st.button("Save Job", key=f"save_{row['id']}"):
                    conn.execute("INSERT OR IGNORE INTO saved_jobs (user, job_id) VALUES (?, ?)", (user, row['id']))
                    conn.commit()
                    st.session_state["save_job_clicked"] = row['id']
                    st.rerun()
            st.button("Apply Now", key=f"apply_{row['id']}")
    st.write(f"Page {page} of {total_pages}")
    conn.close() 