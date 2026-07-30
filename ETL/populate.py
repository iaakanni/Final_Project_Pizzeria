


import os
import random
from datetime import datetime

import psycopg2
from psycopg2.extras import execute_values
from faker import Faker
from dotenv import load_dotenv


load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", "5432"),
}

# fake = the Faker instance. Every fake.name(), fake.email(), etc. call
# below pulls from Faker's built-in realistic-data templates.


fake = Faker()


NUM_STORES = 4
NUM_MENU_ITEMS = 25
NUM_INGREDIENTS = 45
NUM_CUSTOMERS = 1200
NUM_ORDERS = 5500
AVG_ITEMS_PER_ORDER = 3

MENU_CATEGORIES = {
    "Pizza": ["Small", "Medium", "Large"],
    "Drink": ["330ml", "500ml", "1L"],
    "Side": ["N/A"],
    "Dessert": ["N/A"],
}
PIZZA_NAMES = [
    "Pepperoni", "Margherita", "Hawaiian", "BBQ Chicken", "Veggie Supreme",
    "Meat Lovers", "Four Cheese", "Buffalo Chicken", "Mushroom Truffle",
]
DRINK_NAMES = ["Cola", "Lemonade", "Root Beer", "Sparkling Water", "Iced Tea"]
SIDE_NAMES = ["Garlic Bread", "Cheesy Bread", "Buffalo Wings", "Caesar Salad"]
DESSERT_NAMES = ["Cinnamon Sticks", "Chocolate Chip Cookie", "Tiramisu"]

INGREDIENT_UNITS = ["kg", "liters", "units"]


def get_connection():
    """Open one connection, reused for the whole script."""
    return psycopg2.connect(**DB_CONFIG)




def generate_stores(n):
    rows = []
    for _ in range(n):
        rows.append((
            fake.street_address(),
            fake.city(),
            fake.unique.phone_number()[:20],
        ))
    return rows


def generate_ingredients(n):
    # fake.unique ensures Faker never repeats a value across calls,
    # which matters here because `name` has a UNIQUE constraint.
    base_names = [
        "Pizza Dough", "Mozzarella Cheese", "Tomato Sauce", "Pepperoni",
        "Mushrooms", "Onions", "Green Peppers", "Olives", "Bacon",
        "Chicken Breast", "Pineapple", "BBQ Sauce", "Parmesan",
        "Basil", "Garlic", "Ham", "Sausage", "Jalapenos", "Ranch Dressing",
        "Cola Syrup", "Lemon Juice", "Sugar", "Ice", "Lettuce", "Croutons",
    ]
    # Pad the list with faker-generated ingredient-like words if we need
    # more than our curated list provides.
    while len(base_names) < n:
        base_names.append(fake.unique.word().capitalize() + " Extract")

    rows = []
    for name in base_names[:n]:
        rows.append((
            name,
            round(random.uniform(5, 500), 2),
            random.choice(INGREDIENT_UNITS),
        ))
    return rows


def generate_menu_items(n):
    rows = []
    catalog = []
    for name in PIZZA_NAMES:
        catalog.append((name, "Pizza"))
    for name in DRINK_NAMES:
        catalog.append((name, "Drink"))
    for name in SIDE_NAMES:
        catalog.append((name, "Side"))
    for name in DESSERT_NAMES:
        catalog.append((name, "Dessert"))

    for base_name, category in catalog[:n]:
        size = random.choice(MENU_CATEGORIES[category])
        price = round(random.uniform(3, 22), 2) if category == "Pizza" else round(random.uniform(1.5, 8), 2)
        full_name = f"{size} {base_name}" if size != "N/A" else base_name
        rows.append((full_name, category, size, price))
    return rows


def generate_customers(n):
    rows = []
    for _ in range(n):
        first = fake.first_name()
        last = fake.last_name()
        rows.append((
            first,
            last,
            fake.unique.email(),
            fake.unique.phone_number()[:20],
        ))
    return rows


def generate_menu_item_ingredients(item_ids, ingredient_ids):
    """Every pizza/side gets 3-6 random ingredients as its 'recipe'."""
    rows = []
    for item_id in item_ids:
        chosen = random.sample(ingredient_ids, k=random.randint(3, 6))
        for ing_id in chosen:
            rows.append((item_id, ing_id, round(random.uniform(0.05, 2.0), 2)))
    return rows


def generate_orders(n, customer_ids, store_ids):
    """
    Orders reference existing customer_ids/store_ids — this is why
    Customers and Stores must already exist in the DB by this point.
    total_amount is a placeholder here; we recalculate it after
    generating Order_Items so it reflects the real line-item sum.
    """
    rows = []
    for _ in range(n):
        customer_id = random.choice(customer_ids)
        store_id = random.choice(store_ids)
        order_time = fake.date_time_this_year()
        rows.append((customer_id, store_id, order_time, 0.00))
    return rows


