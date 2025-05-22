import streamlit as st
import pandas as pd
import sqlite3
from auth import get_current_user
from datetime import datetime

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

    # Advanced Filters
    with st.expander("Advanced Search Options", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            title_filter = st.text_input("Job Title")
            # Multi-source selection
            all_sources = sorted(df["source"].unique().tolist())
            source_filter = st.multiselect("Source(s)", ["All"] + all_sources, default=["All"])
        with col2:
            company_filter = st.text_input("Company")
            location_filter = st.text_input("Location")
        with col3:
            description_filter = st.text_input("Description")
            link_filter = st.text_input("Link")
        # Creative timestamp filter (date range slider)
        if "timestamp" in df.columns:
            parsed_timestamps = pd.to_datetime(df["timestamp"], errors="coerce", format='mixed')
            min_date = parsed_timestamps.min()
            max_date = parsed_timestamps.max()
            # Convert to Python datetime
            min_date = min_date.to_pydatetime() if hasattr(min_date, "to_pydatetime") else min_date
            max_date = max_date.to_pydatetime() if hasattr(max_date, "to_pydatetime") else max_date
            date_range = st.slider(
                "Date Range (Timestamp)",
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date),
                format="YYYY-MM-DD"
            )
        else:
            date_range = None

    filtered = df.copy()
    if title_filter:
        filtered = filtered[filtered["title"].str.contains(title_filter, case=False, na=False)]
    if company_filter:
        filtered = filtered[filtered["description"].str.contains(company_filter, case=False, na=False)]
    # Multi-source filter
    if source_filter and "All" not in source_filter:
        filtered = filtered[filtered["source"].isin(source_filter)]
    if location_filter:
        if "location" in filtered.columns:
            filtered = filtered[filtered["location"].str.contains(location_filter, case=False, na=False)]
    if description_filter:
        filtered = filtered[filtered["description"].str.contains(description_filter, case=False, na=False)]
    if link_filter:
        filtered = filtered[filtered["link"].str.contains(link_filter, case=False, na=False)]
    if date_range and "timestamp" in filtered.columns:
        filtered["timestamp"] = pd.to_datetime(filtered["timestamp"], errors="coerce", format='mixed')
        filtered = filtered[(filtered["timestamp"] >= date_range[0]) & (filtered["timestamp"] <= date_range[1])]

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