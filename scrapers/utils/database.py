import os
import sqlite3


def connect_to_db(database_name='jobs.db'):
    # Always use jobs.db in the main project directory (one level above scrapers/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(os.path.dirname(current_dir))  # Go up two levels to reach project root
    database_path = os.path.join(parent_dir, database_name)
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    return conn, cursor


def create_db(conn, cursor):
    # Create the `jobs` table (if it doesn't exist)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT,
            job_url TEXT,
            job_title TEXT,
            posted_date DATETIME,
            job_description TEXT,
            job_tags TEXT,
            job_proposals TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

