## Assignment 1 — Generation Task Walkthrough

### What you’ll build
- **Structured summarizer** that:
  - Uses the OpenAI SDK with a model NOT in the GPT‑5 family (e.g., `gpt-4o-mini`).
  - Returns a Pydantic `BaseModel` with fields: `Author`, `Title`, `Relevance`, `Summary`, `Tone`, `InputTokens`, `OutputTokens`.
  - Separates developer (instructions) and user prompts.
  - Dynamically injects your cleaned `document_text` (from earlier cells).

### Why this structure works (theory)
- **Structured outputs**: Enforcing a schema reduces brittle parsing and keeps outputs predictable.
- **Dev vs user prompts**: Stable policy/rules (developer) separated from task/context (user) leads to more consistent behavior.
- **Token usage**: Pulling `input_tokens`/`output_tokens` enables measurement of cost and latency—vital in production.

### Prerequisites
- Kernel: `deploying-ai-env`.
- Earlier cells run and `document_text` contains your cleaned article text.
- `OPENAI_API_KEY` is loaded (via `%dotenv`).

If needed, install deps:
```bash
uv pip install --upgrade openai pydantic
```

---

### Step 1 — Define the Pydantic schema
```python
from typing import Optional
from pydantic import BaseModel, Field

class SummarySchema(BaseModel):
    Author: str = Field(..., description="Author of the article")
    Title: str = Field(..., description="Title of the article")
    Relevance: str = Field(..., description="One paragraph on relevance to AI professionals")
    Summary: str = Field(..., description="Concise summary, <=1000 tokens")
    Tone: str = Field(..., description="The tone used to produce the summary")
    InputTokens: Optional[int] = Field(default=None, description="Filled from response.usage")
    OutputTokens: Optional[int] = Field(default=None, description="Filled from response.usage")
```

Notes:
- Targets Pydantic v2 (e.g., `model_dump()` available).
- Token fields are optional; you’ll fill them from `response.usage`.

### Step 2 — Choose a non‑GPT‑5 model and set your tone
```python
MODEL_NAME = "gpt-4o-mini"   # NOT a GPT-5 family model
TONE = "Legalese"            # e.g., "Victorian English", "AAVE", "Formal Academic"
```

Tip: Pick a tone you can easily recognize—it helps during evaluation.

### Step 3 — Prepare developer and user prompts, inject context dynamically
```python
# Developer (instructions) prompt: rules and constraints
instructions = (
    "You are an information extraction and summarization assistant. "
    "Return output STRICTLY matching the provided JSON schema. "
    "Do not add fields. Do not include extra commentary. "
    "Write the Summary in the specified Tone and keep it under 1000 tokens. "
    "Use only facts from the provided document; avoid speculation or hallucinations."
)

# User prompt template with dynamic injection of tone and context
user_template = (
    "Task: Extract metadata and summarize the document in the specified tone.\n"
    "- Tone: {tone}\n"
    "- Fields to fill: Author, Title, Relevance (<=1 paragraph), Summary (<=1000 tokens), Tone.\n"
    "Token fields will be filled from response usage metrics.\n"
    "Document follows between <<< >>>. Use only its content.\n"
    "<<<\n{context}\n>>>"
)

user_content = user_template.format(tone=TONE, context=document_text)
```

Theory:
- Separate stable “policy” from per‑task instructions.
- Inject `document_text` instead of hard‑coding content.

### Step 4 — Call the OpenAI SDK with structured outputs
```python
from openai import OpenAI

client = OpenAI()  # Reads OPENAI_API_KEY from env

response = client.responses.parse(
    model=MODEL_NAME,
    response_format=SummarySchema,  # enforce schema; returns parsed object
    messages=[
        {"role": "developer", "content": instructions},
        {"role": "user", "content": user_content},
    ],
    max_output_tokens=1200,  # model still instructed to keep summary <=1000 tokens
)
```

Notes:
- `.parse(...)` maps output directly into your `SummarySchema`.

### Step 5 — Add token usage and finalize the structured result
```python
parsed: SummarySchema = response.output_parsed

result = parsed.model_copy(update={
    "Tone": TONE,
    "InputTokens": response.usage.input_tokens,
    "OutputTokens": response.usage.output_tokens,
})

print("Token usage:", response.usage)
print(result.model_dump_json(indent=2))
```

What to verify:
- `InputTokens`/`OutputTokens` are present and integers.
- JSON matches schema exactly.

