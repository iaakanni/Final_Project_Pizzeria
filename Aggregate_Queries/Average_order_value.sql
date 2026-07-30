-- 4. Average order value
-- A single aggregate over the whole Orders table — no JOIN or GROUP BY
-- needed since we want one number for the entire business.
SELECT
    ROUND(AVG(total_amount), 2) AS average_order_value
FROM Orders;
