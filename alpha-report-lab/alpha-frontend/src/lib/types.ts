// Core report types
export type ReportStatus =
  | "pending"
  | "researching"
  | "analyzing"
  | "assessing_risk"
  | "writing"
  | "complete"
  | "error"
  | "cancelled";

export type Recommendation =
  | "STRONG_BUY"
  | "BUY"
  | "HOLD"
  | "SELL"
  | "STRONG_SELL";

export type RiskRating = "LOW" | "MEDIUM" | "HIGH" | "VERY_HIGH";

export type SectionType =
  | "executive_summary"
  | "company_overview"
  | "fundamental_analysis"
  | "technical_analysis"
  | "catalysts"
  | "risk_assessment"
  | "competitive_landscape"
  | "sentiment"
  | "recommendation"
  | "appendix";

export interface ReportSection {
  id: string;
  title: string;
  type: SectionType;
  content: string;
  data?: Record<string, any>;
  agent: string;
  tokens_used: number;
  generation_time_ms: number;
}

export interface ReportMetadata {
  session_id: string;
  user_id: string;
  model: string;
  total_tokens: number;
  total_generation_time_ms: number;
  agents_used: string[];
  tools_called: string[];
  trace_id?: string;
}

export interface AlphaReport {
  id: string;
  ticker: string;
  company_name: string;
  sector: string;
  generated_at: string;
  status: ReportStatus;
  recommendation: Recommendation;
  conviction_score: number;
  target_price: number;
  current_price: number;
  upside_percentage: number;
  risk_rating: RiskRating;
  sections: ReportSection[];
  metadata: ReportMetadata;
}

export interface GenerateRequest {
  ticker: string;
  investment_horizon: "short_term" | "medium_term" | "long_term";
  risk_tolerance: "conservative" | "moderate" | "aggressive";
  focus_areas?: string[];
  custom_instructions?: string;
  user_id?: string;
}

export interface GenerationProgress {
  report_id: string;
  status: ReportStatus;
  current_step: string;
  steps_completed: number;
  total_steps: number;
  current_agent: string;
  elapsed_time_ms: number;
}

export interface FinancialMetrics {
  market_cap: number;
  pe_ratio: number;
  forward_pe: number;
  peg_ratio: number;
  price_to_book: number;
  ev_to_ebitda: number;
  revenue_ttm: number;
  revenue_growth_yoy: number;
  gross_margin: number;
  operating_margin: number;
  net_margin: number;
  roe: number;
  debt_to_equity: number;
  current_ratio: number;
  free_cash_flow: number;
  dividend_yield: number;
  beta: number;
  fifty_two_week_high: number;
  fifty_two_week_low: number;
}

export interface PeerComparison {
  ticker: string;
  company_name: string;
  market_cap: number;
  pe_ratio: number;
  revenue_growth: number;
  margin: number;
}

export interface Headline {
  title: string;
  sentiment: string;
  source: string;
  date: string;
}

export interface SentimentData {
  overall_score: number;
  news_sentiment: number;
  social_sentiment: number;
  analyst_consensus: string;
  analyst_target_price: number;
  recent_headlines: Headline[];
}

export interface HealthResponse {
  service: string;
  status: string;
  version?: string;
  model?: string;
  timestamp?: string;
}
