# Under the Hood: A 2-Week Course on Modern AI Frameworks

**Audience**: Engineers who use LLM APIs or agent frameworks (LangChain, LangGraph, CrewAI, OpenAI Agents SDK, etc.) and want to understand what they actually do internally.

**Method**: The Alpha Report Lab repo deliberately *does not* use a high-level agent framework. Every abstraction you'd get from a library is hand-written here:

| Framework concept | Where it lives in this repo |
|---|---|
| LLM client | `alpha-engine/app/agents/llm_client.py` |
| System / user prompts | Top of each agent file in `alpha-engine/app/agents/` |
| Tool schemas (function calling) | `alpha-engine/app/tools/definitions.py` |
| Tool execution / registry | `execute_tool()` in `llm_client.py` + `TOOL_REGISTRY` |
| Agent = LLM + tools + state | `research_agent.py`, `analysis_agent.py`, etc. |
| Orchestrator / graph | `alpha-engine/app/agents/orchestrator.py` |
| Memory / context | `alpha-engine/app/services/context.py` + `report_store.py` |
| Tracing / observability | `alpha-engine/app/instrumentation.py` |
| Server / streaming | `alpha-engine/app/main.py` + `app/routes/alpha.py` |

Each day has: **Read**, **Explain**, **Exercise**. Budget 60–120 minutes/day. Exercises build on each other and mostly modify files in place — use `git stash` or a branch per day.

## Prereqs

- Repo set up per `README.md`, engine + frontend running.
- An `OPENAI_API_KEY` in `alpha-engine/.env`.
- Comfort with Python, async/await, HTTP, JSON. TypeScript helpful for frontend days.

---

# Week 1 — The Primitives

## Day 1 — The shape of an LLM call

**Goal**: Understand what every framework is ultimately wrapping.

**Read**:
- `alpha-engine/app/agents/llm_client.py` — the `AsyncOpenAI` singleton.
- `alpha-engine/app/agents/research_agent.py` lines around the `client.chat.completions.create(...)` call.

**Explain**:
- An LLM API call is just a POST with `model`, `messages` (list of `{role, content}`), optional `temperature`, `tools`, `tool_choice`, `response_format`.
- Everything you read in LangChain/etc. eventually lowers to this one HTTP call. "Chains", "runnables", "prompts" — all syntactic sugar.
- `AsyncOpenAI` exists so you can `await` and run many calls concurrently (critical for multi-agent systems).

**Exercises**:
1. Add a `scripts/llm_hello.py` (not committed) that imports `get_openai_client()` and calls `chat.completions.create` with a trivial prompt. Print `response.choices[0].message.content` and `response.usage`.
2. Run the same prompt at `temperature=0` three times, then `temperature=1.2` three times. Observe determinism vs. variance.
3. Measure latency with `time.perf_counter()` around the call. Then run 5 calls sequentially vs. `asyncio.gather(...)` of 5. Note the wall-clock difference — this is why agents are async.

## Day 2 — Prompts as interfaces

**Goal**: See that "prompt engineering" is just designing the input contract.

**Read**:
- System prompts at top of `research_agent.py`, `analysis_agent.py`, `risk_agent.py`, `sentiment_agent.py`, `writer_agent.py`.
- How each agent templates a user prompt from `context.gathered_data`.

**Explain**:
- System prompt = role / persona / output format contract.
- User prompt = task + concrete data substituted in.
- Temperature per agent is tuned: research 0.3, analysis 0.25 (more deterministic), writer higher (more creative synthesis).

**Exercises**:
1. Change `RESEARCH_SYSTEM_PROMPT` in `research_agent.py` to "Respond only in JSON with keys `headline`, `thesis`, `risks`." Rerun a report and observe how the downstream sections break. This teaches why agents have brittle implicit contracts.
2. Revert, then add an explicit "Output schema" section to the prompt describing the exact Markdown headings it must produce. Confirm the report becomes more consistent.
3. Move the system prompt out of the Python file into a `prompts/research.md` file loaded with `Path(...).read_text()`. This is the first step toward what frameworks call "prompt templates".

## Day 3 — Tools as JSON Schema

**Goal**: Demystify OpenAI "function calling" / "tools".

