from transformers import pipeline
import logging
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

# Event detection keywords
EVENT_KEYWORDS = {
    "Earnings":        ["results", "earnings", "quarterly", "profit", "loss", "revenue", "ebitda", "eps", "q1", "q2", "q3", "q4"],
    "Corporate Action":["merger", "acquisition", "buyout", "takeover", "stake", "restructuring"],
    "Board Meeting":   ["board meeting", "board decision", "agm", "egm"],
    "Dividend":        ["dividend", "bonus", "buyback", "share repurchase"],
}

# Load finbert globally so it's ready for requests
logger.info("Loading ProsusAI/finbert model... (this may take a moment)")
try:
    sentiment_pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")
    logger.info("Finbert model loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load finbert: {e}")
    sentiment_pipeline = None


def detect_event(title: str) -> Optional[str]:
    """Scan headline for event keywords, return event badge name or None."""
    title_lower = title.lower()
    for badge, keywords in EVENT_KEYWORDS.items():
        if any(kw in title_lower for kw in keywords):
            return badge
    return None


def analyze_sentiment(news_list: List[Dict]) -> Tuple[List[Dict], Dict]:
    """
    Runs confidence-weighted sentiment analysis on a list of news headlines.
    Batches all headlines in a single finBERT call for speed.
    Returns the enriched news list and an aggregated summary.
    """
    if not sentiment_pipeline:
        raise RuntimeError("Sentiment pipeline is not loaded.")

    if not news_list:
        return [], {"positive": 0, "negative": 0, "neutral": 0, "overall": "Neutral",
                    "weighted_score": 0.0}

    # Extract texts and event badges upfront
    texts = [item.get("title", "") or "" for item in news_list]
    event_badges = [detect_event(t) for t in texts]

    # --- Single batched inference call (much faster than looping) ---
    try:
        batch_results = sentiment_pipeline(texts, batch_size=16, truncation=True)
    except Exception as e:
        logger.error(f"Batch sentiment inference failed: {e}")
        # Fallback: classify one by one
        batch_results = []
        for text in texts:
            try:
                batch_results.append(sentiment_pipeline(text, truncation=True)[0])
            except Exception as inner_e:
                logger.error(f"Error classifying '{text}': {inner_e}")
                batch_results.append({"label": "neutral", "score": 0.0})

    analyzed_news = []
    summary_counts = {"positive": 0, "negative": 0, "neutral": 0}
    weighted_scores = []
    total_confidence = 0.0

    for idx, (item, result, event_badge) in enumerate(zip(news_list, batch_results, event_badges)):
        label = result['label']
        conf  = result['score']

        if label == 'positive':
            summary_counts["positive"] += 1
            signed_score = round(conf, 3)
        elif label == 'negative':
            summary_counts["negative"] += 1
            signed_score = -round(conf, 3)
        else:
            summary_counts["neutral"] += 1
            signed_score = 0.0

        weighted_scores.append(signed_score * conf)
        total_confidence += conf

        item_copy = item.copy()
        item_copy['sentiment_label'] = label.capitalize()
        item_copy['sentiment_score'] = signed_score
        item_copy['confidence']      = round(conf, 3)
        item_copy['chart_index']     = idx + 1
        item_copy['event_badge']     = event_badge

        analyzed_news.append(item_copy)

    weighted_avg = (
        sum(weighted_scores) / total_confidence if total_confidence > 0 else 0.0
    )

    pos = summary_counts['positive']
    neg = summary_counts['negative']
    neu = summary_counts['neutral']

    if weighted_avg > 0.1:
        verdict = "Bullish"
    elif weighted_avg < -0.1:
        verdict = "Bearish"
    else:
        verdict = "Neutral"

    summary = {
        **summary_counts,
        "overall": verdict,
        "weighted_score": round(weighted_avg, 4),
    }

    return analyzed_news, summary
