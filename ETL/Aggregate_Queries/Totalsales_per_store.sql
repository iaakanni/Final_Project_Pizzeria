-- 1. Total sales revenue per store
-- Join Orders to Stores so we can label revenue with a human-readable
-- address/city instead of just a store_id number. GROUP BY collapses
-- all orders for the same store into one summed row.
SELECT
    s.store_id,
    s.city,
    s.address,
    SUM(o.total_amount) AS total_revenue
FROM Orders o
JOIN Stores s ON o.store_id = s.store_id
GROUP BY s.store_id, s.city, s.address
ORDER BY total_revenue DESC;

