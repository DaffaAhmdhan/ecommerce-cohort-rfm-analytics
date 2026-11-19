import csv
import os
import random
from datetime import datetime, timedelta

random.seed(108)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
CUSTOMERS_CSV = os.path.join(OUTPUT_DIR, "customers.csv")
ORDERS_CSV = os.path.join(OUTPUT_DIR, "orders.csv")

CITIES = ["Jakarta", "Bandung", "Surabaya", "Bekasi", "Depok", "Tangerang", "Semarang", "Yogyakarta"]
CATEGORIES = [
    ("Electronics & Gadgets", 450000, 2200000),
    ("Home & Living", 120000, 650000),
    ("Fashion & Apparel", 95000, 420000),
    ("Health & Personal Care", 65000, 280000),
    ("Office & Stationery", 50000, 320000),
]


def main():
    num_customers = 2400
    start_date = datetime(2025, 11, 1)
    end_date = datetime(2026, 10, 31)

    customers = []
    for cid in range(1, num_customers + 1):
        signup_offset = random.randint(0, 330)
        signup_date = start_date + timedelta(days=signup_offset)
        city = random.choice(CITIES)
        loyalty_tier = random.choices(["High", "Medium", "Low"], weights=[0.20, 0.45, 0.35])[0]
        customers.append((f"CUST-{cid:04d}", signup_date, city, loyalty_tier))

    with open(CUSTOMERS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["customer_id", "signup_date", "city", "segment_propensity"])
        for c in customers:
            w.writerow([c[0], c[1].strftime("%Y-%m-%d"), c[2], c[3]])

    orders = []
    oid = 1
    for cust_id, signup_date, city, tier in customers:
        if tier == "High":
            n_orders = random.randint(4, 11)
        elif tier == "Medium":
            n_orders = random.randint(2, 5)
        else:
            n_orders = random.choices([1, 2], weights=[0.75, 0.25])[0]

        current_date = signup_date + timedelta(days=random.randint(0, 5))
        for _ in range(n_orders):
            if current_date > end_date:
                break
            cat, low_p, high_p = random.choice(CATEGORIES)
            qty = random.choices([1, 2, 3], weights=[0.7, 0.22, 0.08])[0]
            order_value = round(random.uniform(low_p, high_p) * qty, -2)

            promised_days = random.randint(3, 5)
            is_late = 1 if random.random() < (0.24 if city in ("Surabaya", "Semarang", "Yogyakarta") else 0.12) else 0
            actual_days = promised_days + (random.randint(2, 6) if is_late else random.randint(-1, 0))
            actual_days = max(1, actual_days)

            if is_late:
                review_score = random.choices([1, 2, 3, 4, 5], weights=[0.25, 0.30, 0.25, 0.15, 0.05])[0]
            else:
                review_score = random.choices([1, 2, 3, 4, 5], weights=[0.02, 0.04, 0.10, 0.34, 0.50])[0]

            orders.append([
                f"ORD-{oid:06d}",
                cust_id,
                current_date.strftime("%Y-%m-%d"),
                cat,
                qty,
                int(order_value),
                promised_days,
                actual_days,
                is_late,
                review_score,
            ])
            oid += 1
            current_date += timedelta(days=random.randint(14, 75))

    orders.sort(key=lambda r: r[2])
    with open(ORDERS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "order_id", "customer_id", "order_date", "category", "quantity",
            "order_value_idr", "promised_delivery_days", "actual_delivery_days",
            "is_late_delivery", "review_score"
        ])
        w.writerows(orders)

    print(f"Generated {len(customers)} customers and {len(orders)} orders.")


if __name__ == "__main__":
    main()
