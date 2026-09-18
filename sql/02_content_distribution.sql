-- ==============================================================================
-- Query: 02_content_distribution.sql
-- Business Questions:
-- 1. What is the macro split between Movies and TV Shows on Netflix?
-- 2. How heavily is the platform weighted toward feature-length films vs episodic series?
-- 3. What is the average runtime for movies and average season count for TV shows?
-- Strategic Context:
-- TV shows drive higher multi-month subscriber retention (binge loyalty), while movies
-- drive acquisition surges. Understanding the volume split reveals Netflix's retention vs acquisition engine.
-- ==============================================================================

SELECT 
    type,
    COUNT(*) AS title_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM netflix_titles), 2) AS pct_of_catalog,
    ROUND(AVG(duration_value), 1) AS avg_duration,
    MIN(duration_value) AS min_duration,
    MAX(duration_value) AS max_duration
FROM netflix_titles
GROUP BY type
ORDER BY title_count DESC;
