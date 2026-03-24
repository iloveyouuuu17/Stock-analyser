import yfinance as yf
import logging
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import List, Dict
from services.utils import parse_date

logger = logging.getLogger(__name__)

try:
    from prophet import Prophet
    import pandas as pd
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logger.warning("Prophet not available, falling back to linear regression.")

# Map common index names to their Yahoo Finance ticker symbols
INDEX_MAPPING = {
    "NIFTY 50": "^NSEI",
    "NIFTY50":  "^NSEI",
    "NIFTY":    "^NSEI",
    "SENSEX":   "^BSESN",
    "BSE SENSEX": "^BSESN",
    "BANKNIFTY": "^NSEBANK",
    "NIFTY BANK": "^NSEBANK",
    "NIFTY IT":  "^CNXIT",
    "INDIA VIX": "^INDIAVIX"
}


def _ns_ticker(ticker: str) -> str:
    """Convert user input to the correct yfinance ticker symbol."""
    t = ticker.upper().strip()
    if t in INDEX_MAPPING:
        return INDEX_MAPPING[t]
    if t.startswith('^') or t.endswith('.BO') or t.endswith('.NS'):
        return t
    return f"{t}.NS"


def get_stock_data(ticker: str) -> dict:
    """
    Fetches the current price, 6-month history, projections, Pearson correlation
    and smart money divergence events for an Indian stock or index.
    """
    original_ticker = ticker
    ns_tick = _ns_ticker(ticker)

    logger.info(f"Fetching yfinance data for {ns_tick} (original: {original_ticker})")

    stock = yf.Ticker(ns_tick)
    hist  = stock.history(period="6mo", interval="1d")

    if hist.empty:
        raise ValueError("Ticker Not Found")

    info = stock.info

    # ── 1. History + Projection ───────────────────────────────────────────────
    closes = hist['Close'].dropna()
    daily_pct = hist['Close'].pct_change().dropna()
    dates  = closes.index

    if len(closes) > 1:
        use_prophet = PROPHET_AVAILABLE and len(closes) >= 30
        if use_prophet:
            try:
                # Prepare dataframe for Prophet
                df = pd.DataFrame({'ds': closes.index.tz_localize(None), 'y': closes.values})
                model = Prophet(daily_seasonality=True, yearly_seasonality=False, weekly_seasonality=True)
                model.fit(df)
                
                # 6-month projection (126 trading days)
                future = model.make_future_dataframe(periods=126, freq='B') 
                forecast = model.predict(future)
                
                # Separate history and projection
                # forecast['ds'] is datetime64[ns], df['ds'].max() as well
                max_hist_date = df['ds'].max()
                hist_forecast = forecast[forecast['ds'] <= max_hist_date]
                proj_forecast = forecast[forecast['ds'] > max_hist_date]
                
                history_chart_data = [
                    {
                        "date": dates[i].strftime('%Y-%m-%d'),
                        "price": round(closes.values[i], 2),
                        "trend": round(hist_forecast.iloc[i]['yhat'], 2) if i < len(hist_forecast) else None
                    }
                    for i in range(len(closes))
                ]
                
                future_chart_data = [
                    {
                        "date": row['ds'].strftime('%Y-%m-%d'),
                        "projectedPrice": round(row['yhat'], 2),
                        "projectedLower": round(row['yhat_lower'], 2),
                        "projectedUpper": round(row['yhat_upper'], 2)
                    }
                    for _, row in proj_forecast.iterrows()
                ]
                
                if len(future_chart_data) > 0:
                    projected_final_price = future_chart_data[-1]["projectedPrice"]
                    current_fit_price = history_chart_data[-1]["trend"] or closes.values[-1]
                    projected_change = projected_final_price - current_fit_price
                    projected_change_pct = (projected_change / current_fit_price * 100) if current_fit_price > 0 else 0
                else:
                    projected_change = 0
                    projected_change_pct = 0
            except Exception as e:
                logger.error(f"Prophet failed: {e}. Falling back to linear regression.")
                use_prophet = False

        # Fallback to linear regression if Prophet isn't available or failed
        if not use_prophet:
            x_vals = np.arange(len(closes))
            y_vals = closes.values
            m, c   = np.polyfit(x_vals, y_vals, 1)

            history_chart_data = [
                {
                    "date":  dates[i].strftime('%Y-%m-%d'),
                    "price": round(y_vals[i], 2),
                    "trend": round(m * i + c, 2)
                }
                for i in range(len(closes))
            ]

            future_days = 126
            last_date   = dates[-1]
            future_chart_data = [
                {
                    "date": (last_date + np.timedelta64(i, 'D')).strftime('%Y-%m-%d'),
                    "projectedPrice": round(m * (len(closes) - 1 + i) + c, 2),
                    "projectedLower": round(m * (len(closes) - 1 + i) + c, 2),
                    "projectedUpper": round(m * (len(closes) - 1 + i) + c, 2)
                }
                for i in range(1, future_days + 1)
            ]

            projected_final_price  = future_chart_data[-1]["projectedPrice"]
            current_fit_price      = m * (len(closes) - 1) + c
            projected_change       = projected_final_price - current_fit_price
            projected_change_pct   = (projected_change / current_fit_price * 100) if current_fit_price > 0 else 0
    else:
        history_chart_data    = []
        future_chart_data     = []
        projected_change      = 0
        projected_change_pct  = 0

    # ── 2. Daily Price & Basic Info ──────────────────────────────────────────
    current_price  = info.get('currentPrice') or info.get('regularMarketPrice') or hist['Close'].iloc[-1]
    previous_close = info.get('previousClose') or hist['Open'].iloc[-1]
    daily_change   = current_price - previous_close
    daily_change_pct = (daily_change / previous_close * 100) if previous_close else 0

    # ── Feature 5: Beta ──────────────────────────────────────────────────────
    beta = info.get('beta')

    # ── Feature 7: Circuit Breaker ───────────────────────────────────────────
    circuit_breaker = None
    if previous_close and current_price:
        upper_circuit = previous_close * 1.20
        lower_circuit = previous_close * 0.80
        if current_price >= upper_circuit * 0.98:
            circuit_breaker = {"type": "upper", "message": "🚨 Near Upper Circuit — Price Freeze Risk",
                               "circuit": round(upper_circuit, 2), "proximity": round((current_price / upper_circuit) * 100, 1)}
        elif current_price <= lower_circuit * 1.02:
            circuit_breaker = {"type": "lower", "message": "🚨 Near Lower Circuit — Price Freeze Risk",
                               "circuit": round(lower_circuit, 2), "proximity": round((current_price / lower_circuit) * 100, 1)}

    # ── 6-month price change % (for Gemini prompt) ───────────────────────────
    six_month_change_pct = 0.0
    if len(closes) > 1:
        six_month_change_pct = ((closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0]) * 100

    return {
        "ticker":     original_ticker,
        "ns_ticker":  ns_tick,
        "shortName":  info.get('shortName', ns_tick),
        "longName":   info.get('longName',  ns_tick),
        "currentPrice":   round(current_price, 2)  if current_price  else None,
        "previousClose":  round(previous_close, 2) if previous_close else None,
        "dailyChange":    round(daily_change, 2),
        "dailyChangePercent": round(daily_change_pct, 2),

        # Extended Info
        "fiftyTwoWeekHigh": info.get('fiftyTwoWeekHigh'),
        "fiftyTwoWeekLow":  info.get('fiftyTwoWeekLow'),
        "marketCap":        info.get('marketCap'),
        "peRatio":          info.get('trailingPE') or info.get('forwardPE'),
        "volume":           info.get('volume'),
        "averageVolume":    info.get('averageVolume'),
        "sector":           info.get('sector', 'N/A'),
        "industry":         info.get('industry', 'N/A'),
        "beta":             round(beta, 2) if beta else None,

        # Charts
        "history":               history_chart_data,
        "projection":            future_chart_data,
        "projectedChange":       round(projected_change, 2),
        "projectedChangePercent": round(projected_change_pct, 2),
        "sixMonthChangePct":     round(six_month_change_pct, 2),

        # Circuit Breaker
        "circuitBreaker":        circuit_breaker,

        # Raw daily returns for Pearson correlation (computed later in main.py after sentiment)
        "_daily_pct":  {d.strftime('%Y-%m-%d'): round(r, 6) for d, r in daily_pct.items()},
        "_hist_dates": [d.strftime('%Y-%m-%d') for d in dates],
    }


