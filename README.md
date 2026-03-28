# Stockey — Indian Stock Sentiment Analyzer

> Real-time NLP-powered sentiment intelligence for Nifty 50 stocks, built with FinBERT, Prophet, and Gemini AI.

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react)
![FinBERT](https://img.shields.io/badge/NLP-FinBERT-purple?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## What It Does

Stockey ingests live financial news from ET Markets and Yahoo Finance, runs every headline through ProsusAI/FinBERT for confidence-weighted sentiment scoring, and surfaces actionable market intelligence across a multi-tab React dashboard.

**The core pipeline:**

```
Live News (ET Markets RSS + Yahoo Finance)
        ↓
  FinBERT Sentiment Inference (batched, GPU/CPU)
        ↓
  Pearson Correlation (sentiment ↔ price returns)
        ↓
  Prophet Forecasting (6-month price projections)
        ↓
  Gemini 2.5 Flash (analyst-style summary)
        ↓
  React Dashboard (recharts, dark theme)
```

---

## Features

### Sentiment Engine
- **FinBERT NLP** — ProsusAI/finbert model running confidence-weighted multi-class classification (Bullish / Bearish / Neutral) on every headline
- **Sentiment Momentum** — Chronological split of headlines to detect improving vs deteriorating sentiment trends
- **News Velocity Surge** — Flags abnormal headline volume spikes (24h count vs 30-day daily average) as a volatility signal
- **Event Badge Detection** — Auto-tags headlines with Earnings, Dividend, Board Meeting, or Corporate Action badges via keyword matching

### Price Analysis
- **Prophet Forecasting** — Facebook Prophet model trained on 6 months of daily OHLCV data, outputting `yhat` / `yhat_lower` / `yhat_upper` confidence bands for the next 126 trading days
- **Linear Regression Fallback** — Graceful degradation to NumPy polyfit if Prophet is unavailable or dataset too small
- **Pearson Correlation** — Measures statistical alignment between sentiment scores and daily price returns, reported as a percentage accuracy signal
- **Smart Money Divergence** — Detects days where strong positive sentiment coincided with price drops (or vice versa), surfacing institutional behavior patterns

### Market Intelligence
- **Nifty 50 Heatmap** — Parallel async sentiment scoring across all 50 index stocks, grouped by sector, with 30-minute server-side cache
- **FII/DII Flow Tracker** — Live scrape of NSE's institutional activity endpoint, showing net foreign vs domestic institutional buying/selling
- **Insider Signal Detection** — Cross-references NSE bulk deal data with current sentiment; flags accumulation (institutional buying on negative sentiment) and distribution (selling on positive sentiment)
- **Global Pulse** — Automated macro event scanner using BBC Business RSS, fed into Gemini for sector-by-sector India market impact analysis with timeframe and confidence ratings
- **What-If Simulator** — Natural language scenario input ("US imposes H1B restrictions") with AI-generated sector impact table

### Strategy & Portfolio
- **AI Strategy Lab** — Ticker + natural language query ("Should I buy now?") → structured JSON response with recommendation, entry range, stop-loss, target, confidence, risks, and reasoning
- **Portfolio Sentiment** — Parallel sentiment scoring for up to 10 tickers simultaneously, with weighted aggregate portfolio verdict
- **Watchlist** — LocalStorage-persisted ticker list with 30-minute auto-refresh and sentiment shift alerts (bell icon when score moves >20 points)
- **Circuit Breaker Detection** — Real-time flag when current price is within 2% of NSE upper/lower circuit limits

### AI Summary
- **Gemini Analyst Note** — 3-sentence institutional-style summary generated per ticker, incorporating sentiment score, 6-month price change, projected change, correlation percentage, smart money divergence events, and top 3 headlines

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.11, Uvicorn, asyncio |
| NLP Model | ProsusAI/finbert (HuggingFace Transformers) |
| Forecasting | Facebook Prophet, NumPy (fallback) |
| Market Data | yfinance (.NS auto-append), NSE scraping |
| News | ET Markets RSS (feedparser), Yahoo Finance fallback |
| AI Summaries | Google Gemini 2.5 Flash API |
| Frontend | React 19, Vite, Tailwind CSS, Recharts |
| State | In-memory cache (15-min TTL per ticker, 30-min heatmap) |

---

## Project Structure

```
stockey/
├── backend/
│   ├── main.py                    # FastAPI app, cache layer, feature orchestration
│   ├── requirements.txt
│   └── services/
│       ├── stock_service.py       # yfinance, Prophet/linreg, Pearson, divergence
│       ├── news_service.py        # ET Markets RSS scraper + Yahoo fallback
│       ├── sentiment_service.py   # FinBERT pipeline, batch inference, event tagging
│       ├── heatmap_service.py     # Nifty 50 parallel async sentiment
│       ├── nse_service.py         # FII/DII tracker, bulk deals, insider signals
│       ├── gemini_service.py      # Analyst summary generation
│       ├── global_pulse_service.py# Macro RSS scanner + what-if simulator
│       ├── strategy_service.py    # AI strategy simulator
│       └── utils.py               # Date parsing utilities
└── frontend/
    ├── src/
    │   ├── App.jsx                # Tab routing, search, global state
    │   └── components/
    │       ├── Dashboard.jsx      # Main stock analysis view
    │       ├── Heatmap.jsx        # Nifty 50 sector heatmap
    │       ├── Portfolio.jsx      # Multi-ticker portfolio view
    │       ├── Watchlist.jsx      # Persisted watchlist with alerts
    │       ├── StrategyLab.jsx    # AI strategy simulator UI
    │       └── GlobalPulse.jsx    # Macro event tracker
    └── package.json
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Gemini API key (free tier works)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Add your GEMINI_API_KEY to .env

uvicorn main:app --reload --port 8000
```

First run downloads the FinBERT model (~500MB). Subsequent starts load from HuggingFace cache.

### Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/stock/{ticker}` | Full analysis for a single NSE ticker |
| GET | `/api/heatmap` | Nifty 50 sector sentiment heatmap |
| GET | `/api/fii-dii` | Today's FII/DII institutional flow data |
| GET | `/api/portfolio?tickers=A,B,C` | Parallel multi-ticker portfolio scoring |
| GET | `/api/watchlist/refresh?tickers=...` | Lightweight watchlist sentiment refresh |
| GET | `/api/global-pulse` | Automated macro impact analysis |
| POST | `/api/global-pulse/query` | Custom what-if scenario simulation |
| POST | `/api/strategy/simulate` | AI strategy recommendation |
| GET | `/api/health` | Health check |

**Example:**
```bash
curl http://localhost:8000/api/stock/RELIANCE
```

---

## How the Sentiment Score Works

Each headline gets a signed confidence score:

```
Positive label → score = +confidence  (e.g. +0.847)
Negative label → score = -confidence  (e.g. -0.923)
Neutral label  → score = 0.0
```

The weighted average across all headlines:

```
weighted_score = Σ(score × confidence) / Σ(confidence)
```

Thresholds: `> 0.1` = Bullish, `< -0.1` = Bearish, otherwise Neutral.

---

## Supported Tickers

Any NSE-listed stock ticker works (`.NS` is auto-appended). Also supports indices:

| Input | Resolves To |
|---|---|
| `RELIANCE` | RELIANCE.NS |
| `NIFTY 50` | ^NSEI |
| `SENSEX` | ^BSESN |
| `BANKNIFTY` | ^NSEBANK |
| `INDIA VIX` | ^INDIAVIX |

---

## Caching

| Resource | TTL |
|---|---|
| Per-ticker stock analysis | 15 minutes |
| Nifty 50 heatmap | 30 minutes |
| FII/DII data | 60 minutes |
| Bulk deals / insider signals | 60 minutes |
| Global Pulse (automated) | 2 hours |

---

## Disclaimer

This tool is for educational and research purposes only. Nothing here constitutes financial advice. Sentiment analysis models are imperfect. Always do your own research before making investment decisions.

---

## Author

**Rishabh Kapadia** — Founding Cohort, Mesa School of Business (BBA Entrepreneurship, Class of 2029)

[LinkedIn](https://linkedin.com/in/rishabhkapadia) · [Email](mailto:rishabh_kapadia@ug29.mesaschool.co)
