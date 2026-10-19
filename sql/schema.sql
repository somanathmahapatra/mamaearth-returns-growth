
-- Mamaearth Returns & Growth Intelligence Pipeline
-- Part 1: SQL Relational Layer & Reporting
-- All reports run against raw, uncleaned data.

-- =====================================================
-- Report (a): Order totals, total revenue, average order value
-- =====================================================

/*
Exact output:
total_orders | total_revenue | average_order_value
180          | 99860.20      | 554.78
*/

SELECT
    COUNT(*) AS total_orders,
    ROUND(
        SUM(
            p.price * o.quantity *
            (1 - COALESCE(o.discount_pct, 0) / 100.0)
        ),
        2
    ) AS total_revenue,
    ROUND(
        AVG(
            p.price * o.quantity *
            (1 - COALESCE(o.discount_pct, 0) / 100.0)
        ),
        2
    ) AS average_order_value
FROM orders o
JOIN products p
    ON o.product_id = p.product_id;

-- =====================================================
-- Report (b): COUNT(*) vs COUNT(rating)
-- =====================================================

/*
Exact output:
total_orders | rated_orders | unrated_orders
180          | 165          | 15
*/

SELECT
    COUNT(*) AS total_orders,
    COUNT(rating) AS rated_orders,
    COUNT(*) - COUNT(rating) AS unrated_orders
FROM orders;

-- =====================================================
-- Report (c1): Customers who have never placed an order using LEFT JOIN
-- =====================================================

/*
Expected output:
customer_id | name
C045        | Vihaan
*/

SELECT
c.customer_id,
c.name
FROM customers c
LEFT JOIN orders o
ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;

-- =====================================================
-- Report (c2): Customers who have never placed an order using NOT IN
-- =====================================================

/*
Expected output:
customer_id | name
C045        | Vihaan
*/

SELECT
customer_id,
name
FROM customers
WHERE customer_id NOT IN (
SELECT DISTINCT customer_id
FROM orders
);

-- =====================================================
-- Report (d): City-wise return rate above 20%
-- =====================================================

/*
Expected output:
city      | total_orders | returned_orders | return_rate_pct
Jaipur    | 19           | 8               | 42.1
Lucknow   | 49           | 15              | 30.6
Bangalore | 33           | 8               | 24.2
*/

SELECT
c.city,
COUNT(o.order_id) AS total_orders,
SUM(o.returned) AS returned_orders,
ROUND(
100.0 * SUM(o.returned) / COUNT(o.order_id),
1
) AS return_rate_pct
FROM orders o
JOIN customers c
ON o.customer_id = c.customer_id
GROUP BY c.city
HAVING 100.0 * SUM(o.returned) / COUNT(o.order_id) > 20
ORDER BY return_rate_pct DESC;

-- =====================================================
-- Report (e1): Top 5 customers by total spending
-- =====================================================

/*
Expected output:
customer_id | name    | total_spend
C043        | Reyansh | 12920.00
C026        | Isha    | 8371.60
C008        | Meera   | 4564.60
C011        | Arjun   | 4111.00
C042        | Sanya   | 3785.00
*/

SELECT
c.customer_id,
c.name,
ROUND(
SUM(
p.price * o.quantity *
(1 - COALESCE(o.discount_pct, 0) / 100.0)
),
2
) AS total_spend
FROM customers c
JOIN orders o
ON c.customer_id = o.customer_id
JOIN products p
ON o.product_id = p.product_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 5;

-- =====================================================
-- Report (e2): Positions 3–5 in the spending ranking
-- =====================================================

/*
Expected output:
customer_id | name    | total_spend
C008        | Meera   | 4564.60
C011        | Arjun   | 4111.00
C042        | Sanya   | 3785.00
*/

SELECT
c.customer_id,
c.name,
ROUND(
SUM(
p.price * o.quantity *
(1 - COALESCE(o.discount_pct, 0) / 100.0)
),
2
) AS total_spend
FROM customers c
JOIN orders o
ON c.customer_id = o.customer_id
JOIN products p
ON o.product_id = p.product_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 3 OFFSET 2;

-- =====================================================
-- Report (f): Category-wise order count and revenue
-- =====================================================

/*
Expected output:
category      | order_count | category_revenue
Haircare      | 54          | 44956.10
Skincare      | 60          | 27346.00
Babycare      | 30          | 16805.00
PersonalCare  | 36          | 10753.10
*/

SELECT
p.category,
COUNT(o.order_id) AS order_count,
ROUND(
SUM(
p.price * o.quantity *
(1 - COALESCE(o.discount_pct, 0) / 100.0)
),
2
) AS category_revenue
FROM orders o
JOIN products p
ON o.product_id = p.product_id
JOIN customers c
ON o.customer_id = c.customer_id
GROUP BY p.category
ORDER BY category_revenue DESC;


-- =====================================================
-- Report (g): Customers whose names start with 'A'
-- =====================================================

/*
Expected output:
customer_id | name
C001        | Aarav
C003        | Aditi
C004        | Ananya
C011        | Arjun
C021        | Aryan
C030        | Anika
C031        | Aditya
C036        | Aisha
C041        | Ayaan
C044        | Aria
*/

SELECT
    customer_id,
    name
FROM customers
WHERE name LIKE 'A%'
ORDER BY customer_id;


-- =====================================================
-- Report (h): Distinct customer acquisition sources
-- =====================================================

/*
Expected output:
acquisition_source
Ad
Organic
Referral
Social
*/

SELECT DISTINCT
    acquisition_source
FROM customers
ORDER BY acquisition_source;

```sql
-- =====================================================
-- Report (i): Add loyalty tier and populate it
-- =====================================================

/*
Expected output:
loyalty_tier | customer_count
Gold         | 28
Silver       | 17
*/

ALTER TABLE customers
ADD COLUMN loyalty_tier VARCHAR(10);

UPDATE customers
SET loyalty_tier =
    CASE
        WHEN city_tier = 1 THEN 'Gold'
        ELSE 'Silver'
    END;

SELECT
    loyalty_tier,
    COUNT(*) AS customer_count
FROM customers
GROUP BY loyalty_tier
ORDER BY loyalty_tier;
