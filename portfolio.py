"""
portfolio.py - Simple portfolio tracker for Indian stocks.
"""

from __future__ import annotations

import pandas as pd
from tabulate import tabulate

from analyzer import StockAnalyzer


class Portfolio:
    """Track a collection of Indian stock holdings."""

    def __init__(self):
        # holdings: {symbol: {"qty": int, "avg_price": float, "exchange": str}}
        self._holdings: dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Mutating operations
    # ------------------------------------------------------------------

    def add(self, symbol: str, qty: int, avg_price: float, exchange: str = "NSE") -> None:
        """Add or update a holding.

        Parameters
        ----------
        symbol    : Stock symbol, e.g. ``"RELIANCE"``
        qty       : Number of shares held
        avg_price : Average purchase price per share (₹)
        exchange  : ``"NSE"`` or ``"BSE"``
        """
        symbol = symbol.upper()
        self._holdings[symbol] = {
            "qty": qty,
            "avg_price": avg_price,
            "exchange": exchange,
        }

    def remove(self, symbol: str) -> None:
        """Remove a holding from the portfolio."""
        self._holdings.pop(symbol.upper(), None)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def summary(self) -> str:
        """Fetch current prices and return a formatted portfolio table."""
        if not self._holdings:
            return "Portfolio is empty."

        rows = []
        total_invested = 0.0
        total_current = 0.0

        for symbol, holding in self._holdings.items():
            try:
                analyzer = StockAnalyzer(symbol, holding["exchange"])
                analyzer.fetch_data(period="5d")
                current_price = analyzer._data["Close"].iloc[-1]
            except Exception:
                current_price = float("nan")

            qty = holding["qty"]
            avg = holding["avg_price"]
            invested = qty * avg
            current = qty * current_price
            pnl = current - invested
            pnl_pct = (pnl / invested) * 100 if invested else float("nan")

            pnl_display = "N/A"
            if not pd.isna(pnl):
                arrow = "▲" if pnl >= 0 else "▼"
                pnl_display = f"{arrow} ₹{abs(pnl):,.2f} ({pnl_pct:+.2f}%)"

            rows.append([
                symbol,
                qty,
                f"₹{avg:.2f}",
                f"₹{current_price:.2f}" if not pd.isna(current_price) else "N/A",
                f"₹{invested:,.2f}",
                f"₹{current:,.2f}" if not pd.isna(current) else "N/A",
                pnl_display,
            ])

            if not pd.isna(invested):
                total_invested += invested
            if not pd.isna(current):
                total_current += current

        total_pnl = total_current - total_invested
        total_pnl_pct = (total_pnl / total_invested) * 100 if total_invested else 0

        headers = ["Symbol", "Qty", "Avg Price", "LTP", "Invested", "Current", "P&L"]
        table = tabulate(rows, headers=headers, tablefmt="rounded_outline")

        footer = (
            f"\n  Total Invested : ₹{total_invested:,.2f}"
            f"\n  Current Value  : ₹{total_current:,.2f}"
            f"\n  Overall P&L    : {'▲' if total_pnl >= 0 else '▼'} "
            f"₹{abs(total_pnl):,.2f} ({total_pnl_pct:+.2f}%)"
        )
        return table + footer

    def to_dataframe(self) -> pd.DataFrame:
        """Return holdings as a DataFrame (no live price fetch)."""
        if not self._holdings:
            return pd.DataFrame()
        rows = [
            {"Symbol": sym, **data}
            for sym, data in self._holdings.items()
        ]
        return pd.DataFrame(rows)
