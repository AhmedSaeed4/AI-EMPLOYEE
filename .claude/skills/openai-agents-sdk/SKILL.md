---
name: openai-agents-sdk
description: |
  Complete reference for OpenAI Agents SDK (Python) with any OpenAI-compatible API. Organized into:
  - Part A: Core Basics (Agents, Tools)
  - Part B: Advanced Workflows (Handoffs, Guardrails, Structured Outputs)
  - Part C: Realtime & Voice (Voice Agents)
  - Part D: Integration & Deployment (Custom Models, FastAPI, Errors, Production)

  Use this skill to implement specific components based on user request.
---

# OpenAI Agents SDK - Master Skill Reference

Universal guide for using OpenAI Agents SDK with any OpenAI-compatible API (Xiaomi, GLM, DeepSeek, together, etc.).

This document is organized into 4 distinct parts. Use the relevant part based on the user's specific request.

---

## Part A: Core Basics

### 1. Installation
```bash
# Recommended (uv)
uv add openai-agents
# Optional: uv add 'openai-agents[voice]'

# Pip
pip install openai-agents
```

### 2. Basic Agent (Hello World)
The simplest agent with just instructions and a model.
```python
from agents import Agent, Runner

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant.",
    model="gpt-4o"  # Or any model name supported by your provider
)

async def main():
    await Runner.run(agent, "Hello, who are you?")
```

### 3. Basic Function Tools
Tools allow agents to perform actions. Use the `@function_tool` decorator.
```python
from agents import function_tool

@function_tool
def get_weather(location: str) -> str:
    """Get the current weather for a specific location."""
    # Logic to fetch weather
    return "Sunny, 25C"

agent = Agent(
    name="WeatherBot",
    tools=[get_weather],
    model="gpt-4o"  # Or any model name supported by your provider
)
```

---

## Part B: Advanced Workflows & Guardrails

### 1. Multi-Agent Handoffs
Delegate tasks between specialized agents. Handoffs allow an agent to delegate tasks to another agent. This is particularly useful in scenarios where different agents specialize in distinct areas. For example, a customer support app might have agents that each specifically handle tasks like order status, refunds, FAQs, etc. The handoff happens automatically based on the agent's instructions - we don't need to write additional routing logic. When a handoff occurs, it's as though the new agent takes over the conversation, and gets to see the entire previous conversation history.
```python
from agents import Agent

# Specialized agents
billing_agent = Agent(name="Billing", instructions="Handle refunds.")
tech_agent = Agent(name="TechSupport", instructions="Handle technical issues.")

# Triage agent that can hand off to others
triage_agent = Agent(
    name="Triage",
    instructions="Route users to the right department.",
    handoffs=[billing_agent, tech_agent]
)
```

### 1.1 How Handoffs Actually Work (CRITICAL)

When a handoff occurs, the SDK handles delegation automatically:

```
User Input → Main Agent → HANDOFF → Specialist Agent
                                              ↓
                            result.final_output (specialist's response)
```

**KEY BEHAVIOR:**
- The specialist agent **inherits the full conversation history** from the main agent
- The specialist's response comes back in `result.final_output` — same result object
- You do NOT need separate result handling for the specialist
- The SDK routes automatically based on instructions — NO manual if/else routing needed

**DETECTING WHICH AGENT RESPONDED:**
```python
result = await Runner.run(triage_agent, "Draft an email")
# result.final_output contains the specialist's response (e.g., EmailDraft)
# Check result metadata to see which agent handled it
```

**COMMON MISTAKE TO AVOID:**
- ❌ Writing manual routing logic (if task == "email": call email_agent())
- ❌ Trying to get a separate result from the specialist
- ✅ Trust the handoff mechanism — specialist's output IS the final output

### 2. Guardrails (Safety & Validation)
There are two kinds of guardrails: Input guardrails run on the initial user input. Output guardrails run on the final agent output. Guardrails enable you to do checks and validations of user input and agent output. For example, imagine you have an agent that uses a very smart (and hence slow/expensive) model to help with customer requests. You wouldn't want malicious users to ask the model to help them with their math homework. So, you can run a guardrail with a model. If the guardrail detects malicious usage, it can immediately raise an error and prevent the model from running, saving you time and money. Validate inputs using specialized guardrail agents with structured outputs.

