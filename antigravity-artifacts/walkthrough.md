# Walkthrough: Investment Timing & Decision Agent ("Invest Now vs. Invest Later")

Successfully built, verified, and integrated the **Investment Timing & Decision Agent** ([`decision_agent.py`](file:///Users/kyawagwin/Documents/GitHub/Stock-Agent/decision_agent.py)), designed to provide concrete capital allocation verdicts based on user-provided tickers and timeframes.

---

## 🛠️ Architecture & Changes Made

### 1. New Standalone Agent ([`decision_agent.py`](file:///Users/kyawagwin/Documents/GitHub/Stock-Agent/decision_agent.py))

#### **Institutional Decision Categories**
The agent categorizes investment opportunities into one of 5 distinct institutional actions:
1. `🟢 INVEST NOW (HIGH CONVICTION)`: Immediate capital deployment with favorable risk/reward.
2. `🟡 INVEST NOW (TRANCHE / DCA)`: Favorable long-term thesis with short-term volatility (scale-in 30–50% now).
3. `🟠 INVEST LATER (WAIT FOR PULLBACK / SUPPORT)`: Overbought / stretched above moving averages; provides concrete limit buy targets.
4. `🔵 INVEST LATER (WAIT FOR CATALYST / EARNINGS)`: Elevated binary event risk (e.g., earnings release in < 14 days).
5. `🔴 AVOID / DO NOT INVEST`: Unfavorable risk-to-reward ratio (< 1.5:1), broken technical structure, or deteriorating balance sheet.

#### **Specialized Quantitative Tools**
- [`analyze_timing_and_technical_structure`](file:///Users/kyawagwin/Documents/GitHub/Stock-Agent/decision_agent.py#L21-L100):
  - 20, 50, and 200-day SMAs with percentage extension metrics.
  - 14-day RSI (overbought / oversold detection).
  - MACD (12, 26, 9) histogram momentum dynamics.
  - Bollinger Bands (20-day, 2σ) %B and bandwidth compression.
  - 14-day Average True Range (ATR) for volatility risk buffers.
  - Automatic NaN cleaning to prevent data corruption during open market / unsettled bars.
- [`assess_valuation_and_margin_of_safety`](file:///Users/kyawagwin/Documents/GitHub/Stock-Agent/decision_agent.py#L103-L157):
  - Multiples: Trailing/Forward P/E, PEG Ratio, Price/Sales, EV/EBITDA.
  - Balance Sheet & Solvency: Cash vs. Debt, Free Cash Flow, Profit Margins, Return on Equity (ROE).
  - Consensus Target Spread: Calculates implied upside/downside relative to Wall Street consensus.
- [`check_catalysts_and_risk_events`](file:///Users/kyawagwin/Documents/GitHub/Stock-Agent/decision_agent.py#L160-L220):
  - Next quarterly earnings announcement date countdown (flags `< 14 days` as high binary event risk).
  - Dividend yield and ex-dividend dates.
  - Short Interest (% of float) and systematic market Beta.
- [`fetch_sentiment_and_news_catalysts`](file:///Users/kyawagwin/Documents/GitHub/Stock-Agent/decision_agent.py#L223-L252):
  - Recent headlines, publishers, and sentiment summaries.

#### **Deduplication & Report Engine**
- Automatic Markdown report export into `reports/` prefixed with `DECISION_` (e.g., [`DECISION_NVDA_30_days_2026-09-17.md`](file:///Users/kyawagwin/Documents/GitHub/Stock-Agent/reports/DECISION_NVDA_30_days_2026-09-17.md)).
- SHA-256 content hashing to avoid redundant duplicate files on repeated runs.

---

### 2. Documentation Updates ([`README.md`](file:///Users/kyawagwin/Documents/GitHub/Stock-Agent/README.md))
- Documented both agents side-by-side:
  - **`main.py`**: Market research and 1-sigma volatility range projections.
  - **`decision_agent.py`**: Capital allocation timing and execution blueprints.

---

## 🧪 Verification & Results

### 1. End-to-End Decision Execution: NVDA (30 Days)
- **Verdict**: `🟡 INVEST NOW (TRANCHE / DCA)` with **High Conviction**.
- **Tactical Rationale**: NVDA trades at $212.17 at its 50-day SMA ($213.02) with zero earnings risk in the 30-day window (next earnings in 62 days). Tranche 1 (40%) deploys immediately; Tranche 2 (60%) captures any pullback to lower Bollinger Band ($205.93).
- **Execution Blueprint**:
  - Ideal Entry Zone: `$205.50 – $213.00`
  - Upside Target: `$234.50`
  - Downside Invalidation (Stop): `$196.50`
  - Blended Risk/Reward: `2.17 : 1`
- **Saved Report**: [DECISION_NVDA_30_days_2026-09-17.md](file:///Users/kyawagwin/Documents/GitHub/Stock-Agent/reports/DECISION_NVDA_30_days_2026-09-17.md)

### 2. Swing-Trade Execution: TSLA (14 Days)
- **Verdict**: `🟡 INVEST NOW (TRANCHE / DCA)` with **Medium Conviction**.
- **Tactical Rationale**: TSLA consolidating at 20-day SMA ($356.83) with positive MACD histogram (+0.37) and 3.65 : 1 Risk-to-Reward. Tranche approach accounts for upcoming NHTSA Cybercab regulatory review on September 30.
- **Saved Report**: [DECISION_TSLA_14_days_2026-09-17.md](file:///Users/kyawagwin/Documents/GitHub/Stock-Agent/reports/DECISION_TSLA_14_days_2026-09-17.md)

### 3. Deduplication Test
- Confirmed that running `save_decision_report` on identical content correctly skips creating duplicate files.
