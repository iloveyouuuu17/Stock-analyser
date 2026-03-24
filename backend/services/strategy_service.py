import os
import logging
import requests
import json
from typing import Optional, Dict

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

def simulate_strategy(user_query: str, ticker: str, stock_context: Dict) -> Optional[Dict]:
    """
    Feature 3: AI Strategy Simulator
    Uses Gemini to provide a recommended trading strategy based on user query and stock context.
    Returns a structured dict or None if API fails.
    """
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set — skipping strategy simulation.")
        return None
        
    prompt = f"""You are a professional SEBI-registered equity analyst assistant.
A user has asked for strategic advice regarding the Indian stock: {ticker}.
User Query: "{user_query}"

Analyze this query based on the following real-time data context:
Current Price: {stock_context.get('price')}
Daily Change: {stock_context.get('change_pct')}%
Overall Sentiment: {stock_context.get('sentiment_verdict')} (Score: {stock_context.get('sentiment_score')})
Sentiment Momentum: {stock_context.get('momentum')}
6-Month Price Change: {stock_context.get('six_month_change')}%
Projected 6-Month Change: {stock_context.get('projected_change')}%
Stock Beta: {stock_context.get('beta', 'N/A')}
Recent Institutional Activity (FII/DII): {stock_context.get('fii_dii')}
Recent Smart Money Divergences: {stock_context.get('divergences')}

Top Recent Headlines:
{stock_context.get('headlines')}

Based ONLY on this data, return a JSON response answering the user's query and providing a clear strategy. 
The JSON must strictly match this structure with no markdown formatting or backticks outside the JSON:
{{
  "recommendation": "Buy" | "Sell" | "Hold" | "Wait",
  "entry_range": "e.g., ₹1400 - ₹1450",
  "stop_loss": "e.g., ₹1350",
  "target_price": "e.g., ₹1600",
  "risks": ["Risk 1", "Risk 2"],
  "confidence": "Low" | "Medium" | "High",
  "reasoning": "A brief explanation of why this strategy is recommended based on the user's query and the data provided."
}}
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
        return json.loads(text.strip())
    except Exception as e:
        logger.error(f"Strategy simulation API error: {e}")
        return None