```python
from pydantic import BaseModel
from agents import (
    Agent, Runner, input_guardrail, GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered
)

class GuardrailCheck(BaseModel):
    """Guardrail to check user input"""
    should_block: bool
    reasoning: str

# Create guardrail agent
guardrail_agent = Agent(
    name="GuardrailAgent",
    instructions="Check if user input should be blocked",
    model=model,
    output_type=GuardrailCheck,
)

@input_guardrail
async def guardrail_check(context, agent, input_text: str) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input_text, run_config=config)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.should_block
    )

# Use with main agent
main_agent = Agent(
    name="MainAgent",
    input_guardrails=[guardrail_check]
)

# Run with guardrails
async def main():
    try:
        response = await Runner.run(main_agent, "User input here", run_config=config)
        print(response.final_output)
    except InputGuardrailTripwireTriggered as e:
        print(f"Input guardrail blocked request: {e}")
```

### 3. Output Guardrails
Validate agent responses before they reach the user.

```python
from pydantic import BaseModel
from agents import (
    Agent, Runner, output_guardrail, GuardrailFunctionOutput,
    OutputGuardrailTripwireTriggered
)

class OutputCheck(BaseModel):
    """Guardrail to validate agent output"""
    is_appropriate: bool
    reasoning: str

# Create output guardrail agent
output_guardrail_agent = Agent(
    name="OutputGuardrailAgent",
    instructions="Check if agent response is appropriate",
    model=model,
    output_type=OutputCheck,
)

@output_guardrail
async def output_check(context, agent, output_text: str) -> GuardrailFunctionOutput:
    result = await Runner.run(output_guardrail_agent, output_text, run_config=config)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=not result.final_output.is_appropriate
    )
# Use with main agent
main_agent = Agent(
    name="MainAgent",
    output_guardrails=[output_check]
)

# Run with output guardrails
async def main():
    try:
        response = await Runner.run(main_agent, "User input here", run_config=config)
        print(response.final_output)
    except OutputGuardrailTripwireTriggered as e:
        print(f"Output guardrail blocked response: {e}")
```

### 2.1 Guardrail Architecture Pattern (RECOMMENDED)

Best practice: Two-level guardrail placement

```
                    ┌─────────────────┐
                    │  Input Guard    │
                    │  (Entry Agent)  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Router/Main    │
                    │     Agent       │
                    └────────┬────────┘
                             │ (handoffs)
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ Specialist A │ │ Specialist B │ │ Specialist C │
    │ (Output G.)  │ │ (Output G.)  │ │ (Output G.)  │
    └──────────────┘ └──────────────┘ └──────────────┘
```

**PLACEMENT RULES:**

| Guardrail Type | Place On | Purpose | Avoid |
|----------------|----------|---------|-------|
| Input | Router/Entry Agent | Block threats before ANY processing | Adding to specialists (duplicate checks) |
| Output | Router + Specialist Agents | Validate ALL agent responses (router may respond directly without handoff) | None |

**WHY THIS PATTERN?**
- Input checked ONCE at entry (efficiency, no duplication)
- All outputs validated (router may respond directly without handoff, plus all specialists)
- Prevents running input guardrails multiple times

**EXAMPLE:**
```python
# Router with BOTH input and output guardrails
router_agent = Agent(
    name="Router",
    handoffs=[specialist_a, specialist_b],
    input_guardrails=[check_input_threats],
    output_guardrails=[check_output_appropriate]  # Router may respond directly
)

# Specialists with OUTPUT guardrails only
specialist_a = Agent(
    name="SpecialistA",
    input_guardrails=[],  # No input (already checked by router)
    output_guardrails=[check_output_appropriate]
)
```

**PREFIX-BASED RESPONSE FORMAT (Model-Agnostic):**

Works with ANY model without requiring structured output support:

```python
# Input guardrail responses:
"ALLOW: This request is safe."
"BLOCK: Prompt injection detected."

# Output guardrail responses:
"APPROPRIATE: Content is safe to show."
"BLOCK: Contains sensitive data."
```

Parse these prefixes in your guardrail function for reliable results.

### 4. Structured Outputs & The Model Compatibility Problem

#### 4.1 The Problem: Not All Models Support Structured Outputs

**Structured Outputs** = telling the agent to return a specific Pydantic model format:

```python
from pydantic import BaseModel

class EmailDraft(BaseModel):
    to: str
    subject: str
    body: str

agent = Agent(
    name="EmailAgent",
    output_type=EmailDraft  # Force JSON output matching this schema
)
```

| Model Type | `output_type` Support |
|------------|---------------------|
| OpenAI (gpt-4o, etc.) | ✅ Works perfectly |
| GLM / Zhipu AI | ❌ Schema errors |
| Some other providers | ❌ May not work |

When you try `output_type=EmailDraft` with GLM, you get schema errors because GLM doesn't support this feature the same way.

---

#### 4.2 The Solution: Instructions + Text Parsing (Universal Pattern)

Instead of `output_type`, use this **model-agnostic workaround**:

