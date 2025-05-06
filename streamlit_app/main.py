import streamlit as st
from streamlit_option_menu import option_menu
from auth import login, logout, get_current_user

st.set_page_config(page_title="Job Application Manager", layout="wide")

# User authentication
user = get_current_user()
if not user:
    login()
    st.stop()

# Sidebar navigation
with st.sidebar:
    selected = option_menu(
        "Main Menu",
        ["Job Search", "Saved Jobs", "Applications", "Resume Manager", "Analytics", "Settings"],
        icons=["search", "bookmark", "check2-circle", "file-earmark-person", "bar-chart", "gear"],
        menu_icon="cast",
        default_index=0,
    )
    st.write(f"Logged in as: {user}")
    if st.button("Logout"):
        logout()
        st.experimental_rerun()

# Page routing
if selected == "Job Search":
    from pages.job_search import job_search_page
    job_search_page()
elif selected == "Saved Jobs":
    from pages.saved_jobs import saved_jobs_page
    saved_jobs_page()
elif selected == "Applications":
    from pages.applications import applications_page
    applications_page()
elif selected == "Resume Manager":
    from pages.resume_manager import resume_manager_page
    resume_manager_page()
elif selected == "Analytics":
    from pages.analytics import analytics_page
    analytics_page()
elif selected == "Settings":
    from pages.settings import settings_page
    settings_page() 