### Step 6 — Sanity checks (recommended)
```python
# 1) Required fields present and non-empty
for field in ["Author", "Title", "Relevance", "Summary", "Tone"]:
    assert getattr(result, field) and isinstance(getattr(result, field), str), f"{field} missing/invalid"

# 2) Relevance <= 1 paragraph (simple heuristic)
assert result.Relevance.count(".") <= 6, "Relevance seems longer than a short paragraph"

# 3) Ensure token counts present
assert isinstance(result.InputTokens, int) and isinstance(result.OutputTokens, int), "Token counts missing"

# 4) Tone label preserved
assert result.Tone == TONE, "Tone label not preserved"
```

### Step 7 — Save for later evaluation
```python
import json
summary_json_path = "assignment_1_summary.json"
with open(summary_json_path, "w") as f:
    f.write(result.model_dump_json(indent=2))
summary_json_path
```

---

### Troubleshooting tips
- If parsing fails: increase `max_output_tokens`; reiterate schema strictness in the developer prompt.
- If tone or fields drift: strengthen instructions; enforce post‑hoc checks (as above).
- If token usage missing: ensure you’re calling the Responses API with a recent `openai` client.

### What to submit for this section
- The new code cells implementing Steps 1–7 in `assignment_1.ipynb`.
- Optionally, `assignment_1_summary.json` as an artifact for evaluation.

---

### One‑cell example (paste after your cleaning cell)
```python
# --- Structured Summarization with OpenAI Responses API ---

from typing import Optional
from pydantic import BaseModel, Field
from openai import OpenAI

# 1) Schema
class SummarySchema(BaseModel):
    Author: str = Field(..., description="Author of the article")
    Title: str = Field(..., description="Title of the article")
    Relevance: str = Field(..., description="One paragraph on relevance to AI professionals")
    Summary: str = Field(..., description="Concise summary, <=1000 tokens")
    Tone: str = Field(..., description="The tone used to produce the summary")
    InputTokens: Optional[int] = Field(default=None, description="Filled from response.usage")
    OutputTokens: Optional[int] = Field(default=None, description="Filled from response.usage")

# 2) Model + Tone
MODEL_NAME = "gpt-4o-mini"  # NOT GPT-5 family
TONE = "Legalese"

# 3) Prompts (separated) + dynamic context injection
instructions = (
    "You are an information extraction and summarization assistant. "
    "Return output STRICTLY matching the provided JSON schema. "
    "Do not add fields. Do not include extra commentary. "
    "Write the Summary in the specified Tone and keep it under 1000 tokens. "
    "Use only facts from the provided document; avoid speculation or hallucinations."
)

user_template = (
    "Task: Extract metadata and summarize the document in the specified tone.\n"
    "- Tone: {tone}\n"
    "- Fields to fill: Author, Title, Relevance (<=1 paragraph), Summary (<=1000 tokens), Tone.\n"
    "Token fields will be filled from response usage metrics.\n"
    "Document follows between <<< >>>. Use only its content.\n"
    "<<<\n{context}\n>>>"
)
user_content = user_template.format(tone=TONE, context=document_text)

# 4) Call the model with structured output
client = OpenAI()
response = client.responses.parse(
    model=MODEL_NAME,
    response_format=SummarySchema,
    messages=[
        {"role": "developer", "content": instructions},
        {"role": "user", "content": user_content},
    ],
    max_output_tokens=1200,
)

# 5) Fill tokens and finalize
parsed: SummarySchema = response.output_parsed
result = parsed.model_copy(update={
    "Tone": TONE,
    "InputTokens": response.usage.input_tokens,
    "OutputTokens": response.usage.output_tokens,
})

print("Token usage:", response.usage)
print(result.model_dump_json(indent=2))

# 6) Sanity checks
for field in ["Author", "Title", "Relevance", "Summary", "Tone"]:
    assert getattr(result, field) and isinstance(getattr(result, field), str), f"{field} missing/invalid"
assert result.Relevance.count(".") <= 6, "Relevance seems longer than a short paragraph"
assert isinstance(result.InputTokens, int) and isinstance(result.OutputTokens, int), "Token counts missing"
assert result.Tone == TONE, "Tone label not preserved"

# 7) Save JSON
import json
summary_json_path = "assignment_1_summary.json"
with open(summary_json_path, "w") as f:
    f.write(result.model_dump_json(indent=2))
summary_json_path
```


