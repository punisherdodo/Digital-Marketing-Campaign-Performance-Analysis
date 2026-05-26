import datetime
import numpy as np
import pandas as pd
from utils.data_processing import fmt_currency, fmt_num, length_bucket


def get_patterns_text(df: pd.DataFrame) -> list[str]:
    items = []

    if "platform" in df.columns and "cpa" in df.columns:
        plat_cpa = df.groupby("platform")["cpa"].mean().dropna()
        if not plat_cpa.empty:
            best = plat_cpa.idxmin()
            worst = plat_cpa.idxmax()
            items.append(
                f"{best} has the lowest avg CPA at {fmt_currency(plat_cpa[best])} "
                f"- best platform for efficient paid starts."
            )
            if best != worst:
                items.append(
                    f"{worst} has the highest avg CPA at {fmt_currency(plat_cpa[worst])} "
                    f"- review spend allocation."
                )

    if "platform" in df.columns and "paid_starts" in df.columns:
        plat_paid = df.groupby("platform")["paid_starts"].sum().dropna()
        if not plat_paid.empty:
            best = plat_paid.idxmax()
            items.append(f"{best} drives the most paid starts in total ({fmt_num(plat_paid[best])}).")

    if "format_concept" in df.columns and "cpa" in df.columns:
        concept_cpa = df.groupby("format_concept")["cpa"].mean().dropna()
        if not concept_cpa.empty:
            best_c = concept_cpa.idxmin()
            short = best_c[:60] + "..." if len(best_c) > 60 else best_c
            items.append(f'Best concept by CPA: "{short}" at {fmt_currency(concept_cpa[best_c])}.')

    if "platform" in df.columns and "cpa" in df.columns:
        plat_cpa = df.groupby("platform")["cpa"].mean().dropna()
        rows = " | ".join(f"{p}: {fmt_currency(v)}" for p, v in plat_cpa.items())
        items.append(f"Average CPA by platform - {rows}")

    if "length_s" in df.columns and "cpa" in df.columns:
        d = df.dropna(subset=["length_s", "cpa"]).copy()
        d["bucket"] = d["length_s"].apply(length_bucket)
        bucket_cpa = d.groupby("bucket")["cpa"].mean().dropna()
        ORDER = ["Under 20s", "20-30s", "31-40s", "Over 40s"]
        bucket_cpa = bucket_cpa.reindex([b for b in ORDER if b in bucket_cpa.index])
        if not bucket_cpa.empty:
            rows = " | ".join(f"{b}: {fmt_currency(v)}" for b, v in bucket_cpa.items())
            items.append(f"Average CPA by length - {rows}")
            items.append(f"{bucket_cpa.idxmin()} creatives have the lowest average CPA.")

    return items


