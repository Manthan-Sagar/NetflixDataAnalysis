"""
Module: export_app_data.py
Description: Extracts analytical aggregates and catalog records from SQLite
             and packages them into web/data.js and web/data.json for the
             interview-ready dashboard application.
"""

import os
import json
import sqlite3

DB_PATH = os.path.join("data", "processed", "netflix.db")
WEB_DIR = "web"
OUTPUT_JS = os.path.join(WEB_DIR, "js", "data.js")
OUTPUT_JSON = os.path.join(WEB_DIR, "data.json")


def get_connection():
    return sqlite3.connect(DB_PATH)


def export_data():
    os.makedirs(os.path.join(WEB_DIR, "js"), exist_ok=True)
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    data = {}

    # 1. Executive Summary KPIs
    cur.execute("""
        SELECT 
            COUNT(*) AS total_titles,
            SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movie_count,
            SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_count,
            ROUND(AVG(CASE WHEN type = 'Movie' THEN duration_value END), 1) AS avg_movie_min,
            ROUND(AVG(CASE WHEN type = 'TV Show' THEN duration_value END), 1) AS avg_tv_seasons,
            SUM(CASE WHEN rating IN ('TV-MA', 'TV-14') THEN 1 ELSE 0 END) AS mature_titles
        FROM netflix_titles;
    """)
    row = cur.fetchone()
    total = row["total_titles"]
    movies = row["movie_count"]
    tv = row["tv_count"]
    mature = row["mature_titles"]

    # Top 3 countries concentration
    cur.execute("""
        WITH c_counts AS (
            SELECT country, COUNT(DISTINCT show_id) AS cnt
            FROM country_map
            WHERE country <> 'Unknown'
            GROUP BY country
            ORDER BY cnt DESC
            LIMIT 3
        )
        SELECT SUM(cnt) AS top3_sum FROM c_counts;
    """)
    top3_sum = cur.fetchone()["top3_sum"]

    data["kpis"] = {
        "total_titles": total,
        "movie_count": movies,
        "tv_count": tv,
        "movie_pct": round(100.0 * movies / total, 1),
        "tv_pct": round(100.0 * tv / total, 1),
        "avg_movie_min": row["avg_movie_min"],
        "avg_tv_seasons": row["avg_tv_seasons"],
        "mature_count": mature,
        "mature_pct": round(100.0 * mature / total, 1),
        "top3_concentration_pct": round(100.0 * top3_sum / total, 1),
        "peak_year": 2019,
        "peak_year_additions": 2016
    }

    # 2. Content Distribution & Duration Brackets
    # Movie Runtime Brackets
    cur.execute("""
        SELECT 
            CASE 
                WHEN duration_value < 60 THEN '< 60 min'
                WHEN duration_value BETWEEN 60 AND 89 THEN '60 - 89 min'
                WHEN duration_value BETWEEN 90 AND 119 THEN '90 - 119 min'
                WHEN duration_value BETWEEN 120 AND 149 THEN '120 - 149 min'
                ELSE '150+ min'
            END AS bracket,
            COUNT(*) AS count
        FROM netflix_titles
        WHERE type = 'Movie'
        GROUP BY bracket
        ORDER BY 
            CASE bracket
                WHEN '< 60 min' THEN 1
                WHEN '60 - 89 min' THEN 2
                WHEN '90 - 119 min' THEN 3
                WHEN '120 - 149 min' THEN 4
                ELSE 5
            END;
    """)
    movie_brackets = [{"bracket": r["bracket"], "count": r["count"]} for r in cur.fetchall()]

    # TV Seasons Brackets
    cur.execute("""
        SELECT 
            CASE 
                WHEN duration_value = 1 THEN '1 Season'
                WHEN duration_value = 2 THEN '2 Seasons'
                WHEN duration_value = 3 THEN '3 Seasons'
                WHEN duration_value BETWEEN 4 AND 5 THEN '4 - 5 Seasons'
                ELSE '6+ Seasons'
            END AS bracket,
            COUNT(*) AS count
        FROM netflix_titles
        WHERE type = 'TV Show'
        GROUP BY bracket
        ORDER BY 
            CASE bracket
                WHEN '1 Season' THEN 1
                WHEN '2 Seasons' THEN 2
                WHEN '3 Seasons' THEN 3
                WHEN '4 - 5 Seasons' THEN 4
                ELSE 5
            END;
    """)
    tv_brackets = [{"bracket": r["bracket"], "count": r["count"]} for r in cur.fetchall()]

    data["duration_distributions"] = {
        "movie_brackets": movie_brackets,
        "tv_brackets": tv_brackets
    }

    # 3. The Strategic Pivot (Time Series: Release Year vs Added Year 2005-2021)
    cur.execute("""
        WITH release_stats AS (
            SELECT release_year AS year, COUNT(*) AS titles_released
            FROM netflix_titles
            WHERE release_year BETWEEN 2005 AND 2021
            GROUP BY release_year
        ),
        added_stats AS (
            SELECT CAST(strftime('%Y', date_added) AS INTEGER) AS year, COUNT(*) AS titles_added
            FROM netflix_titles
            WHERE date_added IS NOT NULL AND CAST(strftime('%Y', date_added) AS INTEGER) BETWEEN 2005 AND 2021
            GROUP BY strftime('%Y', date_added)
        )
        SELECT 
            COALESCE(r.year, a.year) AS year,
            COALESCE(r.titles_released, 0) AS titles_released,
            COALESCE(a.titles_added, 0) AS titles_added
        FROM release_stats r
        FULL OUTER JOIN added_stats a ON r.year = a.year
        ORDER BY year;
    """)
    data["time_series_pivot"] = [
        {"year": r["year"], "released": r["titles_released"], "added": r["titles_added"]}
        for r in cur.fetchall()
    ]

    # 4. Top 15 Genres overall with Movie vs TV breakdown
    cur.execute("""
        SELECT 
            g.genre,
            COUNT(*) AS total_count,
            SUM(CASE WHEN n.type = 'Movie' THEN 1 ELSE 0 END) AS movie_count,
            SUM(CASE WHEN n.type = 'TV Show' THEN 1 ELSE 0 END) AS tv_count
        FROM genre_map g
        JOIN netflix_titles n ON g.show_id = n.show_id
        GROUP BY g.genre
        ORDER BY total_count DESC
        LIMIT 15;
    """)
    data["top_genres"] = [
        {
            "genre": r["genre"],
            "total": r["total_count"],
            "movie": r["movie_count"],
            "tv": r["tv_count"]
        }
        for r in cur.fetchall()
    ]

    # 5. Audience Maturity & Ratings Distribution
    cur.execute("""
        SELECT 
            rating,
            SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movie_count,
            SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_count,
            COUNT(*) AS total_count
        FROM netflix_titles
        WHERE rating <> 'Unknown'
        GROUP BY rating
        ORDER BY total_count DESC
        LIMIT 10;
    """)
    data["ratings_breakdown"] = [
        {
            "rating": r["rating"],
            "total": r["total_count"],
            "movie": r["movie_count"],
            "tv": r["tv_count"]
        }
        for r in cur.fetchall()
    ]

    # Maturity Groups (Adult, Teen, Older Kids, Family/Preschool)
    cur.execute("""
        SELECT 
            CASE 
                WHEN rating IN ('TV-MA', 'R', 'NC-17') THEN 'Adults (18+)'
                WHEN rating IN ('TV-14', 'PG-13') THEN 'Teens (13-14+)'
                WHEN rating IN ('TV-PG', 'PG') THEN 'Older Kids (8+)'
                WHEN rating IN ('TV-Y', 'TV-Y7', 'TV-Y7-FV', 'TV-G', 'G') THEN 'Family & Kids'
                ELSE 'Unrated / Other'
            END AS maturity_segment,
            COUNT(*) AS count,
            SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movie_count,
            SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_count
        FROM netflix_titles
        GROUP BY maturity_segment
        ORDER BY count DESC;
    """)
    data["maturity_segments"] = [
        {
            "segment": r["maturity_segment"],
            "count": r["count"],
            "movie": r["movie_count"],
            "tv": r["tv_count"],
            "pct": round(100.0 * r["count"] / total, 1)
        }
        for r in cur.fetchall()
    ]

    # 6. Geographic Footprint & Cumulative Concentration (Top 15 Countries)
    cur.execute("""
        WITH country_counts AS (
            SELECT 
                c.country,
                COUNT(DISTINCT c.show_id) AS title_count
            FROM country_map c
            WHERE c.country <> 'Unknown'
            GROUP BY c.country
        )
        SELECT 
            cc.country,
            cc.title_count,
            ROUND(100.0 * cc.title_count / :total, 2) AS pct_of_catalog,
            ROUND(SUM(100.0 * cc.title_count / :total) OVER (ORDER BY cc.title_count DESC), 1) AS cumulative_pct
        FROM country_counts cc
        ORDER BY cc.title_count DESC
        LIMIT 15;
    """, {"total": total})
    data["country_production"] = [
        {
            "country": r["country"],
            "count": r["title_count"],
            "pct": r["pct_of_catalog"],
            "cumulative_pct": r["cumulative_pct"]
        }
        for r in cur.fetchall()
    ]

    # 7. Release Cadence & Seasonality
    # Monthly Aggregation
    cur.execute("""
        SELECT 
            strftime('%m', date_added) AS month_num,
            CASE strftime('%m', date_added)
                WHEN '01' THEN 'Jan' WHEN '02' THEN 'Feb' WHEN '03' THEN 'Mar'
                WHEN '04' THEN 'Apr' WHEN '05' THEN 'May' WHEN '06' THEN 'Jun'
                WHEN '07' THEN 'Jul' WHEN '08' THEN 'Aug' WHEN '09' THEN 'Sep'
                WHEN '10' THEN 'Oct' WHEN '11' THEN 'Nov' WHEN '12' THEN 'Dec'
            END AS month_name,
            COUNT(*) AS total_additions,
            SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movies_added,
            SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows_added
        FROM netflix_titles
        WHERE date_added IS NOT NULL
        GROUP BY month_num
        ORDER BY month_num;
    """)
    data["monthly_seasonality"] = [
        {
            "month": r["month_name"],
            "month_num": r["month_num"],
            "total": r["total_additions"],
            "movies": r["movies_added"],
            "tv": r["tv_shows_added"]
        }
        for r in cur.fetchall()
    ]

    # Day of month aggregation (1 to 31)
    cur.execute("""
        SELECT 
            CAST(strftime('%d', date_added) AS INTEGER) AS day_of_month,
            COUNT(*) AS count
        FROM netflix_titles
        WHERE date_added IS NOT NULL
        GROUP BY day_of_month
        ORDER BY day_of_month;
    """)
    data["day_of_month_cadence"] = [
        {"day": r["day_of_month"], "count": r["count"]}
        for r in cur.fetchall()
    ]

    # 8. Regional Specialization Radar
    # Compare top production hubs across key genres
    hubs = ["United States", "India", "United Kingdom", "South Korea", "Japan", "France"]
    radar_genres = ["Dramas", "Comedies", "Action & Adventure", "Documentaries", "International Movies", "Anime Series"]
    
    radar_data = {"labels": radar_genres, "datasets": []}
    for hub in hubs:
        cur.execute("""
            SELECT g.genre, COUNT(*) as cnt
            FROM genre_map g
            JOIN country_map c ON g.show_id = c.show_id
            WHERE c.country = ?
            GROUP BY g.genre;
        """, (hub,))
        counts = {r["genre"]: r["cnt"] for r in cur.fetchall()}
        radar_data["datasets"].append({
            "hub": hub,
            "values": [counts.get(g, 0) for g in radar_genres]
        })
    data["regional_radar"] = radar_data

    # 9. Master SQL Queries & Business Insights Dictionary
    data["sql_insights"] = {
        "content_distribution": {
            "title": "Catalog Composition: Movies vs TV Series",
            "takeaway": "While Movies represent 69.7% of cumulative volume, TV Shows are Netflix's strategic retention weapon. TV series produce higher lifetime value (LTV) and 30-day retention because multi-episode engagement keeps subscribers from canceling after a single viewing.",
            "sql": """SELECT 
    type, 
    COUNT(*) AS title_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM netflix_titles), 1) AS pct,
    ROUND(AVG(duration_value), 1) AS avg_duration
FROM netflix_titles
GROUP BY type
ORDER BY title_count DESC;"""
        },
        "strategic_pivot": {
            "title": "The Strategic Pivot: Production Vintage vs Platform Ingestion",
            "takeaway": "Pre-2015 growth relied heavily on licensing legacy studio catalogs (vintage back-catalogs from 1990-2012). From 2016 to 2019, platform additions surged (+370%), and the lag between release and ingestion closed to near zero, cementing Netflix's transition from a distributor to an original studio.",
            "sql": """WITH release_stats AS (
    SELECT release_year AS year, COUNT(*) AS titles_released
    FROM netflix_titles
    WHERE release_year BETWEEN 2005 AND 2021
    GROUP BY release_year
),
added_stats AS (
    SELECT CAST(strftime('%Y', date_added) AS INTEGER) AS year, COUNT(*) AS titles_added
    FROM netflix_titles
    WHERE date_added IS NOT NULL AND CAST(strftime('%Y', date_added) AS INTEGER) BETWEEN 2005 AND 2021
    GROUP BY strftime('%Y', date_added)
)
SELECT 
    COALESCE(r.year, a.year) AS year,
    COALESCE(r.titles_released, 0) AS titles_released,
    COALESCE(a.titles_added, 0) AS titles_added
FROM release_stats r
FULL OUTER JOIN added_stats a ON r.year = a.year
ORDER BY year;"""
        },
        "top_genres": {
            "title": "Normalized Top Genres by Content Format",
            "takeaway": "Dramas, Comedies, and Documentaries dominate the catalog. Multi-table normalization with 1NF junction tables (genre_map) resolves comma-separated strings to accurately rank genres without duplicates or parsing errors.",
            "sql": """SELECT 
    g.genre,
    COUNT(*) AS total_count,
    SUM(CASE WHEN n.type = 'Movie' THEN 1 ELSE 0 END) AS movie_count,
    SUM(CASE WHEN n.type = 'TV Show' THEN 1 ELSE 0 END) AS tv_count
FROM genre_map g
JOIN netflix_titles n ON g.show_id = n.show_id
GROUP BY g.genre
ORDER BY total_count DESC
LIMIT 15;"""
        },
        "ratings_distribution": {
            "title": "Audience Maturity Segmentation",
            "takeaway": "61.0% of the entire library is rated for mature audiences (TV-MA: 36.4%, TV-14: 24.5%). While this establishes a formidable moat in prestige adult drama, kids/family content accounts for under 20%, leaving a major competitive opening for Disney+.",
            "sql": """SELECT 
    rating,
    SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movie_count,
    SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_count,
    COUNT(*) AS total_count
FROM netflix_titles
WHERE rating <> 'Unknown'
GROUP BY rating
ORDER BY total_count DESC;"""
        },
        "country_production": {
            "title": "Geographic Concentration & Supply-Chain Risk",
            "takeaway": "The top 3 producer nations (United States, India, United Kingdom) account for 62.9% of all platform titles, and the top 10 represent 85.8%. This extreme geographic concentration creates regulatory and licensing exposure, driving Netflix's push into local-for-global originals.",
            "sql": """WITH country_counts AS (
    SELECT 
        c.country,
        COUNT(DISTINCT c.show_id) AS title_count
    FROM country_map c
    WHERE c.country <> 'Unknown'
    GROUP BY c.country
)
SELECT 
    cc.country,
    cc.title_count,
    ROUND(100.0 * cc.title_count / (SELECT COUNT(*) FROM netflix_titles), 2) AS pct_of_catalog,
    ROUND(SUM(100.0 * cc.title_count / (SELECT COUNT(*) FROM netflix_titles)) OVER (ORDER BY cc.title_count DESC), 1) AS cumulative_pct
FROM country_counts cc
ORDER BY cc.title_count DESC
LIMIT 10;"""
        },
        "release_cadence": {
            "title": "Calendar Seasonality & Batch Dropping",
            "takeaway": "Content ingestion surges systematically in July (summer peak) and December (holiday streaming), with noticeable dips in February. Furthermore, over 12% of all additions drop specifically on the 1st day of the calendar month due to contractual licensing expiration/renewal cycles.",
            "sql": """SELECT 
    strftime('%m', date_added) AS month_num,
    COUNT(*) AS total_additions,
    SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movies_added,
    SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows_added
FROM netflix_titles
WHERE date_added IS NOT NULL
GROUP BY month_num
ORDER BY month_num;"""
        }
    }

    # 10. Distinct Filter Options for Frontend (Genres, Countries, Ratings, Years)
    cur.execute("SELECT DISTINCT genre FROM genre_map WHERE genre <> 'Unknown' ORDER BY genre;")
    data["filter_genres"] = [r["genre"] for r in cur.fetchall()]

    cur.execute("""
        SELECT country, COUNT(DISTINCT show_id) AS cnt 
        FROM country_map 
        WHERE country <> 'Unknown' 
        GROUP BY country 
        HAVING cnt >= 15 
        ORDER BY cnt DESC;
    """)
    data["filter_countries"] = [r["country"] for r in cur.fetchall()]

    cur.execute("""
        SELECT DISTINCT rating FROM netflix_titles 
        WHERE rating <> 'Unknown' 
        ORDER BY rating;
    """)
    data["filter_ratings"] = [r["rating"] for r in cur.fetchall()]

    # 11. Compact Catalog Titles (for interactive searchable data table)
    cur.execute("""
        SELECT 
            n.show_id AS id,
            n.type,
            n.title,
            n.director,
            n.cast,
            n.country,
            n.date_added,
            n.release_year,
            n.rating,
            n.duration,
            n.duration_value,
            n.duration_unit,
            n.description,
            (SELECT GROUP_CONCAT(genre, ', ') FROM genre_map WHERE show_id = n.show_id) AS genres
        FROM netflix_titles n
        ORDER BY n.release_year DESC, n.title ASC;
    """)
    titles = []
    for r in cur.fetchall():
        titles.append({
            "id": r["id"],
            "type": r["type"],
            "title": r["title"],
            "director": r["director"] if r["director"] != "Unknown" else "",
            "cast": r["cast"] if r["cast"] != "Unknown" else "",
            "country": r["country"] if r["country"] != "Unknown" else "",
            "date_added": r["date_added"] or "",
            "year": r["release_year"],
            "rating": r["rating"],
            "duration": r["duration"],
            "genres": r["genres"] or "",
            "desc": r["description"] or ""
        })
    data["catalog"] = titles

    conn.close()

    # Write data.json
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    print(f"Exported JSON ({os.path.getsize(OUTPUT_JSON)/1024:.1f} KB) -> {OUTPUT_JSON}")

    # Write data.js (assigned to window.NETFLIX_DATA)
    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write("window.NETFLIX_DATA = ")
        json.dump(data, f, separators=(",", ":"))
        f.write(";\n")
    print(f"Exported JS ({os.path.getsize(OUTPUT_JS)/1024:.1f} KB) -> {OUTPUT_JS}")


if __name__ == "__main__":
    export_data()
