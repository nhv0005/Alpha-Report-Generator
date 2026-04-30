# Prompt 3: Python Alpha Engine — AI Agents, Orchestrator & Route Handlers

Create the multi-agent AI system that generates Alpha Reports. Each agent is a
specialized LLM caller with a focused system prompt and access to specific tools.
The orchestrator coordinates them sequentially to build the full report.

Do NOT include instrumentation code yet — that comes in Prompt 4. Focus on clean
agent logic and report assembly.

## Files to Create

### 1. app/agents/research_agent.py
**Purpose**: Gather raw data about the target company/asset

- System prompt: "You are a senior equity research analyst at a top-tier
  investment bank. Your role is to gather and synthesize company data,
  market positioning, and recent developments. Be thorough and factual."
- Tools available: get_price_data, get_financial_metrics, get_quarterly_earnings,
  search_news, get_peers
- **research(context: ReportContext) → dict**:
  1. Call get_price_data(ticker) → store in context
  2. Call get_financial_metrics(ticker) → store in context
  3. Call get_quarterly_earnings(ticker) → store in context
  4. Call search_news(ticker) → store in context
  5. Call get_peers(ticker) → store in context
  6. Use LLM with tool results to produce a "Company Overview" section (markdown)
  7. Return: {company_profile, price_data, financial_metrics, earnings,
     news, peers, company_overview_section}

### 2. app/agents/analysis_agent.py
**Purpose**: Perform fundamental and technical analysis

- System prompt: "You are a quantitative analyst specializing in equity valuation
  and technical analysis. Provide data-driven insights with specific numbers.
  Use standard valuation frameworks: DCF, comparable analysis, sum-of-parts."
- Tools available: get_financial_metrics, compare_peers
- **analyze(context: ReportContext) → dict**:
  1. Receive gathered research data from context
  2. Call compare_peers(ticker, peers) → peer comparison
  3. Use LLM to produce:
     - "Fundamental Analysis" section (valuation, growth, profitability)
     - "Technical Analysis" section (price action, momentum, support/resistance)
     - Target price calculation with methodology
     - Valuation table (current vs. peers vs. historical)
  4. Return: {fundamental_section, technical_section, target_price,
     valuation_data, peer_comparison}

### 3. app/agents/sentiment_agent.py
**Purpose**: Analyze market sentiment and news flow

- System prompt: "You are a sentiment analysis specialist tracking market
  narratives, news flow, and social media sentiment for equities. Quantify
  sentiment where possible and identify narrative shifts."
- Tools available: search_news, get_analyst_ratings, get_sentiment_score
- **analyze_sentiment(context: ReportContext) → dict**:
  1. Call get_sentiment_score(ticker) → overall sentiment
  2. Call get_analyst_ratings(ticker) → consensus
  3. Use LLM to produce:
     - "Sentiment Analysis" section (news themes, narrative analysis)
     - Sentiment score breakdown
     - Key headline analysis
  4. Return: {sentiment_section, sentiment_data, analyst_ratings}

### 4. app/agents/risk_agent.py
**Purpose**: Identify and quantify risks

- System prompt: "You are a risk management specialist at a hedge fund. Your job
  is to identify, categorize, and quantify risks for investment positions. Think
  about: market risk, sector risk, company-specific risk, regulatory risk,
  execution risk, and macro risk. Be contrarian — always consider the bear case."
- Tools available: get_financial_metrics (for debt/liquidity ratios)
- **assess_risk(context: ReportContext) → dict**:
  1. Review all gathered data from context
  2. Use LLM to produce:
     - "Risk Assessment" section with risk matrix
     - Bear case scenario with target price
     - Risk rating: LOW / MEDIUM / HIGH / VERY_HIGH
     - Top 5 risks ranked by probability × impact
  3. Return: {risk_section, risk_rating, bear_case_target, top_risks}

### 5. app/agents/writer_agent.py
**Purpose**: Compose the final polished Alpha Report

