import os
import yfinance as yf
import numpy as np
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor

load_dotenv()

# ==========================================
# 1. Custom Tools for Market & Technical Data
# ==========================================

@tool
def fetch_historical_metrics(ticker: str) -> str:
    """
    Fetches the latest closing price, 52-week range, and 50/200-day simple
    moving averages (SMA) for a given stock ticker.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if hist.empty:
            return f"Error: No trading data available for ticker '{ticker}'."

        latest_close = hist["Close"].iloc[-1]
        sma_50 = hist["Close"].rolling(50).mean().iloc[-1]
        sma_200 = hist["Close"].rolling(200).mean().iloc[-1]
        min_52 = hist["Low"].min()
        max_52 = hist["High"].max()

        return (
            f"Metrics for {ticker.upper()}:\n"
            f"- Current Price: ${latest_close:.2f}\n"
            f"- 50-day SMA: ${sma_50:.2f}\n"
            f"- 200-day SMA: ${sma_200:.2f}\n"
            f"- 52-Week Range: (${min_52:.2f} - ${max_52:.2f})"
        )
    except Exception as e:
        return f"Error fetching market metrics for {ticker}: {str(e)}"


@tool
def calculate_volatility_bands(ticker: str, days: int = 30) -> str:
    """
    Calculates annualized historical volatility and projects an expected
    1-standard-deviation probabilistic price range over the specified number of days.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        if hist.empty or len(hist) < 30:
            return f"Error: Insufficient data to calculate volatility for {ticker}."

        close_prices = hist["Close"]
        daily_returns = close_prices.pct_change().dropna()
        daily_vol = daily_returns.std()
        annualized_vol = daily_vol * np.sqrt(252)

        current_price = close_prices.iloc[-1]
        # 1-sigma expected move: Price * (Daily Vol * sqrt(T))
        t_move = daily_vol * np.sqrt(days)
        lower_bound = current_price * (1 - t_move)
        upper_bound = current_price * (1 + t_move)

        return (
            f"Volatility & Projections for {ticker.upper()} over {days} days:\n"
            f"- Annualized Volatility: {annualized_vol * 100:.2f}%\n"
            f"- 1-Sigma Expected Move: ±{t_move * 100:.2f}%\n"
            f"- Lower Volatility Bound: ${lower_bound:.2f}\n"
            f"- Upper Volatility Bound: ${upper_bound:.2f}"
        )
    except Exception as e:
        return f"Error calculating volatility bands: {str(e)}"


@tool
def get_company_summary(ticker: str) -> str:
    """
    Retrieves company fundamentals: sector, market cap, forward P/E, 
    and analyst consensus target price.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return (
            f"Fundamentals for {ticker.upper()}:\n"
            f"- Sector: {info.get('sector', 'N/A')}\n"
            f"- Market Cap: ${info.get('marketCap', 0):,}\n"
            f"- Forward P/E: {info.get('forwardPE', 'N/A')}\n"
            f"- Wall St Mean Target: ${info.get('targetMeanPrice', 'N/A')}"
        )
    except Exception as e:
        return f"Error fetching fundamental summary: {str(e)}"


# ==========================================
# 2. Agent Configuration
# ==========================================

tools = [fetch_historical_metrics, calculate_volatility_bands, get_company_summary]

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an institutional quantitative equity research assistant. "
        "Your task is to provide objective, range-based price estimation scenarios "
        "for a given ticker and timeframe using tool outputs.\n\n"
        "Guidelines:\n"
        "1. Never guess single-point targets. Always compute bounded ranges (Bull, Base, Bear).\n"
        "2. Ground your base target on moving averages, analyst consensus, and statistical bands.\n"
        "3. Explicitly state the primary technical levels and catalysts that would invalidate the thesis."
    ),
    ("human", "Analyze ticker: {ticker} for the timeframe: {timeframe}."),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# ==========================================
# 3. Execution
# ==========================================

if __name__ == "__main__":
    query = {"ticker": "NVDA", "timeframe": "30 days"}
    response = agent_executor.invoke(query)
    print("\n--- Final Analysis ---")
    print(response["output"])