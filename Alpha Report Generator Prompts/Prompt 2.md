### Prompt 2 — Python Alpha Engine: Mock Tools & Data Models

```markdown
# Prompt 2: Python Alpha Engine — Mock Tools, Data Models & Report Store

Create the foundational layer of the Python Alpha Engine: mock financial data tools,
Pydantic data models, and the in-memory report store. These are the building blocks
that the AI agents (Prompt 3) will use. Do NOT create agents or instrumentation yet.

## Files to Create

### 1. app/models/report.py
Pydantic models mirroring the TypeScript types:

- **AlphaReport** — Full report with all sections, metadata, scores
- **ReportSection** — Individual section with content, agent attribution, token usage
- **ReportMetadata** — Generation metadata (session, model, tokens, agents, tools, trace_id)
- **GenerateRequest** — Incoming request (ticker, horizon, risk tolerance, focus areas)
- **GenerationProgress** — Real-time generation status for polling

### 2. app/models/schemas.py
Pydantic models for financial data:

- **FinancialMetrics** — All fundamental metrics (PE, margins, growth, debt ratios)
- **TechnicalIndicators** — RSI, MACD, moving averages, Bollinger bands, volume
- **PeerComparison** — Competitor comparison data
- **SentimentData** — Overall sentiment, news headlines, analyst consensus
- **CompanyProfile** — Name, sector, industry, description, CEO, employees, HQ
- **PriceData** — Current price, 52-week range, daily change, volume

### 3. app/tools/market_data.py
Mock tool that returns realistic financial data for well-known tickers:

- **get_price_data(ticker: str) → PriceData**
  - Hardcoded data for 10 popular tickers: AAPL, MSFT, NVDA, GOOGL, AMZN,
    META, TSLA, JPM, V, JNJ
  - For unknown tickers: generate plausible random data seeded by ticker hash
  - Returns: current_price, open, high, low, volume, 52wk_high, 52wk_low,
    daily_change_pct, market_cap

- **get_historical_prices(ticker: str, period: str) → List[dict]**
  - Returns mock daily price data for charting (30/90/365 days)
  - Each entry: {date, open, high, low, close, volume}

### 4. app/tools/financial_metrics.py
Mock tool for fundamental data:

- **get_financial_metrics(ticker: str) → FinancialMetrics**
  - Hardcoded for 10 tickers with realistic values
  - Unknown tickers: seeded random generation
  - Returns all metrics defined in the FinancialMetrics model

- **get_quarterly_earnings(ticker: str, quarters: int) → List[dict]**
  - Returns mock quarterly earnings (EPS actual vs estimate, revenue, surprise %)
  - Default: last 4 quarters

### 5. app/tools/news_search.py
Mock tool for news and sentiment:

- **search_news(ticker: str, days: int = 30) → List[dict]**
  - Returns 5-10 mock news headlines per ticker with:
    {title, source, date, url, sentiment: "positive"|"negative"|"neutral", summary}
  - Headlines should be realistic and ticker-specific
  - Example for NVDA: "NVIDIA Reports Record Data Center Revenue, AI Demand Surges"

- **get_analyst_ratings(ticker: str) → dict**
  - Returns: {consensus: "Buy"|"Hold"|"Sell", target_price, num_analysts,
    strong_buy, buy, hold, sell, strong_sell}

- **get_sentiment_score(ticker: str) → SentimentData**
  - Aggregates news sentiment + analyst consensus into overall score (-1.0 to 1.0)

### 6. app/tools/peer_comparison.py
Mock tool for competitive analysis:

- **get_peers(ticker: str) → List[str]**
  - Returns 4-5 peer tickers for the given ticker's sector
  - Example: AAPL → [MSFT, GOOGL, SAMSUNG, DELL, HPQ]

- **compare_peers(ticker: str, peers: List[str]) → List[PeerComparison]**
  - Returns comparison data for ticker vs. peers
  - Each: {ticker, company_name, market_cap, pe_ratio, revenue_growth,
    operating_margin, roe}

### 7. app/services/report_store.py
In-memory report storage (simulates a database):

- **ReportStore** class with:
  - create_report(request: GenerateRequest) → str (returns report_id)
  - get_report(report_id: str) → AlphaReport | None
  - update_report(report_id: str, updates: dict) → None
  - update_status(report_id: str, status: str, current_step: str) → None
  - add_section(report_id: str, section: ReportSection) → None
  - list_reports() → List[AlphaReport]
  - delete_report(report_id: str) → bool
  - get_progress(report_id: str) → GenerationProgress

- Store reports in a dict keyed by report_id
- Track generation progress (steps completed, current agent, elapsed time)
- Thread-safe (use asyncio.Lock)

### 8. app/services/context.py
Session and report context management:

- **ReportContext** dataclass:
  - report_id: str
  - session_id: str
  - user_id: str
  - ticker: str
  - investment_horizon: str
  - risk_tolerance: str
  - focus_areas: List[str]
  - gathered_data: dict (accumulates data from tools across agents)

- **ContextManager** class:
  - create_context(request, report_id) → ReportContext
  - get_context(report_id) → ReportContext
  - update_gathered_data(report_id, key, data) → None

### 9. app/config.py
Environment configuration:

- All OpenAI settings (key, base URL, models)
- Dynatrace settings (env URL, API token)
- App settings (port, service name, log level)
- OpenInference privacy settings
- Sensible defaults for local development

## Key Requirements
- All mock data must be REALISTIC — use actual-looking financial numbers
- Tools must have consistent signatures suitable for OpenAI function calling
- Each tool function must include a docstring that serves as the tool description
  for OpenAI's tool schema
- Tools must return Pydantic models (serializable to JSON)
- Include a TOOL_DEFINITIONS list that exports OpenAI-compatible tool schemas
  for all tools (to be used by agents in Prompt 3)
- Add logging to every tool call: logger.info(f"Tool called: {tool_name}({args})")