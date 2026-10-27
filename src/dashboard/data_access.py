import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
from src.utils.logger import logging

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "RealEstateDB"
COLLECTION_NAME = "loopnet_listings"
CSV_FALLBACK_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/processed/cleaned/cleaned_data.csv"))

def load_data():
    """
    Loads real estate data from MongoDB. 
    If MongoDB is unavailable or collection is empty, falls back to cleaned_data.csv.
    """
    df = pd.DataFrame()
    try:
        logging.info("Attempting to connect to MongoDB...")
        # Short timeout to fail quickly if Mongo is not running
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.server_info() # force connection check
        
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # Only load cleaned/enriched records that have valid price, area, and type
        cursor = collection.find({"price": {"$gt": 0}, "type": {"$ne": None}})
        data = list(cursor)
        if data:
            df = pd.DataFrame(data)
            if '_id' in df.columns:
                df.drop(columns=['_id'], inplace=True)
            logging.info(f"Successfully loaded {len(df)} records from MongoDB.")
        else:
            logging.warning("MongoDB collection has no enriched records.")
    except Exception as e:
        logging.warning(f"MongoDB connection failed: {e}. Falling back to CSV.")
        
    if df.empty or (os.path.exists(CSV_FALLBACK_PATH) and len(pd.read_csv(CSV_FALLBACK_PATH)) > len(df)):
        logging.info(f"Loading data from CSV: {CSV_FALLBACK_PATH}")
        if os.path.exists(CSV_FALLBACK_PATH):
            df = pd.read_csv(CSV_FALLBACK_PATH)
            logging.info(f"Successfully loaded {len(df)} records from CSV.")
        elif df.empty:
            logging.error(f"CSV fallback file not found at {CSV_FALLBACK_PATH}")
            # Generate synthetic data as a last resort
            import numpy as np
            df = pd.DataFrame({
                'listing_id': range(100),
                'price': np.random.randint(100000, 2000000, size=100),
                'area': np.random.randint(500, 5000, size=100),
                'type': np.random.choice(['Office', 'Retail', 'Industrial', 'Multi-Family'], size=100),
                'description': ["Mock property description" for _ in range(100)],
                'title': ["Mock Property" for _ in range(100)],
                'collected_at': pd.date_range(start='2026-01-01', periods=100).strftime('%Y-%m-%d %H:%M:%S')
            })
            
    # Post-process columns
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
    if 'area' in df.columns:
        df['area'] = pd.to_numeric(df['area'], errors='coerce')
        
    # Ensure year column exists
    if 'collected_at' in df.columns:
        df['year'] = pd.to_datetime(df['collected_at'], errors='coerce').dt.year.fillna(2026).astype(int)
    else:
        df['year'] = 2026
        
    return df

def get_available_genres(df):
    """Returns list of unique property types (used interchangeably with 'genres' from instructions)."""
    if 'type' in df.columns:
        return sorted(df['type'].dropna().unique().tolist())
    return []

def get_year_range(df):
    """Returns min and max year in the dataset."""
    if 'year' in df.columns and not df['year'].dropna().empty:
        return int(df['year'].min()), int(df['year'].max())
    return 2026, 2026

def filter_data(df, selected_types, year_range, search_text):
    """Filters the dataset based on type, year range, and search text."""
    filtered_df = df.copy()
    
    # Filter by property type
    if selected_types:
        if isinstance(selected_types, str):
            selected_types = [selected_types]
        filtered_df = filtered_df[filtered_df['type'].isin(selected_types)]
        
    # Filter by year range
    if year_range and len(year_range) == 2:
        min_yr, max_yr = year_range
        filtered_df = filtered_df[(filtered_df['year'] >= min_yr) & (filtered_df['year'] <= max_yr)]
        
    # Filter by search text
    if search_text:
        search_text = search_text.lower()
        title_match = filtered_df['title'].astype(str).str.lower().str.contains(search_text, na=False)
        desc_match = filtered_df['description'].astype(str).str.lower().str.contains(search_text, na=False)
        filtered_df = filtered_df[title_match | desc_match]
        
    return filtered_df
