import logging
from models import Job, DataStorage
from utils import setup_logging, deduplicate_jobs
from scrapers.linkedin import LinkedInScraper
from scrapers.freelancer import FreelancerScraper
from scrapers.wuzzuf import WuzzufScraper
from scrapers.remoteok import RemoteOKScraper
from scrapers.weworkremotely import WeWorkRemotelyScraper
from scrapers.upwork import UpworkScraper

# Configure logging
setup_logging()

# Main function to run scrapers
def main():
    storage = DataStorage(output_format='sqlite', db_name='jobs.db')

    # Remove duplicates at the start (keep the first occurrence by timestamp)
    deduplicate_jobs(storage.conn)

    query = 'android'

    # # Run Selenium for LinkedIn, Freelancer, Wuzzuf, RemoteOK, WeWorkRemotely, and Upwork
    linkedin_scraper = LinkedInScraper(storage, query=query)
    linkedin_scraper.scrape(max_pages=1)
    
    freelancer_scraper = FreelancerScraper(storage, query=query)
    freelancer_scraper.scrape(max_pages=1)
    
    wuzzuf_scraper = WuzzufScraper(storage, query=query)
    wuzzuf_scraper.scrape(max_pages=1)

    remoteok_scraper = RemoteOKScraper(storage, query=query)
    remoteok_scraper.scrape(max_pages=1)

    weworkremotely_scraper = WeWorkRemotelyScraper(storage, query=query)
    weworkremotely_scraper.scrape(max_pages=1)

    upwork_scraper = UpworkScraper(storage, query=query)
    upwork_scraper.scrape(max_pages=1)

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

    # Check for missing fields (now everything should be at least 'non')
    df_missing = pd.read_sql_query("SELECT * FROM jobs WHERE title IS NULL OR description IS NULL OR link IS NULL OR company IS NULL OR source IS NULL OR location IS NULL", storage.conn)
    logging.info(f"Jobs with missing fields:\n{df_missing}")

if __name__ == '__main__':
    main()