import os
import sys
# Add project root to sys.path for absolute imports (more robust approach)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)  # Insert at beginning of path list for priority
import time
from datetime import datetime
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from scrapers.utils.job_helpers import parse_job_details
from scrapers.utils.database import create_db, connect_to_db
from scrapers.settings import config
from models import Job


# LOGGING

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Get paths
scriptdir = os.path.dirname(os.path.abspath(__file__))
logdir = os.path.join(scriptdir, 'log')
if not os.path.exists(logdir):
    os.makedirs(logdir)
mypath = os.path.join(logdir, 'upwork_best_matches_scraper.log')
# Create file handler which logs even DEBUG messages
fh = logging.FileHandler(mypath)
fh.setLevel(logging.DEBUG)
# Create console handler
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('[%(levelname)s. %(name)s, (line #%(lineno)d) - %(asctime)s] %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add handlers to logger
logger.addHandler(fh)
logger.addHandler(ch)


# FUNCTIONS

def get_driver_with_retry(max_attempts=3, chrome_path=None):
    for attempt in range(max_attempts):
        try:
            logger.info(f'Attempt #{attempt+1}/{max_attempts}')
            options = uc.ChromeOptions()
            options.headless = False
            if chrome_path:
                return uc.Chrome(options=options, browser_executable_path=chrome_path)
            else:
                return uc.Chrome(options=options)
        except Exception as e:
            logger.error(f"Failed to launch Chrome driver. Retrying...")
            logger.error(f"Error details: {e}")
    logger.error(f"All attempts failed within {max_attempts} attempts. Unable to launch Chrome driver.")
    logger.error("Make sure Google Chrome is installed and up to date. If Chrome is installed in a non-standard location, specify the path in the config as CHROME_PATH.")
    return None


class UpworkScraper:
    def __init__(self, storage, query='software engineer', proxy=None):
        self.storage = storage
        self.query = query
        self.proxy = proxy

    def login_to_upwork(self, driver):
        """Helper method to handle Upwork login process"""
        try:
            user_login_page = 'https://www.upwork.com/ab/account-security/login'
            logger.info(f'Navigating to `{user_login_page}`')
            driver.get(user_login_page)
            logger.info('Pausing for windows to fully load')
            time.sleep(25)

            logger.info('Switching to main window')
            all_windows = driver.window_handles
            driver.switch_to.window(all_windows[-1])

            logger.info('Submitting username')
            username_input = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located(
                    (By.XPATH,
                     "/html/body/div[4]/div/div/div/main/div/div/div[2]/div[2]/form/div/div/div[1]/div[3]/div/div/div/"
                     "div/input")
                )
            )
            username_input.send_keys(config.UPWORK_USERNAME)

            username_field = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located(
                    (By.XPATH,
                     "/html/body/div[4]/div/div/div/main/div/div/div[2]/div[2]/form/div/div/div[1]/div[3]/div/div/div/"
                     "div/input")
                )
            )
            username_field.send_keys(Keys.ENTER)

            logger.info('Submitting password')
            password_input = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located(
                    (By.XPATH,
                     "/html/body/div[4]/div/div/div/main/div/div/div[2]/div[2]/form/div/div/div[1]/div[3]/div/div/div"
                     "/input")
                )
            )
            password_input.send_keys(config.UPWORK_PASSWORD)

            password_field = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located(
                    (By.XPATH,
                     "/html/body/div[4]/div/div/div/main/div/div/div[2]/div[2]/form/div/div/div[1]/div[3]/div/div/div"
                     "/input")
                )
            )
            password_field.send_keys(Keys.ENTER)

            logger.info(f'Pausing for {getattr(config, "VERIFICATION_PAUSE", 10)} seconds for credentials verification')
            time.sleep(getattr(config, "VERIFICATION_PAUSE", 10))
            return True
        except Exception as e:
            logger.error(f"Failed to login: {e}")
            return False

    def scrape(self, max_pages=1):
        try:
            # First scrape best matches
            logger.info('Launching driver for best matches')
            chrome_path = getattr(config, 'CHROME_PATH', None)
            driver = get_driver_with_retry(max_attempts=getattr(config, 'MAX_ATTEMPTS', 3), chrome_path=chrome_path)

            if driver:
                # Login for best matches
                if not self.login_to_upwork(driver):
                    logger.error("Failed to login for best matches")
                    driver.quit()
                    return

                # Go to target url
                logger.info("Redirecting to Best Matches")
                driver.get('https://www.upwork.com/nx/find-work/best-matches')
                time.sleep(10)

                # Scroll down using keyboard actions
                logger.info('Scrolling down page')
                body = driver.find_elements('xpath', "/html/body")
                for i in range(0, 12):
                    body[-1].send_keys(Keys.PAGE_DOWN)
                    time.sleep(2)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                timeout_wait = 300

                # Wait for element to load
                logger.info(f'Waiting for element to load (max timeout set to {timeout_wait} seconds)...')
                wait = WebDriverWait(driver, timeout_wait)
                wait.until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div[4]/div/div/div/main/div[3]/div[4]')))

                # Get all text as a wall of text (including user's mini bio on the top-right panel)
                text = driver.find_elements('xpath', f'/html/body/div[4]/div/div/div/main/div[3]/div[4]')[-1].text
                # Get rid of the right panel
                text_1 = text.split(config.UPWORK_USER_NAME)[0]
                # Get rid of the top panel
                text_2 = text_1.split('Ordered by most relevant.')[-1]
                # Get all job posts
                job_posts = text_2.split('Posted')[1:]

                # Get urls
                job_links = driver.find_elements("xpath", "//a[contains(@href, '/jobs/')]")
                job_urls = [link.get_attribute("href") for link in job_links
                            if 'ontology_skill_uid' not in link.get_attribute("href")
                            and 'search/saved' not in link.get_attribute("href")
                            and 'search/jobs/saved' not in link.get_attribute("href")
                            ]

                # Scrape jobs
                print('Scraping jobs...')
                counter = 0
                logger.info(f"Adding jobs to database: {self.storage.db_name}")
                for j in job_posts:
                    job_details = parse_job_details(j.split('\n'))
                    job_id = job_details.get('job_id')
                    job_url = job_urls[counter].split('/?')[0]
                    
                    # Create a Job instance using the storage's schema
                    job = Job(
                        title=job_details.get('job_title', 'non'),
                        description=job_details.get('job_description', 'non'),
                        link=job_url,
                        company='Upwork',
                        source='Upwork',
                        timestamp=job_details.get('posted_date', datetime.now().isoformat()),
                        location='Remote'  # Upwork jobs are typically remote
                    )
                    # Add job to storage
                    self.storage.add_job(job)
                    counter += 1

                logger.info(f"Added {counter} jobs to the database")

                # Close the browser
                logger.info('Closing browser for best matches...')
                driver.quit()

                # Now scrape most recent jobs with a fresh login
                logger.info('Launching driver for most recent jobs')
                driver = get_driver_with_retry(max_attempts=getattr(config, 'MAX_ATTEMPTS', 3), chrome_path=chrome_path)
                if not driver:
                    logger.error("Couldn't load driver for most recent jobs")
                    return

                # Login again for most recent jobs
                if not self.login_to_upwork(driver):
                    logger.error("Failed to login for most recent jobs")
                    driver.quit()
                    return

                driver.get('https://www.upwork.com/nx/find-work/most-recent')
                time.sleep(10)
                logger.info('Scrolling down and scraping most recent jobs')
                body = driver.find_elements('xpath', "/html/body")
                # Initial scroll to load jobs
                for _ in range(12):
                    body[-1].send_keys(Keys.PAGE_DOWN)
                    time.sleep(2)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                # Scrape jobs on first load
                def extract_jobs_from_most_recent():
                    text = driver.find_elements('xpath', f'/html/body/div[4]/div/div/div/main/div[3]/div[4]')[-1].text
                    text_1 = text.split(config.UPWORK_USER_NAME)[0]
                    text_2 = text_1.split('Ordered by most relevant.')[-1]
                    job_posts = text_2.split('Posted')[1:]
                    job_links = driver.find_elements("xpath", "//a[contains(@href, '/jobs/')]")
                    job_urls = [link.get_attribute("href") for link in job_links
                                if 'ontology_skill_uid' not in link.get_attribute("href")
                                and 'search/saved' not in link.get_attribute("href")
                                and 'search/jobs/saved' not in link.get_attribute("href")
                                ]
                    counter = 0
                    for j in job_posts:
                        job_details = parse_job_details(j.split('\n'))
                        job_id = job_details.get('job_id')
                        job_url = job_urls[counter].split('/?')[0]
                        job = Job(
                            title=job_details.get('job_title', 'non'),
                            description=job_details.get('job_description', 'non'),
                            link=job_url,
                            company='Upwork',
                            source='Upwork',
                            timestamp=job_details.get('posted_date', datetime.now().isoformat()),
                            location='Remote'
                        )
                        self.storage.add_job(job)
                        counter += 1
                    logger.info(f"Added {counter} jobs from most recent page")

                extract_jobs_from_most_recent()
                # Now click 'Load More Jobs' for each page
                for page in range(1, max_pages):
                    try:
                        load_more_btn = WebDriverWait(driver, 20).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-test="load-more-button"]'))
                        )
                        driver.execute_script("arguments[0].scrollIntoView();", load_more_btn)
                        time.sleep(1)
                        load_more_btn.click()
                        logger.info(f"Clicked Load More Jobs for page {page+1}")
                        time.sleep(5)
                        # Scroll to bottom to trigger more loading
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                        extract_jobs_from_most_recent()
                    except Exception as e:
                        logger.error(f"Error clicking Load More Jobs on page {page+1}: {e}")
                        break
                logger.info('Closing browser for most recent jobs...')
                driver.quit()
            else:
                logger.error("Couldn't load driver")
            
        except Exception as e:
            logger.error(e)

        finally:
            logger.info('Finished UpworkScraper')