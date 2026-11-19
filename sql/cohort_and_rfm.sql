-- ============================================================================
-- E-Commerce Retention, RFM & Delivery Impact SQL Queries
-- ============================================================================

-- 1. Monthly Revenue, Orders, and AOV
SELECT
    strftime('%Y-%m', order_date) AS month,
    COUNT(*) AS total_orders,
    COUNT(DISTINCT customer_id) AS active_customers,
    SUM(order_value_idr) AS total_revenue_idr,
    ROUND(AVG(order_value_idr), 0) AS avg_order_value_idr
FROM orders
GROUP BY strftime('%Y-%m', order_date)
ORDER BY month;

-- 2. Delivery Delay Impact on Customer Review Scores
SELECT
    CASE WHEN is_late_delivery = 1 THEN 'Late Delivery' ELSE 'On-Time Delivery' END AS delivery_status,
    COUNT(*) AS order_count,
    ROUND(AVG(actual_delivery_days), 2) AS avg_delivery_days,
    ROUND(AVG(review_score), 2) AS avg_review_score,
    ROUND(100.0 * SUM(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END) / COUNT(*), 2) AS low_rating_pct
FROM orders
GROUP BY is_late_delivery;

-- 3. Customer-Level RFM Base Table
SELECT
    customer_id,
    CAST(julianday('2026-11-01') - julianday(MAX(order_date)) AS INTEGER) AS recency_days,
    COUNT(order_id) AS frequency,
    SUM(order_value_idr) AS monetary_idr
FROM orders
GROUP BY customer_id;
