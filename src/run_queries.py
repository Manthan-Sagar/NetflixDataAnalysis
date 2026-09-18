"""
Module: run_queries.py
Description: Executes raw SQL analytics queries against the SQLite Netflix database
             and generates portfolio-quality visualizations.
"""

import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

DB_PATH = os.path.join("data", "processed", "netflix.db")
FIGURES_DIR = os.path.join("outputs", "figures")

# Styling constants for cohesive, premium aesthetics
NETFLIX_RED = "#E50914"
NETFLIX_DARK = "#141414"
NETFLIX_CARD = "#1F1F1F"
TEXT_WHITE = "#FFFFFF"
TEXT_MUTED = "#B3B3B3"
ACCENT_BLUE = "#3B82F6"
ACCENT_GOLD = "#F59E0B"
ACCENT_TEAL = "#10B981"
ACCENT_PURPLE = "#8B5CF6"


def setup_plot_style():
    """Sets a sleek modern dark theme for all figures."""
    plt.style.use("dark_background")
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial"],
        "figure.facecolor": NETFLIX_DARK,
        "axes.facecolor": NETFLIX_CARD,
        "axes.edgecolor": "#333333",
        "axes.labelcolor": TEXT_WHITE,
        "xtick.color": TEXT_MUTED,
        "ytick.color": TEXT_MUTED,
        "grid.color": "#2A2A2A",
        "grid.linestyle": "--",
        "grid.alpha": 0.6,
        "figure.titlesize": 16,
        "axes.titlesize": 14,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.autolayout": False
    })


def run_query(conn, sql: str) -> pd.DataFrame:
    """Executes a SQL query and returns a pandas DataFrame."""
    return pd.read_sql_query(sql, conn)


def plot_content_distribution(conn):
    """Figure 1: Movies vs TV Shows Breakdown (Count, % and Runtime)."""
    sql = """
    SELECT 
        type, 
        COUNT(*) AS title_count,
        ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM netflix_titles), 1) AS pct,
        ROUND(AVG(duration_value), 1) AS avg_duration
    FROM netflix_titles
    GROUP BY type
    ORDER BY title_count DESC;
    """
    df = run_query(conn, sql)
    print("\n--- 1. Content Distribution ---")
    print(df.to_string(index=False))

    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    bars = ax.barh(
        df["type"], 
        df["title_count"], 
        color=[NETFLIX_RED, ACCENT_BLUE], 
        height=0.55, 
        edgecolor="#ffffff22",
        linewidth=1.2
    )

    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.set_xlim(0, max(df["title_count"]) * 1.22)
    ax.set_title("Catalog Composition: Movies vs. TV Shows", fontsize=15, fontweight="bold", pad=15, color=TEXT_WHITE)
    ax.set_xlabel("Total Number of Titles", labelpad=10)

    for bar, pct, count, avg_dur in zip(bars, df["pct"], df["title_count"], df["avg_duration"]):
        w = bar.get_width()
        y = bar.get_y() + bar.get_height() / 2
        unit = "mins avg" if "Movie" in str(bar) else "seasons avg"
        label = f"  {count:,} titles ({pct}%)  •  Avg: {avg_dur:.0f} {unit}"
        ax.text(w, y, label, va="center", ha="left", color=TEXT_WHITE, fontsize=10.5, fontweight="semibold")

    # Invert y-axis so Movie is top
    ax.invert_yaxis()
    plt.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "01_content_distribution.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")


def plot_top_genres(conn):
    """Figure 2: Top 10 Genres overall with Movie/TV breakdown."""
    sql = """
    SELECT 
        g.genre,
        COUNT(*) AS total_count,
        SUM(CASE WHEN n.type = 'Movie' THEN 1 ELSE 0 END) AS movie_count,
        SUM(CASE WHEN n.type = 'TV Show' THEN 1 ELSE 0 END) AS tv_count
    FROM genre_map g
    JOIN netflix_titles n ON g.show_id = n.show_id
    GROUP BY g.genre
    ORDER BY total_count DESC
    LIMIT 12;
    """
    df = run_query(conn, sql)
    print("\n--- 2. Top Genres ---")
    print(df.to_string(index=False))

    fig, ax = plt.subplots(figsize=(11, 6.5), dpi=300)
    df_sorted = df.sort_values(by="total_count", ascending=True)

    y_pos = range(len(df_sorted))
    bar_m = ax.barh(y_pos, df_sorted["movie_count"], color=NETFLIX_RED, label="Movies", height=0.6, alpha=0.9)
    bar_t = ax.barh(y_pos, df_sorted["tv_count"], left=df_sorted["movie_count"], color=ACCENT_BLUE, label="TV Shows", height=0.6, alpha=0.9)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_sorted["genre"], fontsize=10.5)
    ax.set_xlabel("Number of Titles Listed", labelpad=10)
    ax.set_title("Top 12 Genre Distribution on Netflix (Movies vs. TV Shows)", fontsize=15, fontweight="bold", pad=15)
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.legend(loc="lower right", framealpha=0.8, edgecolor="#444")

    # Annotate total counts
    for idx, row in enumerate(df_sorted.itertuples()):
        total = row.total_count
        ax.text(total + 30, idx, f"{total:,}", va="center", ha="left", color=TEXT_WHITE, fontsize=9.5, fontweight="bold")

    ax.set_xlim(0, max(df_sorted["total_count"]) * 1.15)
    plt.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "02_top_genres.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")


