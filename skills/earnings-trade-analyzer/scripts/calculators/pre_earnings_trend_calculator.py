#!/usr/bin/env python3
"""
Pre-Earnings Trend Calculator for Earnings Trade Analyzer

Calculates the 20-day price return before the earnings date to assess
the stock's momentum heading into the earnings report.

Endpoint selection:
  - BMO (before market open): close on the day *before* earnings
    (daily_prices[earnings_idx+1]) so the intraday gap on earnings day
    is excluded from the trend measurement.
  - AMC / unknown: close on earnings day (daily_prices[earnings_idx]),
    which is before the next-day gap opens.

Scoring (30% weight):
  return >= 15%: 100
  return >= 10%:  85
  return >= 5%:   70
  return >= 0%:   50
  return >= -5%:  30
  return < -5%:   15
"""


def _find_index_by_date(daily_prices: list[dict], target_date: str) -> int:
    """Find the index of target_date in daily_prices (most-recent-first).

    Returns:
        Index if found, -1 otherwise.
    """
    for i, bar in enumerate(daily_prices):
        if bar.get("date") == target_date:
            return i
    return -1


def _score_trend(return_pct: float) -> float:
    """Score the 20-day pre-earnings return.

    Args:
        return_pct: 20-day return percentage (e.g. 8.5 for 8.5%)

    Returns:
        Score from 0 to 100.
    """
    if return_pct >= 15.0:
        return 100.0
    elif return_pct >= 10.0:
        return 85.0
    elif return_pct >= 5.0:
        return 70.0
    elif return_pct >= 0.0:
        return 50.0
    elif return_pct >= -5.0:
        return 30.0
    else:
        return 15.0


def calculate_pre_earnings_trend(daily_prices: list[dict], earnings_date: str, timing: str = "amc") -> dict:
    """
    Calculate 20-day return before earnings date.

    For BMO stocks, the trend endpoint is the close on the day *before* the
    earnings date (earnings_idx+1 in most-recent-first order) so the gap on
    earnings day is not included in the trend score.  For AMC/unknown the
    endpoint is the close on earnings day itself (before the next-day gap).

    Args:
        daily_prices: list of dicts with 'date', 'close' (most-recent-first)
        earnings_date: YYYY-MM-DD string
        timing: 'bmo', 'amc', or 'unknown' (default 'amc')

    Returns:
        dict with:
          - return_20d_pct: float
          - trend_direction: 'up' or 'down'
          - score: float (0-100)
          - warning: str (optional)
    """
    earnings_idx = _find_index_by_date(daily_prices, earnings_date)

    if earnings_idx == -1:
        return {
            "return_20d_pct": 0.0,
            "trend_direction": "up",
            "score": 0.0,
            "warning": f"Earnings date {earnings_date} not found in price data",
        }

    # Select the trend endpoint depending on timing.
    # BMO: use close[earnings_idx+1] (previous day) to exclude the gap itself.
    # AMC/unknown: use close[earnings_idx] (earnings-day close, gap is next open).
    if timing == "bmo":
        endpoint_idx = earnings_idx + 1
    else:
        endpoint_idx = earnings_idx

    if endpoint_idx >= len(daily_prices):
        return {
            "return_20d_pct": 0.0,
            "trend_direction": "up",
            "score": 0.0,
            "warning": "Insufficient data: no day before earnings for BMO endpoint",
        }

    # 20 trading days before the endpoint.
    # In most-recent-first order, 20 days further back = endpoint_idx + 20.
    lookback_idx = endpoint_idx + 20

    if lookback_idx >= len(daily_prices):
        return {
            "return_20d_pct": 0.0,
            "trend_direction": "up",
            "score": 0.0,
            "warning": "Insufficient data for 20-day pre-earnings trend calculation",
        }

    close_at_endpoint = daily_prices[endpoint_idx]["close"]
    close_20d_before = daily_prices[lookback_idx]["close"]

    if close_20d_before == 0:
        return {
            "return_20d_pct": 0.0,
            "trend_direction": "up",
            "score": 0.0,
            "warning": "Price 20 days before earnings is zero",
        }

    return_20d_pct = ((close_at_endpoint / close_20d_before) - 1.0) * 100.0
    trend_direction = "up" if return_20d_pct >= 0 else "down"
    score = _score_trend(return_20d_pct)

    result = {
        "return_20d_pct": round(return_20d_pct, 2),
        "trend_direction": trend_direction,
        "score": score,
    }
    return result
