"""Mock financial metrics tool."""
from __future__ import annotations

import hashlib
import logging
import random
from typing import Dict, List

from app.models.schemas import FinancialMetrics, QuarterlyEarnings, TechnicalIndicators

logger = logging.getLogger(__name__)

METRICS: Dict[str, FinancialMetrics] = {
    "AAPL": FinancialMetrics(market_cap=2.92e12, pe_ratio=31.5, forward_pe=28.2, peg_ratio=2.6, price_to_book=45.1, ev_to_ebitda=22.9,
        revenue_ttm=383_000_000_000, revenue_growth_yoy=0.018, gross_margin=0.441, operating_margin=0.298, net_margin=0.253,
        roe=1.56, debt_to_equity=1.73, current_ratio=0.99, free_cash_flow=98_000_000_000, dividend_yield=0.0054, beta=1.25,
        fifty_two_week_high=199.62, fifty_two_week_low=164.08),
    "MSFT": FinancialMetrics(market_cap=3.18e12, pe_ratio=36.2, forward_pe=32.4, peg_ratio=2.2, price_to_book=12.6, ev_to_ebitda=24.5,
        revenue_ttm=236_580_000_000, revenue_growth_yoy=0.159, gross_margin=0.697, operating_margin=0.44, net_margin=0.362,
        roe=0.39, debt_to_equity=0.46, current_ratio=1.27, free_cash_flow=65_000_000_000, dividend_yield=0.007, beta=0.91,
        fifty_two_week_high=468.35, fifty_two_week_low=309.45),
    "NVDA": FinancialMetrics(market_cap=2.28e12, pe_ratio=66.8, forward_pe=33.5, peg_ratio=0.92, price_to_book=56.2, ev_to_ebitda=57.0,
        revenue_ttm=79_770_000_000, revenue_growth_yoy=1.26, gross_margin=0.725, operating_margin=0.54, net_margin=0.486,
        roe=1.19, debt_to_equity=0.22, current_ratio=4.17, free_cash_flow=27_000_000_000, dividend_yield=0.0003, beta=1.75,
        fifty_two_week_high=974.00, fifty_two_week_low=373.56),
    "GOOGL": FinancialMetrics(market_cap=2.15e12, pe_ratio=27.4, forward_pe=21.3, peg_ratio=1.3, price_to_book=7.1, ev_to_ebitda=17.8,
        revenue_ttm=307_390_000_000, revenue_growth_yoy=0.087, gross_margin=0.566, operating_margin=0.274, net_margin=0.241,
        roe=0.28, debt_to_equity=0.11, current_ratio=2.15, free_cash_flow=69_000_000_000, dividend_yield=0.004, beta=1.05,
        fifty_two_week_high=178.60, fifty_two_week_low=115.35),
    "AMZN": FinancialMetrics(market_cap=1.94e12, pe_ratio=54.2, forward_pe=35.8, peg_ratio=1.8, price_to_book=8.8, ev_to_ebitda=20.3,
        revenue_ttm=574_780_000_000, revenue_growth_yoy=0.118, gross_margin=0.472, operating_margin=0.066, net_margin=0.053,
        roe=0.18, debt_to_equity=0.54, current_ratio=1.05, free_cash_flow=36_800_000_000, dividend_yield=0.0, beta=1.14,
        fifty_two_week_high=191.70, fifty_two_week_low=118.35),
    "META": FinancialMetrics(market_cap=1.26e12, pe_ratio=27.8, forward_pe=23.1, peg_ratio=1.1, price_to_book=8.6, ev_to_ebitda=16.5,
        revenue_ttm=134_900_000_000, revenue_growth_yoy=0.159, gross_margin=0.81, operating_margin=0.35, net_margin=0.289,
        roe=0.34, debt_to_equity=0.31, current_ratio=2.68, free_cash_flow=43_800_000_000, dividend_yield=0.004, beta=1.21,
        fifty_two_week_high=531.49, fifty_two_week_low=274.38),
    "TSLA": FinancialMetrics(market_cap=5.74e11, pe_ratio=44.6, forward_pe=64.2, peg_ratio=6.5, price_to_book=8.6, ev_to_ebitda=39.2,
        revenue_ttm=96_770_000_000, revenue_growth_yoy=-0.085, gross_margin=0.178, operating_margin=0.076, net_margin=0.131,
        roe=0.22, debt_to_equity=0.18, current_ratio=1.73, free_cash_flow=4_400_000_000, dividend_yield=0.0, beta=2.28,
        fifty_two_week_high=299.29, fifty_two_week_low=138.80),
    "JPM": FinancialMetrics(market_cap=5.69e11, pe_ratio=12.2, forward_pe=11.6, peg_ratio=1.4, price_to_book=2.0, ev_to_ebitda=14.8,
        revenue_ttm=162_430_000_000, revenue_growth_yoy=0.232, gross_margin=1.0, operating_margin=0.44, net_margin=0.305,
        roe=0.17, debt_to_equity=1.29, current_ratio=0.0, free_cash_flow=0, dividend_yield=0.024, beta=1.09,
        fifty_two_week_high=205.88, fifty_two_week_low=135.19),
    "V": FinancialMetrics(market_cap=5.56e11, pe_ratio=31.1, forward_pe=26.8, peg_ratio=1.9, price_to_book=15.5, ev_to_ebitda=22.4,
        revenue_ttm=34_120_000_000, revenue_growth_yoy=0.096, gross_margin=0.98, operating_margin=0.66, net_margin=0.54,
        roe=0.52, debt_to_equity=0.52, current_ratio=1.54, free_cash_flow=20_000_000_000, dividend_yield=0.0076, beta=0.92,
        fifty_two_week_high=290.96, fifty_two_week_low=227.78),
    "JNJ": FinancialMetrics(market_cap=3.56e11, pe_ratio=22.1, forward_pe=15.2, peg_ratio=2.8, price_to_book=5.5, ev_to_ebitda=13.9,
        revenue_ttm=85_480_000_000, revenue_growth_yoy=0.065, gross_margin=0.692, operating_margin=0.263, net_margin=0.164,
        roe=0.23, debt_to_equity=0.43, current_ratio=1.12, free_cash_flow=18_000_000_000, dividend_yield=0.033, beta=0.56,
        fifty_two_week_high=175.97, fifty_two_week_low=143.13),
}


