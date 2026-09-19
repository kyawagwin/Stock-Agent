# 📈 Institutional AI Stock Research & Decision Agents (`stock-agent`)

A suite of institutional-grade financial analysis, forensic due diligence, and capital allocation agents powered by **LangChain** and **Google Gemini (`gemini-3.6-flash`)**.

---

## 🤖 Available Agents & Pipelines

The platform provides a two-stage autonomous orchestration pipeline along with standalone specialized agents:

| Script | Primary Focus | Key Output |
| :--- | :--- | :--- |
| **`pipeline.py`** | **Two-Stage Institutional Diligence & Execution Pipeline** | **End-to-End Orchestrator**: Stage 1 Forensic Audit diagnoses natural horizon (`Long-Term`, `Short-Term`, `All-Weather`, or `Avoid`). If viable, automatically hands off to Stage 2 for tactical buy zones and stops. If toxic, short-circuits to protect capital. |
| **`forensic_agent.py`** | **Forensic Due Diligence & Horizon Classification** | Split-adjusted 3-year share dilution CAGR, 12-month net insider conviction, solvency & cash runway, multi-year operating margin persistence, and beta/cyclicality audit. |
| **`decision_agent.py`** | **Investment Timing & Capital Allocation** | **"Invest Now vs. Invest Later"** verdict, tactical execution blueprint, ideal buy zones, stops, and risk-reward ratios. |
| **`main.py`** | **Market Research & Directional Bias** | Bullish / Bearish / Neutral bias, 1-$\sigma$ volatility bands, and scenario analysis (Bull, Base, Bear). |

---

## ⚡ Key Features

### 1. Two-Stage Institutional Pipeline (`pipeline.py`)
- **Zero-Guesswork Execution**: The user only provides the stock ticker; the system autonomously audits corporate financial health, determines the appropriate investment timeframe, and coordinates execution.
- **Capital Preservation Short-Circuit**: If an asset fails fundamental forensic tests (predatory share dilution, debt distress, or cash burn), execution is immediately halted to prevent speculative capital destruction.
- **Unified Institutional Dossier**: Exports a consolidated report combining forensic audit tables and tactical execution blueprints with SHA-256 deduplication.

### 2. Forensic Due Diligence & Horizon Classifier (`forensic_agent.py`)
- **Deterministic Horizon Rubric**:
  - `🟢 LONG-TERM COMPOUNDER`: Sub-2.5% dilution/buybacks, fortress balance sheet (positive FCF), high operating margins (>15-20%), and strong economic moat. (Recommended Horizon: 1 to 3+ Years).
  - `🟡 SHORT-TERM TACTICAL SWING`: Viable liquidity but elevated beta (>1.5), cyclical margins, or high multiple. (Recommended Horizon: 30 to 60 Days).
  - `🟣 ALL-WEATHER / CORE ASSET`: World-class secular moat meeting all Long-Term criteria, combined with immediate technical entry setup.
  - `🔴 AVOID / TOXIC`: Predatory dilution (>10-15% CAGR), sub-12-month cash runway, or collapsing unit economics. (Immediate Avoidance).
- **Split-Adjusted Share Dilution**: Accurately handles stock splits (e.g. NVDA 10:1, TSLA 3:1) when measuring multi-year share count drift.
- **Insider Conviction Screening**: Classifies SEC Form 4 filings into open-market cash buying vs. 10b5-1 executive selling.
- **Solvency & Cash Runway Audit**: Evaluates Cash vs. Total Debt, current ratios, and calculates remaining operational months for cash-burning businesses.
- **Margin Durability & Moat Tracking**: Evaluates multi-year progression of gross and operating margins.

### 3. Investment Timing & Decision Agent (`decision_agent.py`)
- **Institutional Decision Rubric**: Categorizes decisions into:
  - `🟢 INVEST NOW (HIGH CONVICTION)`
  - `🟡 INVEST NOW (TRANCHE / DCA)`
  - `🟠 INVEST LATER (WAIT FOR PULLBACK / SUPPORT)`
  - `🔵 INVEST LATER (WAIT FOR CATALYST / EARNINGS)`
  - `🔴 AVOID / DO NOT INVEST`
