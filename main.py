"""
main.py - CLI entry point for the Indian Stock Analyzer.

Usage
-----
Analyze a single stock::

    python main.py --ticker RELIANCE --period 1y

Interactive mode::

    python main.py
"""

from __future__ import annotations

import argparse
import sys

from analyzer import StockAnalyzer
from portfolio import Portfolio
from utils import validate_period, NIFTY50_SYMBOLS


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="indian-stock-analyzer",
        description="Analyze Indian stocks listed on NSE / BSE.",
    )
    parser.add_argument(
        "--ticker", "-t",
        metavar="SYMBOL",
        help="Stock symbol to analyze (e.g. RELIANCE, TCS, INFY)",
    )
    parser.add_argument(
        "--exchange", "-x",
        metavar="EXCHANGE",
        default="NSE",
        choices=["NSE", "BSE"],
        help="Exchange: NSE (default) or BSE",
    )
    parser.add_argument(
        "--period", "-p",
        metavar="PERIOD",
        default="1y",
        help=(
            "Historical data period. "
            "Options: 1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max  (default: 1y)"
        ),
    )
    parser.add_argument(
        "--chart", "-c",
        action="store_true",
        help="Display a candlestick chart",
    )
    parser.add_argument(
        "--export", "-e",
        metavar="FILE",
        nargs="?",
        const="",
        help="Export analyzed data to CSV (optional filename)",
    )
    return parser


# ---------------------------------------------------------------------------
# Interactive menu
# ---------------------------------------------------------------------------

def interactive_menu() -> None:  # pragma: no cover
    print("\n╔══════════════════════════════════════╗")
    print("║    Indian Stock Analyzer  🇮🇳 📈       ║")
    print("╚══════════════════════════════════════╝\n")

    portfolio = Portfolio()

    while True:
        print("\nOptions:")
        print("  1. Analyze a stock")
        print("  2. Add stock to portfolio")
        print("  3. View portfolio summary")
        print("  4. List Nifty 50 symbols")
        print("  5. Exit")

        choice = input("\nEnter choice [1-5]: ").strip()

        if choice == "1":
            _interactive_analyze()
        elif choice == "2":
            _interactive_add_portfolio(portfolio)
        elif choice == "3":
            print("\n" + portfolio.summary())
        elif choice == "4":
            cols = 5
            for i, sym in enumerate(NIFTY50_SYMBOLS, start=1):
                end = "\n" if i % cols == 0 else "  "
                print(f"{sym:<16}", end=end)
            print()
        elif choice == "5":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")


def _interactive_analyze() -> None:  # pragma: no cover
    symbol = input("Enter stock symbol (e.g. RELIANCE): ").strip().upper()
    exchange = input("Exchange [NSE/BSE] (default NSE): ").strip().upper() or "NSE"
    period = input("Period [1y/6mo/3mo/...] (default 1y): ").strip() or "1y"

    if not validate_period(period):
        print(f"Invalid period '{period}'. Using default '1y'.")
        period = "1y"

    print(f"\nFetching data for {symbol} ({exchange}) - Period: {period} ...")
    try:
        analyzer = StockAnalyzer(symbol, exchange)
        analyzer.fetch_data(period=period)
        print(analyzer.summary())
    except ValueError as exc:
        print(f"Error: {exc}")
        return

    show_chart = input("\nShow chart? [y/N]: ").strip().lower()
    if show_chart == "y":
        analyzer.plot_chart()

    export = input("Export to CSV? [y/N]: ").strip().lower()
    if export == "y":
        path = analyzer.to_csv()
        print(f"Data exported to: {path}")


def _interactive_add_portfolio(portfolio: Portfolio) -> None:  # pragma: no cover
    symbol = input("Stock symbol: ").strip().upper()
    try:
        qty = int(input("Quantity (number of shares): ").strip())
        avg_price = float(input("Average purchase price (₹): ").strip())
    except ValueError:
        print("Invalid quantity or price.")
        return
    exchange = input("Exchange [NSE/BSE] (default NSE): ").strip().upper() or "NSE"
    portfolio.add(symbol, qty, avg_price, exchange)
    print(f"Added {qty} shares of {symbol} @ ₹{avg_price:.2f}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.ticker:
        # Non-interactive mode
        if not validate_period(args.period):
            parser.error(
                f"Invalid period '{args.period}'. "
                "Valid values: 1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max"
            )

        print(f"Fetching data for {args.ticker} ({args.exchange}) ...")
        try:
            analyzer = StockAnalyzer(args.ticker, args.exchange)
            analyzer.fetch_data(period=args.period)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

        print(analyzer.summary())

        if args.chart:
            analyzer.plot_chart()

        if args.export is not None:
            path = analyzer.to_csv(args.export or None)
            print(f"Data exported to: {path}")
    else:
        # Interactive mode
        interactive_menu()  # pragma: no cover


if __name__ == "__main__":
    main()
