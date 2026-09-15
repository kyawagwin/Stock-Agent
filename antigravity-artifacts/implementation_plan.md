# Implementation Plan: Swap LLM Model from OpenAI to Gemini

This plan outlines the changes required to migrate the `stock-agent` application from using OpenAI's `ChatOpenAI` model to Google's `ChatGoogleGenerativeAI` model via `langchain-google-genai`.

## User Review Required

> [!IMPORTANT]
> - **API Key Name Change**: Gemini uses `GEMINI_API_KEY` or `GOOGLE_API_KEY` instead of `OPENAI_API_KEY`. The `.env` configuration will be updated to reflect this requirement.
> - **Model Name**: The model will be changed from `gpt-4o-mini` to `gemini-2.5-flash` (or `gemini-1.5-flash`), which is fast and supports function calling / tool use.

## Proposed Changes

### Dependencies & Environment

#### [MODIFY] [pyproject.toml](file:///Users/aungwin.kyaw/Projects/stock-agent/pyproject.toml)
- Replace dependency `langchain-openai` with `langchain-google-genai`.

#### [MODIFY] [.env](file:///Users/aungwin.kyaw/Projects/stock-agent/.env)
- Update environment variable template from `OPENAI_API_KEY` to `GEMINI_API_KEY` / `GOOGLE_API_KEY`.

---

### Core Logic

#### [MODIFY] [main.py](file:///Users/aungwin.kyaw/Projects/stock-agent/main.py)
- Import `ChatGoogleGenerativeAI` from `langchain_google_genai` instead of `ChatOpenAI` from `langchain_openai`.
- Instantiate `llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)`.

---

### Sync & Version Control

#### [NEW] [antigravity-artifacts/implementation_plan.md](file:///Users/aungwin.kyaw/Projects/stock-agent/antigravity-artifacts/implementation_plan.md)
- Sync implementation plan artifact to project root in accordance with project rules.

---

## Verification Plan

### Automated & Runtime Tests
- Run `uv add langchain-google-genai` and `uv remove langchain-openai` to synchronize dependencies in `.venv`.
- Verify `main.py` syntax and module imports with `.venv/bin/python main.py`.

### Manual Verification
- Check `.gitignore` to verify secrets and build artifacts (`.env`, `.venv`) remain excluded.
