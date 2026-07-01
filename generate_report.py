import pandas as pd
import json

OPEN_WEBUI_URL = "http://localhost:11434/api/chat"
OPEN_WEBUI_MODEL = "llama3.2"

def build_summary_stats(flagged_df, overspend_df):
    total_spend = flagged_df["amount_inr"].sum()
    flagged_spend = flagged_df.loc[flagged_df["any_flag"], "amount_inr"].sum()
    top_flag_depts = flagged_df[flagged_df["any_flag"]].groupby("department")["amount_inr"].sum().sort_values(ascending=False).head(3)
    top_overspend_depts = overspend_df["department"].value_counts().head(3)
    dup_count = flagged_df["flag_possible_duplicate"].sum()
    dup_value = flagged_df.loc[flagged_df["flag_possible_duplicate"], "amount_inr"].sum()
    return {
        "total_spend": total_spend,
        "flagged_spend": flagged_spend,
        "flagged_pct": flagged_spend / total_spend if total_spend else 0,
        "top_flag_depts": top_flag_depts.to_dict(),
        "top_overspend_depts": top_overspend_depts.to_dict(),
        "dup_count": int(dup_count),
        "dup_value": float(dup_value),
        "period": f"{flagged_df['month'].min()} to {flagged_df['month'].max()}",
    }

def template_narrative(stats):
    top_dept_lines = "\n".join(f"  - {dept}: Rs {amt:,.0f} flagged" for dept, amt in stats["top_flag_depts"].items())
    overspend_lines = "\n".join(f"  - {dept}: {count} month(s) of unusual category growth" for dept, count in stats["top_overspend_depts"].items())
    return f"""EXPENSE REVIEW SUMMARY ({stats['period']})

Total spend reviewed: Rs {stats['total_spend']:,.0f}
Flagged for review: Rs {stats['flagged_spend']:,.0f} ({stats['flagged_pct']:.1%} of total)

Departments with the highest flagged value:
{top_dept_lines}

Departments showing recurring month-on-month overspend:
{overspend_lines}

Possible duplicate payments: {stats['dup_count']} transactions worth Rs {stats['dup_value']:,.0f}

Note: flags are statistical signals, not confirmed waste.
"""

def llm_narrative(stats):
    import urllib.request
    prompt = (
        "You are writing a short plain-English summary for a finance officer "
        "reviewing flagged expense data at a PSU. Be concise and factual. "
        f"Here is the data:\n{json.dumps(stats, indent=2)}"
    )
    payload = {
        "model": OPEN_WEBUI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    req = urllib.request.Request(
        OPEN_WEBUI_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        result = json.loads(resp.read())
    return result["message"]["content"]

if __name__ == "__main__":
    flagged_df = pd.read_csv("data/flagged_expenses.csv")
    overspend_df = pd.read_csv("data/department_overspend.csv")
    stats = build_summary_stats(flagged_df, overspend_df)
    narrative = llm_narrative(stats)
    with open("output/narrative_report.txt", "w") as f:
        f.write(narrative)
    print(narrative)