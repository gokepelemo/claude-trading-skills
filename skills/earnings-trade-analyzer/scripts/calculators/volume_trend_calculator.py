#!/usr/bin/env python3
"""
Volume Trend Calculator for Earnings Trade Analyzer

Calculates the volume ratio around the earnings date:
  ratio = 20-day average volume (pre-earnings) / 60-day average volume (pre-earnings)

Both windows are measured in the 20 / 60 trading days *before* the earnings date.
In most-recent-first price arrays, "before earnings" means higher indices.
  20-day window: daily_prices[earnings_idx+1 : earnings_idx+21]
  60-day window: daily_prices[earnings_idx+1 : earnings_idx+61]

A ratio > 1.0 indicates increased institutional accumulation *leading into* earnings,
which is the signal of interest for PEAD setups.

Scoring (20% weight):
  ratio >= 2.0: 100
  ratio >= 1.5:  80
  ratio >= 1.2:  60
  ratio >= 1.0:  40
  ratio < 1.0:   20
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


def _score_volume_ratio(ratio: float) -> float:
    """Score the volume ratio.

    Args:
        ratio: 20-day avg volume / 60-day avg volume

    Returns:
        Score from 0 to 100.
    """
    if ratio >= 2.0:
        return 100.0
    elif ratio >= 1.5:
        return 80.0
    elif ratio >= 1.2:
        return 60.0
    elif ratio >= 1.0:
        return 40.0
    else:
        return 20.0


def calculate_volume_trend(daily_prices: list[dict], earnings_date: str) -> dict:
    """
    Calculate volume ratio: 20-day avg / 60-day avg around earnings date.

    Args:
        daily_prices: list of dicts with 'date', 'volume' (most-recent-first)
        earnings_date: YYYY-MM-DD string

    Returns:
        dict with:
          - vol_ratio_20_60: float
          - recent_avg_volume: int
          - longer_avg_volume: int
          - score: float (0-100)
          - warning: str (optional)
    """
    earnings_idx = _find_index_by_date(daily_prices, earnings_date)

    if earnings_idx == -1:
        return {
            "vol_ratio_20_60": 0.0,
            "recent_avg_volume": 0,
            "longer_avg_volume": 0,
            "score": 0.0,
            "warning": f"Earnings date {earnings_date} not found in price data",
        }

    # Calculate 20-day average volume in the 20 trading days *before* earnings.
    # In most-recent-first order, higher indices = older dates.
    # earnings_idx is the earnings bar itself; earnings_idx+1 is the day before.
    # Window: indices [earnings_idx+1, earnings_idx+21) = 20 pre-earnings trading days.
    start_20 = earnings_idx + 1
    end_20 = min(earnings_idx + 21, len(daily_prices))

    if end_20 - start_20 < 5:
        return {
            "vol_ratio_20_60": 0.0,
            "recent_avg_volume": 0,
            "longer_avg_volume": 0,
            "score": 0.0,
            "warning": "Insufficient data for 20-day volume calculation",
        }

    volumes_20 = [daily_prices[i]["volume"] for i in range(start_20, end_20)]
    recent_avg = sum(volumes_20) / len(volumes_20)

    # Calculate 60-day baseline volume from the 60 trading days *before* earnings.
    # Window: indices [earnings_idx+1, earnings_idx+61) = 60 pre-earnings trading days.
    start_60 = earnings_idx + 1
    end_60 = min(earnings_idx + 61, len(daily_prices))

    if end_60 - start_60 < 20:
        return {
            "vol_ratio_20_60": 0.0,
            "recent_avg_volume": int(recent_avg),
            "longer_avg_volume": 0,
            "score": 0.0,
            "warning": "Insufficient data for 60-day volume calculation",
        }

    volumes_60 = [daily_prices[i]["volume"] for i in range(start_60, end_60)]
    longer_avg = sum(volumes_60) / len(volumes_60)

    if longer_avg == 0:
        return {
            "vol_ratio_20_60": 0.0,
            "recent_avg_volume": int(recent_avg),
            "longer_avg_volume": 0,
            "score": 0.0,
            "warning": "60-day average volume is zero",
        }

    vol_ratio = recent_avg / longer_avg
    score = _score_volume_ratio(vol_ratio)

    result = {
        "vol_ratio_20_60": round(vol_ratio, 2),
        "recent_avg_volume": int(recent_avg),
        "longer_avg_volume": int(longer_avg),
        "score": score,
    }
    return result
