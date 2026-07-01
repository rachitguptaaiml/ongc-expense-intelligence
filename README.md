# ONGC Expense Waste Detection Pipeline — Prototype

A working prototype for the project: automatically clean expense data, flag
likely waste using ML, and generate both a Power BI-ready dataset and a
plain-English summary report.

Currently running on **synthetic data** built to look like typical PSU
expense records. Once you get real demo reports from your boss, swap the
input file and you're live — see "Switching to real data" below.

## How it's structured

```
generate_sample_data.py   -> creates data/raw_expenses.csv (synthetic, delete once you have real data)
clean_data.py              -> standardizes raw data into a consistent schema
anomaly_detection.py        -> the ML layer: flags potential waste
generate_report.py          -> turns flagged data into a plain-English summary
main.py                     -> runs everything end to end
data/                        -> raw + intermediate CSVs
output/                      -> powerbi_export.xlsx + narrative_report.txt (final deliverables)
```

## Running it

```bash
pip install pandas numpy scikit-learn openpyxl
python generate_sample_data.py   # only needed for the synthetic demo
python main.py                    # runs the full pipeline
```

Outputs land in `output/`:
- **powerbi_export.xlsx** — open this in Power BI Desktop (Get Data → Excel)
  and build dashboards off the `transactions` and `department_overspend` sheets.
- **narrative_report.txt** — the plain-English summary, currently template-based.

## The ML approach (and why it's not one black-box model)

Four complementary, explainable methods, because the people reviewing this
(finance officers) need to trust *why* something got flagged, not just see
a red highlight:

1. **Statistical outliers** (IQR per category) — catches amounts that are
   simply too big relative to that category's normal range.
2. **Isolation Forest** — catches multivariate weirdness (e.g. a weekend
   transaction in an unusual department/category combo) that simple
   thresholds miss.
3. **Duplicate payment detection** — same vendor, same amount, paid within
   days of each other. One of the most common real forms of "waste."
4. **Department/category overspend trend** — flags a department steadily
   overspending on one category month over month, which catches systemic
   waste rather than one-off anomalies.

## Switching to real data

1. Get the demo report from your boss (Excel/CSV ideally; if it's a PDF,
   ping me and we'll add a PDF table extraction step first).
2. Open `clean_data.py` and update `COLUMN_MAP` so the keys match your
   pipeline's expected names and the values match the real file's headers.
3. Run `python main.py` pointed at the real file:
   `main(raw_path="data/your_real_file.csv")`
4. Sanity-check the flagged transaction count and total flagged value in the
   console output before trusting the dashboard — if literally everything
   or nothing gets flagged, the contamination/threshold parameters in
   `anomaly_detection.py` probably need tuning for the real data's scale.

## Wiring up the local LLM (Open WebUI) for the narrative

`generate_report.py` has an `llm_narrative()` function that calls a local
LLM through Open WebUI's chat completions API instead of the template. This
wasn't testable in this sandbox (no network access here), so test it on your
own machine:

1. Make sure Open WebUI is running in Docker and reachable (default
   `http://localhost:3000`).
2. Update `OPEN_WEBUI_URL` and `OPEN_WEBUI_MODEL` in `generate_report.py` to
   match your setup.
3. In `main.py`, swap `narrative = template_narrative(stats)` for
   `narrative = llm_narrative(stats)`.

This is the part worth highlighting to your boss in the demo: the LLM never
needs internet access or to send ONGC financial data anywhere external,
since it's all running inside your Docker container.

## Things still worth deciding with your boss

- Which expense categories actually matter most for "waste" at ONGC
  (travel, contractor payments, fuel/POL, equipment maintenance are the
  common high-waste categories at PSUs, but he may have specific ones in mind).
- What counts as an acceptable false-positive rate — flagging too much
  erodes trust in the tool, flagging too little misses real waste.
- Who actually reviews the flagged items once generated (which determines
  how the report should be formatted/delivered — dashboard link, emailed
  PDF, etc).
