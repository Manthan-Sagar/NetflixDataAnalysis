-- ==============================================================================
-- Query: 04_ratings.sql
-- Business Questions:
-- 1. What is the maturity rating distribution across Netflix's catalog?
-- 2. How does audience targeting differ between feature films and TV shows?
-- 3. What percentage of the catalog requires parental maturity filters (TV-MA, R, NC-17)?
-- Strategic Context:
-- Audience maturity positioning determines subscriber demographics. A catalog skewed
-- heavily towards TV-MA/R positions Netflix as a prestige adult streaming destination,
-- while family content (TV-Y, TV-G, PG) drives multi-profile household retention.
-- ==============================================================================

SELECT 
    rating,
    type,
    COUNT(*) AS title_count,
    ROUND(100.0 * COUNT(*) / (
        SELECT COUNT(*) 
        FROM netflix_titles t2 
        WHERE t2.type = netflix_titles.type
    ), 2) AS pct_within_type,
    CASE 
        WHEN rating IN ('TV-MA', 'R', 'NC-17', 'NR', 'UR') THEN 'Adult / Mature (18+)'
        WHEN rating IN ('TV-14', 'PG-13') THEN 'Teens / Young Adults (14-17)'
        WHEN rating IN ('TV-PG', 'PG') THEN 'Parental Guidance / Older Kids'
        WHEN rating IN ('TV-Y', 'TV-Y7', 'TV-Y7-FV', 'TV-G', 'G') THEN 'Kids / Family Friendly'
        ELSE 'Unrated / Other'
    END AS maturity_bracket
FROM netflix_titles
GROUP BY rating, type
ORDER BY title_count DESC;
