"""Mock peer comparison tool."""
from __future__ import annotations

import logging
from typing import Dict, List

from app.models.schemas import PeerComparison

logger = logging.getLogger(__name__)

PEER_MAP: Dict[str, List[str]] = {
    "AAPL": ["MSFT", "GOOGL", "SSNLF", "DELL", "HPQ"],
    "MSFT": ["GOOGL", "AAPL", "ORCL", "AMZN", "CRM"],
    "NVDA": ["AMD", "INTC", "AVGO", "QCOM", "TSM"],
    "GOOGL": ["META", "MSFT", "AMZN", "AAPL", "SNAP"],
    "AMZN": ["WMT", "GOOGL", "MSFT", "TGT", "SHOP"],
    "META": ["GOOGL", "SNAP", "PINS", "TTD", "NFLX"],
    "TSLA": ["F", "GM", "RIVN", "LCID", "BYDDY"],
    "JPM": ["BAC", "WFC", "C", "GS", "MS"],
    "V": ["MA", "AXP", "PYPL", "DFS", "FIS"],
    "JNJ": ["PFE", "MRK", "ABBV", "LLY", "BMY"],
}


def get_peers(ticker: str) -> List[str]:
    """Return a list of 4-5 peer tickers in the same sector/industry for a given ticker."""
    logger.info(f"Tool called: get_peers(ticker={ticker})")
    t = ticker.upper()
    return PEER_MAP.get(t, ["SPY", "QQQ", "DIA", "IWM"])


def compare_peers(ticker: str, peers: List[str]) -> List[PeerComparison]:
    """Return peer comparison data (market cap, P/E, growth, margins, ROE) for the ticker and provided peers."""
    logger.info(f"Tool called: compare_peers(ticker={ticker}, peers={peers})")
    from app.tools.financial_metrics import get_financial_metrics
    from app.tools.market_data import get_company_profile
    all_tickers = [ticker.upper()] + [p.upper() for p in peers if p.upper() != ticker.upper()]
    out: List[PeerComparison] = []
    for t in all_tickers:
        profile = get_company_profile(t)
        m = get_financial_metrics(t)
        out.append(PeerComparison(
            ticker=t,
            company_name=profile.name,
            market_cap=m.market_cap,
            pe_ratio=m.pe_ratio,
            revenue_growth=m.revenue_growth_yoy,
            operating_margin=m.operating_margin,
            roe=m.roe,
        ))
    return out
