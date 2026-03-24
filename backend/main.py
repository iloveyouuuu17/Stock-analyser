from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import time
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import asyncio

# Load environment variables
load_dotenv()

from services.stock_service import get_stock_data, compute_correlation_and_divergences
from services.news_service import get_stock_news
from services.sentiment_service import analyze_sentiment
from services.heatmap_service import get_heatmap
from services.gemini_service import generate_analyst_summary
from services.nse_service import get_insider_signals, get_fii_dii
from services.strategy_service import simulate_strategy
from services.global_pulse_service import get_automated_global_pulse, analyze_macro_impact
from services.utils import parse_date

# In-memory cache: { TICKER: {"data": ..., "ts": float} }
_STOCK_CACHE: dict = {}
STOCK_CACHE_TTL = 15 * 60  # 15 minutes


class StrategyQuery(BaseModel):
    query: str
    ticker: str

class ScenarioQuery(BaseModel):
    scenario: str

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Indian Stock Sentiment Analyzer API")

# Check for API Keys
if not os.getenv("GEMINI_API_KEY"):
    logger.warning("GEMINI_API_KEY not set — Gemini AI summaries will be disabled.")

# Configure CORS for Vite frontend
_ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _compute_sentiment_momentum(analyzed_news):
    """Feature 2: Split headlines chronologically, compare averages."""
    if len(analyzed_news) < 4:
        return {"direction": "stable", "label": "→ Stable", "oldAvg": 0, "recentAvg": 0}

    mid = len(analyzed_news) // 2
    older  = analyzed_news[:mid]
    recent = analyzed_news[mid:]

    old_avg    = sum(a["sentiment_score"] for a in older)  / len(older)
    recent_avg = sum(a["sentiment_score"] for a in recent) / len(recent)

    threshold = abs(old_avg) * 0.1 if old_avg != 0 else 0.05

    if recent_avg > old_avg + threshold:
        return {"direction": "improving", "label": "↑ Improving", "oldAvg": round(old_avg, 3), "recentAvg": round(recent_avg, 3)}
    elif recent_avg < old_avg - threshold:
        return {"direction": "deteriorating", "label": "↓ Deteriorating", "oldAvg": round(old_avg, 3), "recentAvg": round(recent_avg, 3)}
    else:
        return {"direction": "stable", "label": "→ Stable", "oldAvg": round(old_avg, 3), "recentAvg": round(recent_avg, 3)}


def _compute_news_velocity(analyzed_news):
    """Feature 3: Compare headline count in last 24h vs 30-day daily average."""
    now = datetime.now(timezone.utc)
    cutoff_24h = now - timedelta(hours=24)

    timestamps = []
    count_24h = 0

    for article in analyzed_news:
        pub = article.get("published", "")
        date_str = parse_date(pub)
        if not date_str:
            continue
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            timestamps.append(dt)
            if dt >= cutoff_24h:
                count_24h += 1
        except Exception:
            continue

    if not timestamps:
        return {"count24h": 0, "avgDaily": 0, "surge": False}

    oldest = min(timestamps)
    span_days = max((now - oldest).days, 1)
    avg_daily = len(timestamps) / span_days

    surge = count_24h > (avg_daily * 2) and count_24h >= 3

    return {
        "count24h":  count_24h,
        "avgDaily":  round(avg_daily, 1),
        "surge":     surge,
    }


