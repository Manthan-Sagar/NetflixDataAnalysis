"""
Module: clean_data.py
Description: Cleans, transforms, and normalizes Netflix catalog data.

Key Cleaning & Normalization Decisions:
1. Missing Values (director, cast, country):
   - High missing rates (e.g., director ~30%). Dropping rows would severely bias catalog
     representation and discard ~30-40% of total titles. Imputed with 'Unknown'.
2. Rating Shift Anomaly:
   - Source data has 3 records where the 'duration' shifted into the 'rating' field
     (e.g., '74 min', '84 min', '66 min' for Louis C.K. specials). These values are restored
     into 'duration', and 'rating' is marked as 'Unknown'.
   - Any remaining null ratings (4 records) are also filled with 'Unknown'.
3. Date Added:
   - Whitespace trimmed, parsed into standard ISO format (YYYY-MM-DD) for SQL strftime compatibility.
   - Records with null date_added (~10 rows, <0.12% of data) are dropped since release
     cadence and acquisition trends require valid temporal timestamps.
4. Duration Decomposition:
   - Deconstructed into 'duration_value' (INTEGER) and 'duration_unit' (TEXT: 'min' or 'Season(s)').
   - Movies are measured in minutes, whereas TV shows are measured in seasons. Separating them
     enables valid mathematical aggregations (e.g. AVG, MEDIAN) per type.
5. First Normal Form (1NF) Normalization:
   - 'listed_in' (genres) and 'country' are comma-separated multi-value columns violating 1NF.
   - Exploded into dedicated junction tables 'genre_map' and 'country_map' linked via 'show_id'.
   - Enables pure relational SQL JOINs and GROUP BY operations without hacky LIKE string matching.
"""

import os
import sqlite3
import pandas as pd

RAW_DATA_PATH = os.path.join("data", "raw", "netflix_titles.csv")
DB_PATH = os.path.join("data", "processed", "netflix.db")


def clean_and_normalize_data(csv_path: str = RAW_DATA_PATH, db_path: str = DB_PATH):
    print("Loading data for cleaning pipeline...")
    df = pd.read_csv(csv_path)
    initial_rows = len(df)
    print(f"Initial raw rows: {initial_rows}")

    # 1. Fill high-cardinality metadata nulls with 'Unknown'
    df["director"] = df["director"].fillna("Unknown").str.strip()
    df["cast"] = df["cast"].fillna("Unknown").str.strip()
    df["country"] = df["country"].fillna("Unknown").str.strip()

    # 2. Correct rating data shift anomalies
    # When duration is NaN and rating contains 'min', copy rating into duration
    shift_mask = df["rating"].astype(str).str.contains("min", na=False)
    shifted_count = shift_mask.sum()
    if shifted_count > 0:
        print(f"Correcting {shifted_count} rating/duration shifted records...")
        df.loc[shift_mask, "duration"] = df.loc[shift_mask, "rating"]
        df.loc[shift_mask, "rating"] = "Unknown"

    df["rating"] = df["rating"].fillna("Unknown").str.strip()

    # 3. Clean and parse date_added
    null_dates = df["date_added"].isnull().sum()
    print(f"Dropping {null_dates} rows with missing 'date_added'...")
    df = df.dropna(subset=["date_added"]).copy()
    df["date_added"] = pd.to_datetime(df["date_added"].str.strip(), format="%B %d, %Y", errors="coerce")
    
    # Check if any date parsing failed
    invalid_dates = df["date_added"].isnull().sum()
    if invalid_dates > 0:
        print(f"Dropping {invalid_dates} unparseable date rows...")
        df = df.dropna(subset=["date_added"]).copy()

    # Store formatted ISO date string for SQLite compatibility
    df["date_added_iso"] = df["date_added"].dt.strftime("%Y-%m-%d")

    # 4. Decompose duration into duration_value and duration_unit
    duration_split = df["duration"].astype(str).str.extract(r"^(\d+)\s*(.*)$")
    df["duration_value"] = pd.to_numeric(duration_split[0], errors="coerce").fillna(0).astype(int)
    df["duration_unit"] = duration_split[1].str.strip()

    # 5. Extract Normalized Junction Tables
    # A. Genre Map (show_id, genre)
    print("Building normalized 'genre_map' junction table...")
    genres_df = (
        df[["show_id", "listed_in"]]
        .assign(genre=df["listed_in"].str.split(","))
        .explode("genre")
    )
    genres_df["genre"] = genres_df["genre"].str.strip()
    genres_df = genres_df[genres_df["genre"] != ""][["show_id", "genre"]].drop_duplicates()

    # B. Country Map (show_id, country)
    print("Building normalized 'country_map' junction table...")
    countries_df = (
        df[["show_id", "country"]]
        .assign(country=df["country"].str.split(","))
        .explode("country")
    )
    countries_df["country"] = countries_df["country"].str.strip()
    countries_df = countries_df[countries_df["country"] != ""][["show_id", "country"]].drop_duplicates()

    # Final cleaned titles dataframe
    cleaned_titles = df[[
        "show_id",
        "type",
        "title",
        "director",
        "cast",
        "country",
        "date_added_iso",
        "release_year",
        "rating",
        "duration",
        "duration_value",
        "duration_unit",
        "listed_in",
        "description"
    ]].rename(columns={"date_added_iso": "date_added"})

    print(f"Cleaned dataset rows: {len(cleaned_titles)} (retained {len(cleaned_titles)/initial_rows*100:.2f}%)")
    print(f"Genre map records: {len(genres_df)} (unique genres: {genres_df['genre'].nunique()})")
    print(f"Country map records: {len(countries_df)} (unique countries: {countries_df['country'].nunique()})")

    # Write to SQLite
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        cleaned_titles.to_sql("netflix_titles", conn, if_exists="replace", index=False)
        genres_df.to_sql("genre_map", conn, if_exists="replace", index=False)
        countries_df.to_sql("country_map", conn, if_exists="replace", index=False)

        # Create indexes for optimal SQL performance
        cursor = conn.cursor()
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_titles_show_id ON netflix_titles(show_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_titles_type ON netflix_titles(type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_titles_rating ON netflix_titles(rating);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_titles_date_added ON netflix_titles(date_added);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_titles_release_year ON netflix_titles(release_year);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_genre_map_show_id ON genre_map(show_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_genre_map_genre ON genre_map(genre);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_country_map_show_id ON country_map(show_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_country_map_country ON country_map(country);")
        conn.commit()
        print(f"Successfully saved all normalized tables and indexes to {db_path}")
    finally:
        conn.close()

    return cleaned_titles, genres_df, countries_df


if __name__ == "__main__":
    clean_and_normalize_data()
