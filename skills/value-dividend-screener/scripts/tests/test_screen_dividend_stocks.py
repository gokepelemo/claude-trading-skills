"""Tests for pure-calculation helpers in screen_dividend_stocks.py"""

import pytest
from screen_dividend_stocks import RSICalculator, StockAnalyzer


class TestCalculateCagr:
    def test_doubling_over_three_years(self):
        assert StockAnalyzer.calculate_cagr(1.0, 2.0, 3) == pytest.approx(25.99, abs=0.01)

    @pytest.mark.parametrize("start,end,years", [(0, 1, 3), (1, 0, 3), (-1, 2, 3), (1, 2, 0)])
    def test_invalid_inputs_return_none(self, start, end, years):
        assert StockAnalyzer.calculate_cagr(start, end, years) is None


class TestCheckPositiveTrend:
    def test_rising_series(self):
        assert StockAnalyzer.check_positive_trend([1, 2, 3, 4]) is True

    def test_one_dip_allowed(self):
        assert StockAnalyzer.check_positive_trend([1, 3, 2, 4]) is True

    def test_two_dips_rejected(self):
        assert StockAnalyzer.check_positive_trend([1, 4, 2, 3, 2, 5]) is False

    def test_declining_series(self):
        assert StockAnalyzer.check_positive_trend([4, 3, 2]) is False

    def test_too_few_values(self):
        assert StockAnalyzer.check_positive_trend([1, 2]) is False


class TestRsi:
    def test_insufficient_data(self):
        assert RSICalculator.calculate_rsi([1.0] * 10) is None

    def test_all_gains_is_100(self):
        assert RSICalculator.calculate_rsi([float(i) for i in range(1, 20)]) == 100.0

    def test_all_losses_is_0(self):
        assert RSICalculator.calculate_rsi([float(i) for i in range(20, 1, -1)]) == 0.0
