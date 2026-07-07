from pydantic import BaseModel, Field


class PromptAnalysis(BaseModel):
    """Output schema for the Stage 1 Prompt Analysis."""

    original_prompt: str = Field(
        description="The original raw prompt provided by the user. Pass this through exactly as received."
    )
    missing_context: list[str] = Field(
        description="List of information or context that is absent but an AI would need to perform the task."
    )
    ambiguous_instructions: list[str] = Field(
        description="List of things in the prompt that could be interpreted in multiple ways."
    )
    undefined_output_format: list[str] = Field(
        description="Issues regarding the requested format (e.g., if the user wants a list, code, paragraph)."
    )
    missing_role_definition: list[str] = Field(
        description="Suggestions for an AI persona or role that would improve the output."
    )


class RewrittenPrompt(BaseModel):
    """Schema holding the improved prompt from Stage 2."""

    original_prompt: str = Field(description="The original raw prompt.")
    improved_prompt: str = Field(description="The final improved prompt.")


class DiffedPrompt(BaseModel):
    """Schema holding the prompt changes diff info."""

    original_prompt: str = Field(description="The original raw prompt.")
    improved_prompt: str = Field(description="The final improved prompt.")
    lines_added: int = Field(description="Number of lines added.")
    lines_removed: int = Field(description="Number of lines removed.")
    length_difference: int = Field(description="Difference in string length.")


class FinalSummary(BaseModel):
    """Schema holding the final bullet point summary."""

    improved_prompt: str = Field(description="The final improved prompt.")
    change_log: list[str] = Field(description="3-5 brief bullet points explaining what was changed and why.")
