"""
Flags potential 'waste' using a few complementary, explainable methods rather
than one black-box model -- this matters because the people reviewing this
report (finance officers, not data scientists) need to trust *why* something
got flagged.

Methods:
  1. Statistical outliers per category   (IQR method)
  2. Isolation Forest                    (multivariate anomaly detection)
  3. Duplicate payment detection         (same vendor + amount, close dates)
  4. Department/category overspend trend (month-on-month growth vs own history)
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest


def flag_statistical_outliers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["flag_statistical_outlier"] = False
    for cat, group in df.groupby("expense_category"):
        q1, q3 = group["amount_inr"].quantile([0.25, 0.75])
        iqr = q3 - q1
        upper = q3 + 1.5 * iqr
        df.loc[group.index, "flag_statistical_outlier"] = group["amount_inr"] > upper
    return df


def flag_isolation_forest(df: pd.DataFrame, contamination=0.03) -> pd.DataFrame:
    df = df.copy()
    features = pd.DataFrame({
        "amount_inr": df["amount_inr"],
        "is_weekend": df["is_weekend"].astype(int),
        "dept_code": df["department"].astype("category").cat.codes,
        "cat_code": df["expense_category"].astype("category").cat.codes,
    })
    model = IsolationForest(contamination=contamination, random_state=42)
    preds = model.fit_predict(features)
    df["flag_isolation_forest"] = preds == -1
    return df


def flag_duplicate_payments(df: pd.DataFrame, days_window=7) -> pd.DataFrame:
    df = df.copy()
    df["flag_possible_duplicate"] = False
    for (vendor, amount), group in df.groupby(["vendor", "amount_inr"]):
        if len(group) < 2:
            continue
        dates = group.sort_values("date")["date"]
        close_pairs = dates.diff().dt.days <= days_window
        flagged_idx = group.sort_values("date").index[close_pairs.fillna(False) | close_pairs.shift(-1).fillna(False)]
        df.loc[flagged_idx, "flag_possible_duplicate"] = True
    return df


def flag_department_overspend(df: pd.DataFrame, growth_threshold=0.75, min_txns_per_month=3) -> pd.DataFrame:
    """Flags department+category combos where monthly spend jumped sharply
    vs. their own trailing average -- catches *systemic* overspend, not just
    one-off weird transactions. Requires a minimum transaction count per
    month so a single noisy invoice can't trigger a false alarm."""
    monthly = df.groupby(["department", "expense_category", "month"]).agg(
        amount_inr=("amount_inr", "sum"), txn_count=("amount_inr", "size")
    ).reset_index()
    monthly = monthly.sort_values("month")
    flags = []
    for (dept, cat), group in monthly.groupby(["department", "expense_category"]):
        group = group.sort_values("month")
        rolling_avg = group["amount_inr"].shift(1).rolling(3, min_periods=2).mean()
        overspend = (
            (group["amount_inr"] > rolling_avg * (1 + growth_threshold))
            & rolling_avg.notna()
            & (group["txn_count"] >= min_txns_per_month)
        )
        for m, amt, avg in zip(group.loc[overspend, "month"], group.loc[overspend, "amount_inr"], rolling_avg[overspend]):
            flags.append((dept, cat, m, round(amt), round(avg)))
    return pd.DataFrame(flags, columns=["department", "expense_category", "month", "amount_inr", "trailing_avg_inr"])


def run_all(df: pd.DataFrame):
    df = flag_statistical_outliers(df)
    df = flag_isolation_forest(df)
    df = flag_duplicate_payments(df)
    df["any_flag"] = df[["flag_statistical_outlier", "flag_isolation_forest", "flag_possible_duplicate"]].any(axis=1)
    overspend_df = flag_department_overspend(df)
    return df, overspend_df


if __name__ == "__main__":
    df = pd.read_csv("data/cleaned_expenses.csv", parse_dates=["date"])
    flagged_df, overspend_df = run_all(df)

    flagged_df.to_csv("data/flagged_expenses.csv", index=False)
    overspend_df.to_csv("data/department_overspend.csv", index=False)

    n_flagged = flagged_df["any_flag"].sum()
    flagged_value = flagged_df.loc[flagged_df["any_flag"], "amount_inr"].sum()
    total_value = flagged_df["amount_inr"].sum()

    print(f"Flagged {n_flagged} of {len(flagged_df)} transactions ({n_flagged/len(flagged_df):.1%})")
    print(f"Flagged value: Rs {flagged_value:,.0f} of Rs {total_value:,.0f} total ({flagged_value/total_value:.1%})")
    print(f"Department/category overspend months flagged: {len(overspend_df)}")