def generate_order_items(order_ids, menu_items):
    """
    menu_items is a list of (item_id, price) so unit_price can be
    snapshotted from the current menu price at "order time".
    Returns order_items rows AND a dict of order_id -> total, so the
    Orders table can be updated with correct totals afterward.
    """
    rows = []
    order_totals = {}
    for order_id in order_ids:
        num_items = max(1, round(random.gauss(AVG_ITEMS_PER_ORDER, 1)))
        running_total = 0.0
        for _ in range(num_items):
            item_id, price = random.choice(menu_items)
            qty = random.randint(1, 3)
            rows.append((order_id, item_id, qty, price))
            running_total += float(price) * qty
        order_totals[order_id] = round(running_total, 2)
    return rows, order_totals


def main():
    conn = get_connection()
    cur = conn.cursor()

    try:
        # ---- Independent tables first ----
        print("Inserting Stores...")
        store_rows = generate_stores(NUM_STORES)
        store_ids = execute_values(
            cur,
            "INSERT INTO Stores (address, city, phone_number) VALUES %s RETURNING store_id",
            store_rows,
            fetch=True,
        )
        store_ids = [row[0] for row in store_ids]

        print("Inserting Ingredients...")
        ingredient_rows = generate_ingredients(NUM_INGREDIENTS)
        ingredient_ids = execute_values(
            cur,
            "INSERT INTO Ingredients (name, stock_quantity, unit) VALUES %s RETURNING ingredient_id",
            ingredient_rows,
            fetch=True,
        )
        ingredient_ids = [row[0] for row in ingredient_ids]

        print("Inserting Menu_Items...")
        menu_rows = generate_menu_items(NUM_MENU_ITEMS)
        menu_result = execute_values(
            cur,
            "INSERT INTO Menu_Items (name, category, size, price) VALUES %s RETURNING item_id, price",
            menu_rows,
            fetch=True,
        )
        menu_items = [(row[0], row[1]) for row in menu_result]  # (item_id, price)
        item_ids = [row[0] for row in menu_items]

        print("Inserting Customers...")
        customer_rows = generate_customers(NUM_CUSTOMERS)
        customer_ids = execute_values(
            cur,
            "INSERT INTO Customers (first_name, last_name, email, phone_number) VALUES %s RETURNING customer_id",
            customer_rows,
            fetch=True,
        )
        customer_ids = [row[0] for row in customer_ids]

        conn.commit()  # Safe to commit — nothing below depends on rolling these back together.

        # ---- Junction table: needs Menu_Items + Ingredients to exist ----
        print("Inserting Menu_Item_Ingredients...")
        recipe_rows = generate_menu_item_ingredients(item_ids, ingredient_ids)
        execute_values(
            cur,
            "INSERT INTO Menu_Item_Ingredients (item_id, ingredient_id, quantity_required) VALUES %s",
            recipe_rows,
        )
        conn.commit()

        # ---- Orders: needs Customers + Stores ----
        print(f"Inserting {NUM_ORDERS} Orders...")
        order_rows = generate_orders(NUM_ORDERS, customer_ids, store_ids)
        order_ids = execute_values(
            cur,
            "INSERT INTO Orders (customer_id, store_id, order_timestamp, total_amount) VALUES %s RETURNING order_id",
            order_rows,
            fetch=True,
        )
        order_ids = [row[0] for row in order_ids]
        conn.commit()

        # ---- Order_Items: needs Orders + Menu_Items ----
        print("Inserting Order_Items (this generates ~15,000+ rows)...")
        order_item_rows, order_totals = generate_order_items(order_ids, menu_items)
        execute_values(
            cur,
            "INSERT INTO Order_Items (order_id, item_id, quantity, unit_price) VALUES %s",
            order_item_rows,
        )
        conn.commit()

        # ---- Backfill correct totals now that we know each order's real total ----
        print("Updating Orders.total_amount from actual line items...")
        update_data = [(total, order_id) for order_id, total in order_totals.items()]
        cur.executemany(
            "UPDATE Orders SET total_amount = %s WHERE order_id = %s",
            update_data,
        )
        conn.commit()

        print("Done. Row counts:")
        for table in ["Stores", "Ingredients", "Menu_Items", "Customers",
                      "Menu_Item_Ingredients", "Orders", "Order_Items"]:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            print(f"  {table}: {cur.fetchone()[0]}")

    except Exception as e:
        conn.rollback()
        print(f"Error during population, rolled back: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
