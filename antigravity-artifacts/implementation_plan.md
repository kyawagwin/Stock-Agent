# Implementation Plan: Export Analysis to Markdown with Deduplication

This plan outlines the architecture and implementation for automatically saving the stock agent's final analysis into a dedicated reports folder as structured Markdown (`.md`) files while preventing redundant duplicates.

## User Review Required

> [!NOTE]
> - **Default Output Directory**: Reports will be saved to `reports/` at the project root.
> - **Deduplication Strategy**: 
>   1. **Content Hash Check**: Before saving, the file generator calculates the SHA-256 hash of the analysis body. If an identical report already exists in the destination folder, writing is skipped and the existing file path is reported.
>   2. **Version Suffixing for Changes**: If a report for the same ticker and date exists but has different content (e.g. new market data fetched later that day), a timestamp or version suffix (`_v2.md`) is added to avoid silently overwriting or duplicating identical files.

---

## Proposed Changes

### Core Logic

#### [MODIFY] [main.py](file:///Users/kyawagwin/Documents/GitHub/Stock-Agent/main.py)
- Implement `extract_response_text(response: dict) -> str` to robustly extract final message text regardless of return format (attribute, part list, or string).
- Implement `save_analysis_report(content: str, ticker: str, timeframe: str, output_dir: str = "reports") -> Path | None`:
  - Builds a structured Markdown report with title, metadata banner (ticker, timeframe, timestamp, model info), and analysis body.
  - Generates a normalized filename: `{TICKER}_{timeframe_slug}_{date}.md`.
  - Performs SHA-256 content comparison against existing files in `reports/` to prevent duplicate files.
  - If a file exists with different content, appends a version identifier (`_v2`, `_v3`, etc.) to preserve historical variations without spamming identical copies.
- Update `if __name__ == "__main__":` to invoke `save_analysis_report(...)` and print the output path or deduplication status.

---

### Documentation & Repository Structure

#### [MODIFY] [README.md](file:///Users/kyawagwin/Documents/GitHub/Stock-Agent/README.md)
- Update the project structure diagram to include the `reports/` directory.
- Add documentation on markdown export formatting and deduplication behavior.

---

## Verification Plan

### Automated & Runtime Tests
- Run `uv run main.py` for `NVDA` (`30 days`) to test initial markdown generation into `reports/NVDA_30days_YYYY-MM-DD.md`.
- Run `uv run main.py` a second time with identical content (or a unit test script) to verify deduplication detects existing identical content and avoids creating a duplicate file.
- Verify that running with modified content creates an appropriate versioned/updated file without data loss.

### Manual Verification
- Inspect the generated markdown file in `reports/` to ensure headers, formatting, tables/lists, and markdown syntax render cleanly.
