# Creative Performance Analyzer

A dark-themed Streamlit web app that helps paid social and growth marketing teams score, rank, and act on ad creative performance data — without a BI tool, SQL, or a data warehouse.

Upload a CSV or Excel export from Meta Ads, TikTok Ads, YouTube, or Google Ads, choose your campaign goal, and immediately see which creatives are winning, which to cut, and what to test next.

---

## Who this is for

- Growth marketers and media buyers running paid social campaigns
- Creative strategists who need a fast read on hook performance, CTR, and conversion efficiency
- Performance agencies reviewing creative results with clients
- Anyone who works with ad creative data in spreadsheets and wants a faster way to act on it

---

## What problem it solves

Ad platforms show metrics per creative, but they don't tell you:

- Which creatives to scale vs. cut right now
- Whether a high-CTR creative is actually converting
- Whether a platform problem is actually a creative problem
- What hook, format, or concept is driving the best results
- Where to reallocate budget to maximize paid conversions

This tool surfaces those answers from a plain CSV export in under 60 seconds.

---

## Core features

| Feature | Description |
|---|---|
| **6 goal modes** | Paid Starts, Trial Starts, Efficient Paid Starts, Efficient Trial Starts, Creative Engagement, Full Funnel Quality |
| **Decision labels** | Scale, Keep Testing, Fix Funnel, Cut, Review, Fatiguing — one clear action per creative |
| **8 KPIs scored** | CPA, CPT, Trial→Paid CVR, Paid/$1k, Trials/$1k, CTR Efficiency, Thumbstop Efficiency, Hold Efficiency |
| **Pattern analysis** | Best and worst platform, format, and concept by CPA and volume |
| **Test recommendations** | Rule-based, tied to actual data — not generic advice |
| **Creative fatigue detection** | Flags creatives with rising CPA or falling CTR over time |
| **Statistical significance** | Two-proportion z-test on Trial→Paid CVR per creative |
| **Budget reallocation plan** | Inverse-CPA weighted reallocation across existing budget |
| **Spend pacing tracker** | Budget vs. actual for the current month |
| **Week-over-week comparison** | Upload two periods and compare delta per creative |
| **Benchmark comparison** | Your averages vs. configurable platform benchmarks |
| **Trend sparklines** | Per-creative metric trends over time |
| **Summary snippet** | One-paragraph plain-English read for Slack or email |
| **CSV export** | Ranked creative results with all KPIs |
| **PDF report** | One-page ranked creative summary |
| **PowerPoint report** | 4-slide deck with rankings, charts, and recommendations |
| **Save / reload analyses** | Named analysis snapshots persisted in the session |
| **Column mapper** | Auto-detects common column name variants; manual mapper for the rest |

---

## Quick start — Replit

This app is designed to run in Replit using Streamlit, but it also runs locally after cloning the repo.

1. Fork or open the Replit project
2. Click **Run** — the app starts automatically
3. Open the preview pane or click the external link
4. Click **Use sample data** on the Analyzer page to load the built-in dataset

No API keys, no setup, no accounts required.

---

## Quick start — local

**Python 3.10 or 3.11 recommended.**

