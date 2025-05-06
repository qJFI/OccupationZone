import logging
from models import Job, DataStorage
from utils import setup_logging, deduplicate_jobs
from scrapers.linkedin import LinkedInScraper
from scrapers.freelancer import FreelancerScraper
from scrapers.wuzzuf import WuzzufScraper

# Configure logging
setup_logging()

# Main function to run scrapers
def main():
    storage = DataStorage(output_format='sqlite', db_name='jobs.db')

    # Remove duplicates at the start (keep the first occurrence by timestamp)
    deduplicate_jobs(storage.conn)

    # Run Selenium for LinkedIn, Freelancer, and Wuzzuf
    linkedin_scraper = LinkedInScraper(storage, query='software engineer')
    linkedin_scraper.scrape(max_pages=15)
    
    freelancer_scraper = FreelancerScraper(storage, query='web development')
    freelancer_scraper.scrape(max_pages=15)
    
    wuzzuf_scraper = WuzzufScraper(storage, query='software engineer')
    wuzzuf_scraper.scrape(max_pages=15)

    # Save data
    storage.save()

    # Remove duplicates at the end (keep the first occurrence by timestamp)
    deduplicate_jobs(storage.conn)

    # Log job counts per source
    import pandas as pd
    df_counts = pd.read_sql_query("SELECT source, COUNT(*) as count FROM jobs GROUP BY source", storage.conn)
    logging.info(f"Job counts by source:\n{df_counts}")

    # Check for duplicates
    df_duplicates = pd.read_sql_query("SELECT link, COUNT(*) as count FROM jobs GROUP BY link HAVING count > 1", storage.conn)
    logging.info(f"Duplicates found:\n{df_duplicates}")

    # Check for missing fields
    df_missing = pd.read_sql_query("SELECT * FROM jobs WHERE title IS NULL OR link IS NULL", storage.conn)
    logging.info(f"Jobs with missing fields:\n{df_missing}")

if __name__ == '__main__':
    main()