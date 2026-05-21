# Creative Performance Analyzer

A dark-themed Streamlit app for paid-social growth teams to score, rank, and act on ad creative performance data.

## What it does

Upload a CSV or Excel export from any ad platform (Meta, TikTok, YouTube Shorts, Google) and the app will:

- **Rank creatives** across 6 campaign goal modes (Paid Starts, Trial Starts, Efficient Paid Starts, Efficient Trial Starts, Creative Engagement, Full Funnel Quality)
- **Score 8 KPIs** — CPA, CPT, Trial→Paid CVR, Paid Starts per $1k, Trial Starts per $1k, CTR Efficiency, Thumbstop Efficiency, Hold Efficiency
- **Label every creative** — Scale, Keep Testing, Fix Funnel, Cut, Review, or Fatiguing
- **Detect creative fatigue** — flags creatives with consistently rising CPA or falling CTR across periods
- **Test statistical significance** — two-proportion z-test on Trial→Paid CVR vs. the rest of the cohort
- **Reallocate budget** — inverse-CPA reallocation plan with CSV export
- **Track spend pacing** — monthly budget vs. actual spend
- **Compare periods** — week-over-week delta table and charts
- **Benchmark** — compare your platform averages to industry targets
- **Export** — PDF report, PowerPoint deck (4 slides), ranked CSV, chart CSVs

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Stack

- Python 3.11
- Streamlit 1.32+
- pandas, numpy, plotly
- fpdf2 (PDF export)
- python-pptx (PowerPoint export)
- openpyxl (Excel upload support)

## Supported input columns

The app auto-maps common column name variants. Canonical names:

| Column | Description |
|---|---|
| `creative_id` | Unique ad creative identifier |
| `platform` | Meta / TikTok / YouTube Shorts / Google |
| `format_concept` | Creative format label |
| `spend` | Total spend ($) |
| `thumbstop_rate` | Thumbstop rate (%) |
| `hold_6s` | 6-second hold rate (%) |
| `ctr` | Click-through rate (%) |
| `trial_starts` | Trial start count |
| `paid_starts` | Paid subscription start count |
| `week` / `date` / `period` | Optional — enables fatigue detection and sparklines |

If columns are not auto-detected, the **Column Mapper** expander appears after upload so you can map your headers manually.

## Security notes

- No API keys or secrets are hardcoded anywhere in the source.
- The Integrations page accepts API credentials as browser-session form inputs only — they are never stored or logged.
- `saved_analyses.json` is a runtime file excluded from version control (see `.gitignore`).
- `enableXsrfProtection = false` in `.streamlit/config.toml` is required for Replit's proxied iframe. Set it back to `true` for any other deployment target.

## Advanced settings (sidebar)

- **CPA Target** — affects decision labels and chart reference lines
- **Metric Targets** — CPT, CTR, Thumbstop, 6s Hold Rate, Trial→Paid CVR, Min Paid Starts; shown as reference lines on charts and delta indicators in summary cards
- **Benchmark Targets** — per-platform CTR and CPA benchmarks for the Benchmark Comparison expander
- **Creative Engagement weights** — custom weighting for the CE goal mode
- **Full Funnel Quality weights** — custom weighting for the FFQ goal mode

## User preferences

- Dark theme only.
- No kaleido / PNG chart exports — use CSV downloads or PPTX export instead.
- All PDF and PPTX text must pass through `sanitize_pdf_text()` to avoid Unicode crashes.
