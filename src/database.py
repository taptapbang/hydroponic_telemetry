# src/database.py

#target db info

import os
import logging
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "hydro_data"),
            user=os.getenv("DB_USER", "hydro_user"),
            password=os.getenv("DB_PASSWORD", "")
        )
        return conn
    except Exception as e:
        logging.error(f"Connection failure: {e}")
        raise