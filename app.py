from flask import Flask, render_template, request, jsonify
import pandas as pd
import json, os, urllib.request
from clean_data import load_and_clean
from anomaly_detection import run_all
from generate_report import build_summary_stats

app = Flask(__name__)
app.secret_key = "ongc_secret_2026"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

current_data = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    df = load_and_clean(filepath)
    flagged_df, overspend_df = run_all(df)
    stats = build_summary_stats(flagged_df, overspend_df)
    current_data["flagged_df"] = flagged_df
    current_data["overspend_df"] = overspend_df
    current_data["stats"] = stats

    # --- Chart 1: Monthly spend vs flagged (line chart) ---
    monthly = flagged_df.groupby("month").agg(
        total=("amount_inr","sum"),
        flagged=("amount_inr", lambda x: x[flagged_df.loc[x.index,"any_flag"]].sum())
    ).reset_index().sort_values("month")
    chart_monthly = {
        "labels": monthly["month"].tolist(),
        "total":  [round(v/1e6,2) for v in monthly["total"].tolist()],
        "flagged":[round(v/1e6,2) for v in monthly["flagged"].tolist()],
    }

    # --- Chart 2: Spend by category (donut) ---
    by_cat = flagged_df.groupby("expense_category")["amount_inr"].sum().sort_values(ascending=False).head(7)
    chart_category = {
        "labels": by_cat.index.tolist(),
        "values": [round(v/1e6,2) for v in by_cat.values.tolist()],
    }

    # --- Chart 3: Flagged by department (bar) ---
    dept_flagged = (
        flagged_df[flagged_df["any_flag"]]
        .groupby("department")["amount_inr"].sum()
        .sort_values(ascending=False).head(8)
    )
    chart_dept = {
        "labels": dept_flagged.index.tolist(),
        "values": [round(v/1e6,2) for v in dept_flagged.values.tolist()],
    }

    # --- Chart 4: Flag type breakdown (bar) ---
    chart_flags = {
        "labels": ["Statistical Outlier","Isolation Forest","Duplicate Payment"],
        "values": [
            int(flagged_df["flag_statistical_outlier"].sum()),
            int(flagged_df["flag_isolation_forest"].sum()),
            int(flagged_df["flag_possible_duplicate"].sum()),
        ]
    }

    return jsonify({
        "total_spend":   f"Rs {stats['total_spend']:,.0f}",
        "flagged_spend": f"Rs {stats['flagged_spend']:,.0f}",
        "flagged_pct":   f"{stats['flagged_pct']:.1%}",
        "flagged_pct_raw": round(stats['flagged_pct']*100, 1),
        "dup_count":     stats["dup_count"],
        "dup_value":     f"Rs {stats['dup_value']:,.0f}",
        "period":        stats["period"],
        "top_depts":     stats["top_flag_depts"],
        "chart_monthly": chart_monthly,
        "chart_category":chart_category,
        "chart_dept":    chart_dept,
        "chart_flags":   chart_flags,
    })

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message","").lower()
    stats = current_data.get("stats",{})
    if not stats:
        return jsonify({"reply":"Please upload an expense file first!"})

    if any(w in user_msg for w in ["highest","most","top","department"]):
        top = list(stats["top_flag_depts"].keys())[0]
        amt = list(stats["top_flag_depts"].values())[0]
        return jsonify({"reply":f"The department with the highest flagged expenses is <b>{top}</b> with <b>Rs {amt:,.0f}</b> flagged for review. Transactions are significantly above the normal range for their expense category."})

    if any(w in user_msg for w in ["duplicate","same vendor"]):
        return jsonify({"reply":f"We found <b>{stats['dup_count']} possible duplicate payments</b> worth <b>Rs {stats['dup_value']:,.0f}</b>. These are cases where the same vendor was paid the same amount within a few days — likely double-payment errors worth investigating immediately."})

    if any(w in user_msg for w in ["total","spend","how much"]):
        return jsonify({"reply":f"Total spend reviewed: <b>Rs {stats['total_spend']:,.0f}</b>. Of this, <b>Rs {stats['flagged_spend']:,.0f} ({stats['flagged_pct']:.1%})</b> was flagged as potentially wasteful or anomalous by the ML models."})

    if any(w in user_msg for w in ["summary","overview","tell me","report"]):
        top_depts = ", ".join(list(stats["top_flag_depts"].keys())[:3])
        return jsonify({"reply":f"<b>Summary ({stats['period']}):</b><br>• Total spend: Rs {stats['total_spend']:,.0f}<br>• Flagged: Rs {stats['flagged_spend']:,.0f} ({stats['flagged_pct']:.1%})<br>• Top departments: {top_depts}<br>• Duplicate payments: {stats['dup_count']} transactions worth Rs {stats['dup_value']:,.0f}"})

    if any(w in user_msg for w in ["overspend","over","budget","trend"]):
        top_over = list(stats["top_overspend_depts"].keys())[0]
        return jsonify({"reply":f"The department with the most recurring overspend is <b>{top_over}</b>. Their monthly expenses in a specific category kept exceeding their own historical average — a sign of systemic waste, not a one-off spike."})
    if any(w in user_msg for w in ["suggest","reduce","cut","save","recommendation","improve","fix"]):
        top = list(stats["top_flag_depts"].keys())[0]
        return jsonify({"reply": f"Here are some recommendations to reduce wasteful spending:<br><br>1. <b>Review {top} department</b> — highest flagged spend, needs cost-center owner review<br>2. <b>Investigate {stats['dup_count']} duplicate payments</b> worth {stats['dup_value']} — contact vendors to confirm if double-paid<br>3. <b>Set monthly spend alerts</b> for Maintenance and Drilling which show recurring overspend patterns<br>4. <b>Mandate 3-quote policy</b> for vendors like Local Workshop Co appearing repeatedly in anomalies<br>5. <b>Weekend transaction review</b> — flag approvals made on Saturdays/Sundays for audit"})
    return jsonify({"reply":f"Based on the analysis: <b>Rs {stats['flagged_spend']:,.0f}</b> was flagged out of Rs {stats['total_spend']:,.0f} total spend. Top flagged department: <b>{list(stats['top_flag_depts'].keys())[0]}</b>. {stats['dup_count']} duplicate payments detected.<br><br>Try asking: <i>summary · top department · duplicates · overspend · total spend</i>"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
