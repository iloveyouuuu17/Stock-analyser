"""
heatmap_service.py — Feature 2: Nifty50 Sector-wide Sentiment Heatmap
Fetches 5 headlines per stock in parallel and runs FinBERT.
Results are cached in-memory for 30 minutes.
"""

import asyncio
import logging
import time
from typing import List, Dict

logger = logging.getLogger(__name__)

# Nifty 50 stocks with their sector mapping (as of 2025)
NIFTY50 = [
    {"ticker": "RELIANCE",    "name": "Reliance Industries",    "sector": "Energy"},
    {"ticker": "TCS",         "name": "Tata Consultancy Svcs",  "sector": "IT"},
    {"ticker": "HDFCBANK",    "name": "HDFC Bank",              "sector": "Banking"},
    {"ticker": "ICICIBANK",   "name": "ICICI Bank",             "sector": "Banking"},
    {"ticker": "INFY",        "name": "Infosys",                "sector": "IT"},
    {"ticker": "HINDUNILVR",  "name": "Hindustan Unilever",     "sector": "FMCG"},
    {"ticker": "ITC",         "name": "ITC Limited",            "sector": "FMCG"},
    {"ticker": "SBIN",        "name": "State Bank of India",    "sector": "Banking"},
    {"ticker": "BAJFINANCE",  "name": "Bajaj Finance",          "sector": "Finance"},
    {"ticker": "BHARTIARTL",  "name": "Bharti Airtel",          "sector": "Telecom"},
    {"ticker": "KOTAKBANK",   "name": "Kotak Mahindra Bank",    "sector": "Banking"},
    {"ticker": "LT",          "name": "Larsen & Toubro",        "sector": "Infra"},
    {"ticker": "HCLTECH",     "name": "HCL Technologies",       "sector": "IT"},
    {"ticker": "ASIANPAINT",  "name": "Asian Paints",           "sector": "Consumer"},
    {"ticker": "AXISBANK",    "name": "Axis Bank",              "sector": "Banking"},
    {"ticker": "WIPRO",       "name": "Wipro",                  "sector": "IT"},
    {"ticker": "MARUTI",      "name": "Maruti Suzuki",          "sector": "Auto"},
    {"ticker": "TATAMOTORS",  "name": "Tata Motors",            "sector": "Auto"},
    {"ticker": "SUNPHARMA",   "name": "Sun Pharmaceutical",     "sector": "Pharma"},
    {"ticker": "ULTRACEMCO",  "name": "UltraTech Cement",       "sector": "Materials"},
    {"ticker": "TITAN",       "name": "Titan Company",          "sector": "Consumer"},
    {"ticker": "NESTLEIND",   "name": "Nestle India",           "sector": "FMCG"},
    {"ticker": "POWERGRID",   "name": "Power Grid Corp",        "sector": "Utilities"},
    {"ticker": "NTPC",        "name": "NTPC Limited",           "sector": "Utilities"},
    {"ticker": "TECHM",       "name": "Tech Mahindra",          "sector": "IT"},
    {"ticker": "M&M",         "name": "Mahindra & Mahindra",    "sector": "Auto"},
    {"ticker": "JSWSTEEL",    "name": "JSW Steel",              "sector": "Metals"},
    {"ticker": "TATASTEEL",   "name": "Tata Steel",             "sector": "Metals"},
    {"ticker": "HINDALCO",    "name": "Hindalco Industries",    "sector": "Metals"},
    {"ticker": "ADANIENT",    "name": "Adani Enterprises",      "sector": "Conglomerate"},
    {"ticker": "ADANIPORTS",  "name": "Adani Ports",            "sector": "Infra"},
    {"ticker": "ADANIGREEN",  "name": "Adani Green Energy",     "sector": "Renewables"},
    {"ticker": "COALINDIA",   "name": "Coal India",             "sector": "Energy"},
    {"ticker": "GRASIM",      "name": "Grasim Industries",      "sector": "Materials"},
    {"ticker": "DIVISLAB",    "name": "Divi's Laboratories",    "sector": "Pharma"},
    {"ticker": "DRREDDY",     "name": "Dr. Reddy's Labs",       "sector": "Pharma"},
    {"ticker": "CIPLA",       "name": "Cipla",                  "sector": "Pharma"},
    {"ticker": "ONGC",        "name": "ONGC",                   "sector": "Energy"},
    {"ticker": "BPCL",        "name": "BPCL",                   "sector": "Energy"},
    {"ticker": "HEROMOTOCO",  "name": "Hero MotoCorp",          "sector": "Auto"},
    {"ticker": "EICHERMOT",   "name": "Eicher Motors",          "sector": "Auto"},
    {"ticker": "BAJAJ-AUTO",  "name": "Bajaj Auto",             "sector": "Auto"},
    {"ticker": "BAJAJFINSV",  "name": "Bajaj Finserv",          "sector": "Finance"},
    {"ticker": "HDFCLIFE",    "name": "HDFC Life Insurance",    "sector": "Insurance"},
    {"ticker": "SBILIFE",     "name": "SBI Life Insurance",     "sector": "Insurance"},
    {"ticker": "BRITANNIA",   "name": "Britannia Industries",   "sector": "FMCG"},
    {"ticker": "UPL",         "name": "UPL Limited",            "sector": "Agri"},
    {"ticker": "SHREECEM",    "name": "Shree Cement",           "sector": "Materials"},
    {"ticker": "INDUSINDBK",  "name": "IndusInd Bank",          "sector": "Banking"},
    {"ticker": "APOLLOHOSP",  "name": "Apollo Hospitals",       "sector": "Healthcare"},
]

# ── In-memory cache ───────────────────────────────────────────────────────────
_cache: dict = {"data": None, "timestamp": 0}
CACHE_TTL = 30 * 60  # 30 minutes


async def _get_single_stock_sentiment(stock_meta: dict, news_fn, sentiment_fn) -> dict:
    """Fetch news + run sentiment for one stock. Runs in a thread pool."""
    ticker = stock_meta["ticker"]
    name   = stock_meta["name"]

    try:
        news = await asyncio.to_thread(news_fn, ticker, name)
        top5 = news[:5]
        if not top5:
            return {**stock_meta, "sentiment_score": 0.0, "articles_count": 0}

        analyzed, summary = await asyncio.to_thread(sentiment_fn, top5)
        score = summary.get("weighted_score", 0.0)

        return {
            **stock_meta,
            "sentiment_score":  round(score, 4),
            "articles_count":   len(analyzed),
            "overall":          summary.get("overall", "Neutral"),
        }
    except Exception as e:
        logger.error(f"Heatmap: failed for {ticker}: {e}")
        return {**stock_meta, "sentiment_score": 0.0, "articles_count": 0}


async def get_heatmap(news_fn, sentiment_fn) -> List[Dict]:
    """
    Fetch heatmap data for all Nifty50 stocks in parallel.
    Result is cached for 30 minutes.
    """
    now = time.time()
    if _cache["data"] and (now - _cache["timestamp"]) < CACHE_TTL:
        logger.info("Returning cached heatmap data.")
        return _cache["data"]

    logger.info("Building fresh heatmap data for Nifty50...")
    tasks = [
        _get_single_stock_sentiment(stock, news_fn, sentiment_fn)
        for stock in NIFTY50
    ]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    _cache["data"]      = results
    _cache["timestamp"] = now
    return results