def get_recommendations_text(df: pd.DataFrame) -> list[str]:
    recs = []

    if "platform" in df.columns and "thumbstop_rate" in df.columns and "cpa" in df.columns:
        plat = df.groupby("platform").agg(
            thumbstop=("thumbstop_rate", "mean"),
            cpa=("cpa", "mean"),
        ).dropna()
        has_tiktok = "TikTok" in plat.index
        has_meta = "Meta" in plat.index
        if has_tiktok and has_meta:
            if plat.loc["TikTok", "thumbstop"] > plat.loc["Meta", "thumbstop"] and plat.loc["TikTok", "cpa"] > plat.loc["Meta", "cpa"]:
                recs.append(
                    "TikTok hooks are stopping scrolls but not converting. Test stronger product proof, "
                    "clearer CTA, or a harder offer in the last 5 seconds."
                )
            if plat.loc["Meta", "thumbstop"] < plat.loc["TikTok", "thumbstop"] and plat.loc["Meta", "cpa"] < plat.loc["TikTok", "cpa"]:
                recs.append(
                    "Meta converts better despite lower thumbstop. Test more scroll-stopping hooks on Meta "
                    "while keeping the same proven offer."
                )

    if "ctr" in df.columns and "cpa" in df.columns:
        med_ctr = df["ctr"].median()
        med_cpa = df["cpa"].median()
        hchp = df[(df["ctr"] > med_ctr) & (df["cpa"] > med_cpa)]
        if not hchp.empty:
            ids = ", ".join(hchp["creative_id"].astype(str).tolist())
            recs.append(
                f"Creatives {ids} have strong CTR but high CPA - the drop-off is likely in the landing page "
                "or trial-to-paid flow. Test a more direct offer page or reduce friction in the trial sign-up."
            )

    if "thumbstop_rate" in df.columns and "ctr" in df.columns:
        med_t = df["thumbstop_rate"].median()
        med_c = df["ctr"].median()
        htlc = df[(df["thumbstop_rate"] > med_t) & (df["ctr"] < med_c)]
        if not htlc.empty:
            ids = ", ".join(htlc["creative_id"].astype(str).tolist())
            recs.append(
                f"Creatives {ids} stop the scroll but don't earn the click. "
                "Test a clearer value proposition in the first 3 seconds."
            )

    if "format_concept" in df.columns and "cpa" in df.columns:
        concept_cpa = df.groupby("format_concept")["cpa"].mean().dropna()
        if not concept_cpa.empty and len(concept_cpa) > 1:
            best_c = concept_cpa.idxmin()
            short = best_c[:60] + "..." if len(best_c) > 60 else best_c
            pct = (concept_cpa.mean() - concept_cpa.min()) / concept_cpa.mean() * 100
            recs.append(
                f'Concept "{short}" has the lowest CPA - {pct:.0f}% below average. '
                "Remix this format across other platforms."
            )

    if "platform" in df.columns and "cpa" in df.columns:
        plat_cpa = df.groupby("platform")["cpa"].mean().dropna()
        if len(plat_cpa) > 1:
            worst = plat_cpa.idxmax()
            best = plat_cpa.idxmin()
            recs.append(
                f"Consider shifting budget from {worst} (avg CPA {fmt_currency(plat_cpa[worst])}) "
                f"toward {best} (avg CPA {fmt_currency(plat_cpa[best])})."
            )

    return recs


def build_summary_snippet(df: pd.DataFrame, goal: str, cpa_target: float) -> str:
    lines = [
        f"Creative Performance Summary - {datetime.date.today().strftime('%B %d, %Y')}",
        f"Goal: {goal}  |  CPA Target: ${cpa_target:,.0f}",
        "",
    ]
    if not df.empty and "creative_id" in df.columns:
        top = df.iloc[0]
        lines.append(f"Top creative: {top['creative_id']}")
        if "cpa" in df.columns and pd.notna(top.get("cpa")):
            lines.append(f"  - CPA: ${top['cpa']:,.2f}")
        if "paid_starts" in df.columns and pd.notna(top.get("paid_starts")):
            lines.append(f"  - Paid Starts: {int(top['paid_starts']):,}")
        if "decision_label" in df.columns:
            lines.append(f"  - Action: {top.get('decision_label', '')}")
        lines.append("")
    if "decision_label" in df.columns:
        for label in ["Scale", "Keep Testing", "Fix Funnel", "Cut"]:
            ids = df[df["decision_label"] == label]["creative_id"].tolist()
            if ids:
                lines.append(f"{label}: {', '.join(str(c) for c in ids)}")
        lines.append("")
    if "spend" in df.columns:
        lines.append(f"Total Spend: ${df['spend'].sum(skipna=True):,.0f}")
    if "paid_starts" in df.columns:
        total_paid = df["paid_starts"].sum(skipna=True)
        lines.append(f"Total Paid Starts: {int(total_paid):,}")
        if "spend" in df.columns and total_paid > 0:
            lines.append(f"Blended CPA: ${df['spend'].sum(skipna=True) / total_paid:,.2f}")
    lines += ["", "Generated by Creative Performance Analyzer"]
    return "\n".join(lines)
