"""OpenAI-compatible tool schemas for all mock tools.

Exports TOOL_DEFINITIONS used by agents for function calling.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.tools.financial_metrics import (
    get_financial_metrics,
    get_quarterly_earnings,
    get_technical_indicators,
)
from app.tools.market_data import get_historical_prices, get_price_data
from app.tools.news_search import get_analyst_ratings, get_sentiment_score, search_news
from app.tools.peer_comparison import compare_peers, get_peers

TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_price_data",
            "description": "Get current price, OHLC, volume, 52-week range, and market cap for a ticker.",
            "parameters": {
                "type": "object",
                "properties": {"ticker": {"type": "string", "description": "Stock ticker symbol (e.g., AAPL)"}},
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_financial_metrics",
            "description": "Get fundamental financial metrics (P/E, margins, growth, debt ratios) for a ticker.",
            "parameters": {
                "type": "object",
                "properties": {"ticker": {"type": "string"}},
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_quarterly_earnings",
            "description": "Get recent quarterly earnings (EPS actual vs estimate, revenue, surprise %).",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                    "quarters": {"type": "integer", "default": 4},
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_technical_indicators",
            "description": "Get technical indicators (RSI, MACD, moving averages, support/resistance) for a ticker.",
            "parameters": {
                "type": "object",
                "properties": {"ticker": {"type": "string"}},
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_news",
            "description": "Search recent news headlines for a ticker.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                    "days": {"type": "integer", "default": 30},
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_analyst_ratings",
            "description": "Get Wall Street analyst consensus, target price, and rating distribution.",
            "parameters": {
                "type": "object",
                "properties": {"ticker": {"type": "string"}},
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sentiment_score",
            "description": "Aggregate news and analyst sentiment into an overall sentiment score.",
            "parameters": {
                "type": "object",
                "properties": {"ticker": {"type": "string"}},
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_peers",
            "description": "Get peer tickers in the same sector/industry.",
            "parameters": {
                "type": "object",
                "properties": {"ticker": {"type": "string"}},
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_peers",
            "description": "Compare the ticker with a list of peer tickers across key metrics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                    "peers": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["ticker", "peers"],
            },
        },
    },
]

TOOL_REGISTRY = {
    "get_price_data": get_price_data,
    "get_historical_prices": get_historical_prices,
    "get_financial_metrics": get_financial_metrics,
    "get_quarterly_earnings": get_quarterly_earnings,
    "get_technical_indicators": get_technical_indicators,
    "search_news": search_news,
    "get_analyst_ratings": get_analyst_ratings,
    "get_sentiment_score": get_sentiment_score,
    "get_peers": get_peers,
    "compare_peers": compare_peers,
}
