# Alpha Report Lab — Cheat Sheet

## Start the Lab (Windows PowerShell)

    .\tasks.ps1 setup       # create .env files
    # edit .env with API keys
    .\tasks.ps1 install     # pip + npm installs
    .\tasks.ps1 start       # engine in background, frontend in foreground

Browser: http://localhost:3000

## Individual Commands

    # Terminal 1 - Alpha Engine
    cd alpha-engine
    uvicorn app.main:app --port 8000 --reload

    # Terminal 2 - Next.js Frontend
    cd alpha-frontend
    npm run dev

## Quick Test Commands (PowerShell)

Generate NVDA report (via frontend proxy):

    $body = @{ ticker="NVDA"; investment_horizon="medium_term"; risk_tolerance="moderate" } | ConvertTo-Json
    $r = Invoke-RestMethod -Uri http://localhost:3000/api/alpha/generate -Method Post -ContentType "application/json" -Body $body
    $r | ConvertTo-Json

Check status:

    Invoke-RestMethod http://localhost:3000/api/alpha/status/$($r.report_id) | ConvertTo-Json

Get full report:

    Invoke-RestMethod http://localhost:3000/api/alpha/reports/$($r.report_id) | ConvertTo-Json -Depth 5

List all reports:

    Invoke-RestMethod http://localhost:3000/api/alpha/reports | ConvertTo-Json -Depth 3

Health checks:

    Invoke-RestMethod http://localhost:8000/health
    Invoke-RestMethod http://localhost:3000/api/health

## Task Runner Shortcuts

    .\tasks.ps1 test-health     # both services health
    .\tasks.ps1 test-generate   # single NVDA report
    .\tasks.ps1 test-flow       # full e2e with polling
    .\tasks.ps1 test-batch      # 5-ticker batch
    .\tasks.ps1 stop-all        # stop everything
    .\tasks.ps1 clean           # remove build artifacts

## Span Hierarchy Reference

    alpha_orchestrator (AGENT)
    ├── research_agent (CHAIN)
    │   ├── tool:get_price_data / get_financial_metrics / ... (TOOL)
    │   └── openai.chat (LLM, auto)
    ├── analysis_agent (CHAIN)
    │   ├── tool:compare_peers / get_technical_indicators (TOOL)
    │   └── 2x openai.chat (LLM)
    ├── sentiment_agent (CHAIN)
    │   ├── tool:get_sentiment_score / get_analyst_ratings (TOOL)
    │   └── openai.chat (LLM)
    ├── risk_agent (CHAIN)
    │   ├── tool:get_financial_metrics (TOOL)
    │   └── openai.chat (LLM)
    └── writer_agent (CHAIN)
        └── 3x openai.chat (LLM)
