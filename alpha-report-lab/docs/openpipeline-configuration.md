# OpenPipeline Configuration — OpenInference to Dynatrace AI Obs Attribute Mapping

## Why This Is Needed
OpenInference emits span attributes under the `llm.*` namespace.
Dynatrace's AI Observability Explorer expects the `gen_ai.prompt.*` / `gen_ai.completion.*` namespace to populate the Prompt and Completion sections.

OpenPipeline's `fieldsRename` processor bridges this gap at ingestion time.

## Configuration Steps

### 1. Navigate to OpenPipeline
Settings > Process and contextualize > OpenPipeline > Spans.

### 2. Create a Custom Processing Rule
- **Rule name**: OpenInference to GenAI Attribute Mapping
- **Matcher**: `matchesValue(openinference.span.kind, "LLM") OR isNotNull(llm.model_name)`
- **Processor type**: `fieldsRename`

### 3. Field Rename Mappings

| #  | Source (OpenInference)                    | Target (Dynatrace AI Obs)        |
|----|------------------------------------------|----------------------------------|
| 1-20 | `llm.input_messages.{0..9}.message.content` | `gen_ai.prompt.{0..9}.content` |
|    | `llm.input_messages.{0..9}.message.role`    | `gen_ai.prompt.{0..9}.role`    |
| 21-24 | `llm.output_messages.{0..1}.message.content` | `gen_ai.completion.{0..1}.content` |
|     | `llm.output_messages.{0..1}.message.role`    | `gen_ai.completion.{0..1}.role`    |
| 25 | `llm.model_name`                           | `gen_ai.request.model`             |
| 26 | `llm.token_count.prompt`                   | `gen_ai.usage.input_tokens`        |
| 27 | `llm.token_count.completion`               | `gen_ai.usage.output_tokens`       |

Expand the `{0..9}` / `{0..1}` ranges to concrete rename entries in the UI.

### 4. Automate via Settings API (PowerShell)

    $headers = @{ "Authorization" = "Api-Token $env:DT_API_TOKEN"; "Content-Type" = "application/json" }
    Invoke-RestMethod -Uri "$env:DT_ENV_URL/api/v2/settings/schemas/builtin:openpipeline" -Method Get -Headers $headers | ConvertTo-Json -Depth 3

Note: OpenPipeline configuration is best done through the Dynatrace UI for complex `fieldsRename` rules with many mappings. Use the UI steps above for initial setup, then export via Settings API for automation.

### 5. Validation DQL Queries

Confirm rename is working:

    fetch spans
    | filter dt.service.name == "alpha-engine"
    | filter isNotNull(gen_ai.prompt.0.content)
    | fields span.name, gen_ai.prompt.0.role, gen_ai.prompt.0.content,
             gen_ai.completion.0.content, gen_ai.usage.input_tokens
    | limit 5

Compare source and target on same span:

    fetch spans
    | filter dt.service.name == "alpha-engine"
    | filter isNotNull(llm.model_name)
    | fields span.name, llm.model_name, gen_ai.request.model,
             llm.token_count.prompt, gen_ai.usage.input_tokens
    | limit 5
