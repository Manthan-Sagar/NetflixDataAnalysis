-- ==============================================================================
-- Query: 07_release_cadence.sql
-- Business Questions:
-- 1. How has Netflix's content publishing velocity evolved on a month-over-month basis?
-- 2. Is there demonstrable seasonality in release schedules (e.g., Q4 holiday surges vs summer lulls)?
-- 3. Does Netflix batch releases on specific days of the month (e.g., 1st of the month licensing waves)?
-- Strategic Context:
-- Release pacing impacts subscriber churn. Steady cadence sustains year-round engagement,
-- while clustered drops risk post-binge subscription cancellations.
-- ==============================================================================

-- Part A: Month-over-Month Title Additions Time Series
SELECT 
    strftime('%Y-%m', date_added) AS year_month,
    COUNT(*) AS titles_added,
    SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movies_added,
    SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows_added
FROM netflix_titles
WHERE date_added IS NOT NULL
GROUP BY year_month
ORDER BY year_month;

-- Part B: Seasonal Distribution by Calendar Month (Aggregated Across All Years)
-- SELECT 
--     strftime('%m', date_added) AS month_num,
--     CASE strftime('%m', date_added)
--         WHEN '01' THEN 'January'
--         WHEN '02' THEN 'February'
--         WHEN '03' THEN 'March'
--         WHEN '04' THEN 'April'
--         WHEN '05' THEN 'May'
--         WHEN '06' THEN 'June'
--         WHEN '07' THEN 'July'
--         WHEN '08' THEN 'August'
--         WHEN '09' THEN 'September'
--         WHEN '10' THEN 'October'
--         WHEN '11' THEN 'November'
--         WHEN '12' THEN 'December'
--     END AS month_name,
--     COUNT(*) AS total_additions,
--     ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM netflix_titles WHERE date_added IS NOT NULL), 2) AS pct_of_additions
-- FROM netflix_titles
-- WHERE date_added IS NOT NULL
-- GROUP BY month_num
-- ORDER BY month_num;
