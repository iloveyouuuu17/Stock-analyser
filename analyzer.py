"""
analyzer.py - Core stock analysis logic for Indian stocks.

Fetches OHLCV data via yfinance and computes technical indicators
using the `ta` library.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
import yfinance as yf
import ta

from utils import resolve_ticker, format_number


class StockAnalyzer:
    """Fetch and analyse a single Indian stock."""

    def __init__(self, symbol: str, exchange: str = "NSE"):
        """
        Parameters
        ----------
        symbol   : NSE/BSE symbol, e.g. ``"RELIANCE"``
        exchange : ``"NSE"`` (default) or ``"BSE"``
        """
        self.symbol = symbol.upper()
        self.ticker = resolve_ticker(symbol, exchange)
        self._data: pd.DataFrame = pd.DataFrame()
        self._info: dict = {}

    # ------------------------------------------------------------------
    # Data fetching
    # ------------------------------------------------------------------

    def fetch_data(self, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """Download historical OHLCV data and compute indicators.

        Parameters
        ----------
        period   : yfinance period string (e.g. ``"1y"``, ``"6mo"``)
        interval : yfinance interval string (e.g. ``"1d"``, ``"1wk"``)

        Returns
        -------
        pd.DataFrame with columns Open, High, Low, Close, Volume plus indicators.
        """
        ticker_obj = yf.Ticker(self.ticker)
        df = ticker_obj.history(period=period, interval=interval)
        if df.empty:
            raise ValueError(
                f"No data returned for '{self.ticker}'. "
                "Check the symbol and exchange."
            )
        self._data = self._add_indicators(df)
        try:
            self._info = ticker_obj.info or {}
        except Exception:
            self._info = {}
        return self._data

    # ------------------------------------------------------------------
    # Technical indicators
    # ------------------------------------------------------------------

    @staticmethod
    def _add_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add SMA, EMA, RSI, MACD, and Bollinger Bands to *df*."""
        close = df["Close"]

        # Moving averages
        df["SMA_20"] = ta.trend.sma_indicator(close, window=20)
        df["SMA_50"] = ta.trend.sma_indicator(close, window=50)
        df["EMA_20"] = ta.trend.ema_indicator(close, window=20)

        # RSI
        df["RSI"] = ta.momentum.rsi(close, window=14)

        # MACD
        macd = ta.trend.MACD(close)
        df["MACD"] = macd.macd()
        df["MACD_Signal"] = macd.macd_signal()
        df["MACD_Hist"] = macd.macd_diff()

        # Bollinger Bands
        bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
        df["BB_Upper"] = bb.bollinger_hband()
        df["BB_Middle"] = bb.bollinger_mavg()
        df["BB_Lower"] = bb.bollinger_lband()

        return df

    # ------------------------------------------------------------------
    # Summary / reporting
    # ------------------------------------------------------------------

    def summary(self) -> str:
        """Return a formatted text summary of the stock."""
        if self._data.empty:
            return "No data loaded. Call fetch_data() first."

        latest = self._data.iloc[-1]
        prev = self._data.iloc[-2] if len(self._data) > 1 else latest

        change = latest["Close"] - prev["Close"]
        change_pct = (change / prev["Close"]) * 100

        rsi = latest.get("RSI", float("nan"))
        rsi_signal = (
            "Overbought (>70)" if rsi > 70
            else "Oversold (<30)" if rsi < 30
            else "Neutral"
        )

        info = self._info
        pe = info.get("trailingPE", "N/A")
        market_cap = format_number(info.get("marketCap"))
        div_yield = info.get("dividendYield")
        div_yield_str = f"{div_yield * 100:.2f}%" if div_yield else "N/A"
        sector = info.get("sector", "N/A")
        industry = info.get("industry", "N/A")

        lines = [
            f"{'=' * 50}",
            f"  {self.symbol}  ({self.ticker})",
            f"{'=' * 50}",
            f"  Last Close  : ₹{latest['Close']:.2f}",
            f"  Change      : ₹{change:+.2f} ({change_pct:+.2f}%)",
            f"  Volume      : {int(latest['Volume']):,}",
            f"  52W High    : ₹{self._data['High'].max():.2f}",
            f"  52W Low     : ₹{self._data['Low'].min():.2f}",
            f"  SMA 20      : ₹{latest['SMA_20']:.2f}",
            f"  SMA 50      : ₹{latest['SMA_50']:.2f}",
            f"  RSI (14)    : {rsi:.2f}  [{rsi_signal}]",
            f"  MACD        : {latest['MACD']:.4f}",
            f"  Market Cap  : {market_cap}",
            f"  P/E Ratio   : {pe}",
            f"  Div. Yield  : {div_yield_str}",
            f"  Sector      : {sector}",
            f"  Industry    : {industry}",
            f"{'=' * 50}",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Charts
    # ------------------------------------------------------------------

    def plot_chart(self, save_path: str | None = None) -> None:
        """Plot a candlestick chart with volume and indicators.

        Parameters
        ----------
        save_path : If provided, save the chart to this file path instead
                    of displaying it interactively.
        """
        try:
            import mplfinance as mpf
        except ImportError:
            raise ImportError(
                "mplfinance is required for charting. "
                "Install it with: pip install mplfinance"
            )

        df = self._data.copy()
        # mplfinance expects a DatetimeIndex
        df.index = pd.to_datetime(df.index)
        df.index = df.index.tz_localize(None)

        add_plots = [
            mpf.make_addplot(df["SMA_20"], color="blue", width=0.8, label="SMA 20"),
            mpf.make_addplot(df["SMA_50"], color="orange", width=0.8, label="SMA 50"),
            mpf.make_addplot(df["BB_Upper"], color="grey", linestyle="--", width=0.6),
            mpf.make_addplot(df["BB_Lower"], color="grey", linestyle="--", width=0.6),
        ]

        kwargs = dict(
            type="candle",
            style="charles",
            title=f"{self.symbol} - Price Chart",
            ylabel="Price (₹)",
            volume=True,
            addplot=add_plots,
            figsize=(14, 8),
        )
        if save_path:
            kwargs["savefig"] = save_path
        else:
            kwargs["show_nontrading"] = False

        mpf.plot(df, **kwargs)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def to_csv(self, file_path: str | None = None) -> str:
        """Export the analysed data to a CSV file.

        Parameters
        ----------
        file_path : Destination file path. Defaults to ``<SYMBOL>_analysis.csv``.

        Returns
        -------
        str
            Absolute path of the written file.
        """
        if self._data.empty:
            raise RuntimeError("No data loaded. Call fetch_data() first.")
        file_path = file_path or f"{self.symbol}_analysis.csv"
        self._data.to_csv(file_path)
        return file_path
