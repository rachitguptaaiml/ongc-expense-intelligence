# 🛢️ ONGC Expense Intelligence

> ML-powered expense anomaly detection with local AI — built during ONGC internship 2026

## 🚀 What it does

- Detects anomalous expenses using **Isolation Forest + IQR statistical analysis**
- Flags **duplicate payments** (same vendor, same amount, paid within days)
- Tracks **department overspend trends** month-on-month
- Generates **AI narrative reports** using local LLM (Llama 3.2 via Ollama)
- Interactive **web dashboard** with 4 Chart.js visualizations
- **AI chatbot** for natural language queries on expense data
- **Power BI dashboard** with KPI cards and trend charts

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| ML & Data | Python, pandas, scikit-learn |
| Anomaly Detection | Isolation Forest, IQR, Duplicate Detection |
| Local AI | Docker + Ollama + Llama 3.2 |
| Web Interface | Flask + Chart.js |
| BI Dashboard | Power BI |
| AI Chat UI | Open WebUI |

## 🔒 Privacy First

All AI runs **100% locally** via Docker and Ollama — no financial data ever leaves the network. Designed specifically for PSU environments like ONGC where data security is critical.

## ⚡ Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate sample data
python generate_sample_data.py

# Run ML pipeline
python main.py

# Start web app
python app.py
```

Then open `http://localhost:5000`

## 📊 ML Approach

Four complementary detection methods:

1. **Statistical Outliers (IQR)** — flags amounts far above category norms
2. **Isolation Forest** — catches multivariate anomalies
3. **Duplicate Detection** — same vendor + amount within days
4. **Overspend Trending** — month-on-month category growth alerts

## 🏗️ Project Structure
├── app.py                  # Flask web application
├── main.py                 # Pipeline orchestrator
├── clean_data.py           # Data cleaning & standardization
├── anomaly_detection.py    # ML flagging (4 methods)
├── generate_report.py      # AI narrative report generator
├── generate_sample_data.py # Synthetic ONGC-style data
├── templates/
│   └── index.html          # Full dashboard UI
└── requirements.txt

## 👨‍💻 Built By

Rachit Gupta — CS student, GLA University
Internship Project @ ONGC IT Department, 2026
