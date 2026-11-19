# E-Commerce Cohort Retention & RFM Segmentation

Customer & commercial analytics project evaluating **6,581 orders** across **2,400 customers** (Rp 4.18B total revenue) using **SQL**, **Python**, and an interactive **Cohort & RFM Dashboard**.

## Business Questions
1. How does customer retention evolve across monthly acquisition cohorts (M0–M5)?
2. Which RFM segments drive revenue concentration vs. churn risk?
3. How severely do late deliveries impact customer review scores?

## Key Findings (Verified from `output/ecommerce_metrics.json`)
- **RFM Revenue Concentration:** **Champions** (12.0% of customers) generate **30.7%** of total revenue (Rp 1.28B, averaging **5.48 orders**). Combined with **Loyal Customers** (47.7%), they drive **79.2%** of revenue.
- **High-Value Win-Back Opportunity:** **At Risk** customers (11.4% of base, Rp 432.6M historical spend) have not purchased in an average of **252.6 days**.
- **Delivery SLA Impact:** Late deliveries (1,156 orders, avg **8.02 days**) drop average review scores from **4.25 to 2.45** and surge 1–2 star ratings from **6.38% to 55.1%**.
- **Cohort Retention:** Month-2 retention rebounds to **39.6%–50.5%** across cohorts before tapering to **19.4%–23.9%** by Month 5.

## Strategic Recommendations
1. **Trigger Win-Back Campaigns at Day 90:** Target **At Risk** customers with personalized category vouchers before they cross the 180-day churn threshold.
2. **Fix Logistics Bottlenecks in Outer-Java Routes:** Prioritize 3PL SLA enforcement for delayed corridors to protect review ratings.
3. **VIP Loyalty Tier for Champions:** Offer free priority shipping to the top 12% Champions segment to sustain 5+ annual orders.

## How to Run
```bash
python data/generate_data.py
python src/run_analysis.py
```
Open `dashboard.html` in any browser to view the interactive cohort heatmap and RFM charts.