**Read**:
- `alpha-engine/app/tools/definitions.py` — `TOOL_DEFINITIONS` (OpenAI schema) and `TOOL_REGISTRY` (name → callable).
- `execute_tool()` in `llm_client.py`.
- `alpha-engine/app/tools/market_data.py` for a concrete tool implementation.

**Explain**:
- A "tool" to the LLM is *just a JSON Schema*. The LLM is trained to emit a JSON object that validates against that schema when it decides the tool should run.
- Your app does the actual execution and feeds the result back as a `role: "tool"` message. The LLM never runs anything.
- This is the entire mechanism behind LangChain's `@tool`, CrewAI tools, OpenAI Agents SDK tools, MCP servers, etc.

**Exercises**:
1. Add a new mock tool `get_insider_transactions(ticker)` returning a hardcoded list. Register it in `TOOL_REGISTRY` and add its JSON Schema to `TOOL_DEFINITIONS`.
2. Write a `scripts/tool_loop.py` that: sends a user message "Should I buy AAPL? Use tools." with `tools=TOOL_DEFINITIONS`, then implements the agent loop manually: while the response contains `tool_calls`, execute each via `execute_tool()`, append the results as tool messages, and call the model again. Stop when the model responds with plain text. **This is what LangChain's `AgentExecutor` does.**
3. Intentionally break one tool's schema (remove `required`) and observe how the model starts calling it with missing args.

## Day 4 — Agents as loops vs. pipelines

**Goal**: Recognize two fundamentally different "agent" architectures.

**Read**:
- `research_agent.py` end-to-end. Notice: it *never* gives the LLM a choice. The Python code calls each tool directly, then passes the results into a single LLM call for synthesis.
- Contrast with your Day 3 Exercise 2 — there the LLM decides which tools to call.

**Explain**:
- **Scripted pipeline** (what this repo uses): deterministic, cheap, easy to trace. Fewer tokens, no loops, predictable cost. Downside: no adaptation.
- **ReAct / tool-calling loop**: LLM plans, calls tools, observes, repeats. Flexible, but variable cost, can loop forever, harder to debug.
- LangGraph, OpenAI Agents SDK, and CrewAI are largely about making one or the other safer.

**Exercises**:
1. Rewrite `research_agent.research()` as a true ReAct loop: give the model all research-related tools (`get_company_profile`, `get_price_data`, `get_financial_metrics`, `get_quarterly_earnings`, `search_news`, `get_peers`) via `tools=`, and let it choose what to call. Cap iterations at 6. Compare token usage and latency.
2. Add a `max_iterations` and `budget_tokens` guardrail to your loop. This is exactly the job of `AgentExecutor.max_iterations`.
3. Write a short note in `docs/notes-day4.md`: when would you pick the scripted pipeline over the loop for each of the 5 agents? Consider the research agent vs. a hypothetical "investigator" that must pivot based on findings.

## Day 5 — State, memory, and context windows

**Goal**: See how multi-agent systems actually share data.

**Read**:
- `alpha-engine/app/services/context.py` — `ReportContext` and `ContextManager`.
- `alpha-engine/app/services/report_store.py` — the in-memory report store with status updates.
- `orchestrator.py` — how each agent reads prior agents' output from `context.gathered_data` via `context_mgr.update_gathered_data(...)`.

**Explain**:
- There are two kinds of "memory":
  - **Agent-internal**: the `messages` list sent to the LLM (the context window).
  - **System-level**: structured state shared across agents (this repo uses a Python object; LangGraph uses a `TypedDict` state graph; CrewAI uses `Task.context`).
- Nothing magical happens — it's just a dict being mutated and re-templated into prompts.
- **Context window management** = deciding what fraction of the shared state to actually serialize into the next LLM call. Watch `serialize(peer_comparison)[:1200]` in `analysis_agent.py` — a hard truncation. That's memory management.

