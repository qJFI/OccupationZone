import requests
from bs4 import BeautifulSoup
from models import Job
import logging
import urllib.parse

class PeoplePerHourScraper:
    def __init__(self, storage, query='software', proxy=None):
        self.storage = storage
        self.query = query
        self.proxy = proxy
        self.base_url = "https://www.peopleperhour.com"
        self.logger = logging.getLogger(__name__)

    def scrape(self, max_pages=1):
        query_slug = urllib.parse.quote(self.query.replace(' ', '-'))
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        total_jobs = 0
        for page in range(1, max_pages + 1):
            if page == 1:
                url = f"{self.base_url}/freelance-{query_slug}-jobs"
            else:
                url = f"{self.base_url}/freelance-{query_slug}-jobs?page={page}"
            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                job_items = soup.select('.item__container⤍ListItem⤚Fk4RX')
                for item in job_items:
                    # Title and link
                    title_tag = item.select_one('h6.item__title⤍ListItem⤚2FRMT a')
                    title = title_tag.text.strip() if title_tag else 'non'
                    link = title_tag['href'] if title_tag and title_tag.has_attr('href') else ''
                    if link and not link.startswith('http'):
                        link = self.base_url + link

                    # Description
                    description_tag = item.select_one('p.item__desc⤍ListItem⤚3f4JV')
                    description = description_tag.text.strip() if description_tag else 'non'

                    # User/company
                    user_tag = item.select_one('.card__username⤍ListItem⤚QnBBG')
                    company = user_tag.text.strip() if user_tag else 'PeoplePerHour Client'

                    # Posted date, proposals, location
                    footer = item.select_one('.card__footer-left⤍ListItem⤚16Odv')
                    posted_date = ''
                    proposals = ''
                    location = 'Unknown'
                    if footer:
                        spans = footer.find_all('span')
                        if len(spans) > 0:
                            posted_date = spans[0].text.strip()
                        if len(spans) > 1:
                            proposals = spans[1].text.strip()
                        if len(spans) > 2:
                            location = 'Remote' if 'Remote' in spans[2].text else spans[2].text.strip()

                    job = Job(
                        title=title,
                        description=description,
                        link=link,
                        company=company,
                        source='PeoplePerHour',
                        timestamp=posted_date,
                        location=location
                    )
                    self.storage.add_job(job)
                total_jobs += len(job_items)
                self.logger.info(f"PeoplePerHour: Scraped {len(job_items)} jobs from {url}.")
                # Stop if there are no more jobs on this page
                if not job_items:
                    break
            except Exception as e:
                self.logger.error(f"PeoplePerHour scraping error on page {page}: {e}")
                break
        self.logger.info(f"PeoplePerHour: Scraped a total of {total_jobs} jobs.") 