def _seed_for(ticker: str) -> random.Random:
    h = int(hashlib.sha256(ticker.upper().encode()).hexdigest(), 16) % (10**8)
    return random.Random(h)


def get_financial_metrics(ticker: str) -> FinancialMetrics:
    """Return fundamental financial metrics (P/E, margins, growth, debt ratios) for a ticker."""
    logger.info(f"Tool called: get_financial_metrics(ticker={ticker})")
    t = ticker.upper()
    if t in METRICS:
        return METRICS[t]
    r = _seed_for(t)
    return FinancialMetrics(
        market_cap=r.uniform(1e9, 5e11),
        pe_ratio=round(r.uniform(8, 45), 1),
        forward_pe=round(r.uniform(7, 35), 1),
        peg_ratio=round(r.uniform(0.8, 3.5), 2),
        price_to_book=round(r.uniform(1.0, 10.0), 2),
        ev_to_ebitda=round(r.uniform(8, 25), 1),
        revenue_ttm=r.uniform(1e9, 1e11),
        revenue_growth_yoy=round(r.uniform(-0.1, 0.35), 3),
        gross_margin=round(r.uniform(0.2, 0.75), 3),
        operating_margin=round(r.uniform(0.05, 0.4), 3),
        net_margin=round(r.uniform(0.03, 0.3), 3),
        roe=round(r.uniform(0.05, 0.45), 3),
        debt_to_equity=round(r.uniform(0.1, 1.8), 2),
        current_ratio=round(r.uniform(0.9, 3.0), 2),
        free_cash_flow=r.uniform(1e8, 5e10),
        dividend_yield=round(r.uniform(0.0, 0.04), 4),
        beta=round(r.uniform(0.5, 2.2), 2),
        fifty_two_week_high=round(r.uniform(50, 500), 2),
        fifty_two_week_low=round(r.uniform(10, 200), 2),
    )


def get_quarterly_earnings(ticker: str, quarters: int = 4) -> List[QuarterlyEarnings]:
    """Return recent quarterly earnings (EPS actual vs estimate, revenue, surprise %) for the last N quarters."""
    logger.info(f"Tool called: get_quarterly_earnings(ticker={ticker}, quarters={quarters})")
    r = _seed_for(ticker + "earn")
    out: List[QuarterlyEarnings] = []
    year = 2026
    q = 1
    for i in range(quarters):
        eps_est = round(r.uniform(0.5, 4.5), 2)
        surprise = r.uniform(-0.08, 0.18)
        eps_actual = round(eps_est * (1 + surprise), 2)
        rev_est = r.uniform(5e9, 9e10)
        out.append(QuarterlyEarnings(
            quarter=f"Q{q} {year}",
            eps_actual=eps_actual,
            eps_estimate=eps_est,
            surprise_pct=round(surprise * 100, 2),
            revenue=round(rev_est * (1 + surprise / 2), 0),
            revenue_estimate=round(rev_est, 0),
        ))
        q -= 1
        if q == 0:
            q = 4
            year -= 1
    return out


def get_technical_indicators(ticker: str) -> TechnicalIndicators:
    """Return mock technical indicators (RSI, MACD, moving averages, support/resistance) for a ticker."""
    logger.info(f"Tool called: get_technical_indicators(ticker={ticker})")
    from app.tools.market_data import get_price_data
    pd = get_price_data(ticker)
    r = _seed_for(ticker + "tech")
    price = pd.current_price
    return TechnicalIndicators(
        rsi_14=round(r.uniform(30, 75), 1),
        macd=round(r.uniform(-3, 5), 2),
        macd_signal=round(r.uniform(-3, 5), 2),
        sma_50=round(price * r.uniform(0.92, 1.05), 2),
        sma_200=round(price * r.uniform(0.82, 1.08), 2),
        ema_20=round(price * r.uniform(0.96, 1.03), 2),
        bollinger_upper=round(price * 1.08, 2),
        bollinger_lower=round(price * 0.92, 2),
        avg_volume=r.randint(1_000_000, 60_000_000),
        support=round(price * 0.92, 2),
        resistance=round(price * 1.08, 2),
    )
