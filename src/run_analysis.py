import csv
import json
import os
import sqlite3
from collections import defaultdict
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUSTOMERS_CSV = os.path.join(BASE_DIR, "data", "customers.csv")
ORDERS_CSV = os.path.join(BASE_DIR, "data", "orders.csv")
DB_PATH = os.path.join(BASE_DIR, "output", "ecommerce.db")
JSON_PATH = os.path.join(BASE_DIR, "output", "ecommerce_metrics.json")


def month_diff(m1, m2):
    y1, mo1 = map(int, m1.split("-"))
    y2, mo2 = map(int, m2.split("-"))
    return (y2 - y1) * 12 + (mo2 - mo1)


def quantile_score(values, val, reverse=False):
    sorted_v = sorted(values)
    n = len(sorted_v)
    idx = 0
    for i, v in enumerate(sorted_v):
        if val >= v:
            idx = i
    q = int(4 * idx / max(1, n - 1)) + 1
    q = min(5, max(1, q))
    return (6 - q) if reverse else q


def segment_rfm(r, f, m):
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 3 and f >= 3:
        return "Loyal Customers"
    if r >= 4 and f <= 2:
        return "Recent / Potential"
    if r <= 2 and f >= 3:
        return "At Risk"
    return "Hibernating"


def main():
    os.makedirs(os.path.join(BASE_DIR, "output"), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS orders;")
    cur.execute("""
        CREATE TABLE orders (
            order_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            order_date TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            order_value_idr INTEGER NOT NULL,
            promised_delivery_days INTEGER NOT NULL,
            actual_delivery_days INTEGER NOT NULL,
            is_late_delivery INTEGER NOT NULL,
            review_score INTEGER NOT NULL
        );
    """)

    orders_list = []
    with open(ORDERS_CSV, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            orders_list.append((
                row["order_id"], row["customer_id"], row["order_date"],
                row["category"], int(row["quantity"]), int(row["order_value_idr"]),
                int(row["promised_delivery_days"]), int(row["actual_delivery_days"]),
                int(row["is_late_delivery"]), int(row["review_score"])
            ))
    cur.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", orders_list)
    conn.commit()

    conn.row_factory = sqlite3.Row
    monthly = [dict(r) for r in conn.execute("""
        SELECT
            strftime('%Y-%m', order_date) AS month,
            COUNT(*) AS total_orders,
            COUNT(DISTINCT customer_id) AS active_customers,
            SUM(order_value_idr) AS total_revenue_idr,
            ROUND(AVG(order_value_idr), 0) AS avg_order_value_idr
        FROM orders
        GROUP BY strftime('%Y-%m', order_date)
        ORDER BY month;
    """).fetchall()]

    delivery_impact = [dict(r) for r in conn.execute("""
        SELECT
            CASE WHEN is_late_delivery = 1 THEN 'Late Delivery' ELSE 'On-Time Delivery' END AS delivery_status,
            COUNT(*) AS order_count,
            ROUND(AVG(actual_delivery_days), 2) AS avg_delivery_days,
            ROUND(AVG(review_score), 2) AS avg_review_score,
            ROUND(100.0 * SUM(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END) / COUNT(*), 2) AS low_rating_pct
        FROM orders
        GROUP BY is_late_delivery;
    """).fetchall()]

    rfm_rows = [dict(r) for r in conn.execute("""
        SELECT
            customer_id,
            CAST(julianday('2026-11-01') - julianday(MAX(order_date)) AS INTEGER) AS recency_days,
            COUNT(order_id) AS frequency,
            SUM(order_value_idr) AS monetary_idr
        FROM orders
        GROUP BY customer_id;
    """).fetchall()]

    # Cohort retention calculation
    first_month = {}
    cust_months = defaultdict(set)
    for _, cid, odate, *_ in orders_list:
        ym = odate[:7]
        if cid not in first_month or ym < first_month[cid]:
            first_month[cid] = ym
        cust_months[cid].add(ym)

    cohort_sizes = defaultdict(int)
    cohort_counts = defaultdict(lambda: defaultdict(int))
    for cid, fm in first_month.items():
        cohort_sizes[fm] += 1
        for om in cust_months[cid]:
            diff = month_diff(fm, om)
            if 0 <= diff <= 5:
                cohort_counts[fm][diff] += 1

    cohort_table = []
    for fm in sorted(cohort_sizes.keys())[:6]:
        size = cohort_sizes[fm]
        row = {"cohort": fm, "size": size}
        for m_idx in range(6):
            row[f"m{m_idx}"] = round(100.0 * cohort_counts[fm][m_idx] / size, 1) if size else 0.0
        cohort_table.append(row)

    # RFM segmentation
    r_vals = [x["recency_days"] for x in rfm_rows]
    f_vals = [x["frequency"] for x in rfm_rows]
    m_vals = [x["monetary_idr"] for x in rfm_rows]

    seg_summary = defaultdict(lambda: {"customers": 0, "revenue_idr": 0, "recency_sum": 0, "freq_sum": 0})
    for row in rfm_rows:
        r_s = quantile_score(r_vals, row["recency_days"], reverse=True)
        f_s = quantile_score(f_vals, row["frequency"], reverse=False)
        m_s = quantile_score(m_vals, row["monetary_idr"], reverse=False)
        seg = segment_rfm(r_s, f_s, m_s)
        seg_summary[seg]["customers"] += 1
        seg_summary[seg]["revenue_idr"] += row["monetary_idr"]
        seg_summary[seg]["recency_sum"] += row["recency_days"]
        seg_summary[seg]["freq_sum"] += row["frequency"]

    rfm_segments = []
    total_rev = sum(v["revenue_idr"] for v in seg_summary.values())
    total_cust = sum(v["customers"] for v in seg_summary.values())
    for seg, v in sorted(seg_summary.items(), key=lambda x: -x[1]["revenue_idr"]):
        cnt = v["customers"]
        rfm_segments.append({
            "segment": seg,
            "customers": cnt,
            "pct_customers": round(100.0 * cnt / total_cust, 1),
            "revenue_idr": v["revenue_idr"],
            "pct_revenue": round(100.0 * v["revenue_idr"] / total_rev, 1),
            "avg_recency_days": round(v["recency_sum"] / cnt, 1),
            "avg_frequency": round(v["freq_sum"] / cnt, 2),
        })

    output = {
        "total_orders": len(orders_list),
        "total_customers": total_cust,
        "total_revenue_idr": total_rev,
        "monthly": monthly,
        "delivery_impact": delivery_impact,
        "cohort_table": cohort_table,
        "rfm_segments": rfm_segments,
    }

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    conn.close()
    print(json.dumps({
        "total_orders": output["total_orders"],
        "total_customers": output["total_customers"],
        "total_revenue_idr": output["total_revenue_idr"],
        "delivery_impact": delivery_impact,
        "rfm_segments": rfm_segments,
    }, indent=2))


if __name__ == "__main__":
    main()
