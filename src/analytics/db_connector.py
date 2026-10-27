import pymysql
import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from datetime import datetime
from src.utils.logger import logging

# Load environment variables (assuming DB credentials are in .env)
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "real_estate_db")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SQLITE_FALLBACK_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "analytics", "real_estate_fallback.db")
DEFAULT_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "cleaned", "cleaned_data.csv")

def _get_engine():
    """
    Returns a SQLAlchemy engine for MySQL if reachable, or falls back to local SQLite.
    """
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=2
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            connection.commit()
        finally:
            connection.close()
        return create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
    except Exception as e:
        logging.warning(f"MySQL unavailable ({e}). Falling back to local SQLite database at {SQLITE_FALLBACK_PATH}.")
        os.makedirs(os.path.dirname(SQLITE_FALLBACK_PATH), exist_ok=True)
        return create_engine(f"sqlite:///{SQLITE_FALLBACK_PATH}")

def get_connection():
    """Creates and returns a connection to the MySQL database."""
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def create_db_if_not_exists():
    """Creates the database if it doesn't already exist."""
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=2
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            connection.commit()
        finally:
            connection.close()
    except Exception as e:
        logging.warning(f"Could not connect to MySQL in create_db_if_not_exists: {e}")

def _prepare_financials_df(csv_path):
    """Prepares the financials DataFrame from the cleaned CSV file."""
    df = pd.read_csv(csv_path)
    
    # Map real estate columns to consistent names for analytics
    # Following Lab 10 requirement for financial columns (budget, revenue)
    # We use price to derive mock budget and revenue for the exercise
    df['budget_usd'] = df['price'] * 0.8
    df['revenue_usd'] = df['price']
    
    if 'collected_at' in df.columns:
        df['release_year'] = pd.to_datetime(df['collected_at'], errors='coerce').dt.year.fillna(datetime.now().year).astype(int)
    else:
        df['release_year'] = datetime.now().year

    # Ensure we have the columns required by Lab 10 tasks
    mapping = {
        'listing_id': 'listing_id',
        'title': 'title',
        'budget_usd': 'budget_usd',
        'revenue_usd': 'revenue_usd',
        'release_year': 'release_year',
        'type': 'primary_genre' # Using 'type' as genre per Lab 10
    }
    
    # Rename for consistency with Lab 10 requirements
    df_to_save = df.rename(columns=mapping)
    
    # Keep only relevant columns
    required_columns = ['listing_id', 'title', 'budget_usd', 'revenue_usd', 'release_year', 'primary_genre']
    cols_to_use = [c for c in required_columns if c in df_to_save.columns]
    return df_to_save[cols_to_use].dropna()

def populate_financials(csv_path=DEFAULT_CSV_PATH):
    """
    Reads the cleaned dataset and populates the 'property_financials' table.
    Includes budget and revenue for ROI calculations as per Lab 10 requirements.
    Falls back to SQLite if MySQL is not running.
    """
    df_to_save = _prepare_financials_df(csv_path)
    engine = _get_engine()
    df_to_save.to_sql('property_financials', con=engine, if_exists='replace', index=False)
    print(f"Successfully populated 'property_financials' table with {len(df_to_save)} records.")

def query_financials(query="SELECT * FROM property_financials"):
    """
    Queries the database and returns a DataFrame.
    Automatically populates the fallback database if the table does not exist yet.
    """
    engine = _get_engine()
    try:
        return pd.read_sql(query, con=engine)
    except Exception:
        if os.path.exists(DEFAULT_CSV_PATH):
            populate_financials(DEFAULT_CSV_PATH)
            return pd.read_sql(query, con=engine)
        raise
