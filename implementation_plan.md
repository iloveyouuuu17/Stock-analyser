# Build an Indian Stock Sentiment Analyzer

This document outlines the architecture and steps to build a full-stack Indian Stock Sentiment Analyzer that takes a stock ticker, fetches corresponding news from ET Markets RSS feed, analyzes sentiment over the headlines using finBERT, and displays a modern dashboard with stock data from yfinance.

## User Review Required
> [!IMPORTANT]
> The general ET Markets RSS feeds encompass overall market news. We will fetch standard ET news feeds (e.g., Markets, Company) and filter headlines for the requested stock. If no recent news is found for a less popular stock in the recent feed, the sentiment analysis might be sparse or fallback to general market sentiment. Please let me know if this behavior is acceptable or if you'd prefer falling back to Yahoo Finance news for the specific ticker when ET Markets yields no recent results.

## Proposed Changes

### Backend Setup (FastAPI + Python)
The backend will be responsible for orchestrating external APIs and running the HuggingFace NLP model. We will isolate the ML model loading to run efficiently.

#### [NEW] `backend/requirements.txt`
Dependencies including `fastapi`, `uvicorn`, `yfinance`, `transformers`, `torch`, `feedparser`, `beautifulsoup4`, `pydantic`, `flask-cors` (or fastapi cors).

#### [NEW] `backend/main.py`
The main FastAPI entrypoint exposing `GET /api/stock/{ticker}` and configuring CORS.

#### [NEW] `backend/services/stock_service.py`
Fetch stock price and meta info using `yfinance`. Will automatically append `.NS` for NSE listing if not provided.

#### [NEW] `backend/services/news_service.py`
Fetch XML from ET Markets RSS feeds (e.g. https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms, https://economictimes.indiatimes.com/company/rssfeeds/2143670.cms) and parse out headlines. Filter items containing the stock name or ticker. 

#### [NEW] `backend/services/sentiment_service.py`
Load `ProsusAI/finbert` using HuggingFace `transformers` pipeline. Will parse headlines from `news_service` and classify as Positive, Negative, or Neutral along with confidence scores.

### Frontend Setup (React + Vite + TailwindCSS)
The frontend will visually present the findings using a slick, modern dark theme context.

#### [NEW] `frontend/package.json`
Vite React app dependencies, adding `tailwindcss`, `lucide-react` (icons), `recharts` (for sentiment breakdown charts), `axios`.

#### [NEW] `frontend/src/App.jsx`
Main layout wrapped in a dark theme container with the search bar and dashboard display state.

#### [NEW] `frontend/src/components/Search.jsx`
Input component to accept the NSE stock ticker (e.g., RELIANCE, TCS).

#### [NEW] `frontend/src/components/Dashboard.jsx`
The main visual container consisting of:
- **Price Card**: Current value, daily change.
- **Verdict Card**: Overall Sentiment (Bullish/Bearish/Neutral).
- **Sentiment Chart**: Graphical representation of positive, negative, neutral distribution (using recharts).
- **News List**: Feed of recent headlines colored by their respective sentiment score (Green for Positive, Red for Negative, Gray for Neutral).

## Verification Plan
### Automated Tests
- Running the backend and verifying `/api/stock/RELIANCE` returns valid yfinance data, news articles, and sentiment scores.
- Running the frontend and making sure components render without error using `npm run dev`.
### Manual Verification
- Testing user flow in browser: Open app, type 'TCS', observe the loading state, and verify the resulting dashboard contains legitimate information. Verify the UI matches a dark-themed, modern aesthetic that looks premium.
