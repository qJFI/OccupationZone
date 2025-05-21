import logging
from models import Job, DataStorage
from utils import setup_logging, deduplicate_jobs
from scrapers.linkedin import LinkedInScraper
from scrapers.freelancer import FreelancerScraper
from scrapers.wuzzuf import WuzzufScraper
from scrapers.remoteok import RemoteOKScraper
from scrapers.weworkremotely import WeWorkRemotelyScraper
from scrapers.upwork import UpworkScraper
from scrapers.peopleperhour import PeoplePerHourScraper
import concurrent.futures
from collections import defaultdict
import pandas as pd

# Configure logging
setup_logging()

# Helper to run a scraper with its own DataStorage
def run_scraper(scraper_class, query, db_name):
    storage = DataStorage(output_format='sqlite', db_name=db_name)
    scraper = scraper_class(storage, query=query)
    scraper.scrape(max_pages=5)
    # Optionally, call storage.save() if needed (it just logs for sqlite)
    del storage  # Ensure connection is closed
    return scraper_class.__name__  # For logging

# Main function to run scrapers
def main():
    db_name = 'jobs.db'
    query = 'software'

    # Store initial job counts
    temp_storage = DataStorage(output_format='sqlite', db_name=db_name)
    initial_counts = pd.read_sql_query(
        "SELECT source, COUNT(*) as count FROM jobs GROUP BY source", 
        temp_storage.conn
    ).set_index('source')['count'].to_dict()
    del temp_storage

    # Remove duplicates at the start (keep the first occurrence by timestamp)
    temp_storage = DataStorage(output_format='sqlite', db_name=db_name)
    deduplicate_jobs(temp_storage.conn)
    del temp_storage

    # List of scraper classes
    scraper_classes = [
        LinkedInScraper,
        FreelancerScraper,
        WuzzufScraper,
        RemoteOKScraper,
        WeWorkRemotelyScraper,
        UpworkScraper,
        PeoplePerHourScraper
    ]

    # Run scrapers in parallel, each with its own DataStorage/connection
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(scraper_classes)) as executor:
        futures = {executor.submit(run_scraper, scraper_class, query, db_name): scraper_class.__name__ for scraper_class in scraper_classes}
        for future in concurrent.futures.as_completed(futures):
            scraper_name = futures[future]
            try:
                future.result()
                logging.info(f"{scraper_name} completed successfully")
            except Exception as e:
                logging.error(f"{scraper_name} generated an exception: {e}")

    # After all threads are done, deduplicate and summarize in main thread
    storage = DataStorage(output_format='sqlite', db_name=db_name)
    deduplicate_jobs(storage.conn)

    # Print summary of jobs found in this run
    print("\n========== NEW JOBS FOUND IN THIS RUN ==========")
    job_counts = pd.read_sql_query("SELECT source, COUNT(*) as count FROM jobs GROUP BY source", storage.conn)
    total_new_jobs = 0
    print("\nBreakdown by source:")
    for _, row in job_counts.iterrows():
        source = row['source']
        count = row['count']
        new_jobs = count - initial_counts.get(source, 0)
        total_new_jobs += max(new_jobs, 0)
        print(f"  {source}: {max(new_jobs, 0)} new jobs")
    print(f"\nTotal new jobs found: {total_new_jobs}")
    print("=============================================")

    # Log job counts per source
    logging.info(f"Job counts by source:\n{job_counts}")

    # Check for duplicates
    df_duplicates = pd.read_sql_query("SELECT link, COUNT(*) as count FROM jobs GROUP BY link HAVING count > 1", storage.conn)
    logging.info(f"Duplicates found:\n{df_duplicates}")

    # Check for missing fields (now everything should be at least 'non')
    df_missing = pd.read_sql_query("SELECT * FROM jobs WHERE title IS NULL OR description IS NULL OR link IS NULL OR company IS NULL OR source IS NULL OR location IS NULL", storage.conn)
    logging.info(f"Jobs with missing fields:\n{df_missing}")

    del storage

if __name__ == '__main__':
    main()