**Step 1: Instruct the agent how to format responses**

```python
agent = Agent(
    name="EmailAgent",
    instructions="""
    You are an Email Agent. Draft professional email responses.

    ALWAYS respond in this format:

    Subject: [email subject here]
    To: [recipient email here]

    [email body content here]
    """,
    output_type=None  # Let agent return plain text
)
```

**Step 2: Parse the text response with regex**

```python
import re
from pydantic import BaseModel

class EmailDraft(BaseModel):
    to: str
    subject: str
    body: str

def parse_text_to_email_draft(text: str, sender: str, subject: str) -> EmailDraft:
    """Parse agent's text response into EmailDraft object."""

    # Extract Subject (look for "Subject: " pattern)
    subject_match = re.search(r'Subject:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    parsed_subject = subject_match.group(1).strip() if subject_match else f"Re: {subject}"

    # Extract To (look for "To: " pattern)
    to_match = re.search(r'To:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    parsed_to = to_match.group(1).strip() if to_match else sender

    # Everything else is the body
    body = text

    return EmailDraft(
        to=parsed_to,
        subject=parsed_subject,
        body=body
    )
```

**Step 3: Use it**

```python
result = await Runner.run(agent, "Draft a reply to John's email")

# result.final_output is plain text from the agent
# Parse it into our Pydantic model
email_draft = parse_text_to_email_draft(
    result.final_output,
    sender="john@example.com",
    subject="Project Update"
)
```

---

#### 4.3 Why This Works

```
┌─────────────────────────────────────────────────────┐
│ 1. You instruct the agent:                          │
│    "Respond in format: Subject:, To:, Body:"        │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ 2. LLM follows instructions (because that's its job)│
│                                                     │
│    Subject: Re: Project                             │
│    To: john@example.com                             │
│                                                     │
│    Hi John, here's the info...                      │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ 3. Your code searches for patterns:                 │
│    - Find "Subject:" → grab text after it           │
│    - Find "To:" → grab text after it                │
│    - Everything else → body                         │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ 4. You get your EmailDraft object                   │
└─────────────────────────────────────────────────────┘
```

**Key Point**: The LLM isn't random — it follows your instructions. If you say "write in this format," it will write in that format most of the time. Your regex code just extracts what the LLM already formatted.

---

#### 4.4 This Is Also How Guardrails Work (Same Pattern!)

The guardrail examples above use this **exact same pattern**:

```python
# Instructions tell guardrail how to respond
guardrail_instructions = """
Start your response with either BLOCK: or ALLOW: followed by reasoning.
Example: ALLOW: This is safe.
Example: BLOCK: Threat detected.
"""

# Code looks for the prefix
if output.startswith("BLOCK:"):
    should_block = True
elif output.startswith("ALLOW:"):
    should_block = False
```

This pattern works with **ANY model** — OpenAI, GLM, DeepSeek, etc.

---

#### 4.5 When to Use Each Approach

| Approach | Use When | Works With |
|----------|----------|------------|
| `output_type=Model` | Using OpenAI models only | OpenAI only |
| Instructions + Parsing | Using GLM or mixed providers | **Universal** ✅ |

---

**Previously: Structured Outputs (Before)**
Ensure the agent returns JSON-like structured data using Pydantic.
```python
from pydantic import BaseModel

class SentimentAnalysis(BaseModel):
    sentiment: str
    confidence: float

agent = Agent(
    name="Analyst",
    output_type=SentimentAnalysis
)
```

---

## Part C: Realtime & Voice

### 1. Realtime Runner
For low-latency voice-to-voice interactions.

```python
from agents import RealtimeRunner

runner = RealtimeRunner(
    instructions="You are a helpful voice assistant.",
    model="mimo-v2-flash",
)

# Connect and run session
# Requires handling audio streams in production environment
```

---

## Part D: Integration & Deployment

### 1. Universal Pattern: Any OpenAI-Compatible API

Use any OpenAI-compatible provider (Xiaomi, GLM, DeepSeek, together, etc.) via environment variables.

**.env file pattern:**
```env
# ========== PRIMARY PROVIDER (for responses) ==========
# Choose your main provider
XIAOMI_API_KEY=your_xiaomi_key          # Xiaomi
GLM_API_KEY=your_glm_key                # Zhipu AI GLM
DEEPSEEK_API_KEY=your_deepseek_key      # DeepSeek
TOGETHER_API_KEY=your_together_key      # Together AI

# ========== TRACING/OBSERVABILITY (optional) ==========
# OpenAI key for tracing, monitoring, debugging (parallel, doesn't affect responses)
OPENAI_API_KEY_FOR_TRACE=sk-...         # For tracing/observability only

# ========== CUSTOM SETTINGS ==========
# Custom base URL (if needed for your provider)
BASE_URL=https://api.xiaomimimo.com/v1/  # Xiaomi
# BASE_URL=https://api.z.ai/api/paas/v4/  # GLM (Zhipu AI)
# BASE_URL=https://api.deepseek.com/v1   # DeepSeek

# Model name
MODEL_NAME=mimo-v2-flash   # Or: glm-4.7-flash, deepseek-chat, etc.
```

