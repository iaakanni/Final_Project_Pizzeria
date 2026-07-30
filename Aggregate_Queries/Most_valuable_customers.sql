-- 2. Top 10 most valuable customers by total spending
-- Same pattern as #1, but grouped by customer instead of store, plus
-- LIMIT 10 to only keep the highest spenders. ORDER BY must come
-- before LIMIT so "top 10" actually means the top 10, not a random 10.
SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    SUM(o.total_amount) AS lifetime_spend
FROM Orders o
JOIN Customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name
ORDER BY lifetime_spend DESC
LIMIT 10;

