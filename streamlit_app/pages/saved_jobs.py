import streamlit as st
import pandas as pd
import sqlite3
from auth import get_current_user

def saved_jobs_page():
    st.header("Saved Jobs")
    user = get_current_user()
    conn = sqlite3.connect("jobs.db")
    
    # Get saved jobs for this user
    saved_jobs_query = """
        SELECT jobs.* FROM jobs
        JOIN saved_jobs ON jobs.id = saved_jobs.job_id
        WHERE saved_jobs.user = ?
    """
    saved_jobs_df = pd.read_sql_query(saved_jobs_query, conn, params=(user,))

    if saved_jobs_df.empty:
        st.write("No saved jobs found.")
    else:
        for idx, row in saved_jobs_df.iterrows():
            with st.expander(f"{row['title']} ({row['source']})"):
                st.write(row['description'])
                st.write(f"[View Job Posting]({row['link']})")
                st.button("Apply Now", key=f"apply_{row['id']}")

    conn.close()

# Call the function to render the page
saved_jobs_page() 