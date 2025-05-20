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
    def __init__(self, storage, query='software engineer', proxy=None, sitemap_url='https://weworkremotely.com/sitemap.xml'):
        self.storage = storage
        self.query = query.lower()
        self.sitemap_url = sitemap_url
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
        # Step 1: Parse sitemap for job URLs
        job_urls = self._get_job_urls_from_sitemap()
        if not job_urls:
            logging.error("No job URLs found in sitemap.")
            return
        logging.info(f"Found {len(job_urls)} job URLs in sitemap.")
        
        # Step 2: Filter by query if provided
        filtered_urls = [url for url in job_urls if self.query in url.lower()]
        if not filtered_urls:
            filtered_urls = job_urls  # fallback to all if none match
        logging.info(f"Filtered to {len(filtered_urls)} job URLs matching query '{self.query}'.")

        # Step 3: Visit each job URL and extract details
        driver = webdriver.Chrome(options=self.options)
        try:
            jobs_found = 0
            for url in filtered_urls[:max_pages]:
                logging.info(f"Scraping job: {url}")
                for attempt in range(3):
                    try:
                        driver.get(url)
                        time.sleep(random.uniform(2, 4))
                        soup = BeautifulSoup(driver.page_source, 'html.parser')
                        title_elem = soup.select_one('h1.listing-header-container__title')
                        if not title_elem:
                            title_elem = soup.select_one('h1')
                        title = title_elem.text.strip() if title_elem else 'Unknown'
                        company_elem = soup.select_one('div.listing-header-container__company span')
                        if not company_elem:
                            company_elem = soup.select_one('div.company-card h2.company-name')
                        company = company_elem.text.strip() if company_elem else 'Unknown'
                        location_elem = soup.select_one('span.region')
                        location = location_elem.text.strip() if location_elem else 'Remote'
                        description_elem = soup.select_one('div.listing-container')
                        description = description_elem.text.strip() if description_elem else ''
                        job_data = Job(
                            title=title,
                            description=description,
                            link=url,
                            company=company,
                            source='WeWorkRemotely',
                            location=location
                        )
                        self.storage.add_job(job_data)
                        jobs_found += 1
                        break
                    except Exception as e:
                        logging.warning(f"Job scrape attempt {attempt+1} failed for {url}: {e}")
                        time.sleep(2)
                else:
                    logging.error(f"Failed to scrape job after 3 attempts: {url}")
            logging.info(f"Total jobs scraped from sitemap: {jobs_found}")
        except Exception as e:
            logging.error(f"WeWorkRemotely sitemap scraping error: {e}")
        finally:
            driver.quit()

    def _get_job_urls_from_sitemap(self):
        try:
            driver = webdriver.Chrome(options=self.options)
            try:
                driver.get(self.sitemap_url)
                time.sleep(2)
                xml_content = driver.page_source
            finally:
                driver.quit()
            root = ET.fromstring(xml_content)
            # Support both <url> and <item> tags
            urls = []
            for tag in ['url', 'item']:
                for elem in root.findall(f'.//{{*}}{tag}'):
                    loc = elem.find('{*}loc')
                    if loc is not None and '/listings/' in loc.text:
                        urls.append(loc.text)
            return urls
        except Exception as e:
            logging.error(f"Failed to parse sitemap with Selenium: {e}")
            return []
