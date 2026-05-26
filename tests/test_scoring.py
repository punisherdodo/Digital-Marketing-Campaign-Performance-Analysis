import pytest
import numpy as np
import pandas as pd

from utils.scoring import rank_by_goal, assign_decision_labels


def _full_df():
    return pd.DataFrame({
        "creative_id": [f"C{i:02d}" for i in range(1, 7)],
        "platform": ["Meta"] * 6,
        "spend": [5000.0, 4000.0, 3000.0, 6000.0, 2000.0, 4500.0],
        "paid_starts": [80.0, 40.0, 10.0, 60.0, 5.0, 50.0],
        "trial_starts": [300.0, 200.0, 80.0, 250.0, 40.0, 220.0],
        "ctr": [2.0, 1.5, 0.5, 1.8, 0.3, 1.6],
        "thumbstop_rate": [40.0, 30.0, 15.0, 35.0, 10.0, 32.0],
        "hold_6s": [25.0, 20.0, 10.0, 22.0, 8.0, 21.0],
        "cpa": [62.5, 100.0, 300.0, 100.0, 400.0, 90.0],
        "cpt": [16.7, 20.0, 37.5, 24.0, 50.0, 20.5],
        "trial_to_paid_cvr": [0.27, 0.20, 0.13, 0.24, 0.13, 0.23],
    })


class TestRankByGoal:
    def test_paid_starts_sorts_descending(self):
        df = _full_df()
        ranked = rank_by_goal(df, "Paid Starts")
        assert ranked.iloc[0]["paid_starts"] == df["paid_starts"].max()

    def test_trial_starts_sorts_descending(self):
        df = _full_df()
        ranked = rank_by_goal(df, "Trial Starts")
        assert ranked.iloc[0]["trial_starts"] == df["trial_starts"].max()

    def test_efficient_paid_starts_sorts_by_cpa_ascending(self):
        df = _full_df()
        ranked = rank_by_goal(df, "Efficient Paid Starts", cpa_target=90.0)
        assert ranked.iloc[0]["cpa"] == df["cpa"].min()

    def test_efficient_paid_starts_marks_scale_candidates(self):
        df = _full_df()
        ranked = rank_by_goal(df, "Efficient Paid Starts", cpa_target=90.0)
        assert "scale_candidate" in ranked.columns
        assert ranked[ranked["cpa"] < 90.0]["scale_candidate"].all()

    def test_efficient_trial_starts_sorts_by_cpt_ascending(self):
        df = _full_df()
        ranked = rank_by_goal(df, "Efficient Trial Starts")
        assert ranked.iloc[0]["cpt"] == df["cpt"].min()

    def test_creative_engagement_produces_goal_score(self):
        df = _full_df()
        ranked = rank_by_goal(df, "Creative Engagement")
        assert "goal_score" in ranked.columns
        assert ranked["goal_score"].notna().all()

    def test_creative_engagement_sorted_by_score(self):
        df = _full_df()
        ranked = rank_by_goal(df, "Creative Engagement")
        scores = ranked["goal_score"].tolist()
        assert scores == sorted(scores, reverse=True)

    def test_full_funnel_quality_produces_goal_score(self):
        df = _full_df()
        ranked = rank_by_goal(df, "Full Funnel Quality")
        assert "goal_score" in ranked.columns
        scores = ranked["goal_score"].tolist()
        assert scores == sorted(scores, reverse=True)

    def test_rank_index_starts_at_1(self):
        df = _full_df()
        for goal in ["Paid Starts", "Trial Starts", "Efficient Paid Starts",
                     "Efficient Trial Starts", "Creative Engagement", "Full Funnel Quality"]:
            ranked = rank_by_goal(df, goal)
            assert ranked.index[0] == 1

    def test_custom_ce_weights_respected(self):
        df = _full_df()
        weights = {"thumbstop_rate": 100, "hold_6s": 0, "ctr": 0}
        ranked = rank_by_goal(df, "Creative Engagement", ce_weights=weights)
        assert "goal_score" in ranked.columns
        assert ranked.iloc[0]["thumbstop_rate"] == df["thumbstop_rate"].max()

    def test_missing_sort_column_does_not_raise(self):
        df = _full_df().drop(columns=["paid_starts"])
        ranked = rank_by_goal(df, "Paid Starts")
        assert isinstance(ranked, pd.DataFrame)

    def test_single_row_does_not_raise(self):
        df = _full_df().head(1)
        for goal in ["Paid Starts", "Trial Starts", "Efficient Paid Starts",
                     "Efficient Trial Starts", "Creative Engagement", "Full Funnel Quality"]:
            ranked = rank_by_goal(df, goal)
            assert len(ranked) == 1


