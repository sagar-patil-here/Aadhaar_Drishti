"""
tests/test_preprocessor.py
tests/test_tri_shield.py
Combined test file.

Run:  pytest tests/ -v
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta


# ─────────────────────────────────────────────
# Fixtures: minimal synthetic DataFrames
# ─────────────────────────────────────────────

def _make_enrol(n=20, ghost_spike=False):
    rows = []
    base_date = date(2025, 4, 1)
    for i in range(n):
        age_0_5 = 200 if (ghost_spike and i == 5) else 2
        rows.append({
            "date":           str(base_date + timedelta(days=i % 30)),
            "state":          "Maharashtra",
            "district":       "Pune",
            "pincode":        411001 + (i % 5),
            "age_0_5":        age_0_5,
            "age_5_17":       10,
            "age_18_greater": 30,
        })
    return pd.DataFrame(rows)


def _make_bio(n=20, spike=False):
    rows = []
    base_date = date(2025, 4, 1)
    for i in range(n):
        bio_17 = 5000 if (spike and i == 5) else 5
        rows.append({
            "date":         str(base_date + timedelta(days=i % 30)),
            "state":        "Maharashtra",
            "district":     "Pune",
            "pincode":      411001 + (i % 5),
            "bio_age_5_17": 3,
            "bio_age_17_":  bio_17,
        })
    return pd.DataFrame(rows)


def _make_demo(n=20):
    rows = []
    base_date = date(2025, 4, 1)
    for i in range(n):
        rows.append({
            "date":          str(base_date + timedelta(days=i % 30)),
            "state":         "Maharashtra",
            "district":      "Pune",
            "pincode":       411001 + (i % 5),
            "demo_age_5_17": 1,
            "demo_age_17_":  2,
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# Preprocessor tests
# ─────────────────────────────────────────────

class TestMerge:
    def test_merge_produces_all_columns(self):
        from app.services.preprocessor import merge_feeds
        df = merge_feeds(_make_enrol(), _make_bio(), _make_demo())
        for col in ["age_0_5", "bio_age_5_17", "demo_age_5_17"]:
            assert col in df.columns

    def test_outer_join_fills_missing_with_zero(self):
        from app.services.preprocessor import merge_feeds
        enrol = _make_enrol(5)
        bio   = _make_bio(3)    # fewer rows
        demo  = _make_demo(5)
        df    = merge_feeds(enrol, bio, demo)
        assert df["bio_age_5_17"].isna().sum() == 0


class TestClean:
    def test_bad_pincode_dropped(self):
        from app.services.preprocessor import merge_feeds, clean
        enrol = _make_enrol(5)
        enrol.loc[0, "pincode"] = 99          # invalid
        df = merge_feeds(enrol, _make_bio(5), _make_demo(5))
        df = clean(df)
        assert 99 not in df["pincode"].values

    def test_duplicate_date_district_dropped(self):
        from app.services.preprocessor import merge_feeds, clean
        enrol = pd.concat([_make_enrol(5), _make_enrol(5)])  # exact dupes
        df    = merge_feeds(enrol, _make_bio(5), _make_demo(5))
        before = len(df)
        df = clean(df)
        assert len(df) < before


class TestFeatureEngineering:
    def test_ghost_child_ratio_computed(self):
        from app.services.preprocessor import merge_feeds, clean, engineer_features
        df = merge_feeds(_make_enrol(), _make_bio(), _make_demo())
        df = clean(df)
        df = engineer_features(df)
        assert "ghost_child_ratio" in df.columns
        assert df["ghost_child_ratio"].between(0, 1).all()

    def test_ghost_spike_produces_high_ratio(self):
        from app.services.preprocessor import merge_feeds, clean, engineer_features
        df = merge_feeds(_make_enrol(20, ghost_spike=True), _make_bio(), _make_demo())
        df = clean(df)
        df = engineer_features(df)
        assert df["ghost_child_ratio"].max() > 0.5

    def test_bio_demo_ratio_computed(self):
        from app.services.preprocessor import merge_feeds, clean, engineer_features
        df = merge_feeds(_make_enrol(), _make_bio(20, spike=True), _make_demo())
        df = clean(df)
        df = engineer_features(df)
        assert df["bio_demo_ratio_17_"].max() > 100   # spike row should dominate

    def test_enrollment_velocity_nonnegative(self):
        from app.services.preprocessor import merge_feeds, clean, engineer_features
        df = merge_feeds(_make_enrol(), _make_bio(), _make_demo())
        df = clean(df)
        df = engineer_features(df)
        assert (df["enrollment_velocity"] >= 0).all()


class TestFullPipeline:
    def test_pipeline_returns_correct_feature_count(self, tmp_path):
        from app.services.preprocessor import (
            FEATURE_COLS, run_pipeline_from_dataframes
        )
        df, X = run_pipeline_from_dataframes(_make_enrol(), _make_bio(), _make_demo(), fit=True)
        assert X.shape[1] == len(FEATURE_COLS)
        assert X.shape[0] == len(df)

    def test_no_nans_in_output_matrix(self):
        from app.services.preprocessor import run_pipeline_from_dataframes
        _, X = run_pipeline_from_dataframes(_make_enrol(), _make_bio(), _make_demo(), fit=True)
        assert not np.isnan(X).any()


# ─────────────────────────────────────────────
# Tri-Shield module tests
# ─────────────────────────────────────────────

def _full_df(ghost_spike=False, bio_spike=False):
    from app.services.preprocessor import (
        merge_feeds, clean, engineer_features, encode_categoricals
    )
    df = merge_feeds(
        _make_enrol(40, ghost_spike=ghost_spike),
        _make_bio(40, spike=bio_spike),
        _make_demo(40),
    )
    df = clean(df)
    df = engineer_features(df)
    df = encode_categoricals(df, fit=True)
    return df


class TestGhostScanner:
    def test_adds_flag_column(self):
        from app.services.tri_shield.ghost_scanner import run
        df = run(_full_df())
        assert "ghost_scanner_flag" in df.columns

    def test_spike_gets_flagged(self):
        from app.services.tri_shield.ghost_scanner import run
        df = run(_full_df(ghost_spike=True))
        assert df["ghost_scanner_flag"].any()

    def test_normal_data_mostly_clean(self):
        from app.services.tri_shield.ghost_scanner import run
        df   = run(_full_df(ghost_spike=False))
        rate = df["ghost_scanner_flag"].mean()
        assert rate < 0.3   # fewer than 30% flagged on clean data


class TestLaunderingDetector:
    def test_adds_flag_column(self):
        from app.services.tri_shield.laundering_detector import run
        df = run(_full_df())
        assert "laundering_flag" in df.columns

    def test_bio_spike_triggers_flag(self):
        from app.services.tri_shield.laundering_detector import run
        df = run(_full_df(bio_spike=True))
        assert df["laundering_flag"].any()


class TestMigrationRadar:
    def test_adds_zscore_column(self):
        from app.services.tri_shield.migration_radar import run
        df = run(_full_df())
        assert "migration_zscore" in df.columns
        assert "migration_radar_flag" in df.columns

    def test_zscore_is_float(self):
        from app.services.tri_shield.migration_radar import run
        df = run(_full_df())
        assert df["migration_zscore"].dtype == float


# ─────────────────────────────────────────────
# Decision logic tests
# ─────────────────────────────────────────────

class TestDecisionLogic:
    def _run(self, ghost_spike=False):
        from app.services.preprocessor import run_pipeline_from_dataframes
        from app.services.decision_logic import run_tri_shield, route
        from app.services.anomaly_engine import score_and_flag

        df, X = run_pipeline_from_dataframes(
            _make_enrol(40, ghost_spike=ghost_spike),
            _make_bio(40), _make_demo(40), fit=True
        )
        df = run_tri_shield(df)
        scores, flags = score_and_flag(X)
        return route(df, scores, flags)

    def test_route_returns_correct_keys(self):
        result = self._run()
        assert "secure_records" in result
        assert "red_flags" in result
        assert "flagged_count" in result

    def test_counts_sum_to_total(self):
        result = self._run()
        total = result["secure_count"] + result["flagged_count"]
        assert total == len(result["secure_records"]) + len(result["red_flags"])

    def test_severity_values_valid(self):
        result = self._run(ghost_spike=True)
        valid = {"HIGH", "MEDIUM", "LOW"}
        for flag in result["red_flags"]:
            assert flag["severity"] in valid
