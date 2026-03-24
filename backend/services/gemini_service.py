"""
gemini_service.py — Feature 1: Gemini AI Analyst Summary
Calls Gemini API with stock context to produce a professional 3-sentence summary.
"""
import os
import logging
import requests
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


def generate_analyst_summary(
    ticker: str,
    sentiment_score: float,
    sentiment_verdict: str,
    price_change_6m_pct: float,
    projected_change_pct: float,
    correlation_pct: Optional[float],
    divergences: List[Dict],
    top_headlines: List[str],
) -> Optional[str]:
    """
    Generate a 3-sentence analyst-style summary using Gemini API.
    Returns the summary string or None on failure.
    """
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set — skipping AI summary.")
        return None

    divergence_text = "None detected."
    if divergences:
        parts = []
        for d in divergences[:3]:
            parts.append(f"{d['date']}: {d['type']} (price {d['priceMove']}%)")
        divergence_text = "; ".join(parts)

    headlines_text = "\n".join(f"- {h}" for h in top_headlines[:3]) or "No headlines available."

    prompt = f"""You are a senior Indian equity analyst writing a brief note for institutional clients.

Stock: {ticker}
Current Sentiment: {sentiment_verdict} (weighted score: {sentiment_score:.2f})
6-Month Price Change: {price_change_6m_pct:+.1f}%
6-Month Projected Change (linear regression): {projected_change_pct:+.1f}%
Sentiment–Price Correlation: {f'{correlation_pct:.0f}%' if correlation_pct else 'Insufficient data'}
Smart Money Divergence Events: {divergence_text}

Top 3 Recent Headlines:
{headlines_text}

Write EXACTLY 3 sentences. Sound like a professional analyst note — concise, data-driven, forward-looking. Mention specific numbers. Do NOT use bullet points. Do NOT start with the ticker name."""

    try:
        resp = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 500,
                    "thinkingConfig": {"thinkingBudget": 0},
                }
            },
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text.strip()
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return None
