import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
import yfinance as yf
import numpy as np
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain.agents import create_agent

load_dotenv()

# ==========================================
# 1. Custom Tools for Market & Technical Data
# ==========================================

@tool
def fetch_historical_metrics(ticker: str) -> str:
    """
    Fetches technical indicators for a given stock ticker: current price, 
    52-week price range, 50-day & 200-day Simple Moving Averages (SMA), 
    14-day Relative Strength Index (RSI), and trading volume vs 20-day average volume.
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

        # 14-day RSI calculation
        delta = hist["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi_series = 100 - (100 / (1 + rs))
        rsi_14 = rsi_series.iloc[-1] if not rsi_series.empty and not np.isnan(rsi_series.iloc[-1]) else "N/A"
        rsi_formatted = f"{rsi_14:.2f}" if isinstance(rsi_14, (int, float)) else "N/A"

        # Volume comparison
        latest_vol = hist["Volume"].iloc[-1]
        avg_vol_20 = hist["Volume"].rolling(20).mean().iloc[-1]

        return (
            f"Technical Indicators for {ticker.upper()}:\n"
            f"- Current Price: ${latest_close:.2f}\n"
            f"- 50-day SMA: ${sma_50:.2f}\n"
            f"- 200-day SMA: ${sma_200:.2f}\n"
            f"- 14-day RSI: {rsi_formatted}\n"
            f"- 52-Week Range: (${min_52:.2f} - ${max_52:.2f})\n"
            f"- Latest Volume: {latest_vol:,.0f} (20-day Avg: {avg_vol_20:,.0f})"
        )
    except Exception as e:
        return f"Error fetching technical metrics for {ticker}: {str(e)}"


@tool
def calculate_volatility_bands(ticker: str, days: int = 30) -> str:
    """
    Calculates annualized historical volatility and projects an expected
    1-standard-deviation (1-sigma) probabilistic price range over the specified number of days.
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
    Retrieves fundamental metrics: sector, industry, market cap, valuation ratios (P/E, PEG),
    revenue & earnings growth trends, profit margins (gross, operating, net), free cash flow,
    and Wall Street consensus target price / recommendation.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        def fmt_pct(val):
            return f"{val * 100:.2f}%" if isinstance(val, (int, float)) else "N/A"

        def fmt_curr(val):
            return f"${val:,.0f}" if isinstance(val, (int, float)) else "N/A"

        def fmt_num(val):
            return f"{val:.2f}" if isinstance(val, (int, float)) else "N/A"

        return (
            f"Fundamental Profile for {ticker.upper()}:\n"
            f"- Sector / Industry: {info.get('sector', 'N/A')} | {info.get('industry', 'N/A')}\n"
            f"- Market Cap: {fmt_curr(info.get('marketCap'))}\n"
            f"- Valuation: Trailing P/E: {fmt_num(info.get('trailingPE'))} | Forward P/E: {fmt_num(info.get('forwardPE'))} | PEG Ratio: {fmt_num(info.get('pegRatio'))}\n"
            f"- Growth Trends (YoY): Revenue Growth: {fmt_pct(info.get('revenueGrowth'))} | Earnings Growth: {fmt_pct(info.get('earningsGrowth'))}\n"
            f"- Margins: Gross Margin: {fmt_pct(info.get('grossMargins'))} | Operating Margin: {fmt_pct(info.get('operatingMargins'))} | Profit Margin: {fmt_pct(info.get('profitMargins'))}\n"
            f"- Cash Flow & Revenue: Total Revenue: {fmt_curr(info.get('totalRevenue'))} | Free Cash Flow: {fmt_curr(info.get('freeCashflow'))}\n"
            f"- Wall St Consensus: Target Mean Price: ${info.get('targetMeanPrice', 'N/A')} (Recommendation: {info.get('recommendationKey', 'N/A').capitalize()})"
        )
    except Exception as e:
        return f"Error fetching fundamental summary: {str(e)}"


@tool
def fetch_recent_news(ticker: str) -> str:
    """
    Fetches the latest news headlines, publishers, publish timestamps, and summary snippets
    for a given ticker to analyze recent market catalysts and sentiment polarity.
    """
    try:
        stock = yf.Ticker(ticker)
        news_items = stock.news
        if not news_items:
            return f"No recent news articles found for ticker '{ticker}'."

        formatted_news = [f"Recent News Headlines & Catalysts for {ticker.upper()}:"]
        for idx, item in enumerate(news_items[:6], 1):
            content = item.get("content", item)
            title = content.get("title", item.get("title", "No Title"))
            summary = content.get("summary", item.get("summary", ""))
            pub_date = content.get("pubDate", item.get("pubDate", "Recent"))
            provider = content.get("provider", {}).get("displayName", item.get("publisher", "Financial News"))

            headline_entry = f"{idx}. [{provider}] \"{title}\" ({pub_date})"
            if summary:
                headline_entry += f"\n   Summary: {summary}"
            formatted_news.append(headline_entry)

        return "\n".join(formatted_news)
    except Exception as e:
        return f"Error fetching news for {ticker}: {str(e)}"


# ==========================================
# 2. Agent Configuration
# ==========================================

tools = [fetch_historical_metrics, calculate_volatility_bands, get_company_summary, fetch_recent_news]

