# Implementation Plan: Investment Timing & Decision Agent ("Invest Now vs. Invest Later")

Create a specialized AI-powered quantitative investment decision agent that evaluates whether an investor should **"Invest Now"** or **"Invest Later"** for a given stock ticker and specific investment timeframe.

---

## 🎯 Architecture & Philosophy

The agent solves the classic investor dilemma: *"Is this stock ripe for immediate capital allocation, or is the risk/reward skewed toward waiting for a pullback / catalyst confirmation?"*

### Institutional Decision Rubric:
1. **Actionable Verdicts**:
   - `🟢 INVEST NOW (HIGH CONVICTION)`: Favorable entry point, positive momentum, strong valuation support, no immediate binary risks.
   - `🟡 INVEST NOW (TRANCHE / DCA)`: Long-term bullish thesis intact, but moderate short-term volatility. Recommend a phased entry (e.g. 30–50% initial allocation).
   - `🟠 INVEST LATER (WAIT FOR PULLBACK / SUPPORT)`: Overbought / extended price action. Optimal entry limit zone specified (e.g. at 50-day SMA or key horizontal support).
   - `🔵 INVEST LATER (WAIT FOR CATALYST / EARNINGS)`: Imminent binary risk (e.g. earnings in < 10 days, regulatory decision). Re-evaluate after risk event passes.
   - `🔴 AVOID / DO NOT INVEST`: Unfavorable risk-to-reward ratio, deteriorating fundamentals, or broken technical structure.

2. **Timeframe-Adaptive Reasoning**:
   - **Short-Term (1–4 Weeks)**: Focuses on momentum, RSI, Bollinger Band %B, MACD histogram, distance from 20/50 SMA, and proximity to earnings dates.
   - **Medium-Term (1–6 Months)**: Focuses on quarterly guidance, valuation multiples (Forward P/E, PEG), 50 vs 200 SMA trend structure, and Wall Street target consensus.
   - **Long-Term (1–5 Years)**: Focuses on moat quality, Free Cash Flow yield, revenue/earnings CAGR, balance sheet health, and dollar-cost averaging zones.

---

## 🧩 Proposed Changes

### 1. New Decision Agent Module: `decision_agent.py`

#### [NEW] [`decision_agent.py`](file:///Users/kyawagwin/Documents/GitHub/Stock-Agent/decision_agent.py)

Implement the standalone investment decision agent featuring:

- **Custom Quantitative Tools**:
  1. `analyze_timing_and_technical_structure(ticker: str, timeframe: str)`:
     - Moving average extension (% above/below 20, 50, 200 SMA).
     - 14-day RSI (overbought / oversold detection).
     - MACD (12, 26, 9) and histogram expansion/contraction.
     - Bollinger Bands (20-day, 2σ) position & bandwidth.
     - Key Support levels (S1, S2, S3) and Resistance levels (R1, R2).
     - 14-day Average True Range (ATR) for volatility risk buffer.
     - Robust data cleaning (`.dropna(subset=['Close'])`) to prevent NaN edge cases.
  2. `assess_valuation_and_margin_of_safety(ticker: str)`:
     - Multiples: Trailing P/E, Forward P/E, PEG Ratio, Price/Sales, EV/EBITDA, Price/FCF.
     - Financial Health: Operating Margin, ROE, Debt/Equity, Free Cash Flow.
     - Wall Street consensus (Mean, High, Low target prices & recommendations) with calculated Upside/Downside spread.
  3. `check_catalysts_and_risk_events(ticker: str)`:
     - Next Earnings Date, Days until Earnings, Revenue & EPS consensus forecasts.
     - Ex-Dividend Date & Dividend Yield.
     - Short Interest (% of float) and Beta (systematic risk).
  4. `fetch_sentiment_and_news_catalysts(ticker: str)`:
     - News headlines, publisher info, summaries, and sentiment context.

- **Institutional Decision System Prompt**:
  - Requires explicit output sections:
    - **Verdict & Conviction Level**
    - **Execution Blueprint** (Optimal Buy Range, Upside Target, Invalidation / Stop-Loss Level, Risk/Reward Ratio)
    - **Why Now vs. Why Later Thesis**
    - **Timeframe Alignment & Catalysts Analysis**
    - **Trigger Conditions to Flip / Invalidate Decision**

- **Report Generation & Deduplication Engine**:
  - Generates institutional Markdown reports in `reports/` prefixed with `DECISION_` (e.g. `DECISION_NVDA_30_days_2026-09-17.md`).
  - Implements SHA-256 content deduplication and versioning.

- **Interactive CLI & Direct Script Runner**:
  - Interactive prompts for Ticker and Timeframe with smart defaults.

---

### 2. Documentation & Project Entry Points

#### [MODIFY] [`README.md`](file:///Users/kyawagwin/Documents/GitHub/Stock-Agent/README.md)
- Document both agents:
  1. **Market Movement Research Agent** (`main.py`): Directional bias (Bullish/Bearish/Neutral).
  2. **Investment Decision Agent** (`decision_agent.py`): Capital allocation timing (Invest Now vs. Invest Later).

---

## 🧪 Verification Plan

### Automated & End-to-End Tests
1. **Tool Unit Execution Test**:
   - Run a test harness for all 4 tools against diverse tickers (`NVDA`, `AAPL`, `TSLA`, `MSFT`) to verify zero NaNs, correct data parsing, and graceful error handling when optional fields (like earnings dates) are missing.
   - Command: `uv run python -c "..."`

2. **Full Agent Run**:
   - Execute `decision_agent.py` with both short-term (`14 days`) and long-term (`1 year`) timeframes to verify distinct decision reasoning.
   - Command: `uv run decision_agent.py`

3. **Report Generation & Deduplication Verification**:
   - Verify report output in `reports/DECISION_...md`.
   - Verify that running with identical results detects the existing report and prevents file duplication.
