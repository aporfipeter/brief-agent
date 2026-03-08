import json
import html
import logging
import urllib.parse
from datetime import datetime, timezone

import feedparser
import requests

logger = logging.getLogger(__name__)

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
    try:
        with open("watchlist.json") as f:
            return json.load(f)["watchlist"]
    except Exception:
        logger.exception("Failed to load watchlist")
        return []
    
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

def render_brief_md(brief: dict, max_news_per_ticker: int = 3, top_n: int = 5) -> str:
    lines = []
    lines.append(f"## Morning Stock Brief")
    lines.append(f"_Generated: {brief['generated_at']}_")
    lines.append("")

    watch = brief.get("watch", [])
    if not watch:
        return "\n".join(lines + ["(No watchlist items.)"])

    # Top movers
    top = watch[:top_n]
    lines.append("### Top movers")
    for s in top:
        p = s["price"]
        pct = p["pct_change_1d"]
        close = p["close"]
        sig = ", ".join(s.get("signals", [])) or "—"
        lines.append(f"- **{s['ticker']}**: {pct:+.2f}% (close {close}) — _{sig}_")
    lines.append("")

    # Detail per ticker
    lines.append("### Details")
    for s in watch:
        p = s["price"]
        pct = p["pct_change_1d"]
        close = p["close"]
        date = p["date"]
        sigs = s.get("signals", [])
        sig = ", ".join(sigs) if sigs else "—"

        lines.append(f"**{s['ticker']}** — {pct:+.2f}% (close {close}, {date})")
        lines.append(f"- Signals: {sig}")

        news = s.get("news", [])
        if news:
            lines.append("- Headlines:")
            for item in news[:max_news_per_ticker]:
                title = item.get("title") or "(no title)"
                link = item.get("link")
                if link:
                    lines.append(f"  - [{title}]({link})")
                else:
                    lines.append(f"  - {title}")
        else:
            lines.append("- Headlines: (none)")

        lines.append("")  # blank line between tickers

    return "\n".join(lines)

def render_brief_html(brief: dict, max_news_per_ticker: int = 3, top_n: int = 5) -> str:
    esc = html.escape
    lines = []

    lines.append(f"<b>Morning Stock Brief</b>")
    lines.append(f"<i>Generated: {esc(brief['generated_at'])}</i>")
    lines.append("")

    watch = brief.get("watch", [])
    if not watch:
        return "\n".join(lines + ["(No watchlist items.)"])

    top = watch[:top_n]
    lines.append("<b>Top movers</b>")
    for s in top:
        p = s["price"]
        pct = p["pct_change_1d"]
        close = p["close"]
        sig = ", ".join(s.get("signals", [])) or "—"
        lines.append(f"• <b>{esc(s['ticker'])}</b>: {pct:+.2f}% (close {close}) — <i>{esc(sig)}</i>")
    lines.append("")

    lines.append("<b>Details</b>")
    for s in watch:
        p = s["price"]
        pct = p["pct_change_1d"]
        close = p["close"]
        date = p["date"]
        sigs = s.get("signals", [])
        sig = ", ".join(sigs) if sigs else "—"

        lines.append(f"<b>{esc(s['ticker'])}</b> — {pct:+.2f}% (close {close}, {esc(date)})")
        lines.append(f"Signals: <i>{esc(sig)}</i>")

        news = s.get("news", [])
        if news:
            lines.append("Headlines:")
            for item in news[:max_news_per_ticker]:
                title = esc(item.get("title") or "(no title)")
                link = item.get("link")
                if link:
                    lines.append(f'• <a href="{esc(link)}">{title}</a>')
                else:
                    lines.append(f"• {title}")
        else:
            lines.append("Headlines: (none)")

        lines.append("")  # spacer

    return "\n".join(lines)


if __name__ == "__main__":
    brief = build_brief()
    print(json.dumps(brief, indent=2))
    print("\n" + "=" * 60 + "\n")
    print(render_brief_md(brief))