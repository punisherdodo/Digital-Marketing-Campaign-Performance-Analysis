import io
import pytest
import numpy as np
import pandas as pd

from utils.data_processing import load_and_clean, calculate_kpis


VALID_CSV = """\
Creative ID,Platform,Spend,Thumbstop Rate,6s Hold Rate,CTR,Trial Starts,Paid Starts
C01,Meta,4800,36%,24%,1.7%,267,59
C02,Meta,3200,25%,N/A,0.9%,133,35
C03,TikTok,2700,18%,11%,0.6%,54,12
"""

MINIMAL_CSV = """\
Platform,Spend
Meta,1000
TikTok,2000
"""


class TestLoadAndClean:
    def test_valid_csv_string_returns_dataframe(self):
        df, warnings = load_and_clean(VALID_CSV)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3

    def test_valid_csv_columns_are_normalised(self):
        df, _ = load_and_clean(VALID_CSV)
        assert "creative_id" in df.columns
        assert "spend" in df.columns
        assert "thumbstop_rate" in df.columns
        assert "hold_6s" in df.columns
        assert "ctr" in df.columns
        assert "trial_starts" in df.columns
        assert "paid_starts" in df.columns

    def test_spend_is_numeric(self):
        df, _ = load_and_clean(VALID_CSV)
        assert pd.api.types.is_float_dtype(df["spend"]) or pd.api.types.is_integer_dtype(df["spend"])
        assert df["spend"].iloc[0] == pytest.approx(4800.0)

    def test_percent_columns_parsed_correctly(self):
        df, _ = load_and_clean(VALID_CSV)
        assert df["thumbstop_rate"].iloc[0] == pytest.approx(36.0)
        assert df["ctr"].iloc[0] == pytest.approx(1.7)

    def test_na_value_becomes_nan(self):
        df, _ = load_and_clean(VALID_CSV)
        assert pd.isna(df["hold_6s"].iloc[1])

    def test_missing_creative_id_auto_generates(self):
        df, warnings = load_and_clean(MINIMAL_CSV)
        assert "creative_id" in df.columns
        assert any("auto-generated" in w for w in warnings)
        assert df["creative_id"].iloc[0] == "C01"

    def test_file_path_loads_sample_csv(self):
        df, warnings = load_and_clean("sample_data/sample_creative_performance.csv")
        assert len(df) == 20
        assert "creative_id" in df.columns

    def test_file_object_csv(self):
        buf = io.BytesIO(VALID_CSV.encode("utf-8"))
        buf.name = "test.csv"
        df, _ = load_and_clean(buf)
        assert len(df) == 3

    def test_dollar_sign_in_spend_is_stripped(self):
        csv = 'Creative ID,Spend\nC01,"$1,500"\nC02,$800\n'
        df, _ = load_and_clean(csv)
        assert df["spend"].iloc[0] == pytest.approx(1500.0)
        assert df["spend"].iloc[1] == pytest.approx(800.0)

    def test_percent_as_decimal_is_converted(self):
        csv = "Creative ID,Thumbstop Rate,CTR\nC01,0.36,0.017\n"
        df, _ = load_and_clean(csv)
        assert df["thumbstop_rate"].iloc[0] == pytest.approx(36.0)
        assert df["ctr"].iloc[0] == pytest.approx(1.7)

    def test_length_column_is_parsed_to_seconds(self):
        csv = "Creative ID,Length\nC01,28s\nC02,35\n"
        df, _ = load_and_clean(csv)
        assert "length_s" in df.columns
        assert df["length_s"].iloc[0] == pytest.approx(28.0)
        assert df["length_s"].iloc[1] == pytest.approx(35.0)

    def test_empty_csv_returns_empty_dataframe(self):
        csv = "Creative ID,Spend\n"
        df, _ = load_and_clean(csv)
        assert len(df) == 0


class TestCalculateKpis:
    def _base_df(self):
        return pd.DataFrame({
            "creative_id": ["C01", "C02", "C03"],
            "spend": [4800.0, 3200.0, 2700.0],
            "paid_starts": [60.0, 40.0, 10.0],
            "trial_starts": [200.0, 150.0, 50.0],
            "ctr": [1.7, 0.9, 0.6],
            "thumbstop_rate": [36.0, 25.0, 18.0],
            "hold_6s": [24.0, np.nan, 11.0],
        })

    def test_cpa_calculated(self):
        df, missing = calculate_kpis(self._base_df())
        assert "cpa" in df.columns
        assert df["cpa"].iloc[0] == pytest.approx(4800.0 / 60.0)

    def test_cpt_calculated(self):
        df, _ = calculate_kpis(self._base_df())
        assert "cpt" in df.columns
        assert df["cpt"].iloc[0] == pytest.approx(4800.0 / 200.0)

    def test_trial_to_paid_cvr_calculated(self):
        df, _ = calculate_kpis(self._base_df())
        assert "trial_to_paid_cvr" in df.columns
        assert df["trial_to_paid_cvr"].iloc[0] == pytest.approx(60.0 / 200.0)

    def test_paid_per_1k_calculated(self):
        df, _ = calculate_kpis(self._base_df())
        assert "paid_per_1k" in df.columns
        assert df["paid_per_1k"].iloc[0] == pytest.approx(60.0 / 4800.0 * 1000)

    def test_trial_per_1k_calculated(self):
        df, _ = calculate_kpis(self._base_df())
        assert "trial_per_1k" in df.columns
        assert df["trial_per_1k"].iloc[0] == pytest.approx(200.0 / 4800.0 * 1000)

    def test_zero_paid_starts_produces_nan_cpa(self):
        df = self._base_df()
        df["paid_starts"] = [0.0, 0.0, 0.0]
        df, _ = calculate_kpis(df)
        assert df["cpa"].isna().all()

    def test_zero_spend_produces_zero_cpa(self):
        df = self._base_df()
        df["spend"] = [0.0, 0.0, 0.0]
        df, _ = calculate_kpis(df)
        assert (df["cpa"] == 0.0).all()

    def test_missing_paid_starts_column_adds_warning(self):
        df = self._base_df().drop(columns=["paid_starts"])
        _, missing = calculate_kpis(df)
        assert any("Paid Start" in m for m in missing)

    def test_missing_trial_starts_column_adds_warning(self):
        df = self._base_df().drop(columns=["trial_starts"])
        _, missing = calculate_kpis(df)
        assert any("Trial Start" in m for m in missing)

    def test_missing_spend_column_adds_warning(self):
        df = self._base_df().drop(columns=["spend"])
        _, missing = calculate_kpis(df)
        assert any("Spend" in m for m in missing)

    def test_efficiency_scores_require_cpa(self):
        df = self._base_df().drop(columns=["paid_starts"])
        _, missing = calculate_kpis(df)
        labels = " ".join(missing)
        assert "Efficiency" in labels or "CTR" in labels

    def test_all_nan_paid_starts_adds_warning(self):
        df = self._base_df()
        df["paid_starts"] = np.nan
        _, missing = calculate_kpis(df)
        assert any("Paid Start" in m for m in missing)

    def test_no_missing_when_all_columns_present(self):
        df = self._base_df()
        df, missing = calculate_kpis(df)
        assert len(missing) == 0