**Exercises**:
1. Add a `token_budget` field to `ReportContext`. Before each LLM call in one agent, estimate tokens with `len(prompt)//4` and warn if over budget.
2. Replace the `[:1200]` truncation in `analysis_agent.py` with a smarter summarizer: one cheap `gpt-4o-mini` call that compresses `peer_comparison` to ~300 tokens. This is what LangChain's `ConversationSummaryMemory` does.
3. Make the `ReportStore` persistent: write each report to `data/reports/<id>.json` on finalize. Load on startup. Now you have durable memory — the foundation of long-running agents.

## Day 6 — The orchestrator is just a state machine

**Goal**: See that agent frameworks are mostly directed graphs.

**Read**:
- `alpha-engine/app/agents/orchestrator.py` top-to-bottom, slowly.
- The `await report_store.update_status(...)` calls — these are the "edges" of the graph visible to the UI.
- The `_checkpoint()` cancellation pattern.

**Explain**:
- This file is a hard-coded DAG: research → (analysis ∥ sentiment) → risk → writer → finalize.
- LangGraph would express this as nodes + edges + a shared state type. The runtime difference is close to zero — LangGraph just adds visualization, conditional edges, retries, and persistence.
- Cancellation via checkpoints between stages (not mid-LLM-call) is the correct design — study it. Most homegrown agents get this wrong.

**Exercises**:
1. Draw the DAG on paper, labeling each edge with what state gets read/written.
2. Parallelize `analysis_agent` and `sentiment_agent` with `asyncio.gather`. They don't depend on each other. Measure the latency drop. Add tracing (Day 8) to confirm spans overlap.
3. Add a conditional edge: if `risk_rating == "extreme"`, skip the writer and go straight to a minimal "do not invest" summary. This is a LangGraph `add_conditional_edges` by hand.

## Day 7 — Review + end-to-end trace

**Goal**: Consolidate Week 1 by tracing a single report generation across every layer.

**Exercise** (one long one):
1. Generate a report for `NVDA` from the UI.
2. Open the engine logs and the report JSON in `ReportStore`.
3. Produce a diagram (ASCII, Mermaid, or image) in `docs/notes-day7.md` showing:
   - HTTP POST `/api/alpha/generate` → route → background task → orchestrator.
   - Each agent call, each tool call inside it, each LLM call.
   - Where state flows between agents.
   - Where the response gets streamed back to the frontend (poll `/status/{id}`).
4. Identify the single highest-latency step and write one sentence on how you'd reduce it.

---

# Week 2 — Production Concerns

## Day 8 — Observability: OpenTelemetry + OpenInference

**Goal**: Understand how AI-aware tracing actually works.

**Read**:
- `alpha-engine/app/instrumentation.py` — `setup_instrumentation()`.
- The `tracer.start_as_current_span("...")` blocks in each agent.
- The `OpenAIInstrumentor().instrument(...)` call — this **monkey-patches** `openai` at import time to auto-emit spans.
- The comment at top of `main.py`: instrumentation must run *before* the OpenAI client is constructed.

**Explain**:
- OTel = vendor-neutral tracing. A span = a timed operation with attributes, parent/child relationships, and a trace ID.
- OpenInference = a **semantic convention** on top of OTel for AI workloads. It defines attribute names like `openinference.span.kind` (`AGENT`, `CHAIN`, `TOOL`, `LLM`), `input.value`, `output.value`, `llm.token_count.total`.
- Dynatrace, Arize, Phoenix, Langfuse all read these same conventions.
- This is why you can swap vendors without rewriting instrumentation — vs. LangSmith which is LangChain-locked.

