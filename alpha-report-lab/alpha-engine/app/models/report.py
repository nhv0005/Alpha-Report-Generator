"""Pydantic models for Alpha Report domain."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

ReportStatus = Literal[
    "pending",
    "researching",
    "analyzing",
    "assessing_risk",
    "writing",
    "complete",
    "error",
    "cancelled",
]

Recommendation = Literal[
    "STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"
]

RiskRating = Literal["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]

SectionType = Literal[
    "executive_summary",
    "company_overview",
    "fundamental_analysis",
    "technical_analysis",
    "catalysts",
    "risk_assessment",
    "competitive_landscape",
    "sentiment",
    "recommendation",
    "appendix",
]


class ReportSection(BaseModel):
    id: str
    title: str
    type: SectionType
    content: str
    data: Optional[Dict[str, Any]] = None
    agent: str
    tokens_used: int = 0
    generation_time_ms: int = 0


class ReportMetadata(BaseModel):
    session_id: str
    user_id: str
    model: str
    total_tokens: int = 0
    total_generation_time_ms: int = 0
    agents_used: List[str] = Field(default_factory=list)
    tools_called: List[str] = Field(default_factory=list)
    trace_id: Optional[str] = None


class AlphaReport(BaseModel):
    id: str
    ticker: str
    company_name: str = ""
    sector: str = ""
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    status: ReportStatus = "pending"
    recommendation: Recommendation = "HOLD"
    conviction_score: float = 5.0
    target_price: float = 0.0
    current_price: float = 0.0
    upside_percentage: float = 0.0
    risk_rating: RiskRating = "MEDIUM"
    sections: List[ReportSection] = Field(default_factory=list)
    metadata: ReportMetadata


class GenerateRequest(BaseModel):
    ticker: str
    investment_horizon: Literal["short_term", "medium_term", "long_term"] = "medium_term"
    risk_tolerance: Literal["conservative", "moderate", "aggressive"] = "moderate"
    focus_areas: Optional[List[str]] = None
    custom_instructions: Optional[str] = None
    user_id: Optional[str] = None


class GenerationProgress(BaseModel):
    report_id: str
    status: ReportStatus
    current_step: str
    steps_completed: int
    total_steps: int
    current_agent: str
    elapsed_time_ms: int
