"""Mock market data tool."""
from __future__ import annotations

import hashlib
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List

from app.models.schemas import CompanyProfile, PriceData

logger = logging.getLogger(__name__)

# Hardcoded profiles for 10 popular tickers
PROFILES: Dict[str, CompanyProfile] = {
    "AAPL": CompanyProfile(ticker="AAPL", name="Apple Inc.", sector="Technology",
        industry="Consumer Electronics", description="Designs, manufactures, and markets smartphones, personal computers, tablets, wearables and accessories worldwide.",
        ceo="Tim Cook", employees=161000, hq="Cupertino, CA, USA", founded=1976, website="https://www.apple.com"),
    "MSFT": CompanyProfile(ticker="MSFT", name="Microsoft Corporation", sector="Technology",
        industry="Software - Infrastructure", description="Develops and supports software, services, devices, and solutions worldwide.",
        ceo="Satya Nadella", employees=228000, hq="Redmond, WA, USA", founded=1975, website="https://www.microsoft.com"),
    "NVDA": CompanyProfile(ticker="NVDA", name="NVIDIA Corporation", sector="Technology",
        industry="Semiconductors", description="Leader in accelerated computing platforms powering AI, gaming, data centers, and automotive.",
        ceo="Jensen Huang", employees=29600, hq="Santa Clara, CA, USA", founded=1993, website="https://www.nvidia.com"),
    "GOOGL": CompanyProfile(ticker="GOOGL", name="Alphabet Inc.", sector="Communication Services",
        industry="Internet Content & Information", description="Parent company of Google, YouTube, and other subsidiaries providing online advertising, search, and cloud services.",
        ceo="Sundar Pichai", employees=182000, hq="Mountain View, CA, USA", founded=1998, website="https://abc.xyz"),
    "AMZN": CompanyProfile(ticker="AMZN", name="Amazon.com, Inc.", sector="Consumer Cyclical",
        industry="Internet Retail", description="Global e-commerce, cloud computing (AWS), digital streaming, and AI company.",
        ceo="Andy Jassy", employees=1540000, hq="Seattle, WA, USA", founded=1994, website="https://www.amazon.com"),
    "META": CompanyProfile(ticker="META", name="Meta Platforms, Inc.", sector="Communication Services",
        industry="Internet Content & Information", description="Operates Facebook, Instagram, WhatsApp, and Reality Labs AR/VR.",
        ceo="Mark Zuckerberg", employees=67000, hq="Menlo Park, CA, USA", founded=2004, website="https://about.meta.com"),
    "TSLA": CompanyProfile(ticker="TSLA", name="Tesla, Inc.", sector="Consumer Cyclical",
        industry="Auto Manufacturers", description="Designs, manufactures, and sells electric vehicles and energy generation/storage systems.",
        ceo="Elon Musk", employees=140500, hq="Austin, TX, USA", founded=2003, website="https://www.tesla.com"),
    "JPM": CompanyProfile(ticker="JPM", name="JPMorgan Chase & Co.", sector="Financial Services",
        industry="Banks - Diversified", description="Global financial services firm with operations in investment banking, consumer banking, asset management.",
        ceo="Jamie Dimon", employees=309926, hq="New York, NY, USA", founded=1799, website="https://www.jpmorganchase.com"),
    "V": CompanyProfile(ticker="V", name="Visa Inc.", sector="Financial Services",
        industry="Credit Services", description="Global payments technology company facilitating electronic funds transfers worldwide.",
        ceo="Ryan McInerney", employees=28800, hq="San Francisco, CA, USA", founded=1958, website="https://www.visa.com"),
    "JNJ": CompanyProfile(ticker="JNJ", name="Johnson & Johnson", sector="Healthcare",
        industry="Drug Manufacturers", description="Researches, develops, manufactures, and sells health care products worldwide.",
        ceo="Joaquin Duato", employees=131900, hq="New Brunswick, NJ, USA", founded=1886, website="https://www.jnj.com"),
}