@app.get("/api/stock/{ticker}")
async def get_stock_analysis(ticker: str):
    logger.info(f"Received request for ticker: {ticker}")
    ticker = ticker.upper().strip()

    # Serve from cache if fresh
    cached = _STOCK_CACHE.get(ticker)
    if cached and (time.time() - cached["ts"]) < STOCK_CACHE_TTL:
        logger.info(f"Cache hit for {ticker}")
        return cached["data"]

    fetched_at = datetime.now(timezone.utc).isoformat()

    # 1. Fetch Stock Data
    try:
        stock_data = get_stock_data(ticker)
    except ValueError:
        raise HTTPException(status_code=404, detail="Ticker Not Found")
    except Exception as e:
        logger.error(f"Unexpected error fetching stock data for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching stock data")

    # 2. Fetch News
    try:
        news_articles = get_stock_news(ticker, stock_data.get('shortName', ticker))
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {e}")
        news_articles = []

    if not news_articles:
        raise HTTPException(status_code=404, detail="No News Found")

    # 3. Analyze Sentiment
    try:
        analyzed_news, sentiment_summary = analyze_sentiment(news_articles)
    except Exception as e:
        logger.error(f"Error analyzing sentiment for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Error analyzing sentiment")

    # 4. Pearson Correlation & Smart Money Divergences
    try:
        extra = compute_correlation_and_divergences(stock_data, analyzed_news)
    except Exception as e:
        logger.error(f"Correlation error for {ticker}: {e}")
        extra = {"sentimentPriceCorrelation": None, "smartMoneyDivergences": []}

    # Feature 2: Sentiment Momentum
    momentum = _compute_sentiment_momentum(analyzed_news)

    # Feature 3: News Velocity
    velocity = _compute_news_velocity(analyzed_news)

    # Feature 4: Insider Signals (graceful)
    insider_signals = []
    try:
        insider_signals = await asyncio.to_thread(
            get_insider_signals, ticker, sentiment_summary.get("weighted_score", 0)
        )
    except Exception as e:
        logger.warning(f"Insider signals skipped for {ticker}: {e}")

    # Feature 6: FII/DII (graceful)
    fii_dii = None
    try:
        fii_dii = await asyncio.to_thread(get_fii_dii)
    except Exception as e:
        logger.warning(f"FII/DII data skipped: {e}")

    # Feature 1: Gemini AI Summary (graceful)
    ai_summary = None
    try:
        top_headlines = [a["title"] for a in analyzed_news[:3]]
        ai_summary = await asyncio.to_thread(
            generate_analyst_summary,
            ticker,
            sentiment_summary.get("weighted_score", 0),
            sentiment_summary.get("overall", "Neutral"),
            stock_data.get("sixMonthChangePct", 0),
            stock_data.get("projectedChangePercent", 0),
            extra.get("sentimentPriceCorrelation"),
            extra.get("smartMoneyDivergences", []),
            top_headlines,
        )
    except Exception as e:
        logger.warning(f"Gemini summary skipped for {ticker}: {e}")

    # Strip internal fields
    stock_data.pop("_daily_pct", None)
    stock_data.pop("_hist_dates", None)

    result = {
        "ticker":                ticker,
        "stockInfo":             stock_data,
        "news":                  analyzed_news,
        "sentimentSummary":      sentiment_summary,
        "fetched_at":            fetched_at,
        "aiSummary":             ai_summary,
        "sentimentMomentum":     momentum,
        "newsVelocity":          velocity,
        "insiderSignals":        insider_signals,
        "fiiDii":                fii_dii,
        **extra,
    }
    _STOCK_CACHE[ticker] = {"data": result, "ts": time.time()}
    return result