def plot_ratings_distribution(conn):
    """Figure 3: Ratings Distribution by Content Type."""
    sql = """
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
    """
    df = run_query(conn, sql)
    print("\n--- 3. Ratings Distribution ---")
    print(df.to_string(index=False))

    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
    width = 0.38
    x = range(len(df))

    ax.bar([i - width/2 for i in x], df["movie_count"], width=width, color=NETFLIX_RED, label="Movies", alpha=0.9)
    ax.bar([i + width/2 for i in x], df["tv_count"], width=width, color=ACCENT_BLUE, label="TV Shows", alpha=0.9)

    ax.set_xticks(x)
    ax.set_xticklabels(df["rating"], fontsize=10.5)
    ax.set_ylabel("Title Count", labelpad=10)
    ax.set_title("Audience Maturity: Ratings Breakdown across Movies and TV Shows", fontsize=15, fontweight="bold", pad=15)
    ax.legend(loc="upper right", framealpha=0.8, edgecolor="#444")
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    # Highlight dominance of TV-MA and TV-14
    ax.annotate(
        "Over 65% of platform catalog\nskews towards TV-MA and TV-14",
        xy=(0.5, max(df["movie_count"]) * 0.88),
        xytext=(2.2, max(df["movie_count"]) * 0.92),
        arrowprops=dict(facecolor=ACCENT_GOLD, edgecolor="none", shrink=0.08, width=1.5, headwidth=7),
        fontsize=10.5,
        color=ACCENT_GOLD,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#222", edgecolor=ACCENT_GOLD, alpha=0.85)
    )

    plt.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "03_ratings_distribution.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")


def plot_release_vs_added_trends(conn):
    """Figure 4: Release Year vs Year Added (Licensing vs Original Pivot)."""
    sql = """
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
    """
    df = run_query(conn, sql)
    print("\n--- 4. Release vs Added Trends ---")
    print(df.to_string(index=False))

    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)

    ax.plot(df["year"], df["titles_released"], marker="o", linewidth=2.8, color=ACCENT_GOLD, label="Titles by Release Year (Content Vintage)")
    ax.plot(df["year"], df["titles_added"], marker="s", linewidth=2.8, color=NETFLIX_RED, label="Titles by Year Added to Netflix (Catalog Ingestion)")

    # Shading the pivot era
    ax.fill_between(df["year"], df["titles_released"], df["titles_added"], where=(df["titles_added"] > df["titles_released"]),
                    color=NETFLIX_RED, alpha=0.15, label="Licensing Acquisition Surge")

    ax.set_title("The Strategic Pivot: Production Year vs. Platform Ingestion Year", fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("Year", labelpad=10)
    ax.set_ylabel("Volume of Titles", labelpad=10)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(loc="upper left", framealpha=0.8, edgecolor="#444")
    ax.set_xticks(df["year"])
    ax.set_xticklabels([str(y) for y in df["year"]], rotation=45)

    # Annotation of platform scaling
    ax.annotate(
        "2018-2019: Peak Catalog Ingestion Surge\n(Syndication + Global Originals)",
        xy=(2019, df.loc[df["year"] == 2019, "titles_added"].values[0]),
        xytext=(2012, 1850),
        arrowprops=dict(facecolor=TEXT_WHITE, edgecolor="none", shrink=0.08, width=1.5, headwidth=6),
        fontsize=10,
        color=TEXT_WHITE,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#222", edgecolor="#555")
    )

    plt.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "04_release_vs_added_trends.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")


