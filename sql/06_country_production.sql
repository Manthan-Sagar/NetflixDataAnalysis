-- ==============================================================================
-- Query: 06_country_production.sql
-- Business Questions:
-- 1. Which countries are the largest content suppliers to the Netflix ecosystem?
-- 2. How concentrated is Netflix's catalog among the top producing nations?
-- 3. What genre specializations exist across key content hub markets (e.g. US, India, UK, Japan, South Korea)?
-- Strategic Context:
-- Content concentration creates regulatory and licensing vulnerabilities. Over-reliance on
-- US productions poses risks in non-English speaking markets where local content drives organic subscriber acquisition.
-- ==============================================================================

-- Part A: Top 15 Content-Producing Countries with Catalog Concentration & Cumulative Share
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
    ROUND(SUM(100.0 * cc.title_count / tt.total_catalog) OVER (ORDER BY cc.title_count DESC), 2) AS cumulative_pct
FROM country_counts cc
CROSS JOIN total_titles tt
ORDER BY cc.title_count DESC
LIMIT 15;

-- Part B: Genre Specialization Across Major Production Hubs
-- SELECT 
--     c.country, 
--     g.genre, 
--     COUNT(*) AS title_count
-- FROM country_map c
-- JOIN genre_map g ON c.show_id = g.show_id
-- WHERE c.country IN ('United States', 'India', 'United Kingdom', 'Japan', 'South Korea')
-- GROUP BY c.country, g.genre
-- ORDER BY c.country, title_count DESC;
