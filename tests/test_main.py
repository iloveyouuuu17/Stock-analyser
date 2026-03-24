"""
tests/test_main.py - Unit tests for CLI argument parsing in main.py.
"""

import sys
import os
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import build_parser


class TestBuildParser:
    def test_no_args_gives_no_ticker(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert args.ticker is None

    def test_ticker_short(self):
        parser = build_parser()
        args = parser.parse_args(["-t", "RELIANCE"])
        assert args.ticker == "RELIANCE"

    def test_ticker_long(self):
        parser = build_parser()
        args = parser.parse_args(["--ticker", "TCS"])
        assert args.ticker == "TCS"

    def test_default_exchange_is_nse(self):
        parser = build_parser()
        args = parser.parse_args(["-t", "INFY"])
        assert args.exchange == "NSE"

    def test_exchange_bse(self):
        parser = build_parser()
        args = parser.parse_args(["-t", "INFY", "-x", "BSE"])
        assert args.exchange == "BSE"

    def test_default_period_is_1y(self):
        parser = build_parser()
        args = parser.parse_args(["-t", "SBIN"])
        assert args.period == "1y"

    def test_period_custom(self):
        parser = build_parser()
        args = parser.parse_args(["-t", "SBIN", "-p", "6mo"])
        assert args.period == "6mo"

    def test_chart_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-t", "WIPRO", "--chart"])
        assert args.chart is True

    def test_chart_default_false(self):
        parser = build_parser()
        args = parser.parse_args(["-t", "WIPRO"])
        assert args.chart is False

    def test_invalid_exchange_raises(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-t", "WIPRO", "-x", "NASDAQ"])
