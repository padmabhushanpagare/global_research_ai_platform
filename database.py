import pandas as pd
import sqlite3
from config import DB_PATH, logger

def init_db():
    """Creates the SQLite database and the earnings_reports table if they don't exist."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS earnings_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    quarter TEXT NOT NULL,
                    revenue_billions REAL,
                    eps REAL,
                    sentiment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            logger.info("Database connection established and schema verified.")
    except sqlite3.Error as e:
        logger.error(f"Database initialization failed: {e}")
        raise e

def insert_financial_data(data_dict: dict):
    """Inserts the validated Pydantic dictionary into SQLite."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO earnings_reports 
                (ticker, quarter, revenue_billions, eps, sentiment) 
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data_dict.get('ticker', 'UNKNOWN'), 
                data_dict.get('quarter', 'UNKNOWN'), 
                data_dict.get('revenue_billions', 0.0), 
                data_dict.get('eps', 0.0), 
                data_dict.get('sentiment', 'Neutral')
            ))
            conn.commit()
            logger.info(f"💾 Successfully stored {data_dict.get('ticker')} {data_dict.get('quarter')} in SQLite database.")
    except sqlite3.Error as e:
        logger.error(f"Failed to insert database record: {e}")

def get_historical_reports():
    """Queries the SQLite database and returns all processed records as a clean DataFrame."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # We fetch everything, sorting by the newest entry first
            query = """
                SELECT ticker, quarter, revenue_billions, eps, sentiment, created_at 
                FROM earnings_reports 
                ORDER BY created_at DESC
            """
            df = pd.read_sql_query(query, conn)
            return df
    except Exception as e:
        logger.error(f"Failed to fetch data warehouse metrics: {e}")
        return pd.DataFrame() # Return an empty DataFrame as a fallback