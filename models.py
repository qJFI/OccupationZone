import sqlite3
import pandas as pd
from datetime import datetime
import uuid
import logging

class Job:
    def __init__(self, title=None, description=None, link=None, company=None, source=None, timestamp=None, location=None):
        self.id = str(uuid.uuid4())
        self.title = title or 'non'
        self.description = description or 'non'
        self.link = link or 'non'
        self.company = company or 'non'
        self.source = source or 'non'
        self.timestamp = timestamp or datetime.now().isoformat()
        self.location = location or 'non'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'link': self.link,
            'company': self.company,
            'source': self.source,
            'timestamp': self.timestamp,
            'location': self.location
        }

class DataStorage:
    def __init__(self, output_format='sqlite', db_name='jobs.db'):
        self.jobs = []
        self.output_format = output_format
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    link TEXT,
                    company TEXT,
                    source TEXT,
                    timestamp TEXT,
                    location TEXT
                )
            """)

    def add_job(self, job):
        job_dict = job.to_dict()
        self.jobs.append(job_dict)
        with self.conn:
            self.conn.execute(
                'INSERT OR IGNORE INTO jobs (id, title, description, link, company, source, timestamp, location) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (job_dict['id'], job_dict['title'], job_dict['description'], 
                 job_dict['link'], job_dict['company'], job_dict['source'], job_dict['timestamp'], job_dict['location'])
            )

    def save(self):
        if self.output_format == 'csv':
            df = pd.DataFrame(self.jobs)
            filename = f'job_listings_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            df.to_csv(filename, index=False)
            logging.info(f"Data saved to {filename}")
        elif self.output_format == 'json':
            import json
            filename = f'job_listings_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(filename, 'w') as f:
                json.dump(self.jobs, f, indent=2)
            logging.info(f"Data saved to {filename}")
        logging.info(f"Data saved to {self.db_name}")

    def __del__(self):
        self.conn.close() 