SYSTEM_PROMPT = (
    "Role: You are an expert quantitative financial analyst and market researcher.\n\n"
    "Task: Analyze the provided financial data, recent news headlines, and technical indicators "
    "for the given ticker symbol and timeframe. Evaluate revenue trends, profit margins, macro risks, "
    "and sentiment polarity. Provide a short-term market movement prediction (Bullish, Bearish, or Neutral) "
    "with a confidence level (Low, Medium, High).\n\n"
    "Constraints:\n"
    "1. Cite specific data points or headlines to justify each driver.\n"
    "2. Play devil's advocate by listing the top 2-3 strongest opposing bear/bull arguments.\n"
    "3. Do not offer definitive financial guarantees or absolute target prices; instead, provide probability-based scenarios.\n\n"
    "Output Format:\n"
    "- Executive Summary & Directional Bias (Bullish/Bearish/Neutral) + Confidence Level\n"
    "- Key Fundamental & Sentiment Drivers (with source citation)\n"
    "- Risk Factors & Counter-Arguments\n"
    "- Analytical Conclusion"
)

MODEL_NAME = "gemini-3.6-flash"
llm = ChatGoogleGenerativeAI(model=MODEL_NAME)

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
)

# ==========================================
# 3. Report Generation & Deduplication
# ==========================================

def extract_response_text(response: dict) -> str:
    """Extracts the assistant's final text content from the agent response dict."""
    if not response or "messages" not in response or not response["messages"]:
        return ""
    final_message = response["messages"][-1]
    if hasattr(final_message, "text") and final_message.text:
        return str(final_message.text).strip()
    elif isinstance(final_message.content, list):
        text_parts = []
        for part in final_message.content:
            if isinstance(part, dict) and "text" in part:
                text_parts.append(str(part["text"]))
            elif isinstance(part, str):
                text_parts.append(part)
            else:
                text_parts.append(str(part))
        return "\n".join(text_parts).strip()
    elif isinstance(final_message.content, str):
        return final_message.content.strip()
    return str(final_message.content).strip()


def compute_content_hash(text: str) -> str:
    """Computes SHA-256 hash of normalized text content to detect duplicates."""
    normalized = "".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def save_analysis_report(
    analysis_text: str,
    ticker: str,
    timeframe: str,
    output_dir: str = "reports",
    model_name: str = MODEL_NAME,
) -> tuple[Path | None, bool]:
    """
    Formats and saves the final analysis into a structured Markdown file
    in the specified directory, with deduplication checks.

    Returns:
        tuple[Path | None, bool]: (File path, was_created)
        where was_created is False if an identical report already existed.
    """
    if not analysis_text or not analysis_text.strip():
        print("[Warning] No analysis content to save.")
        return None, False

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    sanitized_ticker = re.sub(r"[^A-Za-z0-9_-]", "", ticker).upper()
    sanitized_timeframe = re.sub(r"[^A-Za-z0-9_-]", "", timeframe.replace(" ", "_")).lower()
    today_str = datetime.now().strftime("%Y-%m-%d")
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_content_hash = compute_content_hash(analysis_text)

    # 1. Check if an identical report for this ticker already exists in output_dir
    for existing_file in target_dir.glob(f"{sanitized_ticker}_*.md"):
        try:
            existing_text = existing_file.read_text(encoding="utf-8")
            if compute_content_hash(existing_text) == new_content_hash or analysis_text.strip() in existing_text:
                return existing_file, False
        except Exception:
            continue

    # 2. Format markdown report with institutional header
    report_markdown = (
        f"# 📊 Quantitative Stock Research: {sanitized_ticker}\n\n"
        f"| Metric / Attribute | Value |\n"
        f"| :--- | :--- |\n"
        f"| **Ticker** | `{sanitized_ticker}` |\n"
        f"| **Timeframe** | `{timeframe}` |\n"
        f"| **Report Date** | `{timestamp_str}` |\n"
        f"| **Analysis Model** | `{model_name}` |\n\n"
        f"---\n\n"
        f"## 📝 Research Summary & Scenario Analysis\n\n"
        f"{analysis_text.strip()}\n"
    )

    # 3. Determine unique filename (handling same-day revisions gracefully)
    base_filename = f"{sanitized_ticker}_{sanitized_timeframe}_{today_str}"
    target_file = target_dir / f"{base_filename}.md"

    version = 2
    while target_file.exists():
        target_file = target_dir / f"{base_filename}_v{version}.md"
        version += 1

    target_file.write_text(report_markdown, encoding="utf-8")
    return target_file, True


# ==========================================
# 4. Execution
# ==========================================

if __name__ == "__main__":
    print("📈 Quantitative Stock Research Assistant")
    print("=" * 45)
    
    raw_ticker = input("Enter Stock Ticker (e.g., NVDA, AAPL, MSFT) [default: NVDA]: ").strip()
    ticker = raw_ticker.upper() if raw_ticker else "NVDA"
    
    raw_timeframe = input("Enter Timeframe (e.g., 30 days, 60 days, 3 months) [default: 30 days]: ").strip()
    timeframe = raw_timeframe if raw_timeframe else "30 days"
    
    user_query = f"Analyze ticker: {ticker} for the timeframe: {timeframe}."
    
    print(f"\nRunning quantitative analysis for {ticker} ({timeframe})...\n")
    response = agent.invoke({"messages": [{"role": "user", "content": user_query}]})
    
    analysis_text = extract_response_text(response)
    
    print("\n--- Final Analysis ---")
    print(analysis_text)
    
    # Save analysis report with deduplication
    report_path, created = save_analysis_report(analysis_text, ticker, timeframe)
    if report_path:
        if created:
            print(f"\n✅ Analysis report saved to: {report_path}")
        else:
            print(f"\nℹ️ Identical report already exists at: {report_path} (Skipped duplicate creation)")