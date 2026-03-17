# OpenAI Agents SDK Skill
(Context: You have access to expert knowledge about OpenAI Agents SDK with any OpenAI-compatible API in SKILL.md)

## ⚠️ CRITICAL INSTRUCTION: TARGETED OUTPUT ONLY
**DO NOT** generate the entire codebase or all examples at once.
**DO NOT** provide installation instructions or basics unless specifically asked.
**ONLY** implement the specific components requested by the user.
**NO FLUFF**: Skip generic introductions. Go straight to the solution.

## Interaction Guidelines

1. **Identify the "Part"**: Map the user's request to one of the **Skill Parts** below.
2. **Isolate Context**: Ignore information from other parts.
3. **Concise Implementation**: Provide *only* the code snippet necessary for that part.
4. **Xiaomi Specific**: Use "mimo-v2-flash" model and Xiaomi endpoint.

## Skill Parts (Use Independently)

### Part A: Core Basics
*Triggers*: "create agent", "simple assistant", "basic tool", "how to start"
*Focus*:
- `Agent` class initialization with Xiaomi model
- Basic `@function_tool`
- Simple `Runner.run()`

### Part B: Advanced Workflows & Guardrails
*Triggers*: "multi-agent", "handoff", "router", "safety", "validation", "guardrail"
*Focus*:
- `input_guardrail` / `output_guardrail`
- Handoff logic (agent-to-agent transfers)
- Structured outputs with Pydantic (OpenAI only) OR instructions + parsing (universal)

**CRITICAL BEHAVIOR NOTES (Read Before Implementing):**

1. **Handoff Output Handling**: When handoff occurs, `result.final_output` contains the SPECIALIST's response, NOT the router's. The router delegates, the specialist responds. You do NOT need separate result handling.

2. **Guardrail Placement**:
   - Input guardrails → ONLY on router/entry agent (check once, avoid duplicate checks)
   - Output guardrails → Router + ALL specialists (router may respond directly without handoff)
   - Input guardrails on specialists cause unnecessary duplicate checks

3. **No Manual Routing**: The SDK handles agent selection via `handoffs=[]`. Do NOT write if/else routing logic.

4. **Prefix-Based Guardrails**: For model compatibility, use "BLOCK:/ALLOW:/APPROPRIATE:" prefixes instead of relying on structured outputs.

5. **Structured Outputs Model Compatibility**:
   - OpenAI models → `output_type=Model` works natively
   - GLM / other providers → Use instructions + text parsing pattern (see SKILL.md section 4.2)
   - The parsing pattern works with ALL models (universal)

6. **Universal API Pattern**: Use environment variables (`XIAOMI_API_KEY`, `GLM_API_KEY`, `DEEPSEEK_API_KEY`, etc.) and optional `BASE_URL` for any OpenAI-compatible provider.

7. **Tracing Pattern**: Set `OPENAI_API_KEY_FOR_TRACE` (which maps to `OPENAI_API_KEY` in code) for observability/tracing alongside your provider key.

### Part C: Realtime & Voice
*Triggers*: "voice", "audio", "speech", "realtime", "conversation"
*Focus*:
- `RealtimeRunner`
- Voice-specific tools
- Audio buffer handling

### Part D: Integration & Deployment
*Triggers*: "api key", "base url", "custom model", "deploy", "env vars", "xiaomi", "glm", "deepseek"
*Focus*:
- Universal OpenAI-compatible API integration
- Environment variable pattern (API_KEY, BASE_URL, MODEL_NAME)
- `AsyncOpenAI` client setup with custom endpoints
- Provider-specific examples (Xiaomi, GLM, DeepSeek, Together, etc.)

## Response Format
When answering:
1. **Selection**: "I will implement the [Part Name] for you."
2. **Code**: [The specific snippet]
3. **Note**: Brief usage comment (1 line).