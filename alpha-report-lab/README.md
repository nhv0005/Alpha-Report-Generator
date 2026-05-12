# Alpha Report Lab

**AI-Powered Investment Research - Dynatrace Instrumentation Demo**

A two-service application that generates institutional-grade Alpha Reports using
a multi-agent AI system, instrumented with Dynatrace OneAgent and OpenInference
for full AI Observability.

## Architecture

```
Next.js Frontend (3000) --HTTP--> Python Alpha Engine (8000)
       |                                 |
       | OneAgent                        | OneAgent + OpenInference
       +------> Dynatrace SaaS <---------+
```

## Prerequisites

- **Node.js 18+** - https://nodejs.org
- **Python 3.12+** - https://python.org
- **Dynatrace OneAgent** - installed locally on your machine
- **OpenAI API key** - or compatible endpoint
- **Dynatrace API token** - with `openTelemetryTrace.ingest` scope

## Running the Lab (Windows PowerShell)

All tasks are managed through `tasks.ps1` at the project root.

### First Time Setup

    .\tasks.ps1 setup          # Create .env files from templates
    # Edit .env with your API keys and Dynatrace credentials
    .\tasks.ps1 install        # Install Python + Node.js dependencies

### Start Services

    .\tasks.ps1 start          # Start both (engine background, frontend foreground)
    .\tasks.ps1 run-engine     # Start Python engine only
    .\tasks.ps1 run-frontend   # Start Next.js frontend only
    .\tasks.ps1 stop           # Stop foreground services
    .\tasks.ps1 stop-all       # Stop all services and background jobs

### Run Tests

    .\tasks.ps1 test-health    # Health check both services
    .\tasks.ps1 test-generate  # Generate a single NVDA report
    .\tasks.ps1 test-flow      # Full end-to-end flow test with polling
    .\tasks.ps1 test-batch     # Batch test 5 tickers sequentially

### Maintenance

    .\tasks.ps1 clean          # Remove build artifacts
    .\tasks.ps1 help           # Show all available tasks

### PowerShell Execution Policy
If you get an execution policy error, run this once in an elevated PowerShell:

    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

## OneAgent Configuration

After installing OneAgent, enable these features in
**Settings > Preferences > OneAgent features**:

| Feature                           | Required | Default  |
|-----------------------------------|----------|----------|
| Python                            | Yes      | Enabled  |
| Node.js                           | Yes      | Enabled  |
| Python FastAPI                    | Yes      | Enabled  |
| Python OpenAI                     | Disable* | Enabled  |
| OpenTelemetry (Python) [Opt-In]   | Yes      | Disabled |
| W3C Trace Context                 | Yes      | Enabled  |

*Disable Python OpenAI to avoid duplicate spans with OpenInference.

See `docs/oneagent-configuration.md` for full setup including Settings API automation.

## OpenPipeline Setup
See `docs/openpipeline-configuration.md` for attribute rename rules
(llm.* -> gen_ai.*).

## Validation
See `docs/validate-dynatrace.md` for the post-test checklist and DQL queries.

## Troubleshooting
See `docs/troubleshooting.md` and `docs/cheat-sheet.md`.

## Environment Variables

See `alpha-engine/.env.example` and `alpha-frontend/.env.local.example` for the complete reference.
See `.env.example` for the complete reference.
