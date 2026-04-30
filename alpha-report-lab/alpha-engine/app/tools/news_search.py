"""Mock news and sentiment tools."""
from __future__ import annotations

import hashlib
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List

from app.models.schemas import AnalystRatings, Headline, SentimentData

logger = logging.getLogger(__name__)

TICKER_HEADLINES: Dict[str, List[dict]] = {
    "AAPL": [
        {"title": "Apple Unveils New iPhone Lineup with Enhanced AI Features", "sentiment": "positive"},
        {"title": "Apple Services Revenue Hits All-Time High in Q2", "sentiment": "positive"},
        {"title": "Regulatory Scrutiny Intensifies for Apple App Store Practices", "sentiment": "negative"},
        {"title": "Apple Expands Vision Pro Availability to New Markets", "sentiment": "positive"},
        {"title": "Analysts Raise Apple Price Target on AI Strategy", "sentiment": "positive"},
        {"title": "China iPhone Sales Show Signs of Weakness", "sentiment": "negative"},
    ],
    "MSFT": [
        {"title": "Microsoft Azure Reports 30% Growth, AI Workloads Surge", "sentiment": "positive"},
        {"title": "Copilot Adoption Accelerates Across Enterprise Customers", "sentiment": "positive"},
        {"title": "OpenAI Partnership Delivers New Enterprise Features", "sentiment": "positive"},
        {"title": "FTC Reviews Microsoft's AI Partnerships", "sentiment": "negative"},
        {"title": "Microsoft Announces Record Cloud Capex for Next Fiscal Year", "sentiment": "neutral"},
    ],
    "NVDA": [
        {"title": "NVIDIA Reports Record Data Center Revenue, AI Demand Surges", "sentiment": "positive"},
        {"title": "Blackwell GPU Ramp Exceeds Wall Street Expectations", "sentiment": "positive"},
        {"title": "Hyperscalers Continue Massive AI Infrastructure Spending", "sentiment": "positive"},
        {"title": "Competition from AMD and Custom ASICs Increases", "sentiment": "negative"},
        {"title": "NVIDIA Announces New Inference Platform for Enterprise AI", "sentiment": "positive"},
        {"title": "China Export Restrictions Weigh on Outlook", "sentiment": "negative"},
    ],
    "GOOGL": [
        {"title": "Google Cloud Growth Accelerates on AI Workloads", "sentiment": "positive"},
        {"title": "YouTube Ad Revenue Beats Estimates on Shorts Monetization", "sentiment": "positive"},
        {"title": "Gemini Models Show Strong Benchmark Performance", "sentiment": "positive"},
        {"title": "Antitrust Ruling Forces Changes to Search Practices", "sentiment": "negative"},
    ],
    "AMZN": [
        {"title": "AWS Operating Margin Expands to Record Levels", "sentiment": "positive"},
        {"title": "Amazon Prime Day Breaks Sales Records", "sentiment": "positive"},
        {"title": "Advertising Business Continues to Outpace Industry", "sentiment": "positive"},
        {"title": "FTC Lawsuit Progresses to Discovery Phase", "sentiment": "negative"},
    ],
    "META": [
        {"title": "Meta's Ad Revenue Accelerates on AI-Driven Targeting", "sentiment": "positive"},
        {"title": "Reality Labs Losses Widen on AR/VR Investment", "sentiment": "negative"},
        {"title": "Llama 3 Open Source Release Drives Developer Adoption", "sentiment": "positive"},
        {"title": "Instagram User Engagement Hits All-Time High", "sentiment": "positive"},
    ],
    "TSLA": [
        {"title": "Tesla Delivers Below Analyst Estimates in Latest Quarter", "sentiment": "negative"},
        {"title": "Robotaxi Reveal Disappoints Investors", "sentiment": "negative"},
        {"title": "FSD v13 Shows Significant Improvements in Testing", "sentiment": "positive"},
        {"title": "EV Price Competition in China Pressures Margins", "sentiment": "negative"},
        {"title": "Energy Storage Business Posts Record Deployments", "sentiment": "positive"},
    ],
    "JPM": [
        {"title": "JPMorgan Beats EPS Estimates on Strong IB and Trading", "sentiment": "positive"},
        {"title": "Net Interest Income Guidance Raised", "sentiment": "positive"},
        {"title": "Dimon Warns on Geopolitical Risks to Financial Markets", "sentiment": "neutral"},
        {"title": "JPMorgan Expands Consumer Banking Branch Footprint", "sentiment": "positive"},
    ],
    "V": [
        {"title": "Visa Payment Volume Growth Remains Resilient", "sentiment": "positive"},
        {"title": "Cross-Border Travel Spending Reaches Pre-Pandemic Peak", "sentiment": "positive"},
        {"title": "Regulators Review Interchange Fee Structures", "sentiment": "negative"},
    ],
    "JNJ": [
        {"title": "J&J Pharma Segment Grows on Oncology Franchise", "sentiment": "positive"},
        {"title": "Talc Litigation Settlement Reduces Tail Risk", "sentiment": "positive"},
        {"title": "Medical Devices Show Modest Growth", "sentiment": "neutral"},
    ],
}

