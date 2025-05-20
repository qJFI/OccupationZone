"""
RemoteOK crawler for the Job Crawler application.
"""

import logging
import re
import json
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin
from models import Job
import time
import random

class RemoteOKScraper:
    def __init__(self, storage, query='software engineer', proxy=None):
        self.storage = storage
        self.query = query.replace(' ', '-')
        self.base_url = 'https://remoteok.com/remote-'
        self.options = Options()
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        self.options.add_argument('--disable-webrtc')
        if proxy:
            self.options.add_argument(f'--proxy-server={proxy}')

    def scrape(self, max_pages=1):
        driver = webdriver.Chrome(options=self.options)
        try:
            for page in range(max_pages):
                url = f"{self.base_url}{self.query}-jobs?page={page+1}"
                logging.info(f"Scraping RemoteOK page {page+1}: {url}")
                for attempt in range(3):
                    try:
                        driver.get(url)
                        time.sleep(random.uniform(3, 5))
                        soup = BeautifulSoup(driver.page_source, 'html.parser')
                        jobs_found = 0
                        job_listings = soup.select('tr.job')
                        for job in job_listings:
                            title_elem = job.select_one('h2')
                            company_elem = job.select_one('h3')
                            link = job.get('data-href')
                            if title_elem and company_elem and link:
                                title = title_elem.text.strip()
                                company = company_elem.text.strip()
                                full_link = urljoin('https://remoteok.com', link)
                                location = 'Remote'
                                description_elem = job.select_one('td.description')
                                description = description_elem.text.strip() if description_elem else f"Company: {company}, Location: {location}"
                                job_data = Job(
                                    title=title,
                                    description=description,
                                    link=full_link,
                                    company=company,
                                    source='RemoteOK',
                                    location=location
                                )
                                self.storage.add_job(job_data)
                                jobs_found += 1
                        logging.info(f"RemoteOK page {page+1}: {jobs_found} jobs found")
                        break
                    except Exception as e:
                        logging.warning(f"RemoteOK page {page+1} attempt {attempt+1} failed: {e}")
                        time.sleep(2)
                else:
                    logging.error(f"RemoteOK page {page+1} failed after 3 attempts")
        except Exception as e:
            logging.error(f"RemoteOK scraping error: {e}")
        finally:
            driver.quit()
