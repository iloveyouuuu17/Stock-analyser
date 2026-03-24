import feedparser
import yfinance as yf
from bs4 import BeautifulSoup
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# ET Markets feeds
RSS_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://economictimes.indiatimes.com/company/rssfeeds/2143670.cms"
]

def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    try:
        soup = BeautifulSoup(raw_html, "lxml")
        return soup.get_text(separator=" ").strip()
    except Exception:
        return raw_html

def get_stock_news(ticker: str, company_name: str) -> List[Dict]:
    """
    Fetches news from ET Markets RSS, filtering by ticker or company name.
    Falls back to Yahoo Finance if fewer than 5 headlines found.
    """
    logger.info(f"Fetching ET Markets news for {ticker} ({company_name})")
    
    ticker = ticker.upper()
    search_terms = {ticker.lower()}
    
    # Add first word of company name as a search term if it exists and > 2 chars
    if company_name:
        first_word = company_name.split()[0].lower()
        if len(first_word) > 2:
            search_terms.add(first_word)
            
    # Clean up empty search terms just in case
    search_terms = {t for t in search_terms if t}
            
    news_items = []
    seen_titles = set()
    
    # 1. Try ET Markets
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.get('title', '')
                summary = clean_html(entry.get('summary', ''))
                
                # Check for match
                text_to_search = f"{title} {summary}".lower()
                if any(term in text_to_search for term in search_terms):
                    if title not in seen_titles:
                        seen_titles.add(title)
                        news_items.append({
                            "title": title,
                            "summary": summary,
                            "link": entry.get('link', ''),
                            "published": entry.get('published', ''),
                            "source": "ET Markets"
                        })
        except Exception as e:
            logger.error(f"Error parsing RSS {feed_url}: {e}")
            
    # 2. Fallback to Yahoo if < 5 items
    if len(news_items) < 5:
        logger.info(f"Only {len(news_items)} ET articles found. Falling back to Yahoo Finance.")
        ns_ticker = ticker if ticker.endswith('.NS') else f"{ticker}.NS"
        try:
            stock = yf.Ticker(ns_ticker)
            yf_news = stock.news
            for item in yf_news:
                # yfinance returns nested dictionaries in recent versions
                content = item.get('content', item) if isinstance(item, dict) else item
                title = content.get('title', '')
                
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    news_items.append({
                        "title": title,
                        "summary": content.get('summary', ''),
                        "link": content.get('clickThroughUrl', {}).get('url') or content.get('link', ''),
                        "published": content.get('pubDate', content.get('providerPublishTime', '')),
                        "source": content.get('provider', {}).get('displayName', 'Yahoo Finance')
                    })
        except Exception as e:
            logger.error(f"Error fetching Yahoo news: {e}")
            
    # Return at most 20 recent articles to keep latency reasonable for the model
    return news_items[:20]
