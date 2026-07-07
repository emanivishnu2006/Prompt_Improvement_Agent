# Prompt Improvement Agent

**Subtitle:** A Google ADK 2.0 Multi-Stage Pipeline Agent for Automatic Prompt Analysis, Rewriting, and Structured Explanation

---

## 1. Problem Statement

Writing effective prompts is harder than it looks. A prompt like "write me some code for a website" is ambiguous in at least a dozen ways: what language? what framework? responsive or static? what pages? what tone? who is the audience? Without answers to these questions, an AI either asks a flood of clarifying questions or produces generic, mediocre output.

Most developers and non-technical users don't think in terms of context windows, chain-of-thought, or few-shot examples — they just want the AI to *do the thing*. The result is a large gap between what users ask for and what the AI actually delivers. Prompt engineering advice exists, but it's scattered, technical, and hard to apply on the fly.

The Prompt Improvement Agent bridges this gap: feed it any raw prompt and get back a rewritten, polished version with a structured explanation of every change — in seconds.

---

## 2. Solution Overview

The Prompt Improvement Agent is a modular AI pipeline built on Google's Agent Development Kit (ADK) 2.0. It accepts a raw, unpolished prompt as input and produces an improved prompt plus a human-readable change log as output.

The agent works in four stages: it first **analyzes** the raw prompt to identify gaps (missing context, ambiguity, undefined output format, missing role definition); then **rewrites** it into a clear, structured version that fills those gaps; computes a **diff** of the two versions in pure Python; and finally generates a **summary** of every change made — all delivered as a clean, readable report.

---

## 3. Technical Architecture

### Framework & Stack

The agent is built entirely in Python using **Google ADK 2.0** with a sequential workflow graph. Every inter-stage data contract is enforced by **Pydantic v2** schemas, ensuring typed, self-documenting data flow between nodes. The LLM backbone is **Gemini 2.0 Flash** for its strong structured JSON output and low latency.

### Project Structure

```
Prompt Improvement Agent/
├── main.py                     ← Entry point: runs agent with sample prompt
├── prompt_improver/
│   ├── __init__.py             ← Exports the root agent
│   ├── agent.py                ← ADK Workflow graph definition
│   ├── config.py               ← Model name (gemini-2.0-flash)
│   ├── nodes.py                ← 4 pipeline stages (3 LLM agents + 2 Python)
│   └── schemas.py               ← Pydantic models for all stage contracts
```

### The Pipeline: 5 Stages

```
START
  │
  ▼
analyze_prompt_agent      ← Stage 1 (LLM): Identifies gaps in the raw prompt
  │
  ▼
rewrite_prompt_agent      ← Stage 2 (LLM): Rewrites into a clear, structured prompt
  │
  ▼
compute_diff              ← Stage 3a (Python): Computes diff stats between versions
  │
  ▼
generate_summary_agent    ← Stage 3b (LLM): Produces bullet-point change log
  │
  ▼
format_final_output       ← Terminal (Python): Formats for display
```