def compute_correlation_and_divergences(stock_data: dict, analyzed_news: List[Dict]) -> dict:
    """
    Feature 1: Pearson correlation between sentiment and price returns.
    Feature 4: Smart Money Divergence detection.

    Called from main.py AFTER sentiment analysis is complete.
    Returns {sentiment_price_correlation, smart_money_divergences}.
    """
    daily_pct   = stock_data.get("_daily_pct", {})
    hist_dates  = set(stock_data.get("_hist_dates", []))

    if not daily_pct or not analyzed_news:
        return {"sentimentPriceCorrelation": None, "smartMoneyDivergences": []}

    # ── Pearson Correlation ───────────────────────────────────────────────────
    # Match each news headline to the closest available trading day

    def closest_trading_day(date_str):
        """Walk back up to 5 days to find the nearest trading day in our history."""
        if not date_str:
            return None
        try:
            base = datetime.strptime(date_str, '%Y-%m-%d')
        except Exception:
            return None
        for delta in range(0, 6):
            candidate = (base - timedelta(days=delta)).strftime('%Y-%m-%d')
            if candidate in daily_pct:
                return candidate
        return None

    paired_sentiment = []
    paired_returns   = []

    for article in analyzed_news:
        raw_date  = article.get('published', '')
        date_str  = parse_date(raw_date)
        trade_day = closest_trading_day(date_str)
        sentiment = article.get('sentiment_score', 0)

        if trade_day and sentiment != 0:  # skip neutral headlines for signal quality
            paired_sentiment.append(sentiment)
            paired_returns.append(daily_pct[trade_day])

    corr_pct = None
    if len(paired_sentiment) >= 4:
        try:
            corr_matrix = np.corrcoef(paired_sentiment, paired_returns)
            raw_corr    = corr_matrix[0, 1]
            if not np.isnan(raw_corr):
                corr_pct = round(abs(raw_corr) * 100, 1)
        except Exception as e:
            logger.warning(f"Correlation calculation failed: {e}")

    # ── Smart Money Divergence ────────────────────────────────────────────────
    divergences = []
    HIGH_SENT   = 0.7
    LOW_SENT    = -0.7

    # Group sentiment scores by trading day
    day_sentiments: dict[str, list] = {}
    for article in analyzed_news:
        raw_date  = article.get('published', '')
        date_str  = parse_date(raw_date)
        trade_day = closest_trading_day(date_str)
        if trade_day:
            day_sentiments.setdefault(trade_day, []).append(
                article.get('sentiment_score', 0)
            )

    for day, scores in sorted(day_sentiments.items(), reverse=True):
        if day not in daily_pct:
            continue
        avg_sent   = sum(scores) / len(scores)
        price_move = daily_pct[day]

        divergence_type = None
        if avg_sent > HIGH_SENT and price_move < 0:
            divergence_type = "Positive Sentiment / Price Fell"
        elif avg_sent < LOW_SENT and price_move > 0:
            divergence_type = "Negative Sentiment / Price Rose"

        if divergence_type:
            divergences.append({
                "date":       day,
                "type":       divergence_type,
                "sentiment":  round(avg_sent, 3),
                "priceMove":  round(price_move * 100, 2),   # as %
            })

        if len(divergences) >= 3:
            break

    return {
        "sentimentPriceCorrelation": corr_pct,
        "smartMoneyDivergences":     divergences,
    }
