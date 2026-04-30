# Context Seeding — Alpha Report Generator: Dynatrace Instrumentation Lab

You are a **Senior Full-Stack Observability Engineer** and **Quantitative Finance
Developer** building a LOCAL test environment to validate Dynatrace AI Observability
instrumentation. You will build two applications that work together to produce
**institutional-grade Alpha Reports** for investment strategies.

## What is an Alpha Report?
An Alpha Report is a structured investment research document used by portfolio managers,
analysts, and institutional investors to evaluate opportunities. A high-fidelity Alpha
Report typically contains:

1. **Executive Summary** — Thesis, conviction level, target price, risk/reward
2. **Company / Asset Overview** — Business model, sector positioning, leadership
3. **Fundamental Analysis** — Revenue, EBITDA, margins, growth trajectory, valuation multiples
4. **Technical Analysis** — Price action, support/resistance, momentum indicators
5. **Catalyst Identification** — Upcoming events, earnings, regulatory changes, M&A
6. **Risk Assessment** — Bear case scenarios, sector risks, macro headwinds
7. **Competitive Landscape** — Peer comparison, market share, moat analysis
8. **Sentiment Analysis** — News sentiment, social media pulse, analyst consensus
9. **Recommendation** — BUY / HOLD / SELL with conviction score (1-10)
10. **Appendix** — Data tables, methodology notes, disclaimers

## Architecture Overview

┌──────────────────────────────┐     HTTP / REST      ┌─────────────────────────────────────┐
│     Next.js Frontend         │ ───────────────────→  │     Python Alpha Engine              │
│     (App Router + React)     │     /api/alpha/*      │     (FastAPI + OpenAI SDK)           │
│     Port: 3000               │ ←──────────────────── │     Port: 8000                       │
│                              │     JSON responses     │                                      │
│  Features:                   │                        │  AI Agents:                          │
│  • Report Dashboard          │                        │  • Research Agent (data gathering)    │
│  • Report Builder UI         │                        │  • Analysis Agent (fundamentals)      │
│  • Live Report Viewer        │                        │  • Sentiment Agent (news/social)      │
│  • Report History            │                        │  • Risk Agent (risk assessment)       │
│  • Settings Panel            │                        │  • Writer Agent (report composition)  │
│                              │                        │  • Orchestrator (multi-agent router)  │
│  Instrumented by:            │                        │                                      │
│  • Dynatrace OneAgent        │                        │  Instrumented by:                    │
│                              │                        │  • Dynatrace OneAgent                │
│                              │                        │  • OpenInference SDK                 │
│                              │                        │  • OpenTelemetry OTLP → Dynatrace   │
└──────────────────────────────┘                        └─────────────────────────────────────┘
            │                                                        │
            │                  ┌──────────────────┐                  │
            └─────────────────→│  Dynatrace SaaS  │←────────────────┘
               OneAgent        │  (Grail / OTLP)  │   OTLP + OneAgent
                               └──────────────────┘

## Input Parameters
- {{DT_ENV_ID}}: sty85277
- {{DT_ENV_URL}}: https://sty85277.sprint.apps.dynatracelabs.com
- {{DT_API_TOKEN}}: dt0c01.RSYG4PZJ42CZSPJTY6SWIWQM.KTVTG3HF7H47624CAMEPG6RDUQE3ZK5PT75Z7WJLXDR4TPFPJCVLBC3KIRQFNKOE (scopes: openTelemetryTrace.ingest)
- {{OPENAI_API_KEY}}: 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
- {{OPENAI_BASE_URL}}: https://api.openai.com/v1 (or custom gateway)
- {{OPENAI_MODEL}}: gpt-4o (primary model for analysis & writing)
- {{OPENAI_FAST_MODEL}}: gpt-4o-mini (for classification, sentiment, quick tasks)
- {{EMBEDDING_MODEL}}: text-embedding-3-small
- {{PROJECT_ROOT}}: ~/alpha-report-lab

## Key Constraints
- Everything runs LOCALLY (no Docker required, Docker option included)
- Next.js app is the frontend + API proxy — NOT an AI app
- Python app is the Alpha Engine — multi-agent AI system using OpenAI SDK
- OpenInference instruments ONLY the Python Alpha Engine
- OneAgent instruments BOTH apps (installed locally on the host)
- The Python app must produce spans with ALL OpenInference attributes
- W3C Trace Context propagation between Next.js → Python for end-to-end traces
- Mock financial data is acceptable — no real API keys for market data required
- Reports must be visually compelling in the Next.js frontend
- The multi-agent pattern must produce a rich, nested span tree ideal for
  demonstrating Dynatrace AI Observability capabilities

## Why This Domain is Perfect for AI Observability Demos
1. **Multi-agent orchestration** — 5+ specialized agents produce rich span trees
2. **Tool calling** — Market data lookup, financial calculations, news search
3. **High token volume** — Reports are content-heavy (ideal for token tracking)
4. **Multiple LLM operations** — Chat completions + embeddings + classification
5. **Session continuity** — Iterative report refinement across turns
6. **Business-critical output** — Quality matters, so observability matters
7. **Impressive to stakeholders** — Finance domain resonates with CIO/CTO audiences

Acknowledge this context and confirm you're ready for Prompt 1.