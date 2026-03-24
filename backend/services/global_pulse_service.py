import os
import time
import logging
import requests
import json
import xml.etree.ElementTree as ET
from typing import Optional, Dict

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

MACRO_KEYWORDS = [
    "war", "sanctions", "oil", "fed rate", "dollar", "china", 
    "us tariff", "recession", "opec", "inflation", "interest rate",
    "fomc", "yield", "geopolitic"
]

CACHE_TTL = 2 * 60 * 60  # 2 hours
_global_pulse_cache = {"data": None, "timestamp": 0}

def fetch_macro_headlines():
    """Fetches BBC Business RSS and filters by macro keywords."""
    url = "http://feeds.bbci.co.uk/news/business/rss.xml"
    headlines = []
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        
        for item in root.findall(".//item"):
            title = item.find('title').text if item.find('title') is not None else ""
            desc = item.find('description').text if item.find('description') is not None else ""
            
            text_to_check = f"{title} {desc}".lower()
            if any(kw in text_to_check for kw in MACRO_KEYWORDS):
                headlines.append(title)
                if len(headlines) >= 10:
                    break
    except Exception as e:
        logger.warning(f"Failed to fetch/parse macro RSS: {e}")
        
    return headlines

def analyze_macro_impact(headlines: list, is_manual_query: bool = False, manual_query: str = "") -> Optional[Dict]:
    """Uses Gemini to analyze macro events and return a sector-impact JSON."""
    if not GEMINI_API_KEY:
        return None
        
    if is_manual_query:
        context_text = f"User Scenario/Query: {manual_query}"
    else:
        if not headlines:
            headlines = ["Global markets remain calm with no major macroeconomic shifts reported today."]
        context_text = "Recent Global Macro Headlines:\n" + "\n".join(f"- {h}" for h in headlines)
        
    prompt = f"""You are a senior macroeconomist and equity strategist for the Indian Stock Market.

{context_text}

Analyze the likely impact of these events/scenario on the Indian stock markets.
Return a JSON array of objects representing the sector by sector impact. 
Focus only on the most affected sectors (e.g., IT, Oil & Gas, Banking, Auto, Pharma, FMCG, Metals).

The JSON must be an array of objects matching this exact structure:
[
  {{
    "sector": "Sector Name",
    "impact": "Positive" | "Negative" | "Neutral",
    "timeframe": "1 week" | "1 month" | "3 months",
    "confidence": "Low" | "Medium" | "High",
    "reason": "One short sentence explaining why."
  }}
]

Output ONLY the raw JSON array. Do not include markdown blocks or backticks.
"""

    try:
        resp = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "response_mime_type": "application/json",
                    "maxOutputTokens": 2000,
                    "thinkingConfig": {"thinkingBudget": 0},
                }
            },
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text.strip())
        return {"impacts": result, "source": "Manual Query" if is_manual_query else "Automated RSS (BBC)"}
    except Exception as e:
        logger.error(f"Global Pulse AI error: {e}")
        return None

def get_automated_global_pulse() -> Optional[Dict]:
    """Returns cached global pulse data or regenerates it."""
    now = time.time()
    if _global_pulse_cache["data"] and (now - _global_pulse_cache["timestamp"]) < CACHE_TTL:
        return _global_pulse_cache["data"]
        
    headlines = fetch_macro_headlines()
    analysis = analyze_macro_impact(headlines)
    
    if analysis:
        analysis["fetched_at"] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))
        _global_pulse_cache["data"] = analysis
        _global_pulse_cache["timestamp"] = now
        
    return analysis
