"""Pydantic models for financial data."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class PriceData(BaseModel):
    ticker: str
    current_price: float
    open: float
    high: float
    low: float
    volume: int
    fifty_two_week_high: float
    fifty_two_week_low: float
    daily_change_pct: float
    market_cap: float


class FinancialMetrics(BaseModel):
    market_cap: float
    pe_ratio: float
    forward_pe: float
    peg_ratio: float
    price_to_book: float
    ev_to_ebitda: float
    revenue_ttm: float
    revenue_growth_yoy: float
    gross_margin: float
    operating_margin: float
    net_margin: float
    roe: float
    debt_to_equity: float
    current_ratio: float
    free_cash_flow: float
    dividend_yield: float
    beta: float
    fifty_two_week_high: float
    fifty_two_week_low: float


class TechnicalIndicators(BaseModel):
    rsi_14: float
    macd: float
    macd_signal: float
    sma_50: float
    sma_200: float
    ema_20: float
    bollinger_upper: float
    bollinger_lower: float
    avg_volume: int
    support: float
    resistance: float


class PeerComparison(BaseModel):
    ticker: str
    company_name: str
    market_cap: float
    pe_ratio: float
    revenue_growth: float
    operating_margin: float
    roe: float


class Headline(BaseModel):
    title: str
    source: str
    date: str
    url: str
    sentiment: str
    summary: str


class SentimentData(BaseModel):
    overall_score: float
    news_sentiment: float
    social_sentiment: float
    analyst_consensus: str
    analyst_target_price: float
    recent_headlines: List[Headline]


class AnalystRatings(BaseModel):
    consensus: str
    target_price: float
    num_analysts: int
    strong_buy: int
    buy: int
    hold: int
    sell: int
    strong_sell: int


class CompanyProfile(BaseModel):
    ticker: str
    name: str
    sector: str
    industry: str
    description: str
    ceo: str
    employees: int
    hq: str
    founded: Optional[int] = None
    website: Optional[str] = None


class QuarterlyEarnings(BaseModel):
    quarter: str
    eps_actual: float
    eps_estimate: float
    surprise_pct: float
    revenue: float
    revenue_estimate: float
