"""Graph nodes for the Prompt Improvement pipeline.

Each function here becomes a node in the ADK Workflow graph.
The Workflow engine automatically wires Event.output -> typed input.

Pipeline:
  START -> analyze_prompt -> rewrite_prompt -> compute_diff -> generate_summary -> format_output
          (LLM)             (LLM)             (Python)        (LLM)               (Python)
"""

from __future__ import annotations

from google.adk import Agent, Event

from .config import MODEL_NAME
from .schemas import (
    DiffedPrompt,
    FinalSummary,
    PromptAnalysis,
    RewrittenPrompt,
)


# ─────────────────────────────────────────────────────────────────────
# Stage 1 — Prompt Analysis (LLM Agent)
# ─────────────────────────────────────────────────────────────────────

analyze_prompt_agent = Agent(
    name="analyze_prompt_agent",
    model=MODEL_NAME,
    description="Analyzes the raw user prompt and identifies missing context, ambiguity, and undefined formats.",
    instruction="""\
You are an expert Prompt Engineer. You will receive a raw user prompt.
Analyze this prompt and identify:
1. Missing context (what information is absent that an AI would need).
2. Ambiguous instructions (things that could be interpreted multiple ways).
3. Undefined output format (does the user want a list? code? paragraph?).
4. Missing role definition (would assigning an AI persona improve output?).

Return valid JSON matching the PromptAnalysis schema.
Make sure to copy the exact raw prompt you received into the `original_prompt` field.
IMPORTANT: DO NOT WRAP YOUR RESPONSE IN ```json ... ``` MARKDOWN BLOCKS. RETURN RAW UNFORMATTED JSON ONLY.
""",
    output_schema=PromptAnalysis,
)


# ─────────────────────────────────────────────────────────────────────
# Stage 2 — Prompt Rewriting (LLM Agent)
# ─────────────────────────────────────────────────────────────────────

rewrite_prompt_agent = Agent(
    name="rewrite_prompt_agent",
    model=MODEL_NAME,
    description="Rewrites the original prompt into a clearer, better-structured version based on the analysis.",
    instruction="""\
You are an expert Prompt Engineer. You will receive a PromptAnalysis JSON object 
containing the `original_prompt` and issues found (missing context, ambiguity, etc.).

Your task is to rewrite the prompt into a clearer, better-structured version that:
- Preserves the original intent exactly — do not change what the user wants.
- Adds missing context where needed.
- Defines an AI role if it would improve output quality.
- Specifies output format and constraints explicitly.
- Removes vagueness without adding unnecessary verbosity.

Pass the `original_prompt` through unchanged, and place your rewritten prompt in the `improved_prompt` field.
Return valid JSON matching the RewrittenPrompt schema.
IMPORTANT: DO NOT WRAP YOUR RESPONSE IN ```json ... ``` MARKDOWN BLOCKS. RETURN RAW UNFORMATTED JSON ONLY.
""",
    input_schema=PromptAnalysis,
    output_schema=RewrittenPrompt,
)


# ─────────────────────────────────────────────────────────────────────
# Stage 3a — Change Summary / Diffing (Pure Python)
# ─────────────────────────────────────────────────────────────────────

def compute_diff(node_input: RewrittenPrompt) -> DiffedPrompt:
    """Computes a simple diff between the original and improved prompt."""
    orig_lines = node_input.original_prompt.strip().splitlines()
    imp_lines = node_input.improved_prompt.strip().splitlines()
    
    # Very simple line diff calculation
    orig_set = set(orig_lines)
    imp_set = set(imp_lines)
    
    lines_added = len(imp_set - orig_set)
    lines_removed = len(orig_set - imp_set)
    length_diff = len(node_input.improved_prompt) - len(node_input.original_prompt)
    
    return DiffedPrompt(
        original_prompt=node_input.original_prompt,
        improved_prompt=node_input.improved_prompt,
        lines_added=lines_added,
        lines_removed=lines_removed,
        length_difference=length_diff,
    )


# ─────────────────────────────────────────────────────────────────────
# Stage 3b — Change Summary Explanation (LLM Agent)
# ─────────────────────────────────────────────────────────────────────

generate_summary_agent = Agent(
    name="generate_summary_agent",
    model=MODEL_NAME,
    description="Produces a brief explanation of what was changed in the prompt and why.",
    instruction="""\
You are an expert Prompt Engineer. You will receive a DiffedPrompt object containing 
the `original_prompt`, the `improved_prompt`, and some diff statistics.

Produce a brief explanation (3-5 bullet points) of what was changed and why. Keep it concise 
so the user can scan it in 10 seconds. Focus on the structural and contextual improvements made.

Pass the `improved_prompt` through unchanged.
Return valid JSON matching the FinalSummary schema.
IMPORTANT: DO NOT WRAP YOUR RESPONSE IN ```json ... ``` MARKDOWN BLOCKS. RETURN RAW UNFORMATTED JSON ONLY.
""",
    input_schema=DiffedPrompt,
    output_schema=FinalSummary,
)


# ─────────────────────────────────────────────────────────────────────
# Terminal Stage — Format Final Output (Pure Python)
# ─────────────────────────────────────────────────────────────────────

def format_final_output(node_input: FinalSummary) -> Event:
    """Formats the structured summary into a clean user-facing message."""
    lines = [
        "═══ Improved Prompt ═══",
        "",
        node_input.improved_prompt,
        "",
        "── Change Log ──",
    ]
    
    for point in node_input.change_log:
        lines.append(f"• {point}")
        
    return Event(message="\n".join(lines))
