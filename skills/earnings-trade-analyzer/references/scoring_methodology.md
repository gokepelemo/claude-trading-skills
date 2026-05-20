# Earnings Trade Analyzer - Scoring Methodology

## Overview

The Earnings Trade Analyzer uses a 5-factor weighted scoring system to evaluate post-earnings stock setups. Each stock receives a composite score (0-100) and a letter grade (A/B/C/D).

## 5-Factor Scoring System

### Factor 1: Gap Size (25% Weight)

Measures the magnitude of the earnings gap, regardless of direction. Larger gaps indicate stronger institutional conviction.

| Absolute Gap | Score |
|-------------|-------|
| >= 10%      | 100   |
| >= 7%       | 85    |
| >= 5%       | 70    |
| >= 3%       | 55    |
| >= 1%       | 35    |
| < 1%        | 15    |

**Timing Logic:**
- **BMO (Before Market Open):** gap = open[earnings_date] / close[previous_day] - 1
- **AMC (After Market Close):** gap = open[next_day] / close[earnings_date] - 1
- **Unknown:** Uses AMC logic as default

**Design note — gap direction:** The score uses absolute gap magnitude so a -15% gap-down scores identically to a +15% gap-up. This is intentional for general volatility detection, but has an important implication for PEAD (Post-Earnings Announcement Drift) strategies: **gap-downs do not produce the same accumulation dynamic as gap-ups**. Buyers chasing a downside gap are fighting the initial reaction. When the calculator returns `gap_type = "down"`, a `gap_down_warning` field is added to the result. Operators should treat any Grade A or B rating where `gap_type = "down"` with extra skepticism — the high gap score is measuring a downside event, not an upside breakout.

### Factor 2: Pre-Earnings Trend (30% Weight)

Measures the 20-day price return in the 20 trading days **before** the earnings date. Stocks trending up before a positive earnings gap show stronger momentum characteristics.

**Window definition (most-recent-first arrays):**
- `close_at_endpoint`: For BMO stocks, `daily_prices[earnings_idx + 1]` (close of the day *before* earnings) to avoid including the gap itself in the trend score. For AMC/unknown, `daily_prices[earnings_idx]` (close on earnings day, before next-day gap).
- `close_20d_before`: `daily_prices[earnings_idx + 21]` (20 trading days before the endpoint).

This ensures the trend score measures pre-earnings accumulation, not the gap reaction itself.

| 20-Day Return | Score |
|--------------|-------|
| >= 15%       | 100   |
| >= 10%       | 85    |
| >= 5%        | 70    |
| >= 0%        | 50    |
| >= -5%       | 30    |
| < -5%        | 15    |

### Factor 3: Volume Trend (20% Weight)

Ratio of 20-day average volume to 60-day average volume, both measured **before** the earnings date. Higher ratios indicate increased institutional interest and accumulation leading into the event.

**Window definition (most-recent-first arrays):**
- 20-day window: `daily_prices[earnings_idx+1 : earnings_idx+21]` (20 trading days immediately before earnings)
- 60-day baseline: `daily_prices[earnings_idx+1 : earnings_idx+61]` (60 trading days before earnings)

Measuring pre-earnings volume rather than post-earnings volume matters: a post-earnings volume spike is an expected reaction to any event. Pre-earnings accumulation reflects *conviction leading in*, which is the signal this factor targets.

| Volume Ratio (20d/60d) | Score |
|------------------------|-------|
| >= 2.0x                | 100   |
| >= 1.5x                | 80    |
| >= 1.2x                | 60    |
| >= 1.0x                | 40    |
| < 1.0x                 | 20    |

### Factor 4: MA200 Position (15% Weight)

Price position relative to the 200-day Simple Moving Average, **anchored to the earnings date**. The SMA is computed from the 200 closes ending at `earnings_idx` so the score reflects the stock's trend structure at the time of the event, not at the time the script is run.

**Staleness warning:** If the script is run more than 5 trading days after earnings, a `staleness_warning` field is added to the result indicating that the SMA was computed as-of the earnings date and may differ from current MA200.

| Distance from MA200 | Score |
|---------------------|-------|
| >= 20%              | 100   |
| >= 10%              | 85    |
| >= 5%               | 70    |
| >= 0%               | 55    |
| >= -5%              | 35    |
| < -5%               | 15    |

### Factor 5: MA50 Position (10% Weight)

Price position relative to the 50-day Simple Moving Average, anchored to the earnings date (same rationale as MA200). Stocks above their 50-day SMA show medium-term strength.

**Staleness warning:** Same staleness flag as MA200 when run >5 days post-earnings.

| Distance from MA50 | Score |
|--------------------|-------|
| >= 10%             | 100   |
| >= 5%              | 80    |
| >= 0%              | 60    |
| >= -5%             | 35    |
| < -5%              | 15    |

## Grade Thresholds

| Grade | Score Range | Description |
|-------|-----------|-------------|
| A     | 85-100    | Strong earnings reaction with institutional accumulation |
| B     | 70-84     | Good earnings reaction worth monitoring |
| C     | 55-69     | Mixed signals, use caution |
| D     | 0-54      | Weak setup, avoid |

## Entry Quality Filter

When `--apply-entry-filter` is enabled, the following stocks are excluded:
- Stocks with current price < $10 (penny stock territory, lower institutional interest)

**Note on the 517-trade backtest:** The entry filter rules were derived from a backtest over 517 historical earnings trades. The backtest script (`entry_filter.py`) and results summary are not currently included in this skill directory. If you need to audit or reproduce the filter logic, reach out to the skill maintainer or check the trading journal for the original session where the rules were derived.

## Historical Win Rate Context

The scoring system is designed to identify stocks with the highest probability of continued post-earnings momentum. Key observations:

- **Grade A stocks** (85+) historically show the strongest post-earnings drift (PEAD)
- **Pre-earnings trend** receives the highest weight (30%) because momentum heading into earnings is the strongest predictor of post-earnings continuation
- **Volume confirmation** (20%) validates institutional participation in the earnings move
- **Moving average positions** (25% combined) confirm the stock is in a favorable trend structure

## Composite Score Formula

```
composite_score = (gap_score * 0.25) + (trend_score * 0.30) + (volume_score * 0.20)
                + (ma200_score * 0.15) + (ma50_score * 0.10)
```

The weights sum to exactly 1.0 (100%).
