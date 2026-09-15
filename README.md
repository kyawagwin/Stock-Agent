# 📈 Quantitative Stock Research Agent (`stock-agent`)

An institutional quantitative equity research assistant powered by **LangChain** and **Google Gemini (`gemini-2.5-flash`)**. 

The agent analyzes stock tickers over customizable timeframes by combining fundamental data, simple moving averages (SMA), 52-week price extremes, and 1-sigma historical volatility price projections to generate objective, range-based market scenario analysis (Bull, Base, Bear).

---

## ⚡ Key Features

- **Automated Technical Metrics**: Fetches 50-day SMA, 200-day SMA, current market prices, and 52-week ranges via `yfinance`.
- **Statistical Volatility Band Projection**: Calculates annualized historical volatility and projects 1-standard-deviation ($\pm 1\sigma$) expected price moves.
- **Fundamental Summary**: Retrieves market capitalization, sector classification, forward P/E ratios, and Wall Street consensus price targets.
- **LangChain Tool-Calling Agent**: Integrates custom Python analytical tools into a structured reasoning loop backed by Google Gemini.

---

## 🛠️ Technology Stack

- **LLM**: Google Gemini (`gemini-2.5-flash`) via `langchain-google-genai`
- **Agent Framework**: `langchain` tool-calling agent & `AgentExecutor`
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

Create and sync the virtual environment using `uv`:
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

### 4. Run the Research Agent

Execute the agent script directly:

```bash
uv run main.py
```

Or using the `.venv` Python executable:

```bash
.venv/bin/python main.py
```

---

## 📁 Project Structure

```text
stock-agent/
├── main.py                     # Main agent script, tools definition, and prompt template
├── pyproject.toml              # Project metadata & dependencies
├── uv.lock                     # Lockfile for reproducible builds
├── .env                        # Local environment credentials (ignored by git)
├── .gitignore                  # Git ignore rules
└── antigravity-artifacts/      # Execution walkthroughs and implementation plans
```

---

## ⚙️ How It Works

1. **Query Input**: The user inputs a ticker (e.g., `NVDA`) and a target horizon (e.g., `30 days`).
2. **Tool Invocation**:
   - `fetch_historical_metrics`: Pulls latest price, moving averages, and 52-week range.
   - `calculate_volatility_bands`: Computes daily returns standard deviation and projects upper/lower bounds.
   - `get_company_summary`: Gathers sector, market cap, P/E ratio, and mean price targets.
3. **Synthesis & Scenario Generation**: The Gemini model processes the tool outputs to generate an objective Bull, Base, and Bear range estimate along with key technical invalidation levels.
