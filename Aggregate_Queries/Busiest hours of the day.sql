
-- 5. Busiest hours of the day for orders
-- EXTRACT(HOUR FROM ...) pulls just the hour (0-23) out of the full
-- timestamp, discarding the date. Grouping by that hour then counting
-- orders shows which hour has the most order volume, regardless of
-- which day it happened on.
SELECT
    EXTRACT(HOUR FROM order_timestamp) AS hour_of_day,
    COUNT(*) AS number_of_orders
FROM Orders
GROUP BY hour_of_day
ORDER BY number_of_orders DESC;