**Exercises**:
1. Run `./tasks.sh run-engine` and watch the console for `OTLP exporter configured -> ...`. If `DT_ENV_URL` isn't set, spans go nowhere — confirm by commenting it out.
2. Add a `TOOL` span around a new tool you write (follow the `_wrap_tool` helper pattern in `research_agent.py`).
3. Add a custom span attribute `report.ticker` to the `alpha_orchestrator` span. Verify in Dynatrace (or print via a `ConsoleSpanExporter` if you don't have DT) that it appears.
4. Break the rule: import `openai` and build a client *before* `setup_instrumentation()`. Observe that no spans appear for that client's calls. This teaches why monkey-patching order matters.

## Day 9 — Streaming and async

**Goal**: Understand how "typing" UIs work.

**Read**:
- `alpha-engine/app/routes/alpha.py` — the `/generate` and `/status/{id}` endpoints.
- How the frontend polls status (search for `PYTHON_SERVICE_URL` in `alpha-frontend/src/app/api/`).

**Explain**:
- Two patterns for long-running AI work:
  - **Poll** (what this repo does): client creates a job, polls status. Simple, robust, resumable.
  - **Stream** (SSE / WebSocket): server pushes tokens or events as they happen. Better UX, harder ops.
- OpenAI's `stream=True` yields `ChatCompletionChunk`s via an async iterator. Same request body, different consumption.

**Exercises**:
1. In `writer_agent.py`, switch the recommendation LLM call to `stream=True` and print chunks as they arrive. Measure time-to-first-token vs. the original total latency.
2. Add a new endpoint `POST /api/alpha/stream-summary` that streams an executive summary for a completed report using Server-Sent Events (`text/event-stream`). FastAPI has `StreamingResponse` for this.
3. Consume that SSE endpoint from a new React component. This is the full stack behind "ChatGPT-style" UIs.

## Day 10 — Evaluation and regression

**Goal**: Learn why shipping LLM apps is hard, and what eval frameworks actually do.

**Read**:
- The recommendation/conviction fields on the finalized report in `orchestrator.py`.
- Any existing eval/test files (likely none; you'll add them).

**Explain**:
- LLM outputs are non-deterministic, so normal unit tests fail. Evaluation frameworks (Ragas, DeepEval, Phoenix, Braintrust) run your system against a dataset and score each output with:
  - **Deterministic checks**: JSON validity, required keys, target price > 0.
  - **LLM-as-judge**: another model grades against a rubric.
  - **Reference-based**: compare to a golden answer (BLEU/Rouge/cosine).

**Exercises**:
1. Create `alpha-engine/eval/dataset.jsonl` with 5 tickers and expected properties (e.g. `AAPL` → sector must be "Technology"; target price must be within 50% of current).
2. Write `alpha-engine/eval/run_eval.py` that: loads the dataset, calls the orchestrator for each, asserts deterministic checks, and writes pass/fail to `eval/results.json`.
3. Add one LLM-as-judge check: given the final report Markdown, ask `gpt-4o-mini` "Is this a coherent investment thesis? Answer JSON `{score: 1-5, reason: str}`." Aggregate average score.
4. Run eval twice and compare — score variance is the real challenge. Discuss in `docs/notes-day10.md`: how many samples do you need for statistical confidence?

## Day 11 — Guardrails, errors, and retries

**Goal**: Make the system robust the way production frameworks do.

**Read**:
- The `except _CancelledByUser` / `except Exception` blocks in `orchestrator.py`.
- The minimal error handling in each agent (mostly absent — good learning opportunity).

**Explain**:
- Failure modes unique to LLM apps: rate limits (429), context-length errors, malformed JSON output, tool hallucination (calling unregistered tool), prompt injection, PII leakage.
- Frameworks like Guardrails AI, NeMo Guardrails, and the OpenAI Agents SDK's `input_guardrails` handle these.

**Exercises**:
1. Wrap every `chat.completions.create` in a helper `safe_chat()` that retries on `RateLimitError` with exponential backoff (2, 4, 8s) and raises a typed `LLMError` on persistent failure.
2. Add an output guardrail for `writer_agent`: if the recommendation isn't one of `BUY|HOLD|SELL`, re-prompt once with a stricter instruction. If still wrong, default to `HOLD` and set a `guardrail_triggered` flag on the report.
3. Add an input guardrail on `/api/alpha/generate`: if `ticker` isn't `[A-Z]{1,5}`, reject with 400 before doing any LLM work. Now compare: cost of each LLM guardrail vs. each deterministic one. Always prefer deterministic.

## Day 12 — Embeddings and retrieval

**Goal**: Understand the "R" in RAG without a vector DB.

**Read**:
- `alpha-engine/app/routes/embeddings.py` — the embeddings endpoint.
- Any news search code in `app/tools/news_search.py`.

**Explain**:
- Embeddings = map text → vector in ~1536-dim space. Similar meaning → small cosine distance.
- RAG = embed a query, do nearest-neighbor search over an embedded corpus, stuff top-k into the prompt.
- Vector DBs (Pinecone, Chroma, pgvector) are just "fast cosine search". You can do it with NumPy for <10k docs.

**Exercises**:
1. Write `scripts/build_news_index.py`: fetch all news from `search_news("AAPL", 90)` and `search_news("NVDA", 90)`, embed each headline with `client.embeddings.create(model="text-embedding-3-small", ...)`, save as a `.npy` matrix + a JSON sidecar of headlines.
2. Write `scripts/query_news.py` that takes a query string, embeds it, and returns the top-3 nearest headlines by cosine similarity (use `numpy`).
3. Integrate: add a new agent `rag_agent` that, given a report ticker, retrieves the top-5 most relevant headlines from the index and stuffs them into the sentiment agent's prompt. Measure the quality improvement (qualitatively).

## Day 13 — Cost, caching, and model routing

**Goal**: Make the system economical.

**Read**:
- `settings.OPENAI_MODEL` and `settings.OPENAI_FAST_MODEL` in `app/config.py`.
- Token counts returned as `response.usage.total_tokens` in each agent.

**Explain**:
- Per-call cost ≈ `input_tokens * in_price + output_tokens * out_price`. At scale, model choice per step dominates the bill.
- Strategies:
  - **Model routing**: cheap model for research/summarization, expensive for final synthesis.
  - **Prompt caching** (OpenAI, Anthropic): keep the static system prompt prefix identical so the provider caches it.
  - **Response caching**: hash of (model, messages) → cached response. Works great for eval re-runs.

**Exercises**:
1. Instrument cost: after each LLM call, compute $USD using a hardcoded price table and attach to the span as `llm.cost_usd`. Sum across the report.
2. Route `research_agent` and `sentiment_agent` to `OPENAI_FAST_MODEL`, keep `writer_agent` on `OPENAI_MODEL`. Re-run eval from Day 10 and compare cost vs. quality.
3. Add a simple `@lru_cache`-backed wrapper over `get_financial_metrics` and other tools. Then add an on-disk cache layer (`diskcache`) over the LLM client keyed by `sha256(model + messages_json)`. Re-running the same report should cost $0 after the first run.

## Day 14 — Capstone: build your own mini-agent framework

**Goal**: Compress everything you learned into a tiny reusable abstraction.

**Exercise**:
Build `alpha-engine/app/miniagent.py`, a ~150-line module that provides:

- `class Agent:` with fields `name`, `system_prompt`, `tools: list[callable]`, `model: str`.
- `.run(user_input: str, max_iterations: int = 6) -> str` that:
  - Auto-generates OpenAI tool schemas from the Python function signatures + docstrings (use `inspect` + type hints).
  - Runs the ReAct loop from Day 3 Exercise 2.
  - Emits OpenInference-compliant spans (`AGENT`, `LLM`, `TOOL`) like Day 8.
  - Enforces `max_iterations` and a token budget (Day 11).
  - Returns a structured result with `content`, `tool_calls_made`, `tokens_used`, `cost_usd`.

Then rewrite `sentiment_agent.py` using `Agent` to prove the abstraction is sufficient. Diff the line counts.

**Reflection** (write in `docs/notes-capstone.md`):
- Which framework concepts were trivial to build? Which were hard?
- What did LangChain / LangGraph / OpenAI Agents SDK add *on top of* your 150 lines?
- When would those additions be worth the learning curve and lock-in, vs. hand-rolling like this repo does?

---

# How to use this course

- **Solo**: one day per weekday, two weeks total. Commit exercises on a `course/day-N` branch.
- **With a study group**: meet at end of each week to compare diagrams and capstone designs.
- **As interview prep**: Days 3, 6, 8, and 14 are the highest-leverage for system-design conversations on AI infra.

# Further reading

- OpenAI API reference (chat, tools, embeddings, streaming).
- OpenInference semantic conventions: https://github.com/Arize-ai/openinference
- LangGraph concepts: https://langchain-ai.github.io/langgraph/concepts/
- "Building effective agents" (Anthropic): https://www.anthropic.com/research/building-effective-agents
- OpenTelemetry Python SDK docs.
