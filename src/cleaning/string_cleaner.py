import pandas as pd
from utils.logger import logging

def clean_string_columns(df, columns=None):
    """
    Cleans string columns by removing whitespace, normalising case, and fixing format.
    Uses vectorized pandas string operations.
    """
    logging.info("Cleaning string columns...")
    
    if columns is None:
        columns = df.select_dtypes(include=['object', 'category']).columns.tolist()

    for col in columns:
        if col in df.columns:
            logging.info(f"Cleaning column: {col}")
            mask = df[col].isna()
            # Ensure it's string type for .str accessor
            df[col] = df[col].astype(str)
            
            # Remove whitespace
            df[col] = df[col].str.strip()
            
            # Normalize case (e.g., lowercase)
            df[col] = df[col].str.lower()
            
            # Replace multiple spaces with a single space
            df[col] = df[col].str.replace(r'\s+', ' ', regex=True)
            
            # Restore NaNs (or handle literal 'nan'/'none' strings)
            df.loc[mask | df[col].isin(['nan', 'none']), col] = None
            
            logging.info(f"Column {col} cleaned.")

    return df

def normalize_property_types(df, column='type'):
    """
    Normalizes property type names.
    """
    if column in df.columns:
        logging.info(f"Normalizing property types in column: {column}")
        mask = df[column].isna()
        df[column] = df[column].astype(str).str.strip().str.title()
        df.loc[mask | df[column].isin(['Nan', 'None', '']), column] = 'Commercial'
    return df