PRICE_DATA: Dict[str, PriceData] = {
    "AAPL": PriceData(ticker="AAPL", current_price=189.45, open=188.20, high=190.11, low=187.55, volume=52340000,
                      fifty_two_week_high=199.62, fifty_two_week_low=164.08, daily_change_pct=0.66, market_cap=2920000000000),
    "MSFT": PriceData(ticker="MSFT", current_price=428.15, open=425.00, high=430.50, low=424.10, volume=22100000,
                      fifty_two_week_high=468.35, fifty_two_week_low=309.45, daily_change_pct=0.74, market_cap=3180000000000),
    "NVDA": PriceData(ticker="NVDA", current_price=925.77, open=911.50, high=932.10, low=908.20, volume=42500000,
                      fifty_two_week_high=974.00, fifty_two_week_low=373.56, daily_change_pct=1.56, market_cap=2280000000000),
    "GOOGL": PriceData(ticker="GOOGL", current_price=174.22, open=172.40, high=175.10, low=171.85, volume=27800000,
                       fifty_two_week_high=178.60, fifty_two_week_low=115.35, daily_change_pct=1.05, market_cap=2150000000000),
    "AMZN": PriceData(ticker="AMZN", current_price=185.69, open=183.50, high=186.70, low=182.90, volume=38400000,
                      fifty_two_week_high=191.70, fifty_two_week_low=118.35, daily_change_pct=1.19, market_cap=1935000000000),
    "META": PriceData(ticker="META", current_price=496.88, open=492.20, high=499.50, low=491.10, volume=14600000,
                      fifty_two_week_high=531.49, fifty_two_week_low=274.38, daily_change_pct=0.95, market_cap=1263000000000),
    "TSLA": PriceData(ticker="TSLA", current_price=180.34, open=178.00, high=183.50, low=177.20, volume=82500000,
                      fifty_two_week_high=299.29, fifty_two_week_low=138.80, daily_change_pct=1.31, market_cap=574000000000),
    "JPM": PriceData(ticker="JPM", current_price=198.22, open=197.10, high=199.45, low=196.55, volume=9800000,
                     fifty_two_week_high=205.88, fifty_two_week_low=135.19, daily_change_pct=0.57, market_cap=569000000000),
    "V": PriceData(ticker="V", current_price=275.34, open=274.50, high=276.80, low=273.90, volume=6100000,
                   fifty_two_week_high=290.96, fifty_two_week_low=227.78, daily_change_pct=0.31, market_cap=556000000000),
    "JNJ": PriceData(ticker="JNJ", current_price=147.88, open=147.20, high=148.55, low=146.80, volume=6900000,
                     fifty_two_week_high=175.97, fifty_two_week_low=143.13, daily_change_pct=0.46, market_cap=356000000000),
}


def _seed_for(ticker: str) -> random.Random:
    h = int(hashlib.sha256(ticker.upper().encode()).hexdigest(), 16) % (10**8)
    return random.Random(h)


def get_company_profile(ticker: str) -> CompanyProfile:
    """Return the company profile (name, sector, description) for a ticker."""
    t = ticker.upper()
    if t in PROFILES:
        return PROFILES[t]
    r = _seed_for(t)
    sectors = ["Technology", "Healthcare", "Financial Services", "Consumer Cyclical", "Industrials"]
    return CompanyProfile(
        ticker=t, name=f"{t} Holdings Inc.", sector=r.choice(sectors),
        industry="Diversified", description=f"{t} is a publicly traded company in its sector.",
        ceo="J. Doe", employees=r.randint(500, 50000), hq="United States",
        founded=r.randint(1950, 2015),
    )


def get_price_data(ticker: str) -> PriceData:
    """Return current price, open/high/low, volume, market cap, and 52-week range for a ticker."""
    logger.info(f"Tool called: get_price_data(ticker={ticker})")
    t = ticker.upper()
    if t in PRICE_DATA:
        return PRICE_DATA[t]
    r = _seed_for(t)
    price = round(r.uniform(25.0, 500.0), 2)
    return PriceData(
        ticker=t,
        current_price=price,
        open=round(price * r.uniform(0.98, 1.01), 2),
        high=round(price * r.uniform(1.00, 1.03), 2),
        low=round(price * r.uniform(0.97, 1.00), 2),
        volume=r.randint(500_000, 50_000_000),
        fifty_two_week_high=round(price * r.uniform(1.10, 1.60), 2),
        fifty_two_week_low=round(price * r.uniform(0.50, 0.90), 2),
        daily_change_pct=round(r.uniform(-3.0, 3.0), 2),
        market_cap=round(price * r.randint(50_000_000, 2_000_000_000), 2),
    )


def get_historical_prices(ticker: str, period: str = "90d") -> List[dict]:
    """Return mock daily OHLCV data for the given period (30d, 90d, or 365d)."""
    logger.info(f"Tool called: get_historical_prices(ticker={ticker}, period={period})")
    days = {"30d": 30, "90d": 90, "365d": 365}.get(period, 90)
    pd = get_price_data(ticker)
    r = _seed_for(ticker.upper() + period)
    price = pd.current_price
    out: List[dict] = []
    today = datetime.utcnow().date()
    for i in range(days, 0, -1):
        d = today - timedelta(days=i)
        change = r.uniform(-0.02, 0.02)
        open_p = round(price * (1 - change / 2), 2)
        close = round(price * (1 + change), 2)
        high = round(max(open_p, close) * r.uniform(1.000, 1.015), 2)
        low = round(min(open_p, close) * r.uniform(0.985, 1.000), 2)
        out.append({
            "date": d.isoformat(),
            "open": open_p,
            "high": high,
            "low": low,
            "close": close,
            "volume": r.randint(1_000_000, 80_000_000),
        })
        price = close
    return out
