"""
Module: load_data.py
Description: Ingests the raw netflix_titles.csv into SQLite database.
"""

import os
import sqlite3
import pandas as pd

RAW_DATA_PATH = os.path.join("data", "raw", "netflix_titles.csv")
DB_PATH = os.path.join("data", "processed", "netflix.db")


def load_raw_data(csv_path: str = RAW_DATA_PATH, db_path: str = DB_PATH) -> int:
    """
    Loads raw CSV data into SQLite as 'netflix_titles_raw' and initializes the DB.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Raw data file not found at: {csv_path}")

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    print(f"Reading raw dataset from: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows and {len(df.columns)} columns.")

    conn = sqlite3.connect(db_path)
    try:
        # Load initially as raw table for auditability and initial state
        df.to_sql("netflix_titles", conn, if_exists="replace", index=False)
        print(f"Successfully loaded {len(df)} records into 'netflix_titles' table in {db_path}")
    finally:
        conn.close()

    return len(df)


if __name__ == "__main__":
    load_raw_data()
