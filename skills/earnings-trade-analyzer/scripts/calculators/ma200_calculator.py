#!/usr/bin/env python3
"""
MA200 Position Calculator for Earnings Trade Analyzer

Calculates the price position relative to the 200-day Simple Moving Average,
anchored to the earnings date so the score reflects conditions at the time of
earnings rather than the current day (which may be post-gap-drift).

SMA200 is computed from the 200 closes ending at (and including) the earnings date.

A staleness warning is emitted when the most-recent bar in daily_prices is more
than 5 trading days newer than earnings_date, indicating the MA has drifted.

Scoring (15% weight):
  distance >= 20%: 100
  distance >= 10%:  85
  distance >= 5%:   70
  distance >= 0%:   55
  distance >= -5%:  35
  distance < -5%:   15
"""
from datetime import datetime, timedelta


def _score_ma200_distance(distance_pct: float) -> float:
    """Score the distance from MA200.

    Args:
        distance_pct: Percentage distance from MA200 (positive = above)

    Returns:
        Score from 0 to 100.
    """
    if distance_pct >= 20.0:
        return 100.0
    elif distance_pct >= 10.0:
        return 85.0
    elif distance_pct >= 5.0:
        return 70.0
    elif distance_pct >= 0.0:
        return 55.0
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


def calculate_ma200_position(daily_prices: list[dict], earnings_date: str | None = None) -> dict:
    """
    Calculate price position relative to 200-day SMA anchored to earnings_date.

    SMA200 and current_price are both measured at earnings_date so the score
    is not contaminated by post-earnings drift.

    When earnings_date is None (legacy mode), anchors to daily_prices[0]
    (most-recent bar) — pre-existing behavior preserved for backward compat.

    Args:
        daily_prices: list of dicts with 'date', 'close' (most-recent-first)
        earnings_date: YYYY-MM-DD string — the date to anchor the MA calculation.
                       Defaults to None (use most-recent bar).

    Returns:
        dict with:
          - ma200: float
          - distance_pct: float (positive = above MA)
          - above_ma200: bool
          - score: float (0-100)
          - warning: str (optional)
          - staleness_warning: str (optional, if run >5 days after earnings)
    """
    if earnings_date is None:
        earnings_idx = 0
    else:
        earnings_idx = _find_index_by_date(daily_prices, earnings_date)

    if earnings_idx == -1:
        return {
            "ma200": 0.0,
            "distance_pct": 0.0,
            "above_ma200": False,
            "score": 0.0,
            "warning": f"Earnings date {earnings_date} not found in price data",
        }

    # We need 200 bars ending at earnings_idx (inclusive).
    end_idx = earnings_idx + 200
    if end_idx > len(daily_prices):
        return {
            "ma200": 0.0,
            "distance_pct": 0.0,
            "above_ma200": False,
            "score": 0.0,
            "warning": f"Insufficient data for MA200: need 200 bars before {earnings_date}",
        }

    closes_200 = [daily_prices[i]["close"] for i in range(earnings_idx, end_idx)]
    ma200 = sum(closes_200) / 200.0
    current_price = daily_prices[earnings_idx]["close"]

    if ma200 == 0:
        return {
            "ma200": 0.0,
            "distance_pct": 0.0,
            "above_ma200": False,
            "score": 0.0,
            "warning": "MA200 is zero",
        }

    distance_pct = ((current_price / ma200) - 1.0) * 100.0
    above_ma200 = distance_pct >= 0
    score = _score_ma200_distance(distance_pct)

    result: dict = {
        "ma200": round(ma200, 2),
        "distance_pct": round(distance_pct, 2),
        "above_ma200": above_ma200,
        "score": score,
    }

    most_recent_date = daily_prices[0].get("date", "")
    if earnings_date is not None and most_recent_date and most_recent_date > earnings_date:
        try:
            delta = (
                datetime.strptime(most_recent_date, "%Y-%m-%d")
                - datetime.strptime(earnings_date, "%Y-%m-%d")
            ).days
            if delta > 7:
                result["staleness_warning"] = (
                    f"MA200 anchored to earnings date {earnings_date}; "
                    f"most-recent bar is {delta} calendar days later. "
                    "Score reflects conditions at earnings, not today."
                )
        except ValueError:
            pass

    return result
