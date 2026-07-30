-- 3. Most popular menu item by quantity sold (across all stores)
-- This is why Order_Items exists as its own table: "quantity sold"
-- lives at the line-item level, not the order level. SUM(quantity)
-- adds up every time that item appeared on any order, anywhere.
SELECT
    mi.item_id,
    mi.name,
    SUM(oi.quantity) AS total_quantity_sold
FROM Order_Items oi
JOIN Menu_Items mi ON oi.item_id = mi.item_id
GROUP BY mi.item_id, mi.name
ORDER BY total_quantity_sold DESC
LIMIT 1;