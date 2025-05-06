import streamlit as st
import pandas as pd
import sqlite3


def analytics_page():
    st.header("Analytics")
    conn = sqlite3.connect("jobs.db")

    # Example analytics
    st.subheader("Total Jobs Scraped")
    total_jobs = pd.read_sql_query("SELECT COUNT(*) FROM jobs", conn).iloc[0, 0]
    st.write(f"Total jobs scraped: {total_jobs}")

    st.subheader("Jobs by Source")
    jobs_by_source = pd.read_sql_query("SELECT source, COUNT(*) as count FROM jobs GROUP BY source", conn)
    st.bar_chart(jobs_by_source.set_index('source'))

    st.subheader("Jobs by Title")
    jobs_by_title = pd.read_sql_query("SELECT title, COUNT(*) as count FROM jobs GROUP BY title ORDER BY count DESC LIMIT 10", conn)
    st.bar_chart(jobs_by_title.set_index('title'))

    st.subheader("Jobs by Company")
    jobs_by_company = pd.read_sql_query("SELECT company, COUNT(*) as count FROM jobs GROUP BY company ORDER BY count DESC LIMIT 10", conn)
    st.bar_chart(jobs_by_company.set_index('company'))

    st.subheader("Jobs by Location")
    jobs_by_location = pd.read_sql_query("SELECT location, COUNT(*) as count FROM jobs GROUP BY location ORDER BY count DESC LIMIT 10", conn)
    st.bar_chart(jobs_by_location.set_index('location'))

    # Add more analytics as needed
    # Placeholder for additional analytics
    for i in range(6, 21):
        st.subheader(f"Analytics {i}")
        st.write("Description and visualization for analytics.")

    conn.close()

# Call the function to render the page
analytics_page() 