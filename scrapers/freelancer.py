from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import random
import logging
from models import Job
from urllib.parse import urljoin

class FreelancerScraper:
    def __init__(self, storage, query='web development', proxy=None):
        self.storage = storage
        self.query = query.replace(' ', '+')
        self.base_url = 'https://www.freelancer.com/jobs/'
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
                url = f"{self.base_url}?keyword={self.query}&page={page+1}"
                logging.info(f"Scraping Freelancer page {page+1}: {url}")
                for attempt in range(3):
                    try:
                        driver.get(url)
                        time.sleep(random.uniform(3, 5))
                        soup = BeautifulSoup(driver.page_source, 'html.parser')
                        jobs_found = 0
                        for job in soup.select('.JobSearchCard-item'):
                            title = job.select_one('.JobSearchCard-primary-heading-link') and job.select_one('.JobSearchCard-primary-heading-link').text.strip()
                            description = job.select_one('.JobSearchCard-primary-description') and job.select_one('.JobSearchCard-primary-description').text.strip()
                            link = job.select_one('a') and urljoin(self.base_url, job.select_one('a')['href'])
                            company = job.select_one('.JobSearchCard-primary-heading-meta') and job.select_one('.JobSearchCard-primary-heading-meta').text.strip()
                            if title and link:
                                job_data = Job(
                                    title=title,
                                    description=description or '',
                                    link=link,
                                    company=company,
                                    source='Freelancer'
                                )
                                self.storage.add_job(job_data)
                                jobs_found += 1
                        logging.info(f"Freelancer page {page+1}: {jobs_found} jobs found")
                        break
                    except Exception as e:
                        logging.warning(f"Freelancer page {page+1} attempt {attempt+1} failed: {e}")
                        time.sleep(2)
                else:
                    logging.error(f"Freelancer page {page+1} failed after 3 attempts")
        except Exception as e:
            logging.error(f"Freelancer scraping error: {e}")
        finally:
            driver.quit() 