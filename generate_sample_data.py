"""
Generates a synthetic expense dataset that mimics what an ONGC-style
demo report might contain. Swap this out once real demo reports arrive --
just make sure your real data has the same column names (or update
COLUMN MAP in clean_data.py).
"""
import pandas as pd
import numpy as np

np.random.seed(42)

DEPARTMENTS = ["Drilling", "Production", "Maintenance", "IT", "Procurement",
               "HSE", "Logistics", "Finance", "HR", "Admin"]

CATEGORY_VENDOR_AMOUNT = {
    "Fuel & POL":            (["IndianOil Corp", "BPCL", "HPCL"], 15000, 250000),
    "Equipment Maintenance": (["Larsen & Toubro", "BHEL", "Schlumberger", "Local Workshop Co"], 8000, 600000),
    "Contractor Payment":    (["Reliance Infra Services", "Tata Projects", "Local Contractor Pvt Ltd"], 50000, 2000000),
    "Travel & Conveyance":   (["IRCTC", "Air India", "Local Taxi Union"], 1500, 45000),
    "Office Supplies":       (["Staples India", "Local Stationery Mart"], 500, 12000),
    "IT Services & Software":(["TCS", "Wipro", "Microsoft India", "Local IT Vendor"], 5000, 350000),
    "Utilities":             (["State Electricity Board", "Municipal Water Dept"], 10000, 180000),
    "Training & Seminars":   (["IIM Institute", "NIIT", "Internal Training Cell"], 3000, 80000),
    "Catering & Hospitality":(["Local Caterers Assoc", "Taj Catering Services"], 2000, 60000),
}

N_NORMAL = 1800
rows = []
start_date = pd.Timestamp("2025-04-01")  # start of Indian FY
end_date = pd.Timestamp("2026-03-31")
date_range_days = (end_date - start_date).days

for i in range(N_NORMAL):
    category = np.random.choice(list(CATEGORY_VENDOR_AMOUNT.keys()))
    vendors, lo, hi = CATEGORY_VENDOR_AMOUNT[category]
    vendor = np.random.choice(vendors)
    amount = float(np.round(np.random.uniform(lo, hi), -2))
    dept = np.random.choice(DEPARTMENTS)
    date = start_date + pd.Timedelta(days=int(np.random.uniform(0, date_range_days)))
    rows.append({
        "transaction_id": f"TXN{i+1:05d}",
        "date": date,
        "department": dept,
        "expense_category": category,
        "vendor": vendor,
        "amount_inr": amount,
        "cost_center": f"CC-{dept[:3].upper()}-{np.random.randint(1,4)}",
        "approved_by": f"EMP{np.random.randint(1000,1050)}",
        "description": f"{category} - routine {dept.lower()} expense",
    })

df = pd.DataFrame(rows)

# ---- Inject deliberate "waste" / anomaly patterns so the ML layer has something to find ----

# 1. Duplicate payments: same vendor, same amount, paid twice within a few days
dup_idx = df.sample(15, random_state=1).index
dup_rows = df.loc[dup_idx].copy()
dup_rows["transaction_id"] = [f"TXN{N_NORMAL+i+1:05d}" for i in range(len(dup_rows))]
dup_rows["date"] = dup_rows["date"] + pd.to_timedelta(np.random.randint(1, 5, len(dup_rows)), unit="D")
dup_rows["description"] = dup_rows["description"] + " (possible duplicate)"

# 2. Sudden spikes: a handful of wildly oversized payments relative to category norm
spike_idx = df.sample(10, random_state=2).index
df.loc[spike_idx, "amount_inr"] = df.loc[spike_idx, "amount_inr"] * np.random.uniform(4, 9, len(spike_idx))
df.loc[spike_idx, "description"] = df.loc[spike_idx, "description"] + " (unusually high amount)"

# 3. Weekend / off-cycle approvals (often a red flag in procurement audits)
weekend_idx = df.sample(20, random_state=3).index
for idx in weekend_idx:
    d = df.loc[idx, "date"]
    df.loc[idx, "date"] = d + pd.Timedelta(days=(5 - d.weekday()) % 7)  # push to Saturday

# 4. One department steadily overspending on one category every month (systemic waste, not a one-off anomaly)
overspend_rows = []
for m in range(12):
    month_date = start_date + pd.DateOffset(months=m, days=10)
    if month_date > end_date:
        break
    overspend_rows.append({
        "transaction_id": f"TXNOS{m+1:03d}",
        "date": month_date,
        "department": "Maintenance",
        "expense_category": "Equipment Maintenance",
        "vendor": "Local Workshop Co",
        "amount_inr": float(np.round(np.random.uniform(450000, 580000), -2)),
        "cost_center": "CC-MAI-1",
        "approved_by": "EMP1012",
        "description": "Equipment Maintenance - recurring high-cost vendor",
    })

df = pd.concat([df, dup_rows, pd.DataFrame(overspend_rows)], ignore_index=True)
df = df.sort_values("date").reset_index(drop=True)

df.to_csv("data/raw_expenses.csv", index=False)
print(f"Generated {len(df)} rows -> data/raw_expenses.csv")
print(df.head())
