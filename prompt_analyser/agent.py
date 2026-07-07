"""Prompt Improvement Agent — ADK 2.0 Graph Workflow."""

from google.adk import Workflow

from .nodes import (
    analyze_prompt_agent,
    compute_diff,
    format_final_output,
    generate_summary_agent,
    rewrite_prompt_agent,
)

prompt_improver_agent = Workflow(
    name="prompt_improver",
    edges=[
        (
            "START",
            analyze_prompt_agent,    # Stage 1: LLM analyzes prompt
            rewrite_prompt_agent,    # Stage 2: LLM rewrites prompt
            compute_diff,            # Stage 3a: Python diffs old/new prompt
            generate_summary_agent,  # Stage 3b: LLM explains changes
            format_final_output,     # Terminal: Python formats final output
        ),
    ],
)
