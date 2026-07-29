---DROP TABLE IF EXISTS Order_Items, Orders, Menu_Item_Ingredients, Menu_Items, Ingredients, Customers, Stores CASCADE;
-- =====================================================================
-- RushMore Pizzeria — schema.sql
-- Normalized to 3NF: every non-key column depends on the whole key,
-- and nothing but the key. Junction tables (Menu_Item_Ingredients,
-- Order_Items) exist specifically to avoid repeating groups.
-- =====================================================================

-- ---------------------------------------------------------------------
-- STORES: one row per physical location. No dependency on anything else,
-- so it's created first.
-- ---------------------------------------------------------------------
CREATE TABLE Stores (
    store_id      SERIAL PRIMARY KEY,
    address       VARCHAR(255) NOT NULL,
    city          VARCHAR(100) NOT NULL,
    phone_number  VARCHAR(20) UNIQUE NOT NULL,
    opened_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- CUSTOMERS: PII table. UNIQUE on email/phone stops duplicate accounts
-- and doubles as a fast lookup index for "find this customer" queries.
-- ---------------------------------------------------------------------
CREATE TABLE Customers (
    customer_id   SERIAL PRIMARY KEY,
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100) NOT NULL,
    email         VARCHAR(255) UNIQUE NOT NULL,
    phone_number  VARCHAR(20) UNIQUE NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- INGREDIENTS: master stock list. Independent table, no foreign keys.
-- ---------------------------------------------------------------------
CREATE TABLE Ingredients (
    ingredient_id   SERIAL PRIMARY KEY,
    name            VARCHAR(100) UNIQUE NOT NULL,
    stock_quantity  NUMERIC(10, 2) NOT NULL DEFAULT 0,
    unit            VARCHAR(20) NOT NULL
);

-- ---------------------------------------------------------------------
-- MENU_ITEMS: the product catalog. `price` is added beyond the brief's
-- literal spec because Order_Items.unit_price and Orders.total_amount
-- both need a source of truth to be calculated from.
-- ---------------------------------------------------------------------
CREATE TABLE Menu_Items (
    item_id   SERIAL PRIMARY KEY,
    name      VARCHAR(150) NOT NULL,
    category  VARCHAR(50) NOT NULL,
    size      VARCHAR(20),
    price     NUMERIC(10, 2) NOT NULL
);

-- ---------------------------------------------------------------------
-- MENU_ITEM_INGREDIENTS: junction table = the "recipe" for each item.
-- A composite primary key (item_id, ingredient_id) means the same
-- ingredient can't be listed twice on the same item's recipe.
-- ON DELETE CASCADE for item_id: if a menu item is deleted, its recipe
-- rows are meaningless, so they go too.
-- ON DELETE RESTRICT for ingredient_id: don't let someone delete an
-- ingredient that's still used in an active recipe.
-- ---------------------------------------------------------------------
CREATE TABLE Menu_Item_Ingredients (
    item_id            INTEGER NOT NULL REFERENCES Menu_Items(item_id) ON DELETE CASCADE,
    ingredient_id      INTEGER NOT NULL REFERENCES Ingredients(ingredient_id) ON DELETE RESTRICT,
    quantity_required  NUMERIC(10, 2) NOT NULL,
    PRIMARY KEY (item_id, ingredient_id)
);

-- ---------------------------------------------------------------------
-- ORDERS: the master transaction / "receipt" table. Depends on
-- Customers and Stores existing first, hence its position here.
-- customer_id: ON DELETE SET NULL keeps the order in history even if
--   the customer account is later deleted (common retail requirement).
-- store_id: ON DELETE RESTRICT — a store can never be deleted while it
--   still has order history attached to it.
-- ---------------------------------------------------------------------
CREATE TABLE Orders (
    order_id         SERIAL PRIMARY KEY,
    customer_id      INTEGER REFERENCES Customers(customer_id) ON DELETE SET NULL,
    store_id         INTEGER NOT NULL REFERENCES Stores(store_id) ON DELETE RESTRICT,
    order_timestamp  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount     NUMERIC(10, 2) NOT NULL
);

-- ---------------------------------------------------------------------
-- ORDER_ITEMS: the "line items" on a receipt. This is what lets one
-- order contain many pizzas/drinks/sides (a one-to-many from Orders).
-- unit_price is copied from Menu_Items.price AT THE TIME OF THE ORDER —
-- this is deliberate, not a normalization mistake. Menu prices change
-- over time; a 2024 order must still show the 2024 price even if
-- today's menu price is different. This is called a "price snapshot".
-- ON DELETE CASCADE for order_id: deleting an order deletes its lines.
-- ON DELETE RESTRICT for item_id: can't delete a menu item that's
-- referenced in historical order data.
-- ---------------------------------------------------------------------
CREATE TABLE Order_Items (
    order_item_id  SERIAL PRIMARY KEY,
    order_id       INTEGER NOT NULL REFERENCES Orders(order_id) ON DELETE CASCADE,
    item_id        INTEGER NOT NULL REFERENCES Menu_Items(item_id) ON DELETE RESTRICT,
    quantity       INTEGER NOT NULL DEFAULT 1,
    unit_price     NUMERIC(10, 2) NOT NULL
);

-- ---------------------------------------------------------------------
-- Indexes: primary keys are auto-indexed by Postgres, but foreign keys
-- are NOT auto-indexed. Without these, every JOIN (e.g. "all orders for
-- this customer") does a full table scan once you hit 5,000+ rows.
-- ---------------------------------------------------------------------
CREATE INDEX idx_orders_customer_id ON Orders(customer_id);
CREATE INDEX idx_orders_store_id ON Orders(store_id);
CREATE INDEX idx_orders_timestamp ON Orders(order_timestamp);
CREATE INDEX idx_order_items_order_id ON Order_Items(order_id);
CREATE INDEX idx_order_items_item_id ON Order_Items(item_id);