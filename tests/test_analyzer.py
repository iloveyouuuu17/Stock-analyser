"""
tests/test_analyzer.py - Unit tests for StockAnalyzer (offline / mocked).
"""

from __future__ import annotations

import pandas as pd
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from analyzer import StockAnalyzer


def _make_ohlcv(n: int = 200) -> pd.DataFrame:
    """Generate synthetic OHLCV data for testing."""
    rng = np.random.default_rng(42)
    close = 1000 + np.cumsum(rng.normal(0, 10, n))
    high = close + rng.uniform(5, 20, n)
    low = close - rng.uniform(5, 20, n)
    open_ = close - rng.normal(0, 5, n)
    volume = rng.integers(100_000, 1_000_000, n).astype(float)

    index = pd.date_range("2023-01-01", periods=n, freq="B")
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=index,
    )


class TestStockAnalyzerInit:
    def test_symbol_uppercased(self):
        a = StockAnalyzer("reliance")
        assert a.symbol == "RELIANCE"

    def test_ticker_nse(self):
        a = StockAnalyzer("TCS", "NSE")
        assert a.ticker == "TCS.NS"

    def test_ticker_bse(self):
        a = StockAnalyzer("INFY", "BSE")
        assert a.ticker == "INFY.BO"

    def test_data_empty_before_fetch(self):
        a = StockAnalyzer("WIPRO")
        assert a._data.empty


class TestAddIndicators:
    def test_columns_present(self):
        df = _make_ohlcv()
        result = StockAnalyzer._add_indicators(df.copy())
        for col in ["SMA_20", "SMA_50", "EMA_20", "RSI", "MACD",
                    "MACD_Signal", "MACD_Hist",
                    "BB_Upper", "BB_Middle", "BB_Lower"]:
            assert col in result.columns, f"Missing column: {col}"

    def test_sma_50_nan_for_first_49_rows(self):
        df = _make_ohlcv()
        result = StockAnalyzer._add_indicators(df.copy())
        # First 49 rows should be NaN for SMA_50 (needs 50 data points)
        assert result["SMA_50"].iloc[:49].isna().all()

    def test_rsi_in_range(self):
        df = _make_ohlcv()
        result = StockAnalyzer._add_indicators(df.copy())
        valid_rsi = result["RSI"].dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()


class TestFetchData:
    def _patched_analyzer(self, df: pd.DataFrame) -> StockAnalyzer:
        """Return a StockAnalyzer whose yf.Ticker is mocked."""
        a = StockAnalyzer("RELIANCE")
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = df
        mock_ticker.info = {"sector": "Energy", "trailingPE": 25.0}

        with patch("analyzer.yf.Ticker", return_value=mock_ticker):
            a.fetch_data(period="1y")
        return a

    def test_fetch_returns_dataframe(self):
        df = _make_ohlcv()
        a = self._patched_analyzer(df)
        assert isinstance(a._data, pd.DataFrame)
        assert not a._data.empty

    def test_indicators_added_after_fetch(self):
        df = _make_ohlcv()
        a = self._patched_analyzer(df)
        assert "RSI" in a._data.columns
        assert "SMA_20" in a._data.columns

    def test_empty_data_raises(self):
        a = StockAnalyzer("INVALID")
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()

        with patch("analyzer.yf.Ticker", return_value=mock_ticker):
            with pytest.raises(ValueError, match="No data returned"):
                a.fetch_data()


class TestSummary:
    def test_summary_before_fetch(self):
        a = StockAnalyzer("RELIANCE")
        assert "fetch_data" in a.summary()

    def test_summary_after_fetch(self):
        df = _make_ohlcv()
        a = StockAnalyzer("RELIANCE")
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = df
        mock_ticker.info = {
            "sector": "Energy",
            "trailingPE": 25.0,
            "marketCap": 15_000_000_000_000,
            "dividendYield": 0.005,
        }

        with patch("analyzer.yf.Ticker", return_value=mock_ticker):
            a.fetch_data(period="1y")

        summary = a.summary()
        assert "RELIANCE" in summary
        assert "RSI" in summary
        assert "SMA 20" in summary
        assert "₹" in summary


class TestToCSV:
    def test_raises_before_fetch(self, tmp_path):
        a = StockAnalyzer("RELIANCE")
        with pytest.raises(RuntimeError, match="fetch_data"):
            a.to_csv(str(tmp_path / "out.csv"))

    def test_csv_written(self, tmp_path):
        df = _make_ohlcv()
        a = StockAnalyzer("RELIANCE")
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = df
        mock_ticker.info = {}

        with patch("analyzer.yf.Ticker", return_value=mock_ticker):
            a.fetch_data(period="1y")

        out = str(tmp_path / "reliance.csv")
        result = a.to_csv(out)
        assert result == out
        import os
        assert os.path.exists(out)
