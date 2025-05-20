"""
WeWorkRemotely crawler for the Job Crawler application.
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
import requests
import xml.etree.ElementTree as ET

class WeWorkRemotelyScraper:
    def __init__(self, storage, query='software engineer', proxy=None):
        self.storage = storage
        self.query = query
        self.base_url = 'https://weworkremotely.com'
        self.search_url = f'{self.base_url}/remote-jobs/search?term={self.query.replace(" ", "+")}'
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
                url = self.search_url + (f'&page={page+1}' if page > 0 else '')
                logging.info(f"Scraping WeWorkRemotely search page {page+1}: {url}")
                for attempt in range(3):
                    try:
                        driver.get(url)
                        time.sleep(random.uniform(3, 5))
                        soup = BeautifulSoup(driver.page_source, 'html.parser')
                        jobs_found = 0
                        job_listings = soup.select('li.new-listing-container')
                        for job in job_listings:
                            link_elem = job.select_one('a[href^="/remote-jobs/"]')
                            title_elem = job.select_one('h4.new-listing__header__title')
                            company_elem = job.select_one('p.new-listing__company-name')
                            location_elem = job.select_one('p.new-listing__company-headquarters')
                            categories_elem = job.select('div.new-listing__categories p.new-listing__categories__category')
                            if link_elem and title_elem and company_elem:
                                link = urljoin(self.base_url, link_elem['href'])
                                title = title_elem.text.strip()
                                company = company_elem.text.strip()
                                location = location_elem.text.strip() if location_elem else 'Remote'
                                categories = ', '.join([cat.text.strip() for cat in categories_elem]) if categories_elem else ''
                                # Optionally, visit the job detail page for full description
                                description = self._get_job_description(driver, link)
                                job_data = Job(
                                    title=title,
                                    description=description,
                                    link=link,
                                    company=company,
                                    source='WeWorkRemotely',
                                    location=location
                                )
                                self.storage.add_job(job_data)
                                jobs_found += 1
                        logging.info(f"WeWorkRemotely page {page+1}: {jobs_found} jobs found")
                        break
                    except Exception as e:
                        logging.warning(f"WeWorkRemotely page {page+1} attempt {attempt+1} failed: {e}")
                        time.sleep(2)
                else:
                    logging.error(f"WeWorkRemotely page {page+1} failed after 3 attempts")
        except Exception as e:
            logging.error(f"WeWorkRemotely scraping error: {e}")
        finally:
            driver.quit()

    def _get_job_description(self, driver, job_url):
        try:
            driver.get(job_url)
            time.sleep(random.uniform(2, 4))
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            desc_elem = soup.select_one('div.listing-container')
            if desc_elem:
                return desc_elem.text.strip()
            return ''
        except Exception as e:
            logging.warning(f"Failed to get job description from {job_url}: {e}")
            return ''
