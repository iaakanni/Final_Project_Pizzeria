# RushMore Pizzeria — Enterprise Database System

Capstone project migrating RushMore Pizzeria from a single `orders.json` file to a
production-ready, cloud-hosted PostgreSQL database — designed, deployed, populated
with 10,000+ rows of masked/synthetic data, and validated with business-intelligence
queries.

## Architecture

```
 Python (Faker + psycopg2)          Azure Database for PostgreSQL
 ┌─────────────────────┐            Flexible Server
 │  populate.py         │──insert──▶  ┌───────────────────────┐
 │  reads .env creds    │            │  rushmore_db           │
 └─────────────────────┘            │  7 normalized tables    │
                                     └───────────┬───────────┘
                                                 │
                        ┌────────────────────────┼────────────────────────┐
                        ▼                        ▼                        ▼
                    pgAdmin                 Tableau Public          (BI tool of choice)
              (schema deployment,          (Top 10 customers,
               row-count verification)      analytics queries)
```

## Repository Contents

| File | Purpose |
|---|---|
| `schema.sql` | All `CREATE TABLE` statements — the normalized (3NF) schema |
| `populate.py` | Faker + psycopg2 script that seeds the database |
| `analytics_queries.sql` | The 5 business-question SQL queries (Part 5) |
| `requirements.txt` | Python dependencies |
| `.env.example` | Template for required environment variables (never commit a real `.env`) |
| `README.md` | This file |
| `RushMore_Capstone_Presentation.pptx` | Final presentation deck |

## Schema Overview

7 tables, normalized to Third Normal Form (3NF):

- **Stores** — physical locations
- **Customers** — PII for registered customers
- **Ingredients** — master stock list
- **Menu_Items** — product catalog (includes `price`, added beyond the original spec
  since `Order_Items` and `Orders.total_amount` both need a price source)
- **Menu_Item_Ingredients** — junction table modeling each item's "recipe"
  (many-to-many between Menu_Items and Ingredients)
- **Orders** — one row per transaction (the "receipt header")
- **Order_Items** — one row per line item on an order (the "receipt lines"),
  with `unit_price` snapshotted at order time so historical orders remain accurate
  even after menu prices change later

Foreign keys use different `ON DELETE` behaviors intentionally:
- `Orders.customer_id` → `SET NULL` (preserve order history if a customer account is deleted)
- `Orders.store_id` → `RESTRICT` (a store can't be deleted while it has order history)
- `Order_Items.order_id` → `CASCADE` (deleting an order removes its line items)
- `Order_Items.item_id` / `Menu_Item_Ingredients.ingredient_id` → `RESTRICT`
  (protect referenced catalog/inventory data)

## Setup & Run Instructions

### 1. Provision the cloud database (Azure)

1. In the Azure Portal: **Create a resource → Databases → Azure Database for PostgreSQL Flexible Server**
2. Fill in subscription, resource group, region, server name, and set PostgreSQL
   authentication (admin username + password)
3. Under **Networking**, enable public access and add a firewall rule for your
   current IP
4. After the server deploys, create a database named `rushmore_db` from the
   server's **Databases** page

### 2. Deploy the schema

1. Connect to the server in **pgAdmin** (host = `<server-name>.postgres.database.azure.com`,
   port `5432`, SSL mode = **Require**)
2. Right-click `rushmore_db` → **Query Tool**
3. Open and run `schema.sql`
4. Verify: `SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';`
   should list all 7 tables

### 3. Configure credentials

Copy `.env.example` to `.env` and fill in your real values:

```
DB_HOST=your-server-name.postgres.database.azure.com
DB_NAME=rushmore_db
DB_USER=your_admin_username
DB_PASSWORD=your_password_here
DB_PORT=5432
```

**Never commit `.env` to git** — add it to `.gitignore`.

### 4. Populate the database

```bash
pip install -r requirements.txt --break-system-packages
python populate.py
```

> **Note on execution environment:** this project was run and debugged inside a
> `.ipynb` notebook in VS Code (Interactive Window / Jupyter-style cell execution)
> rather than as a plain `.py` script. This is convenient for step-by-step
> inspection, but it introduces a real risk: the Python kernel retains function
> and variable definitions across cell re-runs, so an edited function can appear
> to "not update" if a stale cell defining an older version is still in memory.
> **Recommendation:** for one-shot data-population jobs like this, run
> `python populate.py` directly from a terminal instead of cell-by-cell — it
> removes an entire category of stale-state bugs (see Challenges below).

### 5. Verify row counts

```sql
SELECT 'stores' AS table_name, COUNT(*) FROM Stores
UNION ALL SELECT 'customers', COUNT(*) FROM Customers
UNION ALL SELECT 'ingredients', COUNT(*) FROM Ingredients
UNION ALL SELECT 'menu_items', COUNT(*) FROM Menu_Items
UNION ALL SELECT 'menu_item_ingredients', COUNT(*) FROM Menu_Item_Ingredients
UNION ALL SELECT 'orders', COUNT(*) FROM Orders
UNION ALL SELECT 'order_items', COUNT(*) FROM Order_Items;
```

### 6. Run the analytics queries

Open `analytics_queries.sql` in pgAdmin's Query Tool (connected to `rushmore_db`)
and run each of the 5 business questions, or connect Tableau Public / Power BI /
Looker Studio directly to the same Postgres instance for interactive analysis.

### Resetting during development

If a run fails partway through and you need a clean slate:

```sql
TRUNCATE Order_Items, Orders, Menu_Item_Ingredients, Customers, Menu_Items, Ingredients, Stores
RESTART IDENTITY CASCADE;
```

## Challenges Encountered & Resolved

Real debugging log from building this project, kept here because working through
these is as much a part of the DBA/data-engineering skill set as the design itself:

1. **`password authentication failed`** — traced to a stray character (trailing
   space) in the `.env` file's password value, invisible until printed with
   `repr()`.
2. **`no pg_hba.conf entry ... no encryption`** — Azure Flexible Server enforces
   SSL by default; `psycopg2` needed `sslmode="require"` explicitly set in the
   connection config.
3. **`relation "stores" does not exist`** — the population script was run before
   `schema.sql` had ever been executed against the cloud database; also a reminder
   to always confirm `current_database()` matches the database `schema.sql` was
   run against in pgAdmin.
4. **`TypeError: cannot unpack non-iterable NoneType object`** — a stale, edited
   version of `generate_order_items()` was still active in the Jupyter kernel's
   memory even though the on-disk `.py`/`.ipynb` cell looked correct; fixed with a
   full kernel restart and a clean top-to-bottom re-run.
5. **Row count appeared low (1,101 vs. expected 1,200)** — turned out to be a
   misleading pgAdmin grid view ("last 100 rows" ≠ total count); `SELECT COUNT(*)`
   confirmed the true, correct total.
6. **Tableau Public Top N filtering** — needed a "Top / By field" filter
   configuration to correctly surface the top 10 highest-spending customers for
   the business-question analysis.

## Business Questions Answered (Part 5)

1. Total sales revenue per store
2. Top 10 most valuable customers by total spending
3. Most popular menu item (by quantity sold) across all stores
4. Average order value
5. Busiest hours of the day for orders

See `analytics_queries.sql` for the full SQL.

"Setting up version control and pushing to a remote repository"
﻿# Final_Project_Pizzeria
initgit
add
README.mdgit
commit
-m
first commit
git
branch
-M
maingit
remote
add
origin
https://github.com/iaakanni/Final_Project_Pizzeria.gitgit
push
-u
origin
master