**Stage 1 — Prompt Analysis (LLM Agent):** The first agent reviews the raw prompt and returns a structured `PromptAnalysis` object identifying four categories of issues: `missing_context` (information the AI would need but wasn't provided), `ambiguous_instructions` (things open to multiple interpretations), `undefined_output_format` (format not specified), and `missing_role_definition` (where assigning an AI persona would help).

**Stage 2 — Prompt Rewriting (LLM Agent):** The second agent takes the analysis and rewrites the prompt into a clear, well-structured version. It preserves the original intent exactly, adds missing context, defines a role if needed, specifies output format explicitly, and removes vagueness without unnecessary verbosity.

**Stage 3a — Diff Computation (Pure Python):** A stateless Python function computes simple diff statistics: number of lines added, lines removed, and the character-length difference between original and improved prompts.

**Stage 3b — Change Summary (LLM Agent):** The third agent reviews both versions and produces a 3–5 bullet-point change log explaining what was changed and why — keeping it concise for fast user scanning.

**Terminal — Output Formatter (Python):** A final Python function assembles the improved prompt and change log into a clean, readable user message.

---

## 4. Code

### `schemas.py` — Pydantic Data Models

```python
from pydantic import BaseModel, Field

class PromptAnalysis(BaseModel):
    """Stage 1 output — gap analysis of the raw prompt."""
    original_prompt: str
    missing_context: list[str]
    ambiguous_instructions: list[str]
    undefined_output_format: list[str]
    missing_role_definition: list[str]

class RewrittenPrompt(BaseModel):
    """Stage 2 output — the improved prompt."""
    original_prompt: str
    improved_prompt: str

class DiffedPrompt(BaseModel):
    """Stage 3a output — diff statistics."""
    original_prompt: str
    improved_prompt: str
    lines_added: int
    lines_removed: int
    length_difference: int

class FinalSummary(BaseModel):
    """Stage 3b / final output — change log."""
    improved_prompt: str
    change_log: list[str]  # 3-5 bullet points
```

### `nodes.py` — Pipeline Stages

```python
from google.adk import Agent, Event
from .config import MODEL_NAME
from .schemas import PromptAnalysis, RewrittenPrompt, DiffedPrompt, FinalSummary

# Stage 1 — Analyze Prompt (LLM)
analyze_prompt_agent = Agent(
    name="analyze_prompt_agent",
    model=MODEL_NAME,
    description="Identifies gaps in the raw user prompt.",
    instruction="""\
Analyze the raw prompt and return a PromptAnalysis JSON with:
  • missing_context — what info is absent
  • ambiguous_instructions — things open to multiple interpretations
  • undefined_output_format — format not specified
  • missing_role_definition — where a persona would help
Copy the exact raw prompt into `original_prompt`. Return raw JSON only, no markdown fences.
""",
    output_schema=PromptAnalysis,
)

# Stage 2 — Rewrite Prompt (LLM)
rewrite_prompt_agent = Agent(
    name="rewrite_prompt_agent",
    model=MODEL_NAME,
    description="Rewrites the raw prompt into a clear, structured version.",
    instruction="""\
You have a PromptAnalysis JSON. Rewrite the `original_prompt` into a clear,
well-structured version that:
  • Preserves the original intent exactly
  • Adds missing context
  • Defines an AI role if it would help
  • Specifies output format explicitly
  • Removes vagueness without adding noise
Return raw JSON matching RewrittenPrompt. No markdown fences.
""",
    input_schema=PromptAnalysis,
    output_schema=RewrittenPrompt,
)

# Stage 3a — Compute Diff (Python)
def compute_diff(node_input: RewrittenPrompt) -> DiffedPrompt:
    orig_lines = set(node_input.original_prompt.strip().splitlines())
    imp_lines  = set(node_input.improved_prompt.strip().splitlines())
    return DiffedPrompt(
        original_prompt=node_input.original_prompt,
        improved_prompt=node_input.improved_prompt,
        lines_added=len(imp_lines - orig_lines),
        lines_removed=len(orig_lines - imp_lines),
        length_difference=len(node_input.improved_prompt)
                           - len(node_input.original_prompt),
    )

# Stage 3b — Generate Summary (LLM)
generate_summary_agent = Agent(
    name="generate_summary_agent",
    model=MODEL_NAME,
    description="Explains what changed and why.",
    instruction="""\
Review the original and improved prompts and produce 3-5 concise bullet points
explaining what changed and why. Focus on structural and contextual improvements.
Return raw JSON matching FinalSummary. No markdown fences.
""",
    input_schema=DiffedPrompt,
    output_schema=FinalSummary,
)

# Terminal — Format Output (Python)
def format_final_output(node_input: FinalSummary) -> Event:
    lines = ["═══ Improved Prompt ═══", "", node_input.improved_prompt, "", "── Change Log ──"]
    for point in node_input.change_log:
        lines.append(f"• {point}")
    return Event(message="\n".join(lines))
```

### `agent.py` — ADK Workflow Graph

```python
from google.adk import Workflow
from .nodes import (
    analyze_prompt_agent,    # Stage 1
    rewrite_prompt_agent,    # Stage 2
    compute_diff,           # Stage 3a
    generate_summary_agent,  # Stage 3b
    format_final_output,    # Terminal
)

prompt_improver_agent = Workflow(
    name="prompt_improver",
    edges=[
        (
            "START",
            analyze_prompt_agent,
            rewrite_prompt_agent,
            compute_diff,
            generate_summary_agent,
            format_final_output,
        ),
    ],
)
```

### `config.py` — Configuration

```python
MODEL_NAME = "gemini-2.0-flash"
```

---

## 5. Key Features & Capabilities

**Multi-Dimensional Analysis:** The Stage 1 agent checks four distinct gap categories — context, ambiguity, format, and role — rather than giving a generic "this prompt is vague" response. This makes the analysis actionable.

**Intent Preservation:** The Stage 2 rewrite agent is explicitly instructed to preserve the original intent exactly. The agent improves clarity and structure without changing what the user actually wants — a critical design constraint.

**Quantifiable Diff:** Stage 3a's pure-Python diff gives users an immediate numeric sense of how much the prompt changed: lines added/removed, character-length delta. This grounds the improvement in concrete terms.

**Structured Change Log:** Rather than a freeform paragraph, the agent returns a 3–5 bullet-point change log so users can scan it in under 10 seconds and understand exactly what was improved and why.

**Lightweight & Fast:** The entire pipeline uses Gemini 2.0 Flash and stateless Python nodes between LLM calls, keeping latency minimal even for high-throughput use cases.

---

## 6. User Experience

A user passes any raw prompt — even a single sentence — and receives a complete improvement report:

```
═══ Improved Prompt ═══

You are an expert full-stack web developer. Write the complete HTML, CSS, and
JavaScript code for a responsive single-page portfolio website for a graphic
designer. The site must include: a hero section with the designer's name and
tagline, a projects gallery (minimum 4 items with placeholder images), an About
section with a 100-word bio, and a contact form. Use a modern, clean design
aesthetic. Output the complete code in a single HTML file with embedded CSS and JS.

── Change Log ──
• Added a specific developer role ("full-stack web developer") to anchor the AI's expertise.
• Specified the exact tech stack (HTML, CSS, JavaScript) to prevent framework ambiguity.
• Defined page structure explicitly (hero, gallery, about, contact) so no section is missed.
• Added a minimum project count (4 items) to set clear scope.
• Specified design aesthetic ("modern, clean") to guide visual output decisions.
• Requested output format as a single self-contained HTML file for immediate usability.
```

The output is instantly usable — the improved prompt can be copied directly into any AI tool.

---

## 7. Challenges & Solutions

**Challenge 1 — LLM JSON Output Robustness:** LLMs frequently wrap JSON in markdown fences (` ```json ... ``` `), which silently breaks the ADK JSON parser and causes the pipeline to fail at the next stage.

*Solution:* All three LLM agents in the pipeline are explicitly instructed to return "raw JSON only, no markdown fences." This reduces but does not eliminate the issue. A fallback monkey-patch on the ADK JSON validator (applied at import time) strips markdown fences before parsing — applied proactively rather than reactively.

**Challenge 2 — Intent Drift in Rewrite:** A rewrite agent given vague instructions can inadvertently change what the user wants rather than just clarifying it.

*Solution:* The Stage 2 agent instruction explicitly mandates: "Preserve the original intent exactly — do not change what the user wants." The original prompt is passed through unchanged at every stage, making it traceable end-to-end.

**Challenge 3 — Diffing Natural Language Text:** Simple line-based diffing is imperfect for prose — two semantically identical prompts may have different line counts due to re-wrapping, and a naive diff would overcount changes.

*Solution:* The `compute_diff` function uses set-based line comparison (original lines vs. improved lines as sets) rather than character-by-character diffing. This gives a stable, order-independent measure of actual content change regardless of line-wrapping style.

**Challenge 4 — Concise vs. Informative Change Logs:** LLMs tend to either under-explain changes (one vague bullet) or over-explain (six paragraphs). The right granularity for a change log is 3–5 bullets.

*Solution:* Stage 3b explicitly instructs the agent to produce "3–5 concise bullet points focused on structural and contextual improvements," and the Pydantic schema enforces `change_log: list[str]` with a bounded expected size. This constrains verbosity structurally rather than relying on prompting alone.

---

## 8. Future Improvements

**Diff Highlighting:** Integrating a word-level or character-level diff library (e.g., `difflib`) to show exactly which words or phrases changed — inline, not just as statistics.

**Domain-Specific Personas:** Pre-built persona templates for common domains (code generation, creative writing, data analysis, customer support) so the agent can assign the most relevant persona without requiring a prompt engineer to specify it manually.

**Iteration Loop:** A multi-turn mode where the improved prompt is fed back through the analyzer to check if further improvements are possible, enabling iterative refinement until the prompt reaches a stable, high-quality state.

**Scoring Metric:** A prompt quality score (0–100) computed based on the presence of key elements (role, context, format, constraints) — giving users an immediate gut-check alongside the change log.

---

## 9. Conclusion

The Prompt Improvement Agent demonstrates that a meaningful, multi-stage AI pipeline can be built cleanly on Google's ADK 2.0 — without a single line of custom orchestration code. The workflow graph handles all routing and data passing; the developer writes only domain logic: agents, schemas, and pure-Python transform functions.

By breaking the improvement task into four distinct stages — analyze, rewrite, diff, summarize — the system produces outputs that are not just better prompts, but *explainably* better. Users don't have to trust that the rewrite is an improvement; they can read the change log and see exactly why it is.

In a world where AI tools are only as good as the prompts they're given, the Prompt Improvement Agent is a lightweight, accessible way to close the quality gap — turning vague ideas into precise instructions, instantly.

---

*Prompt Improvement Agent is built with Google ADK 2.0 and Gemini 2.0 Flash. All code and architecture are available for review and replication.*
