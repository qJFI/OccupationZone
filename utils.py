import logging

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def deduplicate_jobs(conn):
    with conn:
        conn.execute("""
            DELETE FROM jobs
            WHERE rowid NOT IN (
                SELECT MIN(rowid)
                FROM jobs
                GROUP BY link
            )
        """) 