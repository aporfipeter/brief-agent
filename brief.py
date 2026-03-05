import json
import urllib.parse
from datetime import datetime, timezone

import feedparser
import requests


def fetch_stooq_daily_close(ticker: str):
    url = f"https://stooq.com/q/d/l/?s={ticker}&i=d"
    r = requests.get(url, timeout=20)
    r.raise_for_status()

    lines = r.text.strip().splitlines()
    if len(lines) < 3:
        raise ValueError(f"Not enough price rows returned for {ticker}")

    header = lines[0].split(",")
    close_idx = header.index("Close")

    prev = lines[-2].split(",")
    last = lines[-1].split(",")

    prev_close = float(prev[close_idx])
    last_close = float(last[close_idx])
    pct = (last_close - prev_close) / prev_close * 100.0

    return {
        "ticker": ticker,
        "date": last[0],
        "close": last_close,
        "pct_change_1d": round(pct, 2),
    }


def fetch_google_news_rss(query: str, limit: int = 4):
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)

    items = []
    for e in feed.entries[:limit]:
        items.append(
            {
                "title": e.get("title"),
                "link": e.get("link"),
            }
        )
    return items


def load_watchlist():
    with open("watchlist.json", "r") as f:
        return json.load(f)["watchlist"]
    
def enrich_with_signals(stock):
    pct = stock["price"]["pct_change_1d"]
    news_count = len(stock["news"])

    signals = []

    # Volatility threshold
    if abs(pct) >= 3:
        signals.append("HIGH_VOLATILITY")
    elif abs(pct) >= 1.5:
        signals.append("MODERATE_MOVE")

    # News intensity
    if news_count >= 6:
        signals.append("HEAVY_NEWS_FLOW")
    elif news_count == 0:
        signals.append("NO_NEWS")

    stock["signals"] = signals
    return stock


def build_brief():
    watchlist = load_watchlist()

    results = []

    for item in watchlist:
        ticker = item["ticker"]
        hint = item.get("news_hint")

        price = fetch_stooq_daily_close(ticker)
        news = fetch_google_news_rss(hint or ticker)

        stock = {
            "ticker": ticker,
            "price": price,
            "news": news
        }
        stock = enrich_with_signals(stock)
        results.append(stock)

    # sort by biggest absolute move
    results.sort(key=lambda x: abs(x["price"]["pct_change_1d"]), reverse=True)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "watch": results
    }


if __name__ == "__main__":
    brief = build_brief()
    print(json.dumps(brief, indent=2))