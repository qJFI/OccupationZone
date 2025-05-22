import streamlit as st
from streamlit_option_menu import option_menu
from auth import login, logout, get_current_user

st.set_page_config(page_title="Job Application Manager", layout="wide")

# Inject custom CSS
st.markdown("""
    <style>
    .main .block-container {
        margin-top: 5rem;
        padding-top: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .css-18e3th9 {
        padding: 0 !important;
    }
    .st-emotion-cache-1v0mbdj.ef3psqc12 {
        width: 100% !important;
        max-width: 100% !important;
    }
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# Authentication
user = get_current_user()
if not user:
    login()
    st.stop()

# Navigation
selected = option_menu(
    menu_title="",  # appears inside navbar
    options=["Job Search", "Saved Jobs", "Applications", "Resume Manager", "Analytics", "Settings"],
    icons=["search", "bookmark", "check2-circle", "file-earmark-person", "bar-chart", "gear"],
    menu_icon="briefcase",
    default_index=0,
    orientation="horizontal"
)

st.write(f"Logged in as: {user}")
if st.button("Logout"):
    logout()
    st.rerun()

# Page router
if selected == "Job Search":
    from my_pages.job_search import job_search_page
    job_search_page()
elif selected == "Saved Jobs":
    from my_pages.saved_jobs import saved_jobs_page
    saved_jobs_page()
elif selected == "Applications":
    from my_pages.applications import applications_page
    applications_page()
elif selected == "Resume Manager":
    from my_pages.resume_manager import resume_manager_page
    resume_manager_page()
elif selected == "Analytics":
    from my_pages.analytics import analytics_page
    analytics_page()
elif selected == "Settings":
    from my_pages.settings import settings_page
    settings_page()