@app.get("/api/heatmap")
async def heatmap_route():
    """Nifty50 sector heatmap with 30-minute cache."""
    try:
        data = await get_heatmap(get_stock_news, analyze_sentiment)
        # Also attach FII/DII data for the heatmap page
        fii_dii = None
        try:
            fii_dii = await asyncio.to_thread(get_fii_dii)
        except Exception:
            pass
        return {
            "heatmap":    data,
            "fiiDii":     fii_dii,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Heatmap error: {e}")
        raise HTTPException(status_code=500, detail="Error building heatmap")


@app.get("/api/fii-dii")
async def fii_dii_route():
    """Feature 6: FII/DII standalone endpoint."""
    try:
        data = await asyncio.to_thread(get_fii_dii)
        if not data:
            raise HTTPException(status_code=503, detail="FII/DII data unavailable")
        return {"fiiDii": data, "fetched_at": datetime.now(timezone.utc).isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"FII/DII error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching FII/DII data")


@app.get("/api/portfolio")
async def portfolio_route(tickers: str = Query(..., description="Comma-separated tickers")):
    """Portfolio sentiment — parallel fetch for multiple tickers."""
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if not ticker_list:
        raise HTTPException(status_code=400, detail="No tickers provided")
    if len(ticker_list) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 tickers per portfolio query")

    fetched_at = datetime.now(timezone.utc).isoformat()

    async def analyze_one(t: str):
        try:
            stock_data   = await asyncio.to_thread(get_stock_data, t)
            company_name = stock_data.get("shortName", t)
            news         = await asyncio.to_thread(get_stock_news, t, company_name)
            if not news:
                return {"ticker": t, "error": "No news found", "score": 0.0}
            analyzed, summary = await asyncio.to_thread(analyze_sentiment, news[:10])
            return {
                "ticker":   t,
                "company":  company_name,
                "score":    summary.get("weighted_score", 0.0),
                "overall":  summary.get("overall", "Neutral"),
                "positive": summary.get("positive", 0),
                "negative": summary.get("negative", 0),
                "neutral":  summary.get("neutral", 0),
            }
        except Exception as e:
            logger.error(f"Portfolio error for {t}: {e}")
            return {"ticker": t, "error": str(e), "score": 0.0}

    results = list(await asyncio.gather(*[analyze_one(t) for t in ticker_list]))

    valid = [r for r in results if "error" not in r]
    portfolio_score = round(sum(r["score"] for r in valid) / len(valid), 4) if valid else 0.0
    portfolio_verdict = "Bullish" if portfolio_score > 0.1 else ("Bearish" if portfolio_score < -0.1 else "Neutral")

    return {
        "tickers":          ticker_list,
        "stocks":           results,
        "portfolioScore":   portfolio_score,
        "portfolioVerdict": portfolio_verdict,
        "fetched_at":       fetched_at,
    }


@app.get("/api/watchlist/refresh")
async def watchlist_refresh(tickers: str = Query(..., description="Comma-separated tickers")):
    """Feature 8: Refresh sentiment scores for a watchlist in parallel."""
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if not ticker_list:
        raise HTTPException(status_code=400, detail="No tickers provided")
    if len(ticker_list) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 watchlist tickers")

    async def refresh_one(t: str):
        try:
            stock_data   = await asyncio.to_thread(get_stock_data, t)
            company_name = stock_data.get("shortName", t)
            price        = stock_data.get("currentPrice")
            change_pct   = stock_data.get("dailyChangePercent", 0)
            news         = await asyncio.to_thread(get_stock_news, t, company_name)
            if not news:
                return {"ticker": t, "company": company_name, "price": price, "changePct": change_pct,
                        "score": 0.0, "overall": "Neutral"}
            analyzed, summary = await asyncio.to_thread(analyze_sentiment, news[:5])
            return {
                "ticker":    t,
                "company":   company_name,
                "price":     price,
                "changePct": change_pct,
                "score":     summary.get("weighted_score", 0.0),
                "overall":   summary.get("overall", "Neutral"),
            }
        except Exception as e:
            logger.error(f"Watchlist refresh error for {t}: {e}")
            return {"ticker": t, "error": str(e), "score": 0.0}

    results = list(await asyncio.gather(*[refresh_one(t) for t in ticker_list]))
    return {"stocks": results, "fetched_at": datetime.now(timezone.utc).isoformat()}


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/global-pulse")
async def global_pulse_route():
    """Feature 4: Automated Global Pulse Impacts"""
    try:
        data = await asyncio.to_thread(get_automated_global_pulse)
        if not data:
            raise HTTPException(status_code=503, detail="AI analysis temporarily unavailable")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Global Pulse endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching global pulse")


@app.post("/api/global-pulse/query")
async def global_pulse_query(request: ScenarioQuery):
    """Feature 4: Manual What-if Query"""
    if not request.scenario.strip():
        raise HTTPException(status_code=400, detail="Scenario cannot be empty")
        
    try:
        data = await asyncio.to_thread(analyze_macro_impact, [], True, request.scenario.strip())
        if not data:
            raise HTTPException(status_code=503, detail="AI analysis temporarily unavailable")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Global Pulse query error: {e}")
        raise HTTPException(status_code=500, detail="Error simulating scenario")


@app.post("/api/strategy/simulate")
async def strategy_simulate(request: StrategyQuery):
    """Feature 3: AI Strategy Simulator"""
    ticker = request.ticker.upper().strip()
    try:
        # Fetch minimal fast context
        stock_data = await asyncio.to_thread(get_stock_data, ticker)
        company_name = stock_data.get('shortName', ticker)
        news_articles = await asyncio.to_thread(get_stock_news, ticker, company_name)
        
        analyzed_news, sentiment_summary = await asyncio.to_thread(analyze_sentiment, news_articles[:5])
        momentum = _compute_sentiment_momentum(analyzed_news)
        
        fii_dii = None
        try:
            fii_dii = await asyncio.to_thread(get_fii_dii)
        except: pass
        
        extra = await asyncio.to_thread(compute_correlation_and_divergences, stock_data, analyzed_news)
        
        context = {
            "price": f"₹{stock_data.get('currentPrice', 'N/A')}",
            "change_pct": round(stock_data.get("dailyChangePercent", 0), 2),
            "sentiment_verdict": sentiment_summary.get("overall", "Neutral"),
            "sentiment_score": round(sentiment_summary.get("weighted_score", 0), 2),
            "momentum": momentum.get("label", "Stable"),
            "six_month_change": round(stock_data.get("sixMonthChangePct", 0), 2),
            "projected_change": round(stock_data.get("projectedChangePercent", 0), 2),
            "beta": round(stock_data.get("beta", 1), 2) if stock_data.get("beta") else 'N/A',
            "fii_dii": "Net FII Flow: " + (fii_dii.get("fiiFlow", "Unknown") if fii_dii else "Unknown"),
            "divergences": str(extra.get("smartMoneyDivergences", [])),
            "headlines": "\\n".join(f"- {n['title']}" for n in analyzed_news[:3])
        }

        result = await asyncio.to_thread(simulate_strategy, request.query, ticker, context)
        if not result:
            raise HTTPException(status_code=503, detail="AI analysis temporarily unavailable")
        
        return result
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=404, detail="Ticker Not Found")
    except Exception as e:
        logger.error(f"Strategy endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Error generating strategy")
