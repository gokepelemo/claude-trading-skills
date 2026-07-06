"""Unit tests for pair-trade-screener pure calculation functions.

These tests exercise the deterministic statistical helpers (correlation, beta /
hedge ratio, half-life, z-score) without any network / FMP API access.
"""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]


def _load(module_name, filename):
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


find_pairs = _load("find_pairs", "find_pairs.py")
analyze_spread = _load("analyze_spread", "analyze_spread.py")


def _series(values):
    idx = pd.date_range("2024-01-01", periods=len(values), freq="D")
    return pd.Series(values, index=idx, dtype="float64")


# --- find_pairs -----------------------------------------------------------


def test_calculate_correlation_perfect_positive():
    a = _series(list(range(1, 201)))
    b = _series([2 * x + 5 for x in range(1, 201)])
    corr = find_pairs.calculate_correlation(a, b)
    assert corr == pytest.approx(1.0, abs=1e-9)


def test_calculate_correlation_insufficient_overlap_returns_none():
    a = _series(list(range(1, 51)))  # only 50 points (< 100 required)
    b = _series([2 * x for x in range(1, 51)])
    assert find_pairs.calculate_correlation(a, b) is None


def test_calculate_beta_recovers_slope():
    b = _series([x for x in range(1, 201)])
    a = _series([1.5 * x + 3 for x in range(1, 201)])
    result = find_pairs.calculate_beta(a, b)
    assert result["beta"] == pytest.approx(1.5, abs=1e-6)
    assert result["r_squared"] == pytest.approx(1.0, abs=1e-9)


def test_calculate_current_zscore_zero_std_returns_none():
    flat = _series([10.0] * 120)
    assert find_pairs.calculate_current_zscore(flat) is None


def test_calculate_half_life_mean_reverting_series():
    # Deterministic geometric decay x[t] = 0.5 * x[t-1] -> phi ~= 0.5
    values = [0.5**t for t in range(60)]
    hl = find_pairs.calculate_half_life(_series(values))
    assert hl is not None
    assert 0.5 < hl < 2.0


# --- analyze_spread -------------------------------------------------------


def test_calculate_hedge_ratio_recovers_slope():
    b = _series([x for x in range(1, 151)])
    a = _series([0.8 * x - 2 for x in range(1, 151)])
    result = analyze_spread.calculate_hedge_ratio(a, b)
    assert result["beta"] == pytest.approx(0.8, abs=1e-6)


def test_calculate_zscore_series_matches_manual():
    values = list(range(1, 121))
    zscore = analyze_spread.calculate_zscore_series(_series(values), window=90)
    # First (window-1) entries are NaN; later entries are finite numbers.
    assert np.isnan(zscore.iloc[0])
    assert np.isfinite(zscore.iloc[-1])


def test_calculate_half_life_non_reverting_returns_none():
    # Strictly increasing (unit-root-like) series -> phi >= 1 -> None
    trending = _series([float(x) for x in range(1, 121)])
    assert analyze_spread.calculate_half_life(trending) is None
