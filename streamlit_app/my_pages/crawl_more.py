import streamlit as st
import subprocess
import sys
import os
import importlib

CRAWLER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../crawler.py'))

SCRAPER_OPTIONS = [
    ("LinkedIn", "LinkedInScraper"),
    ("Freelancer", "FreelancerScraper"),
    ("Wuzzuf", "WuzzufScraper"),
    ("RemoteOK", "RemoteOKScraper"),
    ("WeWorkRemotely", "WeWorkRemotelyScraper"),
    ("Upwork", "UpworkScraper"),
    ("PeoplePerHour", "PeoplePerHourScraper"),
]


def crawl_more_page():
    st.title("Crawl More Job Boards")
    st.write("Configure and run job crawlers with custom options.")

    query = st.text_input("Search Query", value="software")
    max_pages = st.number_input("Max Pages per Crawler", min_value=1, max_value=20, value=5)
    active_crawlers = st.multiselect(
        "Select Active Crawlers",
        options=[name for name, _ in SCRAPER_OPTIONS],
        default=[name for name, _ in SCRAPER_OPTIONS],
    )
    push_to_db = st.checkbox("Push results to database (jobs.db)?", value=True)
    run_crawl = st.button("Run Crawl")

    if run_crawl:
        st.info("Crawling in progress...")
        # Build command to run crawler.py with arguments
        selected_scrapers = [class_name for name, class_name in SCRAPER_OPTIONS if name in active_crawlers]
        # We'll use environment variables for options
        env = os.environ.copy()
        env['CRAWL_QUERY'] = query
        env['CRAWL_MAX_PAGES'] = str(max_pages)
        env['CRAWL_SCRAPERS'] = ','.join(selected_scrapers)
        env['CRAWL_PUSH_DB'] = '1' if push_to_db else '0'
        # Run crawler.py as subprocess and capture output
        with st.spinner("Running crawler..."):
            result = subprocess.run([sys.executable, CRAWLER_PATH], capture_output=True, text=True, env=env)
        st.subheader("Crawler Output:")
        st.code(result.stdout)
        if result.stderr:
            st.subheader("Errors:")
            st.code(result.stderr, language="bash") 