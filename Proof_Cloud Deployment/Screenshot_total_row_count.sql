SELECT 'stores' AS table_name, COUNT(*) FROM Stores
UNION ALL SELECT 'customers', COUNT(*) FROM Customers
UNION ALL SELECT 'ingredients', COUNT(*) FROM Ingredients
UNION ALL SELECT 'menu_items', COUNT(*) FROM Menu_Items
UNION ALL SELECT 'menu_item_ingredients', COUNT(*) FROM Menu_Item_Ingredients
UNION ALL SELECT 'orders', COUNT(*) FROM Orders
UNION ALL SELECT 'order_items', COUNT(*) FROM Order_Items;