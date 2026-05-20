#!/usr/bin/env python3
"""
MA50 Position Calculator for Earnings Trade Analyzer

Calculates the price position relative to the 50-day Simple Moving Average,
anchored to the earnings date so the score reflects conditions at the time of
earnings rather than the current day (which may be post-gap-drift).

SMA50 is computed from the 50 closes ending at (and including) the earnings date.

A staleness warning is emitted when the most-recent bar in daily_prices is more
than 5 trading days newer than earnings_date, indicating the MA has drifted.

Scoring (10% weight):
  distance >= 10%: 100
  distance >= 5%:   80
  distance >= 0%:   60
  distance >= -5%:  35
  distance < -5%:   15
"""
from datetime import datetime, timedelta


def _score_ma50_distance(distance_pct: float) -> float:
    """Score the distance from MA50.

    Args:
        distance_pct: Percentage distance from MA50 (positive = above)

    Returns:
        Score from 0 to 100.
    """
    if distance_pct >= 10.0:
        return 100.0
    elif distance_pct >= 5.0:
        return 80.0
    elif distance_pct >= 0.0:
        return 60.0
    elif distance_pct >= -5.0:
        return 35.0
    else:
        return 15.0


def _find_index_by_date(daily_prices: list[dict], target_date: str) -> int:
    """Find the index of target_date in daily_prices (most-recent-first)."""
    for i, bar in enumerate(daily_prices):
        if bar.get("date") == target_date:
            return i
    return -1


def calculate_ma50_position(daily_prices: list[dict], earnings_date: str | None = None) -> dict:
    """
    Calculate price position relative to 50-day SMA anchored to earnings_date.

    SMA50 and current_price are both measured at earnings_date so the score
    is not contaminated by post-earnings drift.  When the script is run later
    (e.g. --lookback-days 5), daily_prices[0] may be days newer than
    earnings_date; a staleness warning is added when that gap exceeds 5 bars.

    When earnings_date is None (legacy mode), anchors to daily_prices[0]
    (most-recent bar) — pre-existing behavior preserved for backward compat.

    Args:
        daily_prices: list of dicts with 'date', 'close' (most-recent-first)
        earnings_date: YYYY-MM-DD string — the date to anchor the MA calculation.
                       Defaults to None (use most-recent bar).

    Returns:
        dict with:
          - ma50: float
          - distance_pct: float (positive = above MA)
          - above_ma50: bool
          - score: float (0-100)
          - warning: str (optional)
          - staleness_warning: str (optional, when run >7 days post-earnings)
    """
    # Determine the anchor index
    if earnings_date is None:
        earnings_idx = 0
    else:
        earnings_idx = _find_index_by_date(daily_prices, earnings_date)

    if earnings_idx == -1:
        return {
            "ma50": 0.0,
            "distance_pct": 0.0,
            "above_ma50": False,
            "score": 0.0,
            "warning": f"Earnings date {earnings_date} not found in price data",
        }

    # We need 50 bars ending at earnings_idx (inclusive).
    # In most-recent-first order those are indices earnings_idx..earnings_idx+49.
    end_idx = earnings_idx + 50
    if end_idx > len(daily_prices):
        return {
            "ma50": 0.0,
            "distance_pct": 0.0,
            "above_ma50": False,
            "score": 0.0,
            "warning": f"Insufficient data for MA50: need 50 bars before {earnings_date}",
        }

    closes_50 = [daily_prices[i]["close"] for i in range(earnings_idx, end_idx)]
    ma50 = sum(closes_50) / 50.0
    current_price = daily_prices[earnings_idx]["close"]

    if ma50 == 0:
        return {
            "ma50": 0.0,
            "distance_pct": 0.0,
            "above_ma50": False,
            "score": 0.0,
            "warning": "MA50 is zero",
        }

    distance_pct = ((current_price / ma50) - 1.0) * 100.0
    above_ma50 = distance_pct >= 0
    score = _score_ma50_distance(distance_pct)

    result: dict = {
        "ma50": round(ma50, 2),
        "distance_pct": round(distance_pct, 2),
        "above_ma50": above_ma50,
        "score": score,
    }

    # Staleness check: if the most-recent bar is more than 5 days after earnings
    # the caller is warned that the MA was measured at earnings, not today.
    if earnings_date is not None:
        most_recent_date = daily_prices[0].get("date", "")
        if most_recent_date and most_recent_date > earnings_date:
            try:
                delta = (
                    datetime.strptime(most_recent_date, "%Y-%m-%d")
                    - datetime.strptime(earnings_date, "%Y-%m-%d")
                ).days
                if delta > 7:  # ~5 trading days
                    result["staleness_warning"] = (
                        f"MA50 anchored to earnings date {earnings_date}; "
                        f"most-recent bar is {delta} calendar days later. "
                        "Score reflects conditions at earnings, not today."
                    )
            except ValueError:
                pass

    return result