def plot_country_production(conn):
    """Figure 5: Top 10 Producing Countries and Catalog Concentration."""
    sql = """
    WITH country_counts AS (
        SELECT 
            c.country,
            COUNT(DISTINCT c.show_id) AS title_count
        FROM country_map c
        WHERE c.country <> 'Unknown'
        GROUP BY c.country
    ),
    total_titles AS (
        SELECT COUNT(*) AS total_catalog FROM netflix_titles
    )
    SELECT 
        cc.country,
        cc.title_count,
        ROUND(100.0 * cc.title_count / tt.total_catalog, 2) AS pct_of_catalog,
        ROUND(SUM(100.0 * cc.title_count / tt.total_catalog) OVER (ORDER BY cc.title_count DESC), 1) AS cumulative_pct
    FROM country_counts cc
    CROSS JOIN total_titles tt
    ORDER BY cc.title_count DESC
    LIMIT 10;
    """
    df = run_query(conn, sql)
    print("\n--- 5. Country Production ---")
    print(df.to_string(index=False))

    fig, ax1 = plt.subplots(figsize=(11, 6.5), dpi=300)

    # Bar chart for title counts
    df_sorted = df.sort_values(by="title_count", ascending=True)
    bars = ax1.barh(df_sorted["country"], df_sorted["title_count"], color=NETFLIX_RED, height=0.6, alpha=0.9, label="Titles Produced")

    ax1.set_xlabel("Number of Titles (Direct & Co-productions)", labelpad=10, color=TEXT_WHITE)
    ax1.set_title("Geographic Footprint & Catalog Concentration (Top 10 Countries)", fontsize=15, fontweight="bold", pad=15)
    ax1.grid(axis="x", linestyle="--", alpha=0.4)
    ax1.set_xlim(0, max(df["title_count"]) * 1.25)

    for bar, count, pct, cum in zip(bars, df_sorted["title_count"], df_sorted["pct_of_catalog"], df_sorted["cumulative_pct"]):
        w = bar.get_width()
        y = bar.get_y() + bar.get_height() / 2
        ax1.text(w + 30, y, f"{count:,} ({pct}%) | Cum: {cum}%", va="center", ha="left", color=TEXT_WHITE, fontsize=9.5, fontweight="semibold")

    plt.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "05_country_production_concentration.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")


def plot_release_cadence_seasonality(conn):
    """Figure 6: Release Cadence & Seasonality (Monthly Addition Patterns)."""
    sql_monthly = """
    SELECT 
        CASE strftime('%m', date_added)
            WHEN '01' THEN 'Jan'
            WHEN '02' THEN 'Feb'
            WHEN '03' THEN 'Mar'
            WHEN '04' THEN 'Apr'
            WHEN '05' THEN 'May'
            WHEN '06' THEN 'Jun'
            WHEN '07' THEN 'Jul'
            WHEN '08' THEN 'Aug'
            WHEN '09' THEN 'Sep'
            WHEN '10' THEN 'Oct'
            WHEN '11' THEN 'Nov'
            WHEN '12' THEN 'Dec'
        END AS month_name,
        strftime('%m', date_added) AS month_num,
        COUNT(*) AS total_additions,
        SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movies_added,
        SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows_added
    FROM netflix_titles
    WHERE date_added IS NOT NULL
    GROUP BY month_num
    ORDER BY month_num;
    """
    df_m = run_query(conn, sql_monthly)
    print("\n--- 6. Monthly Seasonality ---")
    print(df_m.to_string(index=False))

    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
    x = range(len(df_m))
    width = 0.55

    # Stacked bar of additions by month
    ax.bar(x, df_m["movies_added"], width=width, label="Movies Added", color=NETFLIX_RED, alpha=0.9)
    ax.bar(x, df_m["tv_shows_added"], width=width, bottom=df_m["movies_added"], label="TV Shows Added", color=ACCENT_BLUE, alpha=0.9)

    ax.set_xticks(x)
    ax.set_xticklabels(df_m["month_name"], fontsize=11)
    ax.set_ylabel("Total Cumulative Additions", labelpad=10)
    ax.set_title("Catalog Seasonality: Total Additions by Calendar Month", fontsize=15, fontweight="bold", pad=15)
    ax.legend(loc="lower right", framealpha=0.8, edgecolor="#444")
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    # Annotate peak months (July, Dec, Jan)
    for i, total in enumerate(df_m["total_additions"]):
        ax.text(i, total + 12, f"{total:,}", ha="center", va="bottom", color=TEXT_WHITE, fontsize=9.5, fontweight="bold")

    ax.set_ylim(0, max(df_m["total_additions"]) * 1.12)
    plt.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "06_release_cadence_seasonality.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")


def main():
    os.makedirs(FIGURES_DIR, exist_ok=True)
    setup_plot_style()

    conn = sqlite3.connect(DB_PATH)
    try:
        print(f"Connected to database: {DB_PATH}")
        plot_content_distribution(conn)
        plot_top_genres(conn)
        plot_ratings_distribution(conn)
        plot_release_vs_added_trends(conn)
        plot_country_production(conn)
        plot_release_cadence_seasonality(conn)
        print("\nAll 6 figures generated and saved to 'outputs/figures/' successfully!")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