- System prompt: "You are a senior investment writer at a premier research firm.
  Your writing is clear, concise, and compelling. You synthesize complex analysis
  into executive-ready narratives. Format all output in clean Markdown with
  headers, bullet points, bold key figures, and tables where appropriate."
- No tools — pure LLM synthesis
- **compose_report(context: ReportContext) → dict**:
  1. Receive ALL sections from prior agents
  2. Use LLM to produce:
     - "Executive Summary" — synthesize all findings into 3-4 paragraph overview
       with clear thesis, conviction level, target price, risk/reward
     - "Catalyst Identification" — upcoming events and catalysts
     - "Recommendation" — final BUY/HOLD/SELL with conviction score (1-10),
       one-liner thesis, target price, timeframe
  3. Polish and unify the tone across all sections
  4. Return: {executive_summary_section, catalysts_section,
     recommendation_section, recommendation, conviction_score}

### 6. app/agents/orchestrator.py
**Purpose**: Coordinate all agents sequentially to build the complete report

- **generate_alpha_report(request: GenerateRequest, report_store, context_mgr) → AlphaReport**:
  1. Create report entry (status: "pending")
  2. Create context from request
  3. Update status → "researching"
     - Run research_agent.research(context)
     - Add "Company Overview" section to report
  4. Update status → "analyzing"
     - Run analysis_agent.analyze(context) — produces 2 sections
     - Run sentiment_agent.analyze_sentiment(context)
     - Add "Fundamental Analysis", "Technical Analysis", "Sentiment" sections
  5. Update status → "assessing_risk"
     - Run risk_agent.assess_risk(context)
     - Add "Risk Assessment" section
  6. Update status → "writing"
     - Run writer_agent.compose_report(context)
     - Add "Executive Summary", "Catalysts", "Recommendation" sections
  7. Assemble final report:
     - Calculate total tokens across all agents
     - Calculate total generation time
     - Set recommendation, conviction_score, target_price, risk_rating
     - Set upside_percentage = (target_price - current_price) / current_price * 100
     - Set status → "complete"
  8. Return completed AlphaReport

- Must handle errors gracefully: if any agent fails, set status → "error"
  and include partial report

### 7. app/routes/alpha.py
FastAPI router:

- **POST /api/alpha/generate** — Start report generation
  - Accepts GenerateRequest
  - Starts generation in background (asyncio.create_task)
  - Returns immediately: {report_id, status: "pending"}

- **GET /api/alpha/status/{report_id}** — Poll generation progress
  - Returns GenerationProgress

- **GET /api/alpha/reports** — List all generated reports
  - Returns List[AlphaReport] (summary view — truncated sections)

- **GET /api/alpha/reports/{report_id}** — Get full report
  - Returns complete AlphaReport with all sections

- **DELETE /api/alpha/reports/{report_id}** — Delete a report

### 8. app/routes/health.py
- **GET /health** — Returns service name, version, model config, timestamp

### 9. app/routes/embeddings.py
- **POST /api/embeddings** — Generate embeddings for report content
  - Use case: similarity search across reports (future feature)
  - Accepts: {text: str, model?: str}
  - Returns: {embeddings, model, usage, dimensions}

### 10. app/main.py
- Create FastAPI app with CORS middleware
- Include all routers
- Initialize ReportStore and ContextManager as app.state
- Initialize AIService / OpenAI client as shared dependency
- Startup/shutdown events
- Request logging middleware

## Key Requirements
- Each agent must use a DIFFERENT system prompt tailored to its specialty
- Each agent must call tools via OpenAI function calling (not just mock data directly)
  — the LLM decides which tools to call based on the context
- The tool-calling loop must be complete: request → tool_calls → execute → response
- Agents must be composable — the orchestrator passes context between them
- All OpenAI calls must use async/await (AsyncOpenAI)
- Each section must track which agent produced it and how many tokens were used
- The orchestrator must update report status in real-time for progress polling
- Include proper error handling with try/except in each agent
- Add logging throughout: logger.info(f"[{agent_name}] Starting {task}...")
- Code must work standalone: uvicorn app.main:app --port 8000 --reload