import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import StringIO

st.set_page_config(
    page_title="Creative Performance Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS for dark dashboard polish ────────────────────────────────────
st.markdown(
    """
    <style>
    /* Metric card look */
    div[data-testid="metric-container"] {
        background: #161B27;
        border: 1px solid #2A3350;
        border-radius: 10px;
        padding: 14px 18px 10px;
    }
    div[data-testid="metric-container"] label { color: #8A9BC8 !important; font-size: 0.78rem; }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] { font-size: 1.4rem; }

    /* Section headers */
    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #4F8EF7;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 0.5rem 0 0.25rem;
    }

    /* Decision label badges */
    .badge-scale    { background:#1a4731; color:#34d399; border:1px solid #34d399;
                      padding:2px 10px; border-radius:20px; font-size:0.78rem; font-weight:700; }
    .badge-keep     { background:#3b3515; color:#fbbf24; border:1px solid #fbbf24;
                      padding:2px 10px; border-radius:20px; font-size:0.78rem; font-weight:700; }
    .badge-review   { background:#2e2a10; color:#f59e0b; border:1px solid #f59e0b;
                      padding:2px 10px; border-radius:20px; font-size:0.78rem; font-weight:700; }
    .badge-fix      { background:#3b2200; color:#fb923c; border:1px solid #fb923c;
                      padding:2px 10px; border-radius:20px; font-size:0.78rem; font-weight:700; }
    .badge-cut      { background:#3b0a0a; color:#f87171; border:1px solid #f87171;
                      padding:2px 10px; border-radius:20px; font-size:0.78rem; font-weight:700; }

    /* Pattern analysis bullets */
    .insight-box {
        background: #161B27;
        border-left: 3px solid #4F8EF7;
        border-radius: 0 8px 8px 0;
        padding: 10px 16px;
        margin: 6px 0;
        font-size: 0.92rem;
        color: #FAFAFA;
    }
    .rec-box {
        background: #161B27;
        border-left: 3px solid #34d399;
        border-radius: 0 8px 8px 0;
        padding: 10px 16px;
        margin: 6px 0;
        font-size: 0.92rem;
        color: #FAFAFA;
    }

    /* Divider */
    hr { border-color: #2A3350 !important; margin: 1.2rem 0; }

    /* Hide default menu */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Sample data ──────────────────────────────────────────────────────────────
SAMPLE_CSV = """Creative ID,Platform,Format / Concept,Length,Spend,Thumbstop Rate,6s Hold Rate,CTR,Trial Starts,Paid Starts
C01,Meta,"UGC problem/solution: I used to leave every meeting with 4 tabs open...",28s,4800,36%,24%,1.7%,267,59
C02,Meta,"Static screenshots: AI notes in one tap",15s,3200,25%,N/A,0.9%,133,35
C03,Meta,"Founder talking head: Why we built LoopNote",35s,2700,18%,11%,0.6%,54,12
C04,TikTok,"Creator skit: POV your boss asks what was decided in the meeting",23s,5100,45%,31%,2.4%,300,42
C05,TikTok,"Screen-record demo: Turn a rambling voice memo into a task list",21s,4400,39%,27%,2.1%,338,71
C06,TikTok,"AI avatar explainer: Meet your AI productivity assistant",30s,3000,22%,15%,0.8%,64,9
C07,YouTube Shorts,"Before/after comparison: Before vs. after meeting notes",32s,4700,38%,22%,1.3%,235,63
C08,YouTube Shorts,"Tutorial: 3 ways students use LoopNote",45s,3900,33%,29%,1.1%,112,13
C09,Meta,"Creator testimonial: I imported 120 voice notes and found 18 tasks",26s,5500,41%,26%,2.0%,306,67
C10,TikTok,"Trend remix: Things I stopped doing after using LoopNote",18s,3800,50%,35%,1.9%,174,20
"""

# ── Column normalisation map ──────────────────────────────────────────────────
# Maps lowercased / stripped versions of common column names → canonical names
COLUMN_MAP = {
    "creative id": "creative_id",
    "creative_id": "creative_id",
    "creativeid": "creative_id",
    "id": "creative_id",
    "platform": "platform",
    "format / concept": "format_concept",
    "format/concept": "format_concept",
    "format concept": "format_concept",
    "format": "format_concept",
    "concept": "format_concept",
    "length": "length",
    "spend": "spend",
    "thumbstop rate": "thumbstop_rate",
    "thumbstop_rate": "thumbstop_rate",
    "thumbstop": "thumbstop_rate",
    "6s hold rate": "hold_6s",
    "6s_hold_rate": "hold_6s",
    "6s hold": "hold_6s",
    "hold rate": "hold_6s",
    "hold_rate": "hold_6s",
    "ctr": "ctr",
    "click through rate": "ctr",
    "click-through rate": "ctr",
    "trial starts": "trial_starts",
    "trial_starts": "trial_starts",
    "trials": "trial_starts",
    "paid starts": "paid_starts",
    "paid_starts": "paid_starts",
    "paid": "paid_starts",
}

CPA_TARGET = 90.0


def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to canonical names using COLUMN_MAP."""
    rename = {}
    for col in df.columns:
        key = col.strip().lower()
        if key in COLUMN_MAP:
            rename[col] = COLUMN_MAP[key]
    return df.rename(columns=rename)


def clean_numeric(series: pd.Series) -> pd.Series:
    """Strip $, commas and convert to float. Coerce non-numeric → NaN."""
    return (
        series.astype(str)
        .str.replace(r"[$,]", "", regex=True)
        .str.strip()
        .replace({"N/A": np.nan, "n/a": np.nan, "NA": np.nan, "-": np.nan, "": np.nan})
        .astype(float, errors="ignore")
    )


def clean_percent(series: pd.Series) -> pd.Series:
    """Convert percent strings like '36%' or '0.36' to float (0–100 scale)."""
    s = (
        series.astype(str)
        .str.replace(r"[$,]", "", regex=True)
        .str.strip()
        .replace({"N/A": np.nan, "n/a": np.nan, "NA": np.nan, "-": np.nan, "": np.nan})
    )
    result = []
    for v in s:
        try:
            if isinstance(v, str) and "%" in v:
                result.append(float(v.replace("%", "").strip()))
            else:
                val = float(v)
                # If value looks like a decimal proportion (< 1.5), convert to %
                if val < 1.5:
                    result.append(val * 100)
                else:
                    result.append(val)
        except (ValueError, TypeError):
            result.append(np.nan)
    return pd.Series(result, index=series.index)


def extract_seconds(series: pd.Series) -> pd.Series:
    """Convert length strings like '28s' or '28' to numeric seconds."""
    def parse(v):
        if pd.isna(v):
            return np.nan
        v = str(v).strip().lower()
        v = v.replace("s", "").replace("sec", "").strip()
        try:
            return float(v)
        except ValueError:
            return np.nan
    return series.apply(parse)


def load_and_clean(source) -> tuple[pd.DataFrame, list[str]]:
    """Load CSV/Excel/string, normalise columns, clean types. Returns (df, warnings)."""
    warnings = []
    if isinstance(source, str):
        df = pd.read_csv(StringIO(source))
    elif hasattr(source, "name") and source.name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(source)
    else:
        try:
            df = pd.read_csv(source)
        except Exception:
            df = pd.read_excel(source)

    df = normalise_columns(df)

    # Ensure creative_id exists
    if "creative_id" not in df.columns:
        df.insert(0, "creative_id", [f"C{i+1:02d}" for i in range(len(df))])
        warnings.append("No 'Creative ID' column found — auto-generated IDs assigned.")

    # Clean Spend
    if "spend" in df.columns:
        df["spend"] = clean_numeric(df["spend"])

    # Clean percent columns
    for col in ["thumbstop_rate", "hold_6s", "ctr"]:
        if col in df.columns:
            df[col] = clean_percent(df[col])

    # Clean integer columns
    for col in ["trial_starts", "paid_starts"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Clean length
    if "length" in df.columns:
        df["length_s"] = extract_seconds(df["length"])

    return df, warnings


def calculate_kpis(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Add KPI columns where source data exists. Returns (df, missing_warnings)."""
    missing = []

    def safe_div(num, den):
        result = np.where(den != 0, num / den, np.nan)
        return pd.Series(result, index=df.index)

    has = lambda c: c in df.columns and df[c].notna().any()

    if has("spend") and has("paid_starts"):
        df["cpa"] = safe_div(df["spend"], df["paid_starts"])
    else:
        missing.append("Cost per Paid Start (needs Spend + Paid Starts)")

    if has("spend") and has("trial_starts"):
        df["cpt"] = safe_div(df["spend"], df["trial_starts"])
    else:
        missing.append("Cost per Trial Start (needs Spend + Trial Starts)")

    if has("paid_starts") and has("trial_starts"):
        df["trial_to_paid_cvr"] = safe_div(df["paid_starts"], df["trial_starts"])
    else:
        missing.append("Trial→Paid CVR (needs Paid Starts + Trial Starts)")

    if has("paid_starts") and has("spend"):
        df["paid_per_1k"] = safe_div(df["paid_starts"], df["spend"]) * 1000
    else:
        missing.append("Paid Starts per $1k (needs Paid Starts + Spend)")

    if has("trial_starts") and has("spend"):
        df["trial_per_1k"] = safe_div(df["trial_starts"], df["spend"]) * 1000
    else:
        missing.append("Trial Starts per $1k (needs Trial Starts + Spend)")

    if has("ctr") and has("cpa"):
        df["ctr_efficiency"] = safe_div(df["ctr"], df["cpa"])
    else:
        missing.append("CTR Efficiency Score (needs CTR + Cost per Paid Start)")

    if has("thumbstop_rate") and has("cpa"):
        df["thumbstop_efficiency"] = safe_div(df["thumbstop_rate"], df["cpa"])
    else:
        missing.append("Thumbstop Efficiency (needs Thumbstop Rate + Cost per Paid Start)")

    if has("hold_6s") and has("cpa"):
        df["hold_efficiency"] = safe_div(df["hold_6s"], df["cpa"])
    else:
        missing.append("Hold Efficiency (needs 6s Hold Rate + Cost per Paid Start)")

    return df, missing


def _min_max(s: pd.Series, lower_is_better: bool = False) -> pd.Series:
    """Min-max normalise a series to [0, 1]. If lower_is_better, invert."""
    mn, mx = s.min(), s.max()
    if mx == mn:
        return pd.Series(0.5, index=s.index)
    norm = (s - mn) / (mx - mn)
    return (1 - norm) if lower_is_better else norm


def rank_by_goal(df: pd.DataFrame, goal: str) -> pd.DataFrame:
    """Return df sorted by the selected campaign goal, with a Goal Score column."""
    d = df.copy()
    if goal == "Paid Starts":
        if "paid_starts" in d.columns:
            d = d.sort_values("paid_starts", ascending=False)

    elif goal == "Trial Starts":
        if "trial_starts" in d.columns:
            d = d.sort_values("trial_starts", ascending=False)

    elif goal == "Efficient Paid Starts":
        if "cpa" in d.columns:
            d = d.sort_values(
                ["cpa", "paid_starts"], ascending=[True, False], na_position="last"
            )
            d["scale_candidate"] = d["cpa"] < CPA_TARGET

    elif goal == "Efficient Trial Starts":
        if "cpt" in d.columns:
            d = d.sort_values(
                ["cpt", "trial_starts"], ascending=[True, False], na_position="last"
            )

    elif goal == "Creative Engagement":
        cols = []
        weights = []
        if "thumbstop_rate" in d.columns:
            cols.append("thumbstop_rate"); weights.append(0.40)
        if "hold_6s" in d.columns:
            cols.append("hold_6s"); weights.append(0.30)
        if "ctr" in d.columns:
            cols.append("ctr"); weights.append(0.30)
        if cols:
            score = sum(_min_max(d[c]) * w for c, w in zip(cols, weights))
            d["goal_score"] = score / sum(weights)
            d = d.sort_values("goal_score", ascending=False)

    elif goal == "Full Funnel Quality":
        components = [
            ("cpa", 0.30, True),
            ("paid_starts", 0.25, False),
            ("trial_to_paid_cvr", 0.20, False),
            ("ctr", 0.15, False),
            ("thumbstop_rate", 0.10, False),
        ]
        total_w = sum(w for c, w, _ in components if c in d.columns)
        if total_w > 0:
            score = sum(
                _min_max(d[c], inv) * w
                for c, w, inv in components
                if c in d.columns
            )
            d["goal_score"] = score / total_w
            d = d.sort_values("goal_score", ascending=False)

    d = d.reset_index(drop=True)
    d.index = d.index + 1
    return d


def assign_decision_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Add Decision_Label column."""
    d = df.copy()
    labels = []

    median_paid = d["paid_starts"].median() if "paid_starts" in d.columns else np.nan
    median_trial = d["trial_starts"].median() if "trial_starts" in d.columns else np.nan
    median_cvr = d["trial_to_paid_cvr"].median() if "trial_to_paid_cvr" in d.columns else np.nan
    median_thumbstop = d["thumbstop_rate"].median() if "thumbstop_rate" in d.columns else np.nan

    for _, row in d.iterrows():
        cpa = row.get("cpa", np.nan)
        paid = row.get("paid_starts", np.nan)
        trial = row.get("trial_starts", np.nan)
        cvr = row.get("trial_to_paid_cvr", np.nan)
        thumbstop = row.get("thumbstop_rate", np.nan)

        if not np.isnan(cpa) and not np.isnan(paid):
            if cpa < CPA_TARGET and paid > median_paid:
                labels.append("Scale")
                continue
        if not np.isnan(thumbstop) and not np.isnan(paid):
            if thumbstop > median_thumbstop and paid < median_paid:
                labels.append("Keep Testing")
                continue
        if not np.isnan(trial) and not np.isnan(cvr):
            if trial > median_trial and cvr < median_cvr:
                labels.append("Fix Funnel")
                continue
        if not np.isnan(cpa) and not np.isnan(thumbstop):
            if cpa > CPA_TARGET and thumbstop < median_thumbstop:
                labels.append("Cut")
                continue
        labels.append("Review")

    d["decision_label"] = labels
    return d


def badge_html(label: str) -> str:
    cls_map = {
        "Scale": "badge-scale",
        "Keep Testing": "badge-keep",
        "Review": "badge-review",
        "Fix Funnel": "badge-fix",
        "Cut": "badge-cut",
    }
    cls = cls_map.get(label, "badge-review")
    return f'<span class="{cls}">{label}</span>'


def fmt_currency(v):
    if pd.isna(v):
        return "—"
    return f"${v:,.0f}"


def fmt_pct(v):
    if pd.isna(v):
        return "—"
    return f"{v:.1f}%"


def fmt_num(v):
    if pd.isna(v):
        return "—"
    return f"{v:,.0f}"


def fmt_float(v, decimals=2):
    if pd.isna(v):
        return "—"
    return f"{v:,.{decimals}f}"


def length_bucket(s: float) -> str:
    if np.isnan(s):
        return "Unknown"
    if s < 20:
        return "Under 20s"
    elif s <= 30:
        return "20–30s"
    elif s <= 40:
        return "31–40s"
    else:
        return "Over 40s"


def render_summary_cards(df: pd.DataFrame, goal: str):
    total_spend = df["spend"].sum() if "spend" in df.columns else np.nan
    total_trials = df["trial_starts"].sum() if "trial_starts" in df.columns else np.nan
    total_paid = df["paid_starts"].sum() if "paid_starts" in df.columns else np.nan
    blended_cpa = (total_spend / total_paid) if (not np.isnan(total_spend) and total_paid) else np.nan

    best_creative = "—"
    if "decision_label" in df.columns:
        ranked = rank_by_goal(df, goal)
        if not ranked.empty:
            best_creative = ranked.iloc[0].get("creative_id", "—")

    scale_n = (df["decision_label"] == "Scale").sum() if "decision_label" in df.columns else 0
    cut_n = (df["decision_label"] == "Cut").sum() if "decision_label" in df.columns else 0

    cols = st.columns(7)
    with cols[0]:
        st.metric("Total Spend", fmt_currency(total_spend))
    with cols[1]:
        st.metric("Total Trial Starts", fmt_num(total_trials))
    with cols[2]:
        st.metric("Total Paid Starts", fmt_num(total_paid))
    with cols[3]:
        st.metric("Blended CPA", fmt_currency(blended_cpa))
    with cols[4]:
        st.metric("Best Creative", best_creative)
    with cols[5]:
        st.metric("Scale Candidates", int(scale_n))
    with cols[6]:
        st.metric("Cut Candidates", int(cut_n))


_DECISION_LABEL_COLORS = {
    "Scale":        {"color": "#34d399", "background-color": "#1a4731"},
    "Keep Testing": {"color": "#fbbf24", "background-color": "#3b3515"},
    "Review":       {"color": "#f59e0b", "background-color": "#2e2a10"},
    "Fix Funnel":   {"color": "#fb923c", "background-color": "#3b2200"},
    "Cut":          {"color": "#f87171", "background-color": "#3b0a0a"},
}


def _style_decision_cell(val):
    styles = _DECISION_LABEL_COLORS.get(val, {})
    return "; ".join(f"{k}: {v}" for k, v in styles.items())


def render_ranking_table(df: pd.DataFrame):
    display_cols_map = {
        "creative_id": "Creative ID",
        "platform": "Platform",
        "format_concept": "Format / Concept",
        "spend": "Spend ($)",
        "paid_starts": "Paid Starts",
        "trial_starts": "Trial Starts",
        "cpa": "Cost / Paid Start ($)",
        "cpt": "Cost / Trial Start ($)",
        "trial_to_paid_cvr": "Trial→Paid CVR (%)",
        "thumbstop_rate": "Thumbstop Rate (%)",
        "hold_6s": "6s Hold Rate (%)",
        "ctr": "CTR (%)",
        "decision_label": "Decision",
    }

    present = [c for c in display_cols_map if c in df.columns]
    sub = df[present].copy().reset_index(drop=True)
    sub.index = sub.index + 1
    sub.index.name = "Rank"

    # Format display values
    for col in ["spend", "cpa", "cpt"]:
        if col in sub.columns:
            sub[col] = sub[col].apply(lambda v: round(v, 2) if pd.notna(v) else v)
    for col in ["thumbstop_rate", "hold_6s", "ctr", "trial_to_paid_cvr"]:
        if col in sub.columns:
            sub[col] = sub[col].apply(lambda v: round(v, 2) if pd.notna(v) else v)

    sub = sub.rename(columns=display_cols_map)
    display_label = display_cols_map.get("decision_label", "Decision")

    styler = sub.style
    if display_label in sub.columns:
        styler = styler.applymap(_style_decision_cell, subset=[display_label])

    st.markdown(
        "<p style='font-size:0.8rem;color:#8A9BC8;margin-bottom:4px;'>"
        "Click any column header to sort. "
        "<span style='color:#34d399'>■</span> Scale &nbsp;"
        "<span style='color:#fbbf24'>■</span> Keep Testing &nbsp;"
        "<span style='color:#f59e0b'>■</span> Review &nbsp;"
        "<span style='color:#fb923c'>■</span> Fix Funnel &nbsp;"
        "<span style='color:#f87171'>■</span> Cut"
        "</p>",
        unsafe_allow_html=True,
    )
    st.dataframe(styler, use_container_width=True, height=400)


def render_charts(df: pd.DataFrame):
    chart_bg = "#0E1117"
    grid_color = "#1E2A45"
    font_color = "#FAFAFA"

    chart_cols = st.columns(2)

    # 1. CPA bar chart
    with chart_cols[0]:
        st.markdown("<div class='section-header'>Cost per Paid Start by Creative</div>", unsafe_allow_html=True)
        if "cpa" in df.columns and "creative_id" in df.columns:
            d = df[["creative_id", "cpa"]].dropna().sort_values("cpa")
            fig = px.bar(
                d, x="creative_id", y="cpa",
                labels={"creative_id": "Creative", "cpa": "CPA ($)"},
                color="cpa",
                color_continuous_scale=[[0, "#34d399"], [0.5, "#fbbf24"], [1, "#f87171"]],
            )
            fig.add_hline(
                y=CPA_TARGET, line_dash="dash", line_color="#4F8EF7",
                annotation_text=f"${CPA_TARGET} Target", annotation_font_color="#4F8EF7",
            )
            fig.update_layout(
                paper_bgcolor=chart_bg, plot_bgcolor=chart_bg,
                font_color=font_color, showlegend=False,
                coloraxis_showscale=False,
                margin=dict(t=20, b=40, l=50, r=20),
                xaxis=dict(gridcolor=grid_color, tickangle=-30),
                yaxis=dict(gridcolor=grid_color),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need Spend + Paid Starts for this chart.")

    # 2. Paid Starts bar
    with chart_cols[1]:
        st.markdown("<div class='section-header'>Paid Starts by Creative</div>", unsafe_allow_html=True)
        if "paid_starts" in df.columns and "creative_id" in df.columns:
            d = df[["creative_id", "paid_starts", "platform"]].dropna(subset=["paid_starts"]).sort_values("paid_starts", ascending=False)
            color_map = {"Meta": "#4F8EF7", "TikTok": "#34d399", "YouTube Shorts": "#fb923c"}
            fig = px.bar(
                d, x="creative_id", y="paid_starts",
                labels={"creative_id": "Creative", "paid_starts": "Paid Starts"},
                color="platform" if "platform" in d.columns else None,
                color_discrete_map=color_map,
            )
            fig.update_layout(
                paper_bgcolor=chart_bg, plot_bgcolor=chart_bg,
                font_color=font_color, legend_title_text="Platform",
                margin=dict(t=20, b=40, l=50, r=20),
                xaxis=dict(gridcolor=grid_color, tickangle=-30),
                yaxis=dict(gridcolor=grid_color),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need Paid Starts for this chart.")

    chart_cols2 = st.columns(2)

    # 3. Scatter CTR vs CPA
    with chart_cols2[0]:
        st.markdown("<div class='section-header'>CTR vs Cost per Paid Start</div>", unsafe_allow_html=True)
        if "ctr" in df.columns and "cpa" in df.columns:
            d = df[["creative_id", "ctr", "cpa", "spend", "platform", "decision_label"]].dropna(subset=["ctr", "cpa"])
            size_col = d["spend"].fillna(d["spend"].median()) if "spend" in d.columns else None
            color_map = {"Meta": "#4F8EF7", "TikTok": "#34d399", "YouTube Shorts": "#fb923c"}
            fig = px.scatter(
                d, x="cpa", y="ctr",
                size="spend" if size_col is not None else None,
                color="platform" if "platform" in d.columns else None,
                color_discrete_map=color_map,
                text="creative_id",
                labels={"cpa": "CPA ($)", "ctr": "CTR (%)", "spend": "Spend"},
                hover_data=["creative_id", "decision_label"],
            )
            fig.add_vline(
                x=CPA_TARGET, line_dash="dash", line_color="#4F8EF7",
                annotation_text=f"${CPA_TARGET} CPA target", annotation_font_color="#4F8EF7",
            )
            fig.update_traces(textposition="top center", textfont_size=9)
            fig.update_layout(
                paper_bgcolor=chart_bg, plot_bgcolor=chart_bg,
                font_color=font_color, legend_title_text="Platform",
                margin=dict(t=20, b=40, l=50, r=20),
                xaxis=dict(gridcolor=grid_color),
                yaxis=dict(gridcolor=grid_color),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need CTR + Spend + Paid Starts for this chart.")

    # 4. Platform grouped
    with chart_cols2[1]:
        st.markdown("<div class='section-header'>Platform Performance Overview</div>", unsafe_allow_html=True)
        if "platform" in df.columns:
            agg = {}
            if "cpa" in df.columns:
                agg["Avg CPA"] = ("cpa", "mean")
            if "paid_starts" in df.columns:
                agg["Total Paid Starts"] = ("paid_starts", "sum")
            if "ctr" in df.columns:
                agg["Avg CTR"] = ("ctr", "mean")
            if "thumbstop_rate" in df.columns:
                agg["Avg Thumbstop"] = ("thumbstop_rate", "mean")
            if agg:
                plat = df.groupby("platform").agg(**agg).reset_index()
                plat_melt = plat.melt(id_vars="platform", var_name="Metric", value_name="Value")
                fig = px.bar(
                    plat_melt, x="platform", y="Value",
                    color="Metric", barmode="group",
                    labels={"platform": "Platform", "Value": "Value"},
                    color_discrete_sequence=["#4F8EF7", "#34d399", "#fbbf24", "#fb923c"],
                )
                fig.update_layout(
                    paper_bgcolor=chart_bg, plot_bgcolor=chart_bg,
                    font_color=font_color, legend_title_text="Metric",
                    margin=dict(t=20, b=40, l=50, r=20),
                    xaxis=dict(gridcolor=grid_color),
                    yaxis=dict(gridcolor=grid_color),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Need Platform + at least one metric for this chart.")
        else:
            st.info("No Platform column found.")


def render_patterns(df: pd.DataFrame):
    insights = []

    if "platform" in df.columns and "cpa" in df.columns:
        plat_cpa = df.groupby("platform")["cpa"].mean().dropna()
        if not plat_cpa.empty:
            best = plat_cpa.idxmin()
            worst = plat_cpa.idxmax()
            insights.append(f"<b>{best}</b> has the lowest avg CPA at <b>{fmt_currency(plat_cpa[best])}</b> — best platform for efficient paid starts.")
            if best != worst:
                insights.append(f"<b>{worst}</b> has the highest avg CPA at <b>{fmt_currency(plat_cpa[worst])}</b> — review spend allocation.")

    if "platform" in df.columns and "paid_starts" in df.columns:
        plat_paid = df.groupby("platform")["paid_starts"].sum().dropna()
        if not plat_paid.empty:
            best = plat_paid.idxmax()
            insights.append(f"<b>{best}</b> drives the most paid starts in total (<b>{fmt_num(plat_paid[best])}</b>).")

    if "format_concept" in df.columns and "cpa" in df.columns:
        concept_cpa = df.groupby("format_concept")["cpa"].mean().dropna()
        if not concept_cpa.empty:
            best_concept = concept_cpa.idxmin()
            short = best_concept[:60] + "…" if len(best_concept) > 60 else best_concept
            insights.append(f"Best concept by CPA: <b>\"{short}\"</b> at <b>{fmt_currency(concept_cpa[best_concept])}</b>.")

    if "platform" in df.columns and "cpa" in df.columns:
        plat_cpa = df.groupby("platform")["cpa"].mean().dropna()
        rows = " | ".join(f"{p}: {fmt_currency(v)}" for p, v in plat_cpa.items())
        insights.append(f"Average CPA by platform — {rows}")

    if "length_s" in df.columns and "cpa" in df.columns:
        d = df.dropna(subset=["length_s", "cpa"]).copy()
        d["bucket"] = d["length_s"].apply(length_bucket)
        bucket_cpa = d.groupby("bucket")["cpa"].mean().dropna()
        ORDER = ["Under 20s", "20–30s", "31–40s", "Over 40s"]
        bucket_cpa = bucket_cpa.reindex([b for b in ORDER if b in bucket_cpa.index])
        if not bucket_cpa.empty:
            rows = " | ".join(f"{b}: {fmt_currency(v)}" for b, v in bucket_cpa.items())
            best_b = bucket_cpa.idxmin()
            insights.append(f"Average CPA by length bucket — {rows}")
            insights.append(f"<b>{best_b}</b> creatives have the lowest average CPA.")

    if insights:
        for ins in insights:
            st.markdown(f"<div class='insight-box'>{ins}</div>", unsafe_allow_html=True)
    else:
        st.info("Upload data with Platform, Spend, and Paid Starts to see pattern analysis.")


def render_recommendations(df: pd.DataFrame):
    recs = []

    if "platform" in df.columns and "thumbstop_rate" in df.columns and "cpa" in df.columns:
        plat = df.groupby("platform").agg(
            thumbstop=("thumbstop_rate", "mean"),
            cpa=("cpa", "mean"),
            paid=("paid_starts", "sum") if "paid_starts" in df.columns else ("cpa", "count"),
        ).dropna()

        has_tiktok = "TikTok" in plat.index
        has_meta = "Meta" in plat.index

        if has_tiktok and has_meta:
            if plat.loc["TikTok", "thumbstop"] > plat.loc["Meta", "thumbstop"] and plat.loc["TikTok", "cpa"] > plat.loc["Meta", "cpa"]:
                recs.append("TikTok hooks are stopping scrolls but not converting. Test stronger product proof, clearer CTA, or a harder offer in the last 5 seconds of TikTok creatives.")
            if plat.loc["Meta", "thumbstop"] < plat.loc["TikTok", "thumbstop"] and plat.loc["Meta", "cpa"] < plat.loc["TikTok", "cpa"]:
                recs.append("Meta converts better despite lower thumbstop. Test more scroll-stopping hooks on Meta while keeping the same proven offer and CTA structure.")

    if "ctr" in df.columns and "cpa" in df.columns:
        median_ctr = df["ctr"].median()
        median_cpa = df["cpa"].median()
        high_ctr_high_cpa = df[(df["ctr"] > median_ctr) & (df["cpa"] > median_cpa)]
        if not high_ctr_high_cpa.empty:
            ids = ", ".join(high_ctr_high_cpa["creative_id"].astype(str).tolist())
            recs.append(f"Creatives <b>{ids}</b> have strong CTR but high CPA — the drop-off is likely in the landing page or trial-to-paid flow. Test a more direct offer page or reduce friction in the trial sign-up.")

    if "thumbstop_rate" in df.columns and "ctr" in df.columns:
        median_thumb = df["thumbstop_rate"].median()
        median_ctr = df["ctr"].median()
        high_thumb_low_ctr = df[(df["thumbstop_rate"] > median_thumb) & (df["ctr"] < median_ctr)]
        if not high_thumb_low_ctr.empty:
            ids = ", ".join(high_thumb_low_ctr["creative_id"].astype(str).tolist())
            recs.append(f"Creatives <b>{ids}</b> stop the scroll but don't earn the click. Test a clearer, more specific value proposition in the first 3 seconds — viewers are hooked but not yet convinced.")

    if "format_concept" in df.columns and "cpa" in df.columns:
        concept_cpa = df.groupby("format_concept")["cpa"].mean().dropna()
        if not concept_cpa.empty and len(concept_cpa) > 1:
            best_concept = concept_cpa.idxmin()
            short = best_concept[:60] + "…" if len(best_concept) > 60 else best_concept
            pct_better = ((concept_cpa.mean() - concept_cpa.min()) / concept_cpa.mean() * 100)
            recs.append(f"Concept \"{short}\" has the lowest CPA — <b>{pct_better:.0f}% below average</b>. Remix this format across other platforms and creative lengths to expand its reach.")

    if "platform" in df.columns and "cpa" in df.columns:
        plat_cpa = df.groupby("platform")["cpa"].mean().dropna()
        if len(plat_cpa) > 1:
            worst_plat = plat_cpa.idxmax()
            best_plat = plat_cpa.idxmin()
            recs.append(f"Consider shifting budget from <b>{worst_plat}</b> (avg CPA {fmt_currency(plat_cpa[worst_plat])}) toward <b>{best_plat}</b> (avg CPA {fmt_currency(plat_cpa[best_plat])}) until {worst_plat} creative improves.")

    if recs:
        for rec in recs:
            st.markdown(f"<div class='rec-box'>💡 {rec}</div>", unsafe_allow_html=True)
    else:
        st.info("Upload data to generate test recommendations.")


# ══════════════════════════════════════════════════════════════════════════════
# APP LAYOUT
# ══════════════════════════════════════════════════════════════════════════════

# ── Initialise session state ─────────────────────────────────────────────────
if "df_raw" not in st.session_state:
    st.session_state.df_raw = None

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:0.2rem;">
      <span style="font-size:2rem;">📊</span>
      <span style="font-size:1.7rem;font-weight:800;letter-spacing:-0.02em;">Creative Performance Analyzer</span>
    </div>
    <p style="color:#8A9BC8;margin-top:0;margin-bottom:1rem;font-size:0.95rem;">
      Upload your ad creative data · Choose a campaign goal · Review rankings · Read recommendations
    </p>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ── Upload / sample data row ─────────────────────────────────────────────────
upload_col, sample_col = st.columns([3, 1])

with upload_col:
    uploaded_file = st.file_uploader(
        "Upload CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        help="Columns like Creative ID, Platform, Spend, Thumbstop Rate, CTR, Trial Starts, Paid Starts",
    )

with sample_col:
    st.write("")
    st.write("")
    if st.button("📂  Use sample LoopNote data", use_container_width=True):
        df_raw, warns = load_and_clean(SAMPLE_CSV)
        st.session_state.df_raw = df_raw
        st.session_state.warnings = warns

if uploaded_file is not None:
    try:
        df_raw, warns = load_and_clean(uploaded_file)
        st.session_state.df_raw = df_raw
        st.session_state.warnings = warns
    except Exception as e:
        st.error(f"Could not read file: {e}")

# ── Analysis ─────────────────────────────────────────────────────────────────
if st.session_state.df_raw is not None:
    df_raw = st.session_state.df_raw

    # Show any data-loading warnings
    for w in st.session_state.get("warnings", []):
        st.warning(w)

    # Calculate KPIs
    df, kpi_warnings = calculate_kpis(df_raw)

    # Assign decision labels (needs KPIs)
    df = assign_decision_labels(df)

    # ── Goal selector ────────────────────────────────────────────────────────
    goal_options = [
        "Paid Starts",
        "Trial Starts",
        "Efficient Paid Starts",
        "Efficient Trial Starts",
        "Creative Engagement",
        "Full Funnel Quality",
    ]
    goal_col, spacer = st.columns([2, 5])
    with goal_col:
        goal = st.selectbox("Campaign Goal", goal_options, index=0)

    # Rank
    df_ranked = rank_by_goal(df, goal)
    df_ranked = assign_decision_labels(df_ranked)

    st.divider()

    # ── Summary cards ────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Performance Summary</div>", unsafe_allow_html=True)
    render_summary_cards(df_ranked, goal)

    if kpi_warnings:
        with st.expander("⚠️  Some KPIs could not be calculated — expand for details"):
            for w in kpi_warnings:
                st.caption(f"• {w}")

    st.divider()

    # ── Scale candidates callout (Efficient Paid Starts) ─────────────────────
    if goal == "Efficient Paid Starts" and "scale_candidate" in df_ranked.columns:
        candidates = df_ranked[df_ranked["scale_candidate"] == True]["creative_id"].tolist()
        if candidates:
            st.success(f"🚀  **Scale Candidates** (CPA < ${CPA_TARGET}): {', '.join(str(c) for c in candidates)}")

    # ── Ranking table ────────────────────────────────────────────────────────
    st.markdown(f"<div class='section-header'>Creative Rankings — {goal}</div>", unsafe_allow_html=True)
    render_ranking_table(df_ranked)

    st.divider()

    # ── Charts ───────────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Visuals</div>", unsafe_allow_html=True)
    render_charts(df_ranked)

    st.divider()

    # ── Pattern analysis ─────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>What patterns are emerging?</div>", unsafe_allow_html=True)
    render_patterns(df_ranked)

    st.divider()

    # ── Test recommendations ─────────────────────────────────────────────────
    st.markdown("<div class='section-header'>What should we test next?</div>", unsafe_allow_html=True)
    render_recommendations(df_ranked)

else:
    # ── Welcome state ─────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="background:#161B27;border:1px solid #2A3350;border-radius:12px;
                    padding:32px 40px;max-width:700px;margin:24px auto 0;">
          <h3 style="margin-top:0;color:#FAFAFA;">How it works</h3>
          <div style="display:grid;grid-template-columns:40px 1fr;gap:8px 12px;align-items:start;font-size:0.95rem;color:#C5CFDF;">
            <span style="color:#4F8EF7;font-weight:700;font-size:1.1rem;">1</span>
            <span><b>Upload data</b> — CSV or Excel with your ad creative metrics, or use the built-in LoopNote sample.</span>
            <span style="color:#4F8EF7;font-weight:700;font-size:1.1rem;">2</span>
            <span><b>Choose a campaign goal</b> — Paid Starts, Trial Starts, Engagement, or Full Funnel Quality.</span>
            <span style="color:#4F8EF7;font-weight:700;font-size:1.1rem;">3</span>
            <span><b>Review rankings</b> — Creatives are scored and labelled: Scale, Keep Testing, Fix Funnel, Cut, or Review.</span>
            <span style="color:#4F8EF7;font-weight:700;font-size:1.1rem;">4</span>
            <span><b>Read recommendations</b> — Rule-based insights tell you exactly what to test next.</span>
          </div>
          <p style="margin-bottom:0;margin-top:20px;color:#8A9BC8;font-size:0.88rem;">
            Supported columns: Creative ID · Platform · Format/Concept · Length · Spend · Thumbstop Rate ·
            6s Hold Rate · CTR · Trial Starts · Paid Starts
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("**AI / tools used**")
st.text_area(
    label="",
    value=(
        "AI was used to help structure the app logic, ranking methodology, and rule-based recommendation system. "
        "The final tool is a lightweight prototype built for fast creative decision-making, not a production analytics platform."
    ),
    height=80,
    label_visibility="collapsed",
)
