"""
nse_service.py — Features 4 & 6
- Bulk Deals from NSE (Insider Signal Detection)
- FII/DII daily activity tracker
Both cached for 60 minutes server-side.
"""
import logging
import time
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}

CACHE_TTL = 60 * 60  # 60 minutes

# ── Caches ────────────────────────────────────────────────────────────────────
_bulk_deals_cache: Dict = {"data": None, "timestamp": 0}
_fii_dii_cache: Dict = {"data": None, "timestamp": 0}


def _get_nse_session() -> requests.Session:
    """Create a session that first hits NSE homepage to get cookies."""
    session = requests.Session()
    session.headers.update(NSE_HEADERS)
    try:
        session.get("https://www.nseindia.com/", timeout=5)
    except Exception:
        pass
    return session


# ── Feature 4: Bulk Deals ─────────────────────────────────────────────────────

def get_bulk_deals() -> List[Dict]:
    """
    Fetch all bulk deals from NSE. Cached for 60 minutes.
    Returns list of deal dicts or empty list on failure.
    """
    now = time.time()
    if _bulk_deals_cache["data"] is not None and (now - _bulk_deals_cache["timestamp"]) < CACHE_TTL:
        return _bulk_deals_cache["data"]

    try:
        session = _get_nse_session()
        resp = session.get("https://www.nseindia.com/api/snapshot-capital-market-largedeal", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        deals = data.get("BLOCK_DEALS_DATA", []) + data.get("BULK_DEALS_DATA", [])
        _bulk_deals_cache["data"] = deals
        _bulk_deals_cache["timestamp"] = now
        logger.info(f"Fetched {len(deals)} bulk/block deals from NSE.")
        return deals
    except Exception as e:
        logger.warning(f"Could not fetch NSE bulk deals (will skip): {e}")
        return _bulk_deals_cache.get("data") or []


def get_insider_signals(ticker: str, sentiment_score: float) -> List[Dict]:
    """
    Feature 4: Cross-reference bulk deals with sentiment for a given ticker.
    Returns list of insider signal alerts.
    """
    deals = get_bulk_deals()
    if not deals:
        return []

    signals = []
    ticker_upper = ticker.upper().replace(".NS", "").replace(".BO", "")

    for deal in deals:
        symbol = (deal.get("symbol") or deal.get("SYMBOL") or "").upper()
        if symbol != ticker_upper:
            continue

        buy_sell = (deal.get("buySell") or deal.get("BUY_SELL") or "").upper()
        qty = deal.get("quantityTraded") or deal.get("QTY_TRD") or 0
        client = deal.get("clientName") or deal.get("CLIENT_NAME") or "Unknown"

        if buy_sell == "BUY" and sentiment_score < -0.3:
            signals.append({
                "type": "accumulation",
                "emoji": "🏦",
                "message": "Institutional Accumulation Detected — Smart Money Buying",
                "detail": f"{client} bought {qty:,} shares while sentiment was negative ({sentiment_score:.2f})",
            })
        elif buy_sell == "SELL" and sentiment_score > 0.3:
            signals.append({
                "type": "distribution",
                "emoji": "⚠️",
                "message": "Institutional Distribution — Smart Money Exiting",
                "detail": f"{client} sold {qty:,} shares while sentiment was positive ({sentiment_score:.2f})",
            })

    return signals[:5]  # cap at 5 most relevant


# ── Feature 6: FII/DII Activity ──────────────────────────────────────────────

def get_fii_dii() -> Optional[Dict]:
    """
    Fetch today's FII/DII net buy/sell data from NSE.
    Cached for 60 minutes. Returns dict or None on failure.
    """
    now = time.time()
    if _fii_dii_cache["data"] is not None and (now - _fii_dii_cache["timestamp"]) < CACHE_TTL:
        return _fii_dii_cache["data"]

    try:
        session = _get_nse_session()
        resp = session.get("https://www.nseindia.com/api/fiidiiTradeReact", timeout=10)
        resp.raise_for_status()
        raw = resp.json()

        # Parse the response — NSE returns a list of category entries
        result = {"fii": {}, "dii": {}, "date": None}

        for entry in raw:
            category = (entry.get("category") or "").upper()
            if "FII" in category or "FPI" in category:
                result["fii"] = {
                    "buyValue": entry.get("buyValue", 0),
                    "sellValue": entry.get("sellValue", 0),
                    "netValue": entry.get("netValue", 0),
                }
                result["date"] = entry.get("date", "")
            elif "DII" in category:
                result["dii"] = {
                    "buyValue": entry.get("buyValue", 0),
                    "sellValue": entry.get("sellValue", 0),
                    "netValue": entry.get("netValue", 0),
                }

        fii_net = result["fii"].get("netValue", 0)
        if isinstance(fii_net, str):
            fii_net = float(fii_net.replace(",", "")) if fii_net else 0
        result["fiiFlow"] = "IN" if fii_net > 0 else "OUT"

        _fii_dii_cache["data"] = result
        _fii_dii_cache["timestamp"] = now
        logger.info(f"Fetched FII/DII data: FII net={fii_net}")
        return result
    except Exception as e:
        logger.warning(f"Could not fetch FII/DII data (will skip): {e}")
        return _fii_dii_cache.get("data")
