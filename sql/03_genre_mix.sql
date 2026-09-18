-- ==============================================================================
-- Query: 03_genre_mix.sql
-- Business Questions:
-- 1. Which genres dominate Netflix's global catalog?
-- 2. How does the genre landscape diverge between Movies and episodic TV Shows?
-- 3. Are high-budget niches (e.g. Sci-Fi) as common as broad appeal content (Dramas, Comedies)?
-- Strategic Context:
-- Uncovering genre dominance informs content greenlighting and acquisition budgeting.
-- Joining the normalized 'genre_map' ensures titles tagged with multiple genres are
-- accurately counted across their appropriate thematic categories without string distortion.
-- ==============================================================================

-- Top 20 Genres Split by Content Type (Movies vs TV Shows)
SELECT 
    g.genre,
    n.type,
    COUNT(*) AS title_count,
    ROUND(100.0 * COUNT(*) / (
        SELECT COUNT(*) 
        FROM genre_map gm 
        JOIN netflix_titles nt ON gm.show_id = nt.show_id 
        WHERE nt.type = n.type
    ), 2) AS pct_within_type
FROM genre_map g
JOIN netflix_titles n ON g.show_id = n.show_id
GROUP BY g.genre, n.type
ORDER BY title_count DESC
LIMIT 20;
