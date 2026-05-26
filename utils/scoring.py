import math
import numpy as np
import pandas as pd

CPA_TARGET = 90.0
CE_WEIGHTS_DEFAULT = {"thumbstop_rate": 40, "hold_6s": 30, "ctr": 30}
FFQ_WEIGHTS_DEFAULT = {"cpa": 30, "paid_starts": 25, "trial_to_paid_cvr": 20, "ctr": 15, "thumbstop_rate": 10}


def _min_max(s: pd.Series, lower_is_better: bool = False) -> pd.Series:
    mn, mx = s.min(), s.max()
    if mx == mn:
        return pd.Series(0.5, index=s.index)
    norm = (s - mn) / (mx - mn)
    return (1 - norm) if lower_is_better else norm


def rank_by_goal(
    df: pd.DataFrame,
    goal: str,
    cpa_target: float = CPA_TARGET,
    ce_weights: dict | None = None,
    ffq_weights: dict | None = None,
) -> pd.DataFrame:
    if ce_weights is None:
        ce_weights = CE_WEIGHTS_DEFAULT
    if ffq_weights is None:
        ffq_weights = FFQ_WEIGHTS_DEFAULT

    d = df.copy()

    if goal == "Paid Starts":
        if "paid_starts" in d.columns:
            d = d.sort_values("paid_starts", ascending=False)

    elif goal == "Trial Starts":
        if "trial_starts" in d.columns:
            d = d.sort_values("trial_starts", ascending=False)

    elif goal == "Efficient Paid Starts":
        if "cpa" in d.columns:
            d = d.sort_values(["cpa", "paid_starts"], ascending=[True, False], na_position="last")
            d["scale_candidate"] = d["cpa"] < cpa_target

    elif goal == "Efficient Trial Starts":
        if "cpt" in d.columns:
            d = d.sort_values(["cpt", "trial_starts"], ascending=[True, False], na_position="last")

    elif goal == "Creative Engagement":
        ce_col_order = ["thumbstop_rate", "hold_6s", "ctr"]
        cols, weights = [], []
        for col in ce_col_order:
            if col in d.columns and col in ce_weights:
                cols.append(col)
                weights.append(ce_weights[col] / 100.0)
        if cols:
            total_w = sum(weights)
            score = sum(_min_max(d[c]) * w for c, w in zip(cols, weights))
            d["goal_score"] = score / total_w if total_w > 0 else 0
            d = d.sort_values("goal_score", ascending=False)

    elif goal == "Full Funnel Quality":
        ffq_col_order = [
            ("cpa", True), ("paid_starts", False), ("trial_to_paid_cvr", False),
            ("ctr", False), ("thumbstop_rate", False),
        ]
        components = [
            (c, ffq_weights.get(c, 0) / 100.0, inv)
            for c, inv in ffq_col_order
            if c in d.columns and ffq_weights.get(c, 0) > 0
        ]
        total_w = sum(w for _, w, _ in components)
        if total_w > 0:
            d["goal_score"] = sum(_min_max(d[c], inv) * w for c, w, inv in components) / total_w
            d = d.sort_values("goal_score", ascending=False)

    d = d.reset_index(drop=True)
    d.index = d.index + 1
    return d


def assign_decision_labels(df: pd.DataFrame, cpa_target: float = CPA_TARGET) -> pd.DataFrame:
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
            if cpa < cpa_target and paid > median_paid:
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
            if cpa > cpa_target and thumbstop < median_thumbstop:
                labels.append("Cut")
                continue
        labels.append("Review")

    d["decision_label"] = labels
    return d


def detect_fatigue_ids(df: pd.DataFrame) -> set:
    from utils.data_processing import detect_date_col
    date_col = detect_date_col(df)
    if date_col is None or "creative_id" not in df.columns:
        return set()
    fatigue = set()
    for cid, sub in df.groupby("creative_id"):
        sub = sub.sort_values(date_col)
        if "cpa" in sub.columns:
            vals = sub["cpa"].dropna().tolist()
            if len(vals) >= 2 and all(vals[i] < vals[i + 1] for i in range(len(vals) - 1)):
                fatigue.add(cid)
        if "ctr" in sub.columns:
            vals = sub["ctr"].dropna().tolist()
            if len(vals) >= 2 and all(vals[i] > vals[i + 1] for i in range(len(vals) - 1)):
                fatigue.add(cid)
    return fatigue


def compute_significance(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "trial_starts" not in df.columns or "paid_starts" not in df.columns:
        return df
    total_trials = df["trial_starts"].sum(skipna=True)
    total_paid = df["paid_starts"].sum(skipna=True)
    labels = []
    for _, row in df.iterrows():
        n1 = row.get("trial_starts", 0)
        x1 = row.get("paid_starts", 0)
        if pd.isna(n1) or pd.isna(x1) or n1 <= 0:
            labels.append("-")
            continue
        n2 = total_trials - n1
        x2 = total_paid - x1
        if n2 <= 0 or (x1 + x2) <= 0:
            labels.append("-")
            continue
        p_pool = (x1 + x2) / (n1 + n2)
        denom = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2)) if p_pool not in (0, 1) else 0
        if denom == 0:
            labels.append("-")
            continue
        z = abs((x1 / n1) - (x2 / n2)) / denom
        if z > 2.576:
            labels.append("99% sig.")
        elif z > 1.96:
            labels.append("95% sig.")
        elif z > 1.645:
            labels.append("~90% sig.")
        else:
            labels.append("Not sig.")
    df["stat_sig"] = labels
    return df
