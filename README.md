# Prompt Improvement Agent

**An intelligent AI pipeline that takes any raw prompt and returns a rewritten, polished version with a structured change log — powered by Google ADK 2.0 and Gemini 2.0 Flash.**

Enter any vague or incomplete prompt and get back a clear, well-structured version with a bullet-point explanation of every improvement made.

---

## The Problem

Most people write prompts like: *"write me some code for a website"* — which is ambiguous in a dozen ways: what language? what framework? what pages? what audience? Without answers, an AI either floods you with clarifying questions or produces generic, mediocre output.

Prompt engineering advice exists, but it's scattered and technical. Most users don't have time to become prompt engineers.

**Prompt Improvement Agent bridges that gap** — taking any raw prompt and returning a clear, structured, immediately usable rewrite with a plain-English explanation of every change.

---

## The Solution

The agent runs a 5-stage pipeline:

1. **Analyze** — Identifies missing context, ambiguity, undefined format, and missing role definition
2. **Rewrite** — Transforms the prompt into a clear, well-structured version
3. **Diff** — Computes line-count and character-length statistics between versions
4. **Summarize** — Produces a 3–5 bullet-point change log
5. **Format** — Delivers everything as a clean, readable report

---

## Architecture

Built on **Google's Agent Development Kit (ADK) 2.0** using a sequential workflow graph. All inter-stage data contracts are enforced by **Pydantic v2** schemas.

### Project Structure

```
Prompt Improvement Agent/
├── main.py                     ← Entry point: runs agent with sample prompt
├── prompt_improver/
│   ├── __init__.py             ← Exports the root agent
│   ├── agent.py                ← ADK Workflow graph definition
│   ├── config.py               ← Model name (gemini-2.0-flash)
│   ├── nodes.py                ← 4 pipeline stages (3 LLM agents + 2 Python)
│   └── schemas.py              ← Pydantic models for all stage contracts
```

### The Pipeline

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

### Stage Schemas

| Schema | Stage | Purpose |
|---|---|---|
| `PromptAnalysis` | 1 → 2 | Gap analysis: missing context, ambiguity, format, role |
| `RewrittenPrompt` | 2 → 3a | Original + improved prompt |
| `DiffedPrompt` | 3a → 3b | Diff stats: lines added/removed, length delta |
| `FinalSummary` | 3b → output | Improved prompt + change log |

### Tech Stack

- **Framework:** Google ADK 2.0 (Agent Development Kit)
- **LLM:** Gemini 2.0 Flash (via Google AI Studio)
- **Data Validation:** Pydantic v2
- **Environment:** python-dotenv
- **Language:** Python 3.10+

---

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- A Google AI Studio API key (free tier at [aistudio.google.com](https://aistudio.google.com))

### 1. Clone / Download the Repository

```bash
git clone <your-repo-url>
cd "Prompt Improvement Agent"
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install google-adk pydantic python-dotenv
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# .env
GOOGLE_API_KEY=your_google_ai_studio_api_key_here
GOOGLE_GENAI_USE_VERTEXAI=FALSE
```

> ⚠️ **Never commit your `.env` file.** Add it to `.gitignore` before pushing.

### 5. Run the Agent

```bash
python main.py
```

Sample output for the default prompt `"write me some code for a website"`:

```
═══ Improved Prompt ═══

You are an expert full-stack web developer. Write the complete HTML, CSS, and
JavaScript code for a responsive single-page portfolio website for a graphic
designer. The site must include: a hero section with the designer's name and
tagline, a projects gallery (minimum 4 items with placeholder images), an About
section with a 100-word bio, and a contact form. Use a modern, clean design
aesthetic. Output the complete code in a single HTML file with embedded CSS and JS.

── Change Log ──
• Added a specific developer role ("full-stack web developer") to anchor expertise.
• Specified the exact tech stack (HTML, CSS, JavaScript) to prevent framework ambiguity.
• Defined page structure explicitly (hero, gallery, about, contact) so no section is missed.
• Added a minimum project count (4 items) to set clear scope.
• Specified design aesthetic ("modern, clean") to guide visual output decisions.
• Requested output as a single self-contained HTML file for immediate usability.
```

### 6. Use with Your Own Prompts

Edit `main.py` and change the `raw_prompt` variable:

```python
def main():
    raw_prompt = "your prompt here"
    result = prompt_improver_agent(Event(message=raw_prompt))
    print(result.message)
```

---

## Deployment

Deploy as a web service using Google Cloud Run and the ADK 2.0 deployment tooling:

```bash
# Build and deploy the agent
google-adk deploy --agent=prompt_improver.prompt_improver_agent --platform=cloud_run

# Or via Google Cloud CLI
gcloud run deploy prompt-improvement-agent \
  --source=. \
  --entry-point=main.py \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated
```

---

## Key Design Decisions

- **ADK Workflow Graph:** Chosen over simple prompt chaining for strict type safety between stages and clean extensibility. The graph handles all routing and data passing — developers write only domain logic.
- **Pydantic Schemas:** Every stage boundary has a typed schema — no malformed data can silently propagate through the pipeline.
- **Intent Preservation:** Stage 2 is explicitly instructed to preserve the original user intent exactly. The original prompt is passed through unchanged at every stage, making the full pipeline auditable and traceable.
- **Set-Based Diffing:** Stage 3a uses set comparison rather than character-by-character diffing to avoid overcounting changes caused by line-wrapping differences in prose.
- **Bounded Change Log:** The Pydantic schema constrains `change_log` to a list of strings, and the agent instruction targets 3–5 bullets. This structurally prevents both the "too vague" and "too verbose" failure modes.

---

## License

MIT License
