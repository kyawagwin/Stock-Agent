# Walkthrough: Markdown Analysis Report Export & Deduplication

Successfully implemented automatic Markdown export of research agent results into a dedicated `reports/` folder with SHA-256 based deduplication logic.

---

## 🛠️ Changes Made

### 1. Main Script & Report Generation (`main.py`)
- **[extract_response_text](file:///Users/kyawagwin/Documents/GitHub/Stock-Agent/main.py#L125-L144)**: Extracts clean, normalized response text regardless of response object format (string, list of parts, or message attribute).
- **[compute_content_hash](file:///Users/kyawagwin/Documents/GitHub/Stock-Agent/main.py#L147-L150)**: Generates SHA-256 hashes of normalized content to detect identical reports.
- **[save_analysis_report](file:///Users/kyawagwin/Documents/GitHub/Stock-Agent/main.py#L153-L222)**:
  - Formats analysis with structured header metadata (Ticker, Timeframe, Date, Model).
  - Checks if an identical report exists in `reports/` to prevent redundant duplicates.
  - Automatically handles same-day revisions with version suffixes (`_v2.md`).
- **[Main Execution Block](file:///Users/kyawagwin/Documents/GitHub/Stock-Agent/main.py#L229-L255)**: Prompts the user interactively for the stock ticker (e.g. `NVDA`, `AAPL`) and timeframe (e.g. `30 days`, `60 days`) with intuitive fallbacks on Enter, invokes the agent, outputs the analysis to the terminal, and saves the deduplicated report to `reports/`.

### 2. Documentation & Structure (`README.md`)
- Updated [README.md](file:///Users/kyawagwin/Documents/GitHub/Stock-Agent/README.md) to document the `reports/` folder, key features, and deduplication workflow.

---

## 🧪 Verification Results

### 1. End-to-End Analysis & File Generation
Ran `uv run main.py` for `NVDA` (`30 days`):
- Generated analysis report: [NVDA_30_days_2026-09-16.md](file:///Users/kyawagwin/Documents/GitHub/Stock-Agent/reports/NVDA_30_days_2026-09-16.md)
- Terminal confirmation: `✅ Analysis report saved to: reports/NVDA_30_days_2026-09-16.md`

### 2. Deduplication & Versioning Verification
Ran test suite verifying deduplication behavior:
```python
# Re-saving identical content detected existing report and skipped duplicate creation:
Test 1 (Identical content): path = reports/NVDA_30_days_2026-09-16.md created = False

# New ticker or modified content created new report:
Test 2 (New report for TSLA): path = reports/TSLA_30_days_2026-09-16.md created = True

# Re-running with identical TSLA content skipped duplicate creation:
Test 3 (Identical TSLA content): path = reports/TSLA_30_days_2026-09-16.md created = False
```

### 3. Generated Report Output Preview

```markdown
# 📊 Quantitative Stock Research: NVDA

| Metric / Attribute | Value |
| :--- | :--- |
| **Ticker** | `NVDA` |
| **Timeframe** | `30 days` |
| **Report Date** | `2026-09-16 09:13:41` |
| **Analysis Model** | `gemini-3.6-flash` |

---

## 📝 Research Summary & Scenario Analysis
...
```
