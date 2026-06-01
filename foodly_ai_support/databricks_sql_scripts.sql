-- ============================================================
-- Foodly AI Support - Complete SQL Setup Script
-- ============================================================
-- Run this script in a Databricks SQL Warehouse or Notebook
-- This creates ALL the tables, data, and UC functions needed
-- ============================================================

-- ============================================================
-- STEP 1: Create Schemas
-- ============================================================
CREATE SCHEMA IF NOT EXISTS agents.orders_data;
CREATE SCHEMA IF NOT EXISTS agents.escalation;

-- ============================================================
-- STEP 2: Create Orders Tables
-- ============================================================
CREATE TABLE IF NOT EXISTS agents.orders_data.orders (
    order_id STRING,
    user_id STRING,
    restaurant_name STRING,
    status STRING,             -- 'Placed', 'Preparing', 'Out for delivery', 'Delivered', 'Cancelled'
    eta STRING,                -- estimated time e.g. '20 min'
    rider_name STRING,
    delivery_address STRING,
    total_price DECIMAL(10,2),
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agents.orders_data.order_items (
    order_id STRING,
    item_name STRING,
    quantity INT,
    price DECIMAL(10,2)
);

-- ============================================================
-- STEP 3: Insert Sample Data
-- ============================================================
INSERT INTO agents.orders_data.orders VALUES
('ORD001', 'USR123', 'Pizza Palace',      'Placed',            '25 min', 'Ramesh', '221B Baker Street', 599.00, current_timestamp()),
('ORD002', 'USR123', 'Burger Bazaar',     'Preparing',         '30 min', 'Suresh', '221B Baker Street', 399.00, current_timestamp() - INTERVAL 1 HOUR),
('ORD003', 'USR456', 'Curry Corner',      'Out for delivery',  '15 min', 'Mahesh', '742 Evergreen Terrace', 799.00, current_timestamp() - INTERVAL 2 HOUR),
('ORD004', 'USR456', 'Pasta Point',       'Delivered',         '0 min',  'Ganesh', '742 Evergreen Terrace', 499.00, current_timestamp() - INTERVAL 1 DAY);

INSERT INTO agents.orders_data.order_items VALUES
('ORD001', 'Margherita Pizza', 1, 299.00),
('ORD001', 'Garlic Bread',     1, 150.00),
('ORD001', 'Coke',             2, 75.00),
('ORD002', 'Cheeseburger',     2, 199.50),
('ORD002', 'Fries',            1, 100.00),
('ORD003', 'Paneer Tikka',     1, 299.00),
('ORD003', 'Butter Naan',      4, 100.00),
('ORD003', 'Gulab Jamun',      2, 100.00),
('ORD004', 'Alfredo Pasta',    1, 299.00),
('ORD004', 'Garlic Bread',     1, 150.00),
('ORD004', 'Lemonade',         1, 50.00);

-- ============================================================
-- STEP 4: Create UC Functions (Agent Tools)
-- ============================================================

-- Tool 1: Get all orders for a user
CREATE OR REPLACE FUNCTION agents.orders_data.get_all_orders(
    user_id_input STRING COMMENT 'User ID used to retrieve all active or recent orders'
)
RETURNS TABLE (
    order_id STRING,
    restaurant STRING,
    status STRING,
    eta STRING
)
COMMENT 'Returns all active or recent orders for the given user_id, including restaurant name, status, and ETA.'
RETURN (
    SELECT order_id, restaurant_name AS restaurant, status, eta
    FROM agents.orders_data.orders
    WHERE user_id = user_id_input
    ORDER BY created_at DESC
    LIMIT 10
);

-- Tool 2: Get order status
CREATE OR REPLACE FUNCTION agents.orders_data.get_order_status(
    order_id_input STRING COMMENT 'Order ID to retrieve the current status'
)
RETURNS TABLE (
    status STRING,
    eta STRING,
    restaurant STRING,
    rider STRING
)
COMMENT 'Returns the current status, ETA, restaurant, and rider for the provided order_id.'
RETURN (
    SELECT status, eta, restaurant_name AS restaurant, rider_name AS rider
    FROM agents.orders_data.orders
    WHERE order_id = order_id_input
    LIMIT 1
);

-- Tool 3: Get order details (items breakdown)
CREATE OR REPLACE FUNCTION agents.orders_data.get_order_details(
    order_id_input STRING COMMENT 'Order ID to retrieve full details'
)
RETURNS TABLE (
    item_name STRING,
    quantity INT,
    price DECIMAL(10,2),
    delivery_address STRING,
    placed_at TIMESTAMP
)
COMMENT 'Returns detailed information for the given order_id including items, quantity, price, delivery address, and order time.'
RETURN (
    SELECT i.item_name, i.quantity, i.price, o.delivery_address, o.created_at AS placed_at
    FROM agents.orders_data.order_items i
    JOIN agents.orders_data.orders o ON i.order_id = o.order_id
    WHERE o.order_id = order_id_input
);

-- Tool 4: Cancel an order
CREATE OR REPLACE FUNCTION agents.orders_data.cancel_order(
    order_id_input STRING COMMENT 'Order ID to attempt cancellation'
)
RETURNS TABLE (
    success BOOLEAN,
    message STRING,
    refund_initiated BOOLEAN,
    refund_amount DECIMAL(10,2)
)
COMMENT 'Attempts to cancel the given order_id. Returns whether it was successful, a message, and refund details if applicable.'
RETURN (
    SELECT
      CASE WHEN status NOT IN ('Preparing','Out for delivery','Delivered') THEN TRUE ELSE FALSE END AS success,
      CASE WHEN status NOT IN ('Preparing','Out for delivery','Delivered') THEN 'Order has been cancelled successfully.' ELSE 'Order cannot be cancelled at this stage.' END AS message,
      CASE WHEN status NOT IN ('Preparing','Out for delivery','Delivered') THEN TRUE ELSE FALSE END AS refund_initiated,
      CASE WHEN status NOT IN ('Preparing','Out for delivery','Delivered') THEN total_price ELSE 0.00 END AS refund_amount
    FROM agents.orders_data.orders
    WHERE order_id = order_id_input
    LIMIT 1
);

-- Tool 5: Escalate to human
CREATE OR REPLACE FUNCTION agents.escalation.escalate_to_human(
    user_id_input STRING COMMENT 'User ID needing escalation',
    summary_input STRING COMMENT 'Brief summary of the conversation or issue'
)
RETURNS TABLE (
    ticket_id STRING,
    eta_minutes INT,
    message STRING
)
COMMENT 'Creates a support ticket for human intervention, returns a ticket ID, estimated response time, and a user-facing message.'
RETURN (
    SELECT
      CONCAT('TCK-', CAST(FLOOR(RAND() * 1000000) AS STRING)) AS ticket_id,
      30 AS eta_minutes,
      CONCAT('We have escalated your issue to a human support specialist. You can expect a response within ', 30, ' minutes.') AS message
);
