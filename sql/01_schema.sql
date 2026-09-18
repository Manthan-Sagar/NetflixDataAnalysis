-- ==============================================================================
-- File: 01_schema.sql
-- Description: DDL definitions for the normalized Netflix Content Library database.
-- Architecture: 1NF normalized schema separating multi-value genres and countries
--               into dedicated junction tables with optimized B-tree indexes.
-- ==============================================================================

-- Master Content Catalog Table
CREATE TABLE IF NOT EXISTS netflix_titles (
    show_id TEXT PRIMARY KEY,
    type TEXT NOT NULL,                  -- 'Movie' or 'TV Show'
    title TEXT NOT NULL,
    director TEXT DEFAULT 'Unknown',
    cast TEXT DEFAULT 'Unknown',
    country TEXT DEFAULT 'Unknown',
    date_added TEXT,                    -- Formatted ISO date (YYYY-MM-DD)
    release_year INTEGER NOT NULL,      -- Year of original release / theatrical release
    rating TEXT DEFAULT 'Unknown',      -- MPAA / TV Parental Guidelines rating
    duration TEXT NOT NULL,             -- Raw string representation
    duration_value INTEGER NOT NULL,    -- Numeric duration (minutes or season count)
    duration_unit TEXT NOT NULL,         -- 'min' or 'Season' / 'Seasons'
    listed_in TEXT,                     -- Original raw genre string
    description TEXT
);

-- Normalized Junction Table: Title-to-Genre (1-to-Many)
CREATE TABLE IF NOT EXISTS genre_map (
    show_id TEXT NOT NULL,
    genre TEXT NOT NULL,
    PRIMARY KEY (show_id, genre),
    FOREIGN KEY (show_id) REFERENCES netflix_titles(show_id) ON DELETE CASCADE
);

-- Normalized Junction Table: Title-to-Country (1-to-Many)
CREATE TABLE IF NOT EXISTS country_map (
    show_id TEXT NOT NULL,
    country TEXT NOT NULL,
    PRIMARY KEY (show_id, country),
    FOREIGN KEY (show_id) REFERENCES netflix_titles(show_id) ON DELETE CASCADE
);

-- Analytical Indexes
CREATE INDEX IF NOT EXISTS idx_titles_type ON netflix_titles(type);
CREATE INDEX IF NOT EXISTS idx_titles_rating ON netflix_titles(rating);
CREATE INDEX IF NOT EXISTS idx_titles_date_added ON netflix_titles(date_added);
CREATE INDEX IF NOT EXISTS idx_titles_release_year ON netflix_titles(release_year);
CREATE INDEX IF NOT EXISTS idx_genre_map_genre ON genre_map(genre);
CREATE INDEX IF NOT EXISTS idx_country_map_country ON country_map(country);
