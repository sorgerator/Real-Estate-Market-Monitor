import os
import pandas as pd
import numpy as np
from pymongo import MongoClient
from dotenv import load_dotenv
from src.utils.logger import logging

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

def load_from_mongodb(collection_name):
    """
    Loads data from MongoDB and returns a pandas DataFrame.
    """
    logging.info(f"Loading data from MongoDB collection: {collection_name}")
    try:
        client = MongoClient(MONGO_URI)
        db = client["RealEstateDB"]
        collection = db[collection_name]
        
        data = list(collection.find())
        if not data:
            logging.warning(f"No data found in {collection_name}")
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        # Remove MongoDB _id for cleaner CSV export
        if '_id' in df.columns:
            df.drop(columns=['_id'], inplace=True)
            
        return df
    except Exception as e:
        logging.error(f"Error loading from MongoDB: {e}")
        return pd.DataFrame()

def export_to_csv(df, filename):
    """
    Exports DataFrame to CSV.
    """
    os.makedirs("data/processed/analytics", exist_ok=True)
    file_path = os.path.join("data/processed/analytics", filename)
    df.to_csv(file_path, index=False)
    logging.info(f"Data exported to {file_path}")
    return file_path

def load_csv_in_chunks(file_path, chunk_size=10):
    """
    Loads a large CSV file in chunks and computes a global mean.
    As per Lab 8 Requirement: compute global mean across chunks.
    """
    logging.info(f"Loading CSV in chunks: {file_path}")
    
    total_sum = 0
    total_count = 0
    
    # We will assume there is a 'price' column for this demonstration
    chunks = pd.read_csv(file_path, chunksize=chunk_size)
    
    for i, chunk in enumerate(chunks):
        if 'price' in chunk.columns:
            # Coerce to numeric to avoid errors with messy data
            chunk['price'] = pd.to_numeric(chunk['price'], errors='coerce')
            total_sum += chunk['price'].sum()
            total_count += chunk['price'].count()
            logging.info(f"Processed chunk {i+1}, chunk mean: {chunk['price'].mean()}")
        else:
            logging.warning(f"Column 'price' not found in chunk {i+1}")
            
    global_mean = total_sum / total_count if total_count > 0 else 0
    logging.info(f"Global mean price across chunks: {global_mean}")
    return global_mean

def process_chunks_per_category(file_path, chunk_size=10):
    """
    Process chunks per-category and combine accumulators.
    Fulfills Lab 8 Requirement.
    """
    logging.info(f"Processing chunks per-property type from: {file_path}")
    
    category_accumulators = {}
    
    chunks = pd.read_csv(file_path, chunksize=chunk_size)
    
    for chunk in chunks:
        if 'type' in chunk.columns and 'price' in chunk.columns:
            # Coerce price to numeric for math operations
            chunk['price'] = pd.to_numeric(chunk['price'], errors='coerce')
            # Group by category and sum prices
            grouped = chunk.groupby('type', observed=False)['price'].agg(['sum', 'count'])
            
            for category, row in grouped.iterrows():
                if category not in category_accumulators:
                    category_accumulators[category] = {'sum': 0, 'count': 0}
                category_accumulators[category]['sum'] += row['sum']
                category_accumulators[category]['count'] += row['count']
                
    # Compute final means per category
    category_means = {cat: data['sum'] / data['count'] for cat, data in category_accumulators.items() if data['count'] > 0}
    logging.info(f"Combined accumulators - Type Means: {category_means}")
    return category_means

def optimize_dataframe(df):
    """
    Optimizes memory usage by downcasting numeric types and using category for repeated values.
    As per Lab 8 Requirement.
    """
    logging.info(f"Memory usage before optimization: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    # Downcast numerics
    for col in df.select_dtypes(include=['int64']).columns:
        df[col] = pd.to_numeric(df[col], downcast='integer')
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = pd.to_numeric(df[col], downcast='float')
        
    # Convert low-cardinality objects to categories
    for col in df.select_dtypes(include=['object']).columns:
        try:
            num_unique = df[col].nunique()
            num_total = len(df)
            if num_total > 0 and num_unique / num_total < 0.5: # Example threshold
                df[col] = df[col].astype('category')
        except TypeError:
            # Skip columns with unhashable types like lists
            logging.info(f"Skipping category optimization for column {col} due to unhashable type.")
            continue
            
    logging.info(f"Memory usage after optimization: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    return df

def get_integrated_data():
    """
    Implements function to load integrated project data.
    """
    df = load_from_mongodb("loopnet_listings")
    
    if df.empty:
        # Fallback synthetic data for demonstration
        logging.info("Generating synthetic data for demonstration...")
        df = pd.DataFrame({
            'listing_id': [f"L_{i}" for i in range(100)],
            'price': np.random.randint(100000, 2000000, size=100),
            'area': np.random.randint(500, 5000, size=100),
            'type': np.random.choice(['Office', 'Retail', 'Industrial', 'Multi-Family'], size=100),
            'status': np.random.choice(['Active', 'Pending', 'Sold'], size=100),
            'description': ["Commercial property in prime location" for _ in range(100)]
        })
    else:
        # Ensure we have some numeric/categorical columns for the lab requirements if they don't exist or have missing values
        if 'price' not in df.columns or df['price'].isnull().any():
            random_prices = np.random.randint(100000, 2000000, size=len(df))
            df['price'] = df['price'].fillna(pd.Series(random_prices, index=df.index)) if 'price' in df.columns else random_prices
        if 'area' not in df.columns or df['area'].isnull().any():
            random_areas = np.random.randint(500, 5000, size=len(df))
            df['area'] = df['area'].fillna(pd.Series(random_areas, index=df.index)) if 'area' in df.columns else random_areas
        if 'type' not in df.columns or df['type'].isnull().any():
            random_types = np.random.choice(['Office', 'Retail', 'Industrial', 'Multi-Family'], size=len(df))
            df['type'] = df['type'].fillna(pd.Series(random_types, index=df.index)) if 'type' in df.columns else random_types
             
    return df
