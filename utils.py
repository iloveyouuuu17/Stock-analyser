"""
utils.py - Helper utilities for the Indian Stock Analyzer.
"""

import re


# NSE top 50 symbols (Nifty 50 constituents, illustrative list)
NIFTY50_SYMBOLS = [
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK",
    "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BPCL", "BHARTIARTL",
    "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY",
    "EICHERMOT", "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE",
    "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK", "ITC",
    "INDUSINDBK", "INFY", "JSWSTEEL", "KOTAKBANK", "LTIM",
    "LT", "M&M", "MARUTI", "NTPC", "NESTLEIND",
    "ONGC", "POWERGRID", "RELIANCE", "SBILIFE", "SHREECEM",
    "SBIN", "SUNPHARMA", "TCS", "TATACONSUM", "TATAMOTORS",
    "TATASTEEL", "TECHM", "TITAN", "ULTRACEMCO", "WIPRO",
]


def resolve_ticker(symbol: str, exchange: str = "NSE") -> str:
    """
    Convert a bare Indian stock symbol to a Yahoo Finance ticker.

    Parameters
    ----------
    symbol   : Stock symbol, e.g. ``"RELIANCE"`` or ``"RELIANCE.NS"``
    exchange : ``"NSE"`` (default) or ``"BSE"``

    Returns
    -------
    str
        Yahoo Finance ticker string, e.g. ``"RELIANCE.NS"``
    """
    symbol = symbol.strip().upper()
    # Already has a suffix
    if re.search(r"\.(NS|BO)$", symbol):
        return symbol
    suffix = ".NS" if exchange.upper() == "NSE" else ".BO"
    return symbol + suffix


def format_number(value: float | None, decimals: int = 2) -> str:
    """Return a human-readable string for a large number (crores / lakhs)."""
    if value is None:
        return "N/A"
    abs_val = abs(value)
    if abs_val >= 1e7:
        return f"₹{value / 1e7:.{decimals}f} Cr"
    if abs_val >= 1e5:
        return f"₹{value / 1e5:.{decimals}f} L"
    return f"₹{value:.{decimals}f}"


def validate_period(period: str) -> bool:
    """Check that *period* is a valid yfinance period string."""
    valid = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}
    return period in valid
