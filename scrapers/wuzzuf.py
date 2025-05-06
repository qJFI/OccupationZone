from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random
import logging
from urllib.parse import urljoin
from models import Job

class WuzzufScraper:
    def __init__(self, storage, query='software engineer', proxy=None):
        self.storage = storage
        self.query = query.replace(' ', '+')
        self.base_url = 'https://wuzzuf.net/search/jobs/'
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
                url = f"{self.base_url}?q={self.query}&start={page}"
                logging.info(f"Scraping Wuzzuf page {page+1}: {url}")
                for attempt in range(3):
                    try:
                        driver.get(url)
                        for _ in range(3):
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            time.sleep(2)
                        WebDriverWait(driver, 20).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.css-1gatmva.e1v1l3u10"))
                        )
                        soup = BeautifulSoup(driver.page_source, 'html.parser')
                        job_cards = soup.select("div.css-1gatmva.e1v1l3u10")
                        logging.info(f"Wuzzuf page {page+1}: Found {len(job_cards)} job cards")
                        if job_cards:
                            logging.info(f"Sample job card class: {job_cards[0].get('class')}")
                        jobs_found = 0
                        for job in job_cards:
                            title_elem = job.select_one("h2.css-m604qf a")
                            title = title_elem and title_elem.text.strip()
                            company = job.select_one("a.css-17s97q8") and job.select_one("a.css-17s97q8").text.strip()
                            location = job.select_one("span.css-5wys0k") and job.select_one("span.css-5wys0k").text.strip()
                            job_type = job.select_one("span.css-1ve4b75.eoyjyou0") and job.select_one("span.css-1ve4b75.eoyjyou0").text.strip()
                            site = job.select_one("span.css-o1vzmt.eoyjyou0") and job.select_one("span.css-o1vzmt.eoyjyou0").text.strip()
                            description = f"Company: {company or 'N/A'}, Location: {location or 'N/A'}, Type: {job_type or 'N/A'}, Site: {site or 'N/A'}"
                            link = title_elem and urljoin(self.base_url, title_elem['href'])
                            if title and link:
                                job_data = Job(
                                    title=title,
                                    description=description,
                                    link=link,
                                    source='Wuzzuf'
                                )
                                self.storage.add_job(job_data)
                                jobs_found += 1
                        logging.info(f"Wuzzuf page {page+1}: {jobs_found} jobs extracted")
                        break
                    except Exception as e:
                        logging.warning(f"Wuzzuf page {page+1} attempt {attempt+1} failed: {e}")
                        time.sleep(2)
                else:
                    logging.error(f"Wuzzuf page {page+1} failed after 3 attempts")
        except Exception as e:
            logging.error(f"Wuzzuf scraping error: {e}")
        finally:
            driver.quit() 