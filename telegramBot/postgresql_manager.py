import os

from dotenv import load_dotenv
import psycopg2


class PostgresSQLManager:
    def __init__(self):
        load_dotenv()
        self.db = os.getenv('DATABASE_URL')

    def __enter__(self):
        self.conn = psycopg2.connect(self.db)
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.cursor.close()
        self.conn.close()
