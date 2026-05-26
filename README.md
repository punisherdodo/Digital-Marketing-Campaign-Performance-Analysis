# Creative Performance Analyzer

A dark-themed Streamlit app for paid-social growth teams to score, rank, and act on ad creative performance data — no BI tool required.

---

## Features

- **Upload CSV or Excel** exports from Meta, TikTok, YouTube Shorts, or Google Ads
- **Auto-maps column names** — common header variants are detected automatically; a manual mapper appears if needed
- **6 goal modes** — Paid Starts, Trial Starts, Efficient Paid Starts, Efficient Trial Starts, Creative Engagement, Full Funnel Quality
- **8 KPIs scored per creative** — CPA, CPT, Trial→Paid CVR, Paid Starts/$1k, Trial Starts/$1k, CTR Efficiency, Thumbstop Efficiency, Hold Efficiency
- **Decision labels** — Scale, Keep Testing, Fix Funnel, Cut, Review, Fatiguing
- **Creative fatigue detection** — flags creatives with rising CPA or falling CTR over time
- **Statistical significance testing** — two-proportion z-test on Trial→Paid CVR
- **Budget reallocation planner** — inverse-CPA weighted plan with CSV export
- **Spend pacing tracker** — monthly budget vs. actual
- **Week-over-week comparison page**
- **Benchmark comparison** — your platform averages vs. configurable industry targets
- **Trend sparklines** per creative
- **AI summary snippet** — one-paragraph plain-English read of the data
- **Export** — PDF report, PowerPoint deck (4 slides), ranked CSV, chart CSVs
- **Save / reload analyses** — persist named snapshots in the browser session

---

## Quick start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/creative-performance-analyzer.git
cd creative-performance-analyzer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501` by default.

---

## Requirements

| Package | Purpose |
|---|---|
| `streamlit >= 1.32` | App framework |
| `pandas >= 2.0` | Data processing |
| `numpy >= 1.24` | Calculations |
| `plotly >= 5.18` | Interactive charts |
| `openpyxl >= 3.1` | Excel file support |
| `fpdf2 >= 2.7` | PDF export |
| `python-pptx >= 0.6.23` | PowerPoint export |

Install all at once:

```bash
pip install -r requirements.txt
```

---

## Project structure

```
creative-performance-analyzer/
├── app.py                          # Streamlit UI — render_* and page_* functions only
├── requirements.txt
├── sample_data/
│   └── sample_creative_performance.csv  # 20-row generic sample (Meta / TikTok / YouTube Shorts)
├── utils/
│   ├── __init__.py
│   ├── data_processing.py          # Column mapping, load/clean, KPI calculation, formatters, save helpers
│   ├── scoring.py                  # CPA target, ranking logic, decision labels, fatigue, significance
│   ├── recommendations.py          # Pattern insights, test recommendations, summary snippet
│   ├── exports.py                  # CSV, PDF (fpdf2), and PowerPoint (python-pptx) export builders
│   └── integrations.py             # Prototype connection tests and Google Sheets loader
└── .streamlit/
    └── config.toml                 # Dark theme + Replit iframe config
```

Import hierarchy (no circular dependencies):

```
data_processing  ←  scoring
data_processing  ←  recommendations
data_processing
recommendations  ←  exports
app.py           ←  all of the above
```

---

## Supported input columns

The app auto-detects common column name variants. Canonical names:

| Column | Description |
|---|---|
| `creative_id` | Unique ad creative identifier |
| `platform` | Meta / TikTok / YouTube Shorts / Google |
| `format_concept` | Creative format or concept label |
| `spend` | Total spend ($) |
| `thumbstop_rate` | Thumbstop rate (%) |
| `hold_6s` | 6-second hold rate (%) |
| `ctr` | Click-through rate (%) |
| `trial_starts` | Trial start count |
| `paid_starts` | Paid subscription start count |
| `week` / `date` / `period` | Optional — enables fatigue detection, sparklines, and WoW comparison |

If your column headers don't match, a **Column Mapper** expander appears after upload so you can assign them manually.

---

## Configuration

All settings live in the **sidebar** inside the app:

- **CPA Target** — reference line on charts, used for decision labels
- **Metric Targets** — CPT, CTR, Thumbstop Rate, 6s Hold Rate, Trial→Paid CVR, Min Paid Starts; shown as reference lines and delta indicators
- **Benchmark Targets** — per-platform CTR and CPA benchmarks
- **Goal weights** — custom weights for Creative Engagement and Full Funnel Quality modes

---

## Deployment note

`.streamlit/config.toml` sets `enableXsrfProtection = false`, which is required when running inside Replit's proxied iframe. If you deploy elsewhere (Streamlit Community Cloud, a VPS, Docker), change this back to `true`:

```toml
[server]
enableXsrfProtection = true
```

---

## License

MIT
