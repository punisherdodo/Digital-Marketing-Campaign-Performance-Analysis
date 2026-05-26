import io
import pytest
import numpy as np
import pandas as pd

from utils.exports import build_export_csv


def _ranked_df():
    return pd.DataFrame({
        "creative_id": ["C01", "C02", "C03"],
        "platform": ["Meta", "TikTok", "Meta"],
        "format_concept": ["UGC", "Skit", "Demo"],
        "spend": [4800.0, 3200.0, 2700.0],
        "paid_starts": [60.0, 40.0, 10.0],
        "trial_starts": [200.0, 150.0, 50.0],
        "cpa": [80.0, 80.0, 270.0],
        "cpt": [24.0, 21.3, 54.0],
        "trial_to_paid_cvr": [0.30, 0.27, 0.20],
        "paid_per_1k": [12.5, 12.5, 3.7],
        "trial_per_1k": [41.7, 46.9, 18.5],
        "thumbstop_rate": [36.0, 25.0, 18.0],
        "hold_6s": [24.0, np.nan, 11.0],
        "ctr": [1.7, 0.9, 0.6],
        "goal_score": [0.85, 0.60, 0.20],
        "decision_label": ["Scale", "Review", "Cut"],
    })


class TestBuildExportCsv:
    def test_returns_bytes(self):
        result = build_export_csv(_ranked_df())
        assert isinstance(result, bytes)

    def test_is_valid_csv(self):
        result = build_export_csv(_ranked_df())
        df = pd.read_csv(io.BytesIO(result), index_col=0)
        assert isinstance(df, pd.DataFrame)

    def test_rank_index_in_output(self):
        result = build_export_csv(_ranked_df())
        df = pd.read_csv(io.BytesIO(result), index_col=0)
        assert df.index.name == "Rank"
        assert df.index[0] == 1

    def test_column_labels_are_human_readable(self):
        result = build_export_csv(_ranked_df())
        df = pd.read_csv(io.BytesIO(result), index_col=0)
        assert "Creative ID" in df.columns
        assert "Spend ($)" in df.columns
        assert "Cost / Paid Start ($)" in df.columns
        assert "Decision" in df.columns

    def test_row_count_matches_input(self):
        result = build_export_csv(_ranked_df())
        df = pd.read_csv(io.BytesIO(result), index_col=0)
        assert len(df) == 3

    def test_numeric_columns_are_rounded(self):
        result = build_export_csv(_ranked_df())
        df = pd.read_csv(io.BytesIO(result), index_col=0)
        spend_val = df["Spend ($)"].iloc[0]
        assert spend_val == pytest.approx(4800.0, abs=0.01)

    def test_only_known_columns_included(self):
        df_in = _ranked_df()
        df_in["unexpected_extra_col"] = 999
        result = build_export_csv(df_in)
        df_out = pd.read_csv(io.BytesIO(result), index_col=0)
        assert "unexpected_extra_col" not in df_out.columns

    def test_missing_optional_columns_omitted_gracefully(self):
        df_in = _ranked_df().drop(columns=["goal_score", "hold_6s", "cpt"])
        result = build_export_csv(df_in)
        df_out = pd.read_csv(io.BytesIO(result), index_col=0)
        assert "Goal Score" not in df_out.columns
        assert "6s Hold Rate (%)" not in df_out.columns
        assert "Cost / Trial Start ($)" not in df_out.columns

    def test_nan_values_preserved_as_empty(self):
        result = build_export_csv(_ranked_df())
        df_out = pd.read_csv(io.BytesIO(result), index_col=0)
        assert pd.isna(df_out["6s Hold Rate (%)"].iloc[1])

    def test_single_row_dataframe(self):
        result = build_export_csv(_ranked_df().head(1))
        df_out = pd.read_csv(io.BytesIO(result), index_col=0)
        assert len(df_out) == 1

    def test_decision_label_preserved(self):
        result = build_export_csv(_ranked_df())
        df_out = pd.read_csv(io.BytesIO(result), index_col=0)
        assert df_out["Decision"].iloc[0] == "Scale"
        assert df_out["Decision"].iloc[2] == "Cut"
