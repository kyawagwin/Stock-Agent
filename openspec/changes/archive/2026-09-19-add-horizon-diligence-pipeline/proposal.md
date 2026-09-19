## Why

Investors often suffer severe capital impairment by mistaking a speculative, high-dilution trading vehicle for a long-term compounder, or attempting to buy-and-hold cyclical assets through brutal drawdowns. Currently, the system requires users to pre-determine their investment horizon before evaluating entry timing. By introducing an automated forensic background check and horizon classification stage, the system diagnoses whether an asset's financial DNA qualifies for multi-year compounding, short-term tactical trading, or immediate avoidance—and automatically hands off viable assets to the execution agent.

## What Changes

- **New Forensic Due Diligence Module (`forensic_diligence`)**: Quantitative screening engine analyzing 3-year share count dilution/float expansion, net insider buying vs. dumping, solvency/debt cliffs (Cash vs. Debt, Current Ratio, FCF coverage), and 3-year margin durability.
- **New Horizon Classification & Triage Engine (`horizon_classifier`)**: Deterministic classification of stocks into four definitive verdicts: `LONG-TERM COMPOUNDER`, `SHORT-TERM TACTICAL SWING`, `ALL-WEATHER`, or `AVOID / TOXIC`.
- **Two-Stage Orchestration Pipeline (`pipeline.py`)**: Unified entrypoint that runs Stage 1 (Forensic Horizon Audit), short-circuits with an uninvestable risk audit if toxic, or passes the diagnosed horizon into Stage 2 (`decision_agent`) to produce entry zones, stop losses, and risk-reward blueprints.
- **Reporting & Deduplication Expansion**: Saves structured forensic dossiers and unified intelligence reports in `reports/` with SHA-256 content hashing.

## Capabilities

### New Capabilities
- `forensic-diligence`: Quantitative forensic screening covering multi-year share dilution, insider transaction conviction, balance sheet solvency/debt load, and operating margin persistence using market data.
- `horizon-classifier`: Classification of assets into definitive investment horizons (`LONG-TERM COMPOUNDER`, `SHORT-TERM TACTICAL SWING`, `ALL-WEATHER`, `AVOID / TOXIC`) and automated routing/short-circuiting into tactical execution.

### Modified Capabilities
*(None; openspec/specs is currently empty)*

## Impact

- **New Files**: `forensic_agent.py` (or forensic tool module), `pipeline.py` (two-stage runner).
- **Existing Files**: `decision_agent.py` (importable entrypoint function/agent callable from pipeline).
- **Dependencies**: Uses existing `yfinance`, `numpy`, `pandas`, and `langchain_google_genai` dependencies without requiring new third-party paid APIs.