class TestAssignDecisionLabels:
    def _make_df(self, cpa, paid, trial, cvr, thumbstop, cpa_target=90.0):
        df = pd.DataFrame({
            "creative_id": [f"C{i+1:02d}" for i in range(len(cpa))],
            "cpa": cpa,
            "paid_starts": paid,
            "trial_starts": trial,
            "trial_to_paid_cvr": cvr,
            "thumbstop_rate": thumbstop,
        })
        return assign_decision_labels(df, cpa_target=cpa_target)

    def test_scale_label_assigned(self):
        df = self._make_df(
            cpa=[50.0, 120.0, 200.0, 150.0],
            paid=[100.0, 20.0, 5.0, 10.0],
            trial=[300.0, 100.0, 30.0, 50.0],
            cvr=[0.33, 0.20, 0.17, 0.20],
            thumbstop=[40.0, 25.0, 15.0, 20.0],
            cpa_target=90.0,
        )
        assert "decision_label" in df.columns
        assert "Scale" in df["decision_label"].values

    def test_cut_label_assigned(self):
        df = self._make_df(
            cpa=[200.0, 180.0, 190.0, 170.0, 195.0, 185.0],
            paid=[5.0, 6.0, 4.0, 7.0, 3.0, 8.0],
            trial=[30.0, 25.0, 20.0, 28.0, 18.0, 22.0],
            cvr=[0.17, 0.24, 0.20, 0.25, 0.17, 0.36],
            thumbstop=[8.0, 10.0, 7.0, 9.0, 6.0, 11.0],
            cpa_target=90.0,
        )
        assert "Cut" in df["decision_label"].values

    def test_keep_testing_label_assigned(self):
        df = pd.DataFrame({
            "creative_id": ["C01", "C02"],
            "cpa": [np.nan, np.nan],
            "paid_starts": [5.0, 20.0],
            "trial_starts": [50.0, 100.0],
            "trial_to_paid_cvr": [0.10, 0.20],
            "thumbstop_rate": [60.0, 10.0],
        })
        df = assign_decision_labels(df, cpa_target=90.0)
        assert "Keep Testing" in df["decision_label"].values

    def test_fix_funnel_label_assigned(self):
        df = pd.DataFrame({
            "creative_id": ["C01", "C02"],
            "cpa": [np.nan, np.nan],
            "paid_starts": [10.0, 10.0],
            "trial_starts": [500.0, 50.0],
            "trial_to_paid_cvr": [0.02, 0.20],
            "thumbstop_rate": [20.0, 20.0],
        })
        df = assign_decision_labels(df, cpa_target=90.0)
        assert "Fix Funnel" in df["decision_label"].values

    def test_review_label_is_fallback(self):
        df = pd.DataFrame({
            "creative_id": ["C01"],
            "cpa": [np.nan],
            "paid_starts": [np.nan],
            "trial_starts": [np.nan],
            "trial_to_paid_cvr": [np.nan],
            "thumbstop_rate": [np.nan],
        })
        df = assign_decision_labels(df, cpa_target=90.0)
        assert df["decision_label"].iloc[0] == "Review"

    def test_all_rows_get_a_label(self):
        df = _full_df()
        labeled = assign_decision_labels(df, cpa_target=90.0)
        assert labeled["decision_label"].notna().all()
        valid = {"Scale", "Cut", "Keep Testing", "Fix Funnel", "Review"}
        assert set(labeled["decision_label"].unique()).issubset(valid)

    def test_cpa_target_affects_scale_label(self):
        df = pd.DataFrame({
            "creative_id": ["C01", "C02"],
            "cpa": [150.0, 50.0],
            "paid_starts": [80.0, 10.0],
            "trial_starts": [300.0, 50.0],
            "trial_to_paid_cvr": [0.27, 0.20],
            "thumbstop_rate": [40.0, 15.0],
        })
        result_low = assign_decision_labels(df.copy(), cpa_target=200.0)
        result_high = assign_decision_labels(df.copy(), cpa_target=90.0)
        assert "Scale" in result_low["decision_label"].values
        assert "Scale" not in result_high["decision_label"].values
