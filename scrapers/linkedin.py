from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random
import logging
from models import Job

class LinkedInScraper:
    def __init__(self, storage, query='software engineer', proxy=None):
        self.storage = storage
        self.query = query.replace(' ', '%20')
        self.base_url = 'https://www.linkedin.com/jobs/search/'
        self.options = Options()
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        self.options.add_argument('--disable-webrtc')
        if proxy:
            self.options.add_argument(f'--proxy-server={proxy}')

    def scrape(self, max_pages=15):
        driver = webdriver.Chrome(options=self.options)
        try:
            for page in range(max_pages):
                url = f"{self.base_url}?keywords={self.query}&start={page*25}"
                logging.info(f"Scraping LinkedIn page {page+1}: {url}")
                driver.get(url)
                time.sleep(random.uniform(3, 5))
                try:
                    load_more = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Show more')]"))
                    )
                    load_more.click()
                    time.sleep(2)
                except:
                    pass
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                jobs_found = 0
                for job in soup.select('.job-search-card'):
                    title = job.select_one('.base-search-card__title') and job.select_one('.base-search-card__title').text.strip() or 'Unknown'
                    description = job.select_one('.job-search-card__snippet') and job.select_one('.job-search-card__snippet').text.strip() or 'Unknown'
                    link = job.select_one('a') and job.select_one('a')['href'] or 'Unknown'
                    company = job.select_one('.base-search-card__subtitle') and job.select_one('.base-search-card__subtitle').text.strip() or 'Unknown'
                    location = job.select_one('.job-search-card__location') and job.select_one('.job-search-card__location').text.strip() or 'Unknown'
                    if title and link and company and location:
                        job_data = Job(
                            title=title,
                            description=description,
                            link=link,
                            company=company,
                            location=location,
                            source='LinkedIn'
                        )
                        self.storage.add_job(job_data)
                        jobs_found += 1
                logging.info(f"LinkedIn page {page+1}: {jobs_found} jobs found")
        except Exception as e:
            logging.error(f"LinkedIn scraping error: {e}")
        finally:
            driver.quit() 