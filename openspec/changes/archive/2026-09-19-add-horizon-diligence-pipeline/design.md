## Context

The repository currently contains two independent agents:
- `main.py`: Performs directional bias analysis and calculates 1-sigma volatility bands.
- `decision_agent.py`: Requires a user-specified ticker AND timeframe, then calculates an "Invest Now vs. Invest Later" decision along with tactical buy zones, stop losses, and risk/reward ratios.

However, individual investors frequently misclassify the fundamental nature of assets—either treating high-dilution, cash-burning speculative stocks as multi-year "buy-and-hold" compounders, or attempting to hold highly cyclical stocks through painful drawdowns. There is currently no mechanism to audit the financial hygiene (dilution, insider conviction, debt solvency, margin durability) of an asset or to determine its suitable investment horizon before deciding entry timing.

This design introduces a **Two-Stage Diligence & Execution Pipeline**:
1. **Stage 1 (Forensic Due Diligence & Horizon Gatekeeper)**: Audits hard quantitative corporate health signals via `yfinance` to classify the asset into one of four definitive horizons (`LONG-TERM COMPOUNDER`, `SHORT-TERM TACTICAL SWING`, `ALL-WEATHER`, `AVOID / TOXIC`).
2. **Stage 2 (Tactical Execution Handoff)**: If the asset passes the gate, the diagnosed horizon is automatically forwarded to the execution agent (`decision_agent.py`) to generate entry price levels, profit targets, and invalidation stops. If deemed `AVOID / TOXIC`, execution is short-circuited to preserve capital.

## Goals / Non-Goals

**Goals:**
- Provide a quantitative forensic background check on tickers using:
  - 3-year share dilution / float expansion CAGR.
  - 12-month net insider transactions (open-market buying vs. selling).
  - Balance sheet solvency (Cash vs. Total Debt, Quick/Current ratios, Free Cash Flow burn).
  - 3-year operating & gross margin stability.
  - Volatility and beta profile.
- Classify ticker into exactly one definitive verdict: `LONG-TERM COMPOUNDER`, `SHORT-TERM TACTICAL SWING`, `ALL-WEATHER`, or `AVOID / TOXIC`.
- Automatically route the diagnosed horizon into Stage 2 (`decision_agent`) to produce an execution blueprint without requiring the user to guess a timeframe.
- Short-circuit the execution blueprint if the company fails forensic checks (`AVOID / TOXIC`), generating an uninvestable risk dossier.
- Persist structured reports with SHA-256 deduplication and auto-versioning in `reports/`.

**Non-Goals:**
- Scraping external social media, Twitter/X, Reddit, or qualitative blog sentiment.
- Replacing SEC Edgar filings for legal discovery or complex restructuring bankruptcies.
- Executing live broker trades or handling portfolio rebalancing orders.

## Decisions

### Decision 1: Quantitative Forensics over Qualitative Sentiment
- **Choice**: Base the background check on hard mathematical metrics (dilution %, net insider shares, debt/cash coverage, margin delta) rather than news sentiment summaries.
- **Rationale**: Management PR and media headlines often mask deteriorating underlying unit economics. Hard financial statements from `yfinance` provide an objective reality check.
- **Alternatives Considered**: Using news search and sentiment analysis as the primary screen. Rejected because headlines are lagging and prone to hype cycles.

### Decision 2: Two-Stage Pipeline (`pipeline.py`) Orchestration
- **Choice**: Create a master orchestrator `pipeline.py` that invokes Stage 1 (`forensic_agent.py`), parses the horizon classification, and if viable, invokes `decision_agent.run_decision_agent(ticker, diagnosed_timeframe)`.
- **Rationale**: Keeps components modular. `decision_agent.py` can still be run standalone for custom timeframes, while `pipeline.py` provides the fully autonomous "zero-guesswork" end-to-end investment committee.
- **Alternatives Considered**: Merging all code directly into `decision_agent.py`. Rejected because `decision_agent.py` is already 470+ lines; bundling forensic calculations would create an unmaintainable monolith.

### Decision 3: Short-Circuiting on `AVOID / TOXIC`
- **Choice**: If a company fails basic solvency or exhibits predatory dilution (>15% annualized dilution with negative cash flow), Stage 2 tactical analysis is completely bypassed.
- **Rationale**: Generating buy entry zones or profit targets on a mathematically broken business creates a false sense of legitimacy for retail investors. The agent should strictly advise avoidance and document the red flags.
- **Alternatives Considered**: Always generating a short-term trading setup even for toxic stocks. Rejected because capital preservation is the first mandate of institutional portfolio management.

```
                      ┌───────────────────────────────────────┐
                      │          User Inputs: TICKER          │
                      └──────────────────┬────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: FORENSIC BACKGROUND & HORIZON GATEKEEPER (`forensic_agent.py`)         │
├─────────────────────────────────────────────────────────────────────────────────┤
│  • Share Dilution Analysis (3-yr share count drift)                             │
│  • Insider Conviction (12-mo net buy vs sell)                                   │
│  • Solvency & Cash Runway (Cash vs Debt, Current Ratio, FCF)                    │
│  • Moat & Margin Durability (3-yr margin delta)                                 │
│  • Volatility & Beta Profile                                                    │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   │                                           │
         [ Fails Forensic Check ]                    [ Passes Forensics ]
                   │                                           │
                   ▼                                           ▼
       ┌────────────────────────┐                  Diagnosed Horizon:
       │  🔴 AVOID / TOXIC      │                  • LONG_TERM   (e.g., 1–3 Years)
       │  Capital Destruction   │                  • SHORT_TERM  (e.g., 1 Month)
       │  Risk High             │                  • ALL_WEATHER (Dual play)
       └───────────┬────────────┘                              │
                   │                                           ▼
                   │             ┌───────────────────────────────────────────────┐
                   │             │ STAGE 2: TACTICAL EXECUTION (`decision_agent`)│
                   │             ├───────────────────────────────────────────────┤
                   │             │ Evaluates timing FOR that diagnosed horizon:  │
                   │             │ • Invest Now vs Invest Later                  │
                   │             │ • Ideal Buy Zones & Support/Resistance        │
                   │             │ • Invalidation Stop & Profit Targets          │
                   │             │ • Calculated Risk-to-Reward Ratio             │
                   │             └───────────────────────┬───────────────────────┘
                   │                                     │
                   ▼                                     ▼
       ┌────────────────────────┐            ┌───────────────────────────────────┐
       │ Forensic Audit Dossier │            │ Full Intelligence Report          │
       │ (Execution Bypassed)   │            │ (Forensics + Execution Blueprint) │
       └────────────────────────┘            └───────────────────────────────────┘
```

## Risks / Trade-offs

- **[Risk] Foreign Tickers (ADRs) or Fresh IPOs with sparse data** → *Mitigation*: The forensic tool implements graceful degradation. If 3-year share data or insider filings are missing from `yfinance`, the tool returns `INSUFFICIENT_DATA_NEUTRAL` rather than flagging false alarms.
- **[Risk] High-Growth Tech with high Stock-Based Compensation (SBC)** → *Mitigation*: Dilution is contextualized against revenue growth. Moderate dilution (3–5%) is permitted for hyper-growth companies (>25% YoY revenue growth).
- **[Risk] Cyclical Value Traps** → *Mitigation*: Operating margin volatility and debt leverage checks flag companies at the peak of their cycle to prevent long-term misclassification.