```bash
# 1. Clone the repo
git clone https://github.com/punisherdodo/Digital-Marketing-Campaign-Performance-Analysis.git
cd Digital-Marketing-Campaign-Performance-Analysis

# 2. (Optional but recommended) create a virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app opens at **http://localhost:8501** by default.

Click **Use sample data** to load the built-in dataset and explore immediately.

---

## Loading the sample dataset

On the **Analyzer** page:

1. Click **📂 Use sample data**
2. Choose a **Campaign Goal** from the dropdown
3. The full analysis runs immediately — rankings, charts, patterns, and recommendations

The sample file is `sample_data/sample_creative_performance.csv` — 20 creative rows across Meta, TikTok, and YouTube Shorts. It is committed to the repo and works out of the box.

---

## Uploading your own data

1. Export creative-level performance data from your ad platform as CSV or Excel
2. Click **Upload CSV or Excel file** on the Analyzer page
3. If column headers don't match automatically, a **Column Mapper** appears so you can assign them manually
4. Choose a Campaign Goal and review the results

The app handles most common column name variants automatically (e.g. `Creative Name`, `creative_id`, `Ad Name` all map to `creative_id`).

---

## Input columns

### Required for basic analysis

| Column | Accepted variants | Description |
|---|---|---|
| `creative_id` | Creative ID, Ad Name, Creative Name, Ad | Unique identifier for each creative |
| `spend` | Spend, Amount Spent, Cost | Total spend in dollars |

### Strongly recommended

| Column | Accepted variants | Description |
|---|---|---|
| `platform` | Platform, Channel, Network | Meta / TikTok / YouTube Shorts / Google |
| `paid_starts` | Paid Starts, Paid Conversions, Purchases, Paid | Paid subscription or purchase conversions |
| `trial_starts` | Trial Starts, Trials, Leads, Signups | Upper-funnel conversion count |

### Optional — unlocks additional features

| Column | Accepted variants | Description |
|---|---|---|
| `format_concept` | Format, Concept, Ad Format | Creative format or concept label |
| `length_s` | Length, Duration, Video Length | Video length in seconds |
| `thumbstop_rate` | Thumbstop Rate, Thumbstop, Hook Rate, 2s View Rate | % of impressions that stopped scrolling |
| `hold_6s` | 6s Hold Rate, 6-Second View Rate, Hold Rate | % of impressions that watched 6 seconds |
| `ctr` | CTR, Click Through Rate, Click-Through Rate | Click-through rate (%) |
| `week` / `date` / `period` | Week, Date, Period, Reporting Period | Enables fatigue detection, sparklines, and WoW comparison |

If a required column is missing after upload, the app shows a friendly error explaining what to fix.

---

## Configuration (sidebar)

All settings are in the **Advanced settings** expander in the sidebar:

| Setting | Default | Description |
|---|---|---|
| **CPA Target** | $80 | Creatives below this CPA are flagged as Scale candidates; used as reference line on charts |
| **Metric Targets** | Off | CPT, CTR, Thumbstop, 6s Hold, CVR, Min Paid Starts — shown as dashed reference lines and delta indicators in summary cards |
| **Benchmark Targets** | Off | Per-platform CTR and CPA averages — unlocks delta columns in the Benchmark Comparison expander |
| **Creative Engagement weights** | 40/30/30 | Relative weight of Thumbstop, Hold, CTR in the CE scoring mode |
| **Full Funnel Quality weights** | 30/25/20/15/10 | Relative weight of CPA, Paid Starts, CVR, CTR, Thumbstop in the FFQ scoring mode |

---

## Deployment

### Streamlit Community Cloud (free tier)

```
Repo:   github.com/YOUR_USERNAME/creative-performance-analyzer
Branch: main
File:   app.py
```

Set `enableXsrfProtection = true` in `.streamlit/config.toml` before deploying (see note below).

### Replit Deployments

Click **Deploy** in the Replit toolbar. The run command is already configured.

### Render / Railway / Fly.io

```bash
# Build command (none needed for Python)
# Start command:
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

Set the `PORT` environment variable to whatever your hosting platform expects (usually 8080 or 10000).

### XSRF note for non-Replit deployments

`.streamlit/config.toml` currently has `enableXsrfProtection = false`. This is required for Replit's proxied iframe. If you deploy anywhere else, change it back to `true`:

```toml
[server]
enableXsrfProtection = true
```

---

## What is production-ready now

