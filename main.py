"""
Runs the full pipeline end to end: clean -> detect -> report -> export.
This is the file you'd actually run for a demo.

Power BI usage: open Power BI Desktop -> Get Data -> Excel -> point it at
output/powerbi_export.xlsx -> build visuals off the 'transactions' and
'department_overspend' sheets. Refresh the source file and Power BI's
refresh button keeps the dashboard current as new data comes in.
"""
import pandas as pd
from clean_data import load_and_clean
from anomaly_detection import run_all
from generate_report import build_summary_stats, template_narrative, llm_narrative


def main(raw_path="data/raw_expenses.csv"):
    print("1. Cleaning data...")
    df = load_and_clean(raw_path)

    print("2. Running ML flagging...")
    flagged_df, overspend_df = run_all(df)

    print("3. Building narrative report...")
    stats = build_summary_stats(flagged_df, overspend_df)
    narrative = llm_narrative(stats)

    print("4. Exporting Power BI-ready workbook...")
    with pd.ExcelWriter("output/powerbi_export.xlsx", engine="openpyxl") as writer:
        flagged_df.to_excel(writer, sheet_name="transactions", index=False)
        overspend_df.to_excel(writer, sheet_name="department_overspend", index=False)
        pd.DataFrame([stats]).to_excel(writer, sheet_name="summary_stats", index=False)

    with open("output/narrative_report.txt", "w") as f:
        f.write(narrative)

    print("\nDone. Outputs in ./output/:")
    print("  - powerbi_export.xlsx  (feed this into Power BI)")
    print("  - narrative_report.txt (plain-English summary)")
    print("\n" + narrative)
    return flagged_df, overspend_df, stats


if __name__ == "__main__":
    main()
