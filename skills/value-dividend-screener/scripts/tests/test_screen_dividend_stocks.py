"""Tests for the pure analysis helpers in screen_dividend_stocks.

These cover the deterministic, offline-safe calculators (no network / API
calls) so the screening math can be validated without an FMP or FINVIZ key.
"""

from screen_dividend_stocks import RSICalculator, StockAnalyzer


class TestCalculateCAGR:
    def test_positive_growth(self):
        # 100 -> 133.1 over 3 years == 10% CAGR
        cagr = StockAnalyzer.calculate_cagr(100.0, 133.1, 3)
        assert cagr is not None
        assert round(cagr, 1) == 10.0

    def test_no_growth_is_zero(self):
        assert StockAnalyzer.calculate_cagr(100.0, 100.0, 3) == 0.0

    def test_non_positive_values_return_none(self):
        assert StockAnalyzer.calculate_cagr(0, 100.0, 3) is None
        assert StockAnalyzer.calculate_cagr(100.0, -5.0, 3) is None
        assert StockAnalyzer.calculate_cagr(100.0, 100.0, 0) is None


class TestCheckPositiveTrend:
    def test_steady_uptrend(self):
        assert StockAnalyzer.check_positive_trend([1.0, 2.0, 3.0, 4.0]) is True

    def test_allows_single_dip(self):
        assert StockAnalyzer.check_positive_trend([1.0, 3.0, 2.0, 4.0]) is True

    def test_rejects_two_dips(self):
        assert StockAnalyzer.check_positive_trend([1.0, 3.0, 2.0, 1.5]) is False

    def test_flat_or_declining_rejected(self):
        assert StockAnalyzer.check_positive_trend([4.0, 3.0, 2.0, 1.0]) is False

    def test_too_few_values(self):
        assert StockAnalyzer.check_positive_trend([1.0, 2.0]) is False


class TestIsReit:
    def test_real_estate_sector(self):
        assert StockAnalyzer.is_reit({"sector": "Real Estate"}) is True

    def test_reit_in_industry(self):
        assert StockAnalyzer.is_reit({"industry": "REIT - Retail"}) is True

    def test_non_reit(self):
        assert StockAnalyzer.is_reit({"sector": "Technology", "industry": "Software"}) is False

    def test_missing_fields(self):
        assert StockAnalyzer.is_reit({}) is False


class TestFFO:
    def test_ffo_sums_net_income_and_depreciation(self):
        cash_flows = [{"netIncome": 100, "depreciationAndAmortization": 40}]
        assert StockAnalyzer.calculate_ffo(cash_flows) == 140

    def test_ffo_none_when_empty(self):
        assert StockAnalyzer.calculate_ffo([]) is None

    def test_ffo_payout_ratio(self):
        cash_flows = [{"netIncome": 100, "depreciationAndAmortization": 40, "dividendsPaid": -70}]
        # dividends 70 / FFO 140 == 50%
        assert StockAnalyzer.calculate_ffo_payout_ratio(cash_flows) == 50.0


class TestRSICalculator:
    def test_insufficient_data_returns_none(self):
        assert RSICalculator.calculate_rsi([1.0, 2.0, 3.0], period=14) is None

    def test_all_gains_returns_100(self):
        prices = [float(i) for i in range(1, 20)]  # strictly increasing
        assert RSICalculator.calculate_rsi(prices, period=14) == 100.0

    def test_returns_value_in_range(self):
        prices = [
            10,
            11,
            10.5,
            11.2,
            10.8,
            11.5,
            11.1,
            12.0,
            11.6,
            12.3,
            11.9,
            12.6,
            12.1,
            12.8,
            12.4,
            13.0,
        ]
        rsi = RSICalculator.calculate_rsi([float(p) for p in prices], period=14)
        assert rsi is not None
        assert 0.0 <= rsi <= 100.0


class TestFinancialHealth:
    def test_healthy_balance_sheet(self):
        bs = [
            {
                "totalDebt": 100,
                "totalStockholdersEquity": 100,
                "totalCurrentAssets": 200,
                "totalCurrentLiabilities": 100,
            }
        ]
        result = StockAnalyzer.analyze_financial_health(bs)
        assert result["debt_to_equity"] == 1.0
        assert result["current_ratio"] == 2.0
        assert result["healthy"] is True

    def test_unhealthy_high_debt(self):
        bs = [
            {
                "totalDebt": 300,
                "totalStockholdersEquity": 100,
                "totalCurrentAssets": 50,
                "totalCurrentLiabilities": 100,
            }
        ]
        result = StockAnalyzer.analyze_financial_health(bs)
        assert result["healthy"] is False

    def test_empty_balance_sheet(self):
        result = StockAnalyzer.analyze_financial_health([])
        assert result["healthy"] is False
        assert result["debt_to_equity"] is None
