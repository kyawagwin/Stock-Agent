# 📈 Institutional AI Stock Research & Decision Agents (`stock-agent`)

A suite of institutional-grade financial analysis and capital allocation agents powered by **LangChain** and **Google Gemini (`gemini-3.6-flash`)**.

---

## 🤖 Available Agents

The platform provides two specialized AI agents designed for distinct investment workflows:

| Agent Script | Primary Focus | Key Output |
| :--- | :--- | :--- |
| **`main.py`** | **Market Research & Directional Bias** | Bullish / Bearish / Neutral bias, 1-$\sigma$ volatility bands, and scenario analysis (Bull, Base, Bear). |
| **`decision_agent.py`** | **Investment Timing & Capital Allocation** | **"Invest Now vs. Invest Later"** verdict, tactical execution blueprint, ideal buy zones, stops, and risk-reward ratios. |

---

## ⚡ Key Features

### 1. Investment Timing & Decision Agent (`decision_agent.py`)
- **Institutional Decision Rubric**: Categorizes decisions into:
  - `🟢 INVEST NOW (HIGH CONVICTION)`
  - `🟡 INVEST NOW (TRANCHE / DCA)`
  - `🟠 INVEST LATER (WAIT FOR PULLBACK / SUPPORT)`
  - `🔵 INVEST LATER (WAIT FOR CATALYST / EARNINGS)`
  - `🔴 AVOID / DO NOT INVEST`
- **Tactical Execution Blueprint**: Concrete buy entry zone, profit target, invalidation stop-loss, and calculated Risk-to-Reward ratio.
- **Quantitative Timing & Technical Structure**: Moving average extensions (20, 50, 200 SMA), 14-day RSI, MACD momentum expansion/contraction, Bollinger Bands (%B and bandwidth), 14-day ATR volatility buffer, and swing support/resistance levels.
- **Valuation & Margin of Safety**: Trailing/Forward P/E, PEG ratio, P/S, EV/EBITDA, Free Cash Flow, ROE, and Wall Street consensus target spread.
- **Event Risk & Binary Catalyst Detection**: Detects upcoming quarterly earnings release countdowns, ex-dividend dates, short interest % of float, and market beta.

### 2. Market Research Agent (`main.py`)
- **Automated Technical Indicators**: 50-day SMA, 200-day SMA, 14-day RSI, volume comparison vs 20-day average, and 52-week price range.
- **Probabilistic Volatility Projections**: 1-sigma expected move upper and lower price bands over custom time horizons.
- **Company Fundamental Profile**: Profit margins, revenue & earnings growth trends, and balance sheet cash flows.
- **Scenario Analysis**: Bull, Base, and Bear probabilities and invalidation criteria.

### 3. Institutional Reporting & SHA-256 Deduplication
- **Markdown Export**: Saves structured institutional reports in `reports/` (e.g. `DECISION_NVDA_30_days_2026-09-17.md` and `NVDA_30_days_2026-09-16.md`).
- **Content-Hash Deduplication**: SHA-256 hashing prevents redundant file creation when running repeated queries with unchanged market data.
- **Revision Handling**: Gracefully versions same-day revisions (`_v2.md`) when underlying market indicators shift.

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

#### 🎯 Run the Investment Timing & Decision Agent ("Invest Now vs. Invest Later")
```bash
uv run decision_agent.py
```

#### 📊 Run the Market Research Agent (Directional Bias & Volatility Bands)
```bash
uv run main.py
```

---

## 📁 Project Structure

```text
stock-agent/
├── decision_agent.py           # Investment Timing & Decision Agent ('Invest Now vs Invest Later')
├── main.py                     # Quantitative Stock Research & Volatility Agent
├── reports/                    # Generated Markdown analysis and decision reports (deduplicated)
│   ├── DECISION_NVDA_30_days_2026-09-17.md
│   ├── DECISION_TSLA_14_days_2026-09-17.md
│   └── NVDA_30_days_2026-09-16.md
├── pyproject.toml              # Project metadata & dependencies
├── uv.lock                     # Lockfile for reproducible builds
├── .env                        # Local environment credentials (ignored by git)
├── .gitignore                  # Git ignore rules
└── antigravity-artifacts/      # Execution walkthroughs and implementation plans
```

---

## ⚙️ How It Works

1. **User Input**: Enter target ticker (e.g., `NVDA`, `TSLA`, `AAPL`) and timeframe (e.g., `14 days`, `1 month`, `6 months`, `1 year`).
2. **Tool Invocation**: The agent autonomously queries specialized quantitative tools for technical structure, valuation, catalysts, and news sentiment.
3. **Synthesis & Reasoning**: Gemini synthesizes the quantitative signals into a coherent investment thesis, evaluates the bear/bull balance, and issues a definitive recommendation.
4. **Export & Storage**: Automatically compiles and saves a Markdown report with metadata, execution tables, and deduplication safeguards into `reports/`.