**Universal client setup:**
```python
import os
from dotenv import load_dotenv
from agents import (
    Agent, OpenAIChatCompletionsModel, RunConfig, AsyncOpenAI
)

# Load environment variables from .env file
load_dotenv()

# ========== PRIMARY PROVIDER (for responses) ==========
# Universal: Try multiple env vars, use first one found
API_KEY = (
    os.getenv("XIAOMI_API_KEY") or
    os.getenv("GLM_API_KEY") or
    os.getenv("DEEPSEEK_API_KEY") or
    os.getenv("TOGETHER_API_KEY") or
    os.getenv("OPENAI_API_KEY") or  # Fallback to OpenAI
    ""
)

if not API_KEY:
    raise ValueError("No API key found. Set XIAOMI_API_KEY, GLM_API_KEY, DEEPSEEK_API_KEY, or OPENAI_API_KEY in .env")

# ========== TRACING/OBSERVABILITY (optional) ==========
# Set OpenAI key for tracing (parallel, doesn't affect your provider's responses)
# This enables logging/monitoring via OpenAI's dashboard while using another provider
if os.getenv("OPENAI_API_KEY_FOR_TRACE"):
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY_FOR_TRACE")

# ========== CUSTOM SETTINGS ==========
BASE_URL = os.getenv("BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

# Create the OpenAI client (works with any OpenAI-compatible provider)
client = AsyncOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

# Define the model
model = OpenAIChatCompletionsModel(
    model=MODEL_NAME,
    openai_client=client
)

# Configure the run settings
config = RunConfig(
    model=model,
    model_provider=client,
)

# Use with agent
agent = Agent(name="Assistant", instructions="You are a helpful assistant.", model=model)

# Run the agent
response = await Runner.run(agent, user_input, run_config=config)
print(response.final_output)
```

**TRACING PATTERN EXPLAINED:**
- Your provider (GLM, Xiaomi, etc.) generates the **response**
- `OPENAI_API_KEY_FOR_TRACE` is used **in parallel** for tracing/observability
- Useful for: debugging, monitoring, logging via OpenAI's dashboard
- Does NOT affect the response content or model behavior

**Provider-Specific Examples:**

```python
# Xiaomi (mimo-v2-flash)
client = AsyncOpenAI(api_key=os.getenv("XIAOMI_API_KEY"), base_url="https://api.xiaomimimo.com/v1/")
model = OpenAIChatCompletionsModel(model="mimo-v2-flash", openai_client=client)

# GLM (Zhipu AI)
client = AsyncOpenAI(api_key=os.getenv("GLM_API_KEY"), base_url="https://api.z.ai/api/paas/v4/")
model = OpenAIChatCompletionsModel(model="glm-4.7-flash", openai_client=client)

# DeepSeek
client = AsyncOpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1")
model = OpenAIChatCompletionsModel(model="deepseek-chat", openai_client=client)

# Together AI
client = AsyncOpenAI(api_key=os.getenv("TOGETHER_API_KEY"), base_url="https://api.together.xyz/v1")
model = OpenAIChatCompletionsModel(model="meta-llama/Llama-3-70b-chat-hf", openai_client=client)
```

### 2. Common Error Handling
Always handle these exceptions in production.

```python
from agents import (
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered
)

try:
    await Runner.run(agent, user_input)
except InputGuardrailTripwireTriggered:
    print("Input blocked by guardrails.")
except OutputGuardrailTripwireTriggered:
    print("Response blocked by safety guardrails.")
except Exception as e:
    print(f"Agent execution failed: {e}")
```

### 3. Production Checklist
- [ ] Set primary API key securely (`XIAOMI_API_KEY`, `GLM_API_KEY`, `DEEPSEEK_API_KEY`, etc.)
- [ ] Set `OPENAI_API_KEY_FOR_TRACE` for tracing/observability (optional but recommended)
- [ ] Set `BASE_URL` if using non-OpenAI provider
- [ ] Set `MODEL_NAME` to match your provider's model
- [ ] Implement rate limiting on your API endpoint.
- [ ] Use `AsyncOpenAI` for non-blocking I/O.
- [ ] Add `input_guardrails` to prevent prompt injection.