"""
tests/test_utils.py - Unit tests for utility helpers.
"""

import pytest
from utils import resolve_ticker, format_number, validate_period, NIFTY50_SYMBOLS


class TestResolveTicker:
    def test_nse_default(self):
        assert resolve_ticker("RELIANCE") == "RELIANCE.NS"

    def test_nse_explicit(self):
        assert resolve_ticker("TCS", "NSE") == "TCS.NS"

    def test_bse(self):
        assert resolve_ticker("INFY", "BSE") == "INFY.BO"

    def test_already_has_ns_suffix(self):
        assert resolve_ticker("WIPRO.NS") == "WIPRO.NS"

    def test_already_has_bo_suffix(self):
        assert resolve_ticker("SBIN.BO") == "SBIN.BO"

    def test_lowercase_input(self):
        assert resolve_ticker("reliance") == "RELIANCE.NS"

    def test_strips_whitespace(self):
        assert resolve_ticker("  TCS  ") == "TCS.NS"


class TestFormatNumber:
    def test_crores(self):
        result = format_number(1_500_000_000)
        assert "Cr" in result
        assert "150.00" in result

    def test_lakhs(self):
        result = format_number(250_000)
        assert "L" in result
        assert "2.50" in result

    def test_small_number(self):
        result = format_number(999.5)
        assert "₹999.50" in result

    def test_none(self):
        assert format_number(None) == "N/A"

    def test_negative(self):
        result = format_number(-5_000_000)
        assert "L" in result


class TestValidatePeriod:
    @pytest.mark.parametrize("period", [
        "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max",
    ])
    def test_valid_periods(self, period):
        assert validate_period(period) is True

    def test_invalid_period(self):
        assert validate_period("1week") is False

    def test_empty_string(self):
        assert validate_period("") is False


class TestNifty50Symbols:
    def test_list_not_empty(self):
        assert len(NIFTY50_SYMBOLS) > 0

    def test_contains_common_stocks(self):
        assert "RELIANCE" in NIFTY50_SYMBOLS
        assert "TCS" in NIFTY50_SYMBOLS
        assert "INFY" in NIFTY50_SYMBOLS
