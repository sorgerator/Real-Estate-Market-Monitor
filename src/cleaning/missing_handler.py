import pandas as pd
import numpy as np
import os
from utils.logger import logging

def identify_missing_values(df):
    """
    Identifies missing values in the DataFrame and returns a summary.
    """
    logging.info("Identifying missing values...")
    missing_summary = df.isnull().sum()
    missing_percentage = (df.isnull().sum() / len(df)) * 100
    
    report = pd.DataFrame({
        'column': missing_summary.index,
        'missing_count': missing_summary.values,
        'missing_percentage': missing_percentage.values
    })
    
    return report

def generate_missing_value_report(df, output_path="data/processed/cleaned/missing_report.csv"):
    """
    Generates and saves a missing-value report.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    report = identify_missing_values(df)
    report.to_csv(output_path, index=False)
    logging.info(f"Missing value report saved to {output_path}")
    return report

def handle_missing_values(df, critical_columns=None, text_columns=None, numeric_columns=None, threshold=0.5):
    """
    Handles missing values based on specified strategies.
    - Remove rows with missing critical identifiers.
    - Fill descriptive text fields with placeholders.
    - Replace unrealistic zero values with NaN for numeric columns.
    - Fill numeric missing values with medians.
    - Drop columns with missing-data ratio > threshold.
    """
    logging.info("Handling missing values...")
    
    if critical_columns is None:
        critical_columns = ['listing_id']
    if text_columns is None:
        text_columns = ['description', 'title']
    if numeric_columns is None:
        numeric_columns = ['price', 'area']

    # 1. Drop columns with too high missing-data ratio
    missing_ratio = df.isnull().mean()
    cols_to_drop = missing_ratio[missing_ratio > threshold].index.tolist()
    if cols_to_drop:
        logging.info(f"Dropping columns due to high missing ratio: {cols_to_drop}")
        df = df.drop(columns=cols_to_drop)

    # 2. Remove rows with missing critical identifiers
    for col in critical_columns:
        if col in df.columns:
            initial_count = len(df)
            df = df.dropna(subset=[col])
            dropped_count = initial_count - len(df)
            if dropped_count > 0:
                logging.info(f"Dropped {dropped_count} rows with missing critical identifier: {col}")

    # 3. Replace unrealistic zero values with NaN for numeric columns
    for col in numeric_columns:
        if col in df.columns:
            # For real estate, price or area shouldn't be zero
            df[col] = df[col].replace(0, np.nan)
            logging.info(f"Replaced zeros with NaN in numeric column: {col}")

    # 4. Fill numeric missing values with medians
    for col in numeric_columns:
        if col in df.columns:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            logging.info(f"Filled missing values in {col} with median: {median_val}")

    # 5. Fill descriptive text fields with placeholders
    for col in text_columns:
        if col in df.columns:
            if isinstance(df[col].dtype, pd.CategoricalDtype):
                if "No description provided" not in df[col].cat.categories:
                    df[col] = df[col].cat.add_categories(["No description provided"])
            df[col] = df[col].fillna("No description provided")
            logging.info(f"Filled missing values in {col} with placeholder.")

    return df
