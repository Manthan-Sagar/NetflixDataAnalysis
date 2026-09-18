-- ==============================================================================
-- Query: 05_release_trends.sql
-- Business Questions:
-- 1. What is the historical vintage of content available on Netflix (release_year)?
-- 2. When did Netflix experience its rapid catalog acquisition and publishing surges (year_added)?
-- 3. How does the release year compare with the year added, illustrating the strategic pivot
--    from licensing classic back-catalogs to commissioning contemporary Netflix Originals?
-- Strategic Context:
-- Pre-2015 Netflix relied heavily on syndication and third-party studio licensing.
-- From 2016 onward, studio retrenchment (Disney+, HBO Max launch preparation) forced
-- Netflix to heavily accelerate same-year or near-term original releases.
-- ==============================================================================

-- Part A: Volume of Content Produced by Release Year (Content Vintage)
-- SELECT release_year, COUNT(*) AS titles_released
-- FROM netflix_titles
-- GROUP BY release_year
-- ORDER BY release_year;

-- Part B: Volume of Content Ingested by Year Added (Catalog Expansion Velocity)
-- SELECT strftime('%Y', date_added) AS year_added, COUNT(*) AS titles_added
-- FROM netflix_titles
-- WHERE date_added IS NOT NULL
-- GROUP BY year_added
-- ORDER BY year_added;

-- Part C: Unified Comparative Trend (Modern Era: 2000 - Present)
WITH release_stats AS (
    SELECT 
        release_year AS year,
        COUNT(*) AS titles_released
    FROM netflix_titles
    WHERE release_year >= 2000
    GROUP BY release_year
),
added_stats AS (
    SELECT 
        CAST(strftime('%Y', date_added) AS INTEGER) AS year,
        COUNT(*) AS titles_added
    FROM netflix_titles
    WHERE date_added IS NOT NULL
    GROUP BY strftime('%Y', date_added)
)
SELECT 
    COALESCE(r.year, a.year) AS year,
    COALESCE(r.titles_released, 0) AS titles_released,
    COALESCE(a.titles_added, 0) AS titles_added,
    (COALESCE(a.titles_added, 0) - COALESCE(r.titles_released, 0)) AS net_delta
FROM release_stats r
FULL OUTER JOIN added_stats a ON r.year = a.year
ORDER BY year;
