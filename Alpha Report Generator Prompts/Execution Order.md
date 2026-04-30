---

## 🏁 Execution Order Summary

| # | Prompt | What It Produces | Depends On |
|---|--------|-----------------|------------|
| 0 | **Context Seed** | Architecture, domain context, input parameters | — |
| 1 | **Scaffolding** | Full directory structure, configs, types, dependencies | Prompt 0 |
| 2 | **Mock Tools & Data** | Financial data tools, Pydantic models, report store | Prompt 1 |
| 3 | **AI Agents & Orchestrator** | 5 specialized agents, orchestrator, FastAPI routes | Prompt 2 |
| 4 | **OpenInference Instrumentation** | Full instrumentation layer on Python app | Prompt 3 |
| 5 | **Next.js Frontend** | Dashboard, report builder, report viewer, API proxy | Prompt 1 |
| 6 | **Docker & OneAgent Config** | Docker, scripts, OneAgent features, OpenPipeline rules | Prompts 4-5 |
| 7 | **Validation & DQL** | DQL queries, troubleshooting, cheat sheet | All |

> 💡 **Note**: Prompts 4 and 5 are independent of each other — you can run them in either order or in parallel.