- **Tactical Execution Blueprint**: Concrete buy entry zone, profit target, invalidation stop-loss, and calculated Risk-to-Reward ratio.
- **Quantitative Timing & Technical Structure**: Moving average extensions (20, 50, 200 SMA), 14-day RSI, MACD momentum, Bollinger Bands (%B and bandwidth), 14-day ATR volatility buffer, and swing support/resistance levels.
- **Valuation & Margin of Safety**: Trailing/Forward P/E, PEG ratio, P/S, EV/EBITDA, Free Cash Flow, ROE, and Wall Street consensus target spread.
- **Event Risk & Binary Catalyst Detection**: Detects upcoming quarterly earnings release countdowns, ex-dividend dates, short interest % of float, and market beta.

### 4. Market Research Agent (`main.py`)
- **Automated Technical Indicators**: 50-day SMA, 200-day SMA, 14-day RSI, volume comparison vs 20-day average, and 52-week price range.
- **Probabilistic Volatility Projections**: 1-sigma expected move upper and lower price bands over custom time horizons.
- **Company Fundamental Profile**: Profit margins, revenue & earnings growth trends, and balance sheet cash flows.
- **Scenario Analysis**: Bull, Base, and Bear probabilities and invalidation criteria.

---

## 🛠️ Technology Stack

- **LLM**: Google Gemini (`gemini-3.6-flash`) via `langchain-google-genai`
- **Agent Framework**: `langchain.agents.create_agent`
- **Market & Financial Data**: `yfinance`, `numpy`, `pandas`
- **Environment & Package Management**: `uv`, `python-dotenv`

---

## 🚀 Quickstart Guide

### 1. Prerequisites

Ensure you have **Python 3.12+** and **`uv`** installed:
```bash
python3 --version
uv --version
```

### 2. Virtual Environment Setup

```bash
# Sync dependencies and create .venv
uv sync
```

### 3. Configure Environment Variables

Create or update the `.env` file in the project root with your Google Gemini API Key:

```ini
GEMINI_API_KEY="your-gemini-api-key-here"
```

> 💡 *Note: You can acquire a Gemini API key from [Google AI Studio](https://aistudio.google.com/).*

### 4. Run the Agents

#### 🏛️ Master Pipeline: Autonomous Diligence & Execution (Recommended)
```bash
uv run pipeline.py
```
*Prompts for a ticker, performs the forensic audit, diagnoses the natural horizon, and automatically routes to Stage 2 for tactical execution levels.*

#### 🔬 Run Standalone Forensic Due Diligence & Horizon Classifier
```bash
uv run forensic_agent.py
```

#### 🎯 Run Standalone Investment Timing & Decision Agent
```bash
uv run decision_agent.py
```

#### 📊 Run Standalone Market Research Agent
```bash
uv run main.py
```

---

## 📁 Project Structure

```text
stock-agent/
├── pipeline.py                 # Master Orchestrator (Forensics -> Horizon -> Tactical Execution)
├── forensic_agent.py           # Stage 1: Forensic Due Diligence & Horizon Classification Agent
├── decision_agent.py           # Stage 2: Investment Timing & Tactical Decision Agent
├── main.py                     # Market Research & Volatility Projections Agent
├── reports/                    # Generated Markdown intelligence dossiers (SHA-256 deduplicated)
│   ├── UNIFIED_NVDA_ALL_WEATHER_2026-09-19.md
│   ├── UNIFIED_NKLA_AVOID_2026-09-19.md
│   └── DECISION_NVDA_30_days_2026-09-17.md
├── pyproject.toml              # Project metadata & dependencies
├── uv.lock                     # Lockfile for reproducible builds
├── .env                        # Local environment credentials (ignored by git)
└── openspec/                   # OpenSpec specifications and changes
```
