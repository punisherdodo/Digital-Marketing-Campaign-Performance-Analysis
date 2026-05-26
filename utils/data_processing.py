import re
import json
import os
import datetime
import numpy as np
import pandas as pd
from io import StringIO

SAVES_PATH = "saved_analyses.json"

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

_DATE_COL_NAMES = {"date", "week", "period", "month", "week_num", "day", "period_label", "run_date"}

_EXPECTED_COLS = {
    "creative_id": "Creative ID",
    "platform": "Platform",
    "spend": "Spend ($)",
    "paid_starts": "Paid Starts",
    "trial_starts": "Trial Starts",
    "ctr": "CTR (%)",
    "thumbstop_rate": "Thumbstop Rate (%)",
    "hold_6s": "6s Hold Rate (%)",
}


def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for col in df.columns:
        key = col.strip().lower()
        if key in COLUMN_MAP:
            rename[col] = COLUMN_MAP[key]
    return df.rename(columns=rename)


def clean_numeric(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace(r"[$,]", "", regex=True)
        .str.strip()
        .replace({"N/A": np.nan, "n/a": np.nan, "NA": np.nan, "-": np.nan, "": np.nan})
    )
    return pd.to_numeric(cleaned, errors="coerce")


def clean_percent(series: pd.Series) -> pd.Series:
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
                result.append(val * 100 if 0 < val <= 1 else val)
        except (ValueError, TypeError):
            result.append(np.nan)
    return pd.Series(result, index=series.index)


def extract_seconds(series: pd.Series) -> pd.Series:
    def parse(v):
        if pd.isna(v):
            return np.nan
        v = str(v).strip().lower().replace("s", "").replace("sec", "").strip()
        try:
            return float(v)
        except ValueError:
            return np.nan
    return series.apply(parse)


def load_and_clean(source) -> tuple[pd.DataFrame, list[str]]:
    """Load CSV/Excel/string/file-path, normalise columns, clean types. Returns (df, warnings)."""
    warnings = []
    if isinstance(source, str):
        if os.path.exists(source):
            if source.endswith((".xlsx", ".xls")):
                df = pd.read_excel(source)
            else:
                df = pd.read_csv(source)
        else:
            df = pd.read_csv(StringIO(source))
    elif hasattr(source, "name") and source.name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(source)
    else:
        try:
            df = pd.read_csv(source)
        except Exception:
            df = pd.read_excel(source)

    df = normalise_columns(df)

    if "creative_id" not in df.columns:
        df.insert(0, "creative_id", [f"C{i+1:02d}" for i in range(len(df))])
        warnings.append("No 'Creative ID' column found — auto-generated IDs assigned.")

    if "spend" in df.columns:
        df["spend"] = clean_numeric(df["spend"])

    for col in ["thumbstop_rate", "hold_6s", "ctr"]:
        if col in df.columns:
            df[col] = clean_percent(df[col])

    for col in ["trial_starts", "paid_starts"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "length" in df.columns:
        df["length_s"] = extract_seconds(df["length"])

    return df, warnings


def calculate_kpis(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Add KPI columns where source data exists. Returns (df, missing_warnings)."""
    missing = []

    def safe_div(num, den):
        return pd.Series(np.where(den != 0, num / den, np.nan), index=df.index)

    def has(c):
        return c in df.columns and df[c].notna().any()

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
        missing.append("Trial->Paid CVR (needs Paid Starts + Trial Starts)")

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


def detect_date_col(df: pd.DataFrame) -> str | None:
    for c in df.columns:
        if c.lower() in _DATE_COL_NAMES:
            return c
    return None


def fmt_currency(v):
    if pd.isna(v):
        return "-"
    return f"${v:,.0f}"


def fmt_pct(v):
    if pd.isna(v):
        return "-"
    return f"{v:.1f}%"


def fmt_num(v):
    if pd.isna(v):
        return "-"
    return f"{v:,.0f}"


def fmt_float(v, decimals=2):
    if pd.isna(v):
        return "-"
    return f"{v:,.{decimals}f}"


def length_bucket(s: float) -> str:
    if np.isnan(s):
        return "Unknown"
    if s < 20:
        return "Under 20s"
    elif s <= 30:
        return "20-30s"
    elif s <= 40:
        return "31-40s"
    else:
        return "Over 40s"


def _load_saves_file() -> list[dict]:
    if not os.path.exists(SAVES_PATH):
        return []
    try:
        with open(SAVES_PATH, "r") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _write_saves_file(saves: list[dict]) -> None:
    with open(SAVES_PATH, "w") as f:
        json.dump(saves, f, indent=2)


def list_saves() -> list[dict]:
    saves = _load_saves_file()
    return sorted(saves, key=lambda s: s.get("saved_at", ""), reverse=True)


def save_analysis(name: str, df_raw: pd.DataFrame, goal: str, cpa_target: float) -> None:
    saves = _load_saves_file()
    saves.append({
        "id": datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f"),
        "name": name.strip() or "Untitled",
        "saved_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "csv_data": df_raw.to_csv(index=False),
        "goal": goal,
        "cpa_target": cpa_target,
    })
    _write_saves_file(saves)


def delete_save(save_id: str) -> None:
    saves = _load_saves_file()
    _write_saves_file([s for s in saves if s.get("id") != save_id])


def load_save(save_id: str) -> dict | None:
    for s in _load_saves_file():
        if s.get("id") == save_id:
            return s
    return None