- File upload (CSV + Excel)
- Column auto-detection and manual mapper
- 6 goal-based ranking modes with custom weights
- All 8 KPI calculations with division-by-zero protection
- Decision labels (Scale, Keep Testing, Fix Funnel, Cut, Review, Fatiguing)
- Creative fatigue detection
- Statistical significance testing
- Budget reallocation planner
- Spend pacing tracker
- Week-over-week comparison
- Platform benchmark comparison
- Trend sparklines
- Pattern analysis
- Test-next recommendations
- Summary snippet
- CSV, PDF, and PowerPoint export
- Save and reload named analyses
- Sample dataset included

---

## What would still be needed for real ad-platform integrations

The **Integrations** page in the app shows prototype connection cards for Meta Ads, TikTok Ads, Google Sheets, Airtable, Slack, Notion, Google Drive, Mixpanel, Amplitude, and HubSpot.

These are **prototype-level**. They demonstrate what real integrations would pull and test a connection endpoint, but they are not production OAuth flows. For production use, each integration would need:

- OAuth 2.0 authentication (not manual API key paste)
- Encrypted secret storage (environment variables or a secrets manager)
- Role-based permissions
- API rate-limit handling and retry logic
- Scheduled data refresh
- Source-specific data mapping and normalization
- Error logging and alerting

The core app works fully without any integrations. Data cloud connections (Snowflake, BigQuery, Databricks) are not included and are not required.

---

## Troubleshooting

**App doesn't start locally**
- Check Python version: `python --version` — use 3.10 or 3.11
- Reinstall dependencies: `pip install -r requirements.txt`
- Run: `streamlit run app.py`

**Upload fails or shows blank results**
- Make sure your file has at least `creative_id` and `spend` columns
- Use the Column Mapper to assign your actual column names
- Check that numeric columns don't contain currency symbols (e.g. `$1,200` → `1200`)

**PDF or PowerPoint export fails**
- Ensure `fpdf2` and `python-pptx` are installed: `pip install fpdf2 python-pptx`
- If exporting from Replit, check the workflow logs for the specific error

**Saved analyses disappear on restart**
- Analyses are saved to `saved_analyses.json` in the project folder — this file is session-persistent but not backed up
- The file is excluded from Git so it will not be present after a fresh clone

**"enableXsrfProtection" warning**
- Safe to ignore in Replit; required to be `false` for Replit's iframe proxy
- Change to `true` before deploying anywhere outside Replit

---

## Project structure

```
creative-performance-analyzer/
├── app.py                               # Streamlit UI — render_* and page_* functions only
├── requirements.txt                     # Python dependencies (7 packages, no Node/TS)
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml                      # Dark theme + Replit iframe config
├── sample_data/
│   └── sample_creative_performance.csv  # 20-row generic sample (Meta / TikTok / YouTube Shorts)
└── utils/
    ├── __init__.py
    ├── data_processing.py               # Column mapping, load/clean, KPI calculation, formatters, save helpers
    ├── scoring.py                       # CPA target, ranking logic, decision labels, fatigue, significance
    ├── recommendations.py               # Pattern insights, test recommendations, summary snippet
    ├── exports.py                       # CSV, PDF (fpdf2), and PowerPoint (python-pptx) export builders
    └── integrations.py                  # Prototype connection tests and Google Sheets loader
```

Import hierarchy (no circular dependencies):

```
data_processing  ←  scoring
data_processing  ←  recommendations
recommendations  ←  exports
app.py           ←  all of the above
```

The `artifacts/`, `lib/`, `scripts/`, and Node/TypeScript files in this Replit project are Replit platform scaffolding. They are excluded from Git and are not required to run the Streamlit app.

---

## Requirements

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | ≥ 1.32 | App framework |
| `pandas` | ≥ 2.0 | Data processing |
| `numpy` | ≥ 1.24 | Numeric calculations |
| `plotly` | ≥ 5.18 | Interactive charts |
| `openpyxl` | ≥ 3.1 | Excel file support (.xlsx) |
| `fpdf2` | ≥ 2.7 | PDF export |
| `python-pptx` | ≥ 0.6.23 | PowerPoint export |

No API keys, no environment variables, and no cloud connections are required to run the core app.

---

## License

MIT