GENERIC_HEADLINES = [
    {"title": "Company Reports Solid Quarterly Results", "sentiment": "positive"},
    {"title": "Analyst Upgrade Cites Improving Fundamentals", "sentiment": "positive"},
    {"title": "Macro Headwinds May Pressure Near-Term Outlook", "sentiment": "negative"},
    {"title": "Management Reaffirms Full-Year Guidance", "sentiment": "neutral"},
    {"title": "New Product Launch Generates Positive Early Reviews", "sentiment": "positive"},
]

NEWS_SOURCES = ["Reuters", "Bloomberg", "WSJ", "CNBC", "Financial Times", "Barron's"]


def _seed_for(ticker: str) -> random.Random:
    h = int(hashlib.sha256(ticker.upper().encode()).hexdigest(), 16) % (10**8)
    return random.Random(h)


def search_news(ticker: str, days: int = 30) -> List[Headline]:
    """Search recent news for a ticker. Returns a list of headlines with title, source, date, sentiment, and summary."""
    logger.info(f"Tool called: search_news(ticker={ticker}, days={days})")
    t = ticker.upper()
    headlines = TICKER_HEADLINES.get(t, GENERIC_HEADLINES)
    r = _seed_for(t + "news")
    out: List[Headline] = []
    today = datetime.utcnow().date()
    for i, h in enumerate(headlines):
        d = today - timedelta(days=r.randint(0, days))
        out.append(Headline(
            title=h["title"],
            source=r.choice(NEWS_SOURCES),
            date=d.isoformat(),
            url=f"https://example.com/news/{t.lower()}/{i}",
            sentiment=h["sentiment"],
            summary=f"Coverage highlights implications of this development for {t} and its sector.",
        ))
    return out


def get_analyst_ratings(ticker: str) -> AnalystRatings:
    """Return Wall Street analyst consensus, target price, and rating distribution for a ticker."""
    logger.info(f"Tool called: get_analyst_ratings(ticker={ticker})")
    r = _seed_for(ticker + "rat")
    from app.tools.market_data import get_price_data
    pd = get_price_data(ticker)
    strong_buy = r.randint(3, 20)
    buy = r.randint(3, 20)
    hold = r.randint(2, 15)
    sell = r.randint(0, 5)
    strong_sell = r.randint(0, 3)
    total = strong_buy + buy + hold + sell + strong_sell
    positive = strong_buy + buy
    negative = sell + strong_sell
    if positive > total * 0.6:
        consensus = "Buy"
    elif negative > total * 0.3:
        consensus = "Sell"
    else:
        consensus = "Hold"
    target = round(pd.current_price * r.uniform(0.92, 1.28), 2)
    return AnalystRatings(
        consensus=consensus, target_price=target, num_analysts=total,
        strong_buy=strong_buy, buy=buy, hold=hold, sell=sell, strong_sell=strong_sell,
    )


def get_sentiment_score(ticker: str) -> SentimentData:
    """Aggregate news sentiment and analyst consensus into an overall sentiment score (-1.0 to 1.0) with recent headlines."""
    logger.info(f"Tool called: get_sentiment_score(ticker={ticker})")
    headlines = search_news(ticker, 30)
    ratings = get_analyst_ratings(ticker)
    pos = sum(1 for h in headlines if h.sentiment == "positive")
    neg = sum(1 for h in headlines if h.sentiment == "negative")
    n = max(len(headlines), 1)
    news_score = (pos - neg) / n
    r = _seed_for(ticker + "sent")
    social = round(r.uniform(-0.3, 0.6), 3)
    overall = round((news_score * 0.5 + social * 0.3 + (0.4 if ratings.consensus == "Buy" else -0.4 if ratings.consensus == "Sell" else 0.0) * 0.2), 3)
    return SentimentData(
        overall_score=overall,
        news_sentiment=round(news_score, 3),
        social_sentiment=social,
        analyst_consensus=ratings.consensus,
        analyst_target_price=ratings.target_price,
        recent_headlines=headlines,
    )
