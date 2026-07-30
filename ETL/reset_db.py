# reset_db.py
import psycopg2
from populate import DB_CONFIG  # reuse the same config

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()
cur.execute("""
    TRUNCATE Order_Items, Orders, Menu_Item_Ingredients, Customers, Menu_Items, Ingredients, Stores
    RESTART IDENTITY CASCADE;
""")
conn.commit()
cur.close()
conn.close()
print("Database reset.")