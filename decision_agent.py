import os
import re
import hashlib
from datetime import datetime, date
from pathlib import Path
import yfinance as yf
import numpy as np
import pandas as pd
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain.agents import create_agent

load_dotenv()

# ==========================================================
# 1. Custom Quantitative Tools for Investment Timing & Decision
# ==========================================================

@tool
def analyze_timing_and_technical_structure(ticker: str, timeframe: str = "30 days") -> str:
    """
    Evaluates market timing and technical structure: current price, moving average extensions 
    (20, 50, 200 SMA), 14-day RSI, MACD momentum, Bollinger Bands (%B and bandwidth), 
    ATR volatility risk, and key support / resistance zones.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if hist.empty:
            return f"Error: No historical trading data available for ticker '{ticker}'."

        # Clean any trailing NaN rows (e.g., unsettled real-time market bars)
        hist = hist.dropna(subset=["Close", "High", "Low", "Volume"])
        if len(hist) < 30:
            return f"Error: Insufficient historical price bars ({len(hist)}) for {ticker}."

        close = hist["Close"]
        high = hist["High"]
        low = hist["Low"]
        volume = hist["Volume"]

        current_price = close.iloc[-1]

        # Moving Averages
        sma_20 = close.rolling(20).mean().iloc[-1] if len(close) >= 20 else current_price
        sma_50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else current_price
        sma_200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else current_price

        ext_50 = ((current_price - sma_50) / sma_50) * 100 if sma_50 else 0
        ext_200 = ((current_price - sma_200) / sma_200) * 100 if sma_200 else 0

        # 14-day RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi_series = 100 - (100 / (1 + rs))
        rsi_14 = rsi_series.iloc[-1] if not rsi_series.empty and not np.isnan(rsi_series.iloc[-1]) else 50.0

        # MACD (12, 26, 9)
        exp12 = close.ewm(span=12, adjust=False).mean()
        exp26 = close.ewm(span=26, adjust=False).mean()
        macd = exp12 - exp26
        signal = macd.ewm(span=9, adjust=False).mean()
        macd_val = macd.iloc[-1]
        signal_val = signal.iloc[-1]
        macd_hist = macd_val - signal_val

        # Bollinger Bands (20-day, 2 std)
        rolling_std = close.rolling(20).std().iloc[-1]
        bb_upper = sma_20 + (2 * rolling_std)
        bb_lower = sma_20 - (2 * rolling_std)
        bb_bandwidth = ((bb_upper - bb_lower) / sma_20) * 100 if sma_20 else 0
        pct_b = (current_price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) != 0 else 0.5

        # 14-day ATR
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr_14 = tr.rolling(14).mean().iloc[-1] if len(tr) >= 14 else 0

        # Key Support & Resistance Levels
        recent_60 = hist.tail(60)
        swing_high_60 = recent_60["High"].max()
        swing_low_60 = recent_60["Low"].min()
        high_52w = hist["High"].max()
        low_52w = hist["Low"].min()

        # Overbought / Oversold Assessment
        if rsi_14 >= 70:
            timing_condition = "OVERBOUGHT (RSI >= 70) - High risk of mean-reversion pullback"
        elif rsi_14 <= 30:
            timing_condition = "OVERSOLD (RSI <= 30) - Potential bargain / reversal zone"
        elif ext_50 > 12:
            timing_condition = "EXTENDED ABOVE 50 SMA (> +12%) - Chasing risk elevated"
        elif ext_50 < -12:
            timing_condition = "DISCOUNTED BELOW 50 SMA (< -12%) - Deep value or severe downtrend"
        else:
            timing_condition = "HEALTHY CONSOLIDATION / NEUTRAL OSCILLATION"

        return (
            f"Technical Structure & Timing Analysis for {ticker.upper()} (Horizon: {timeframe}):\n"
            f"- Current Price: ${current_price:.2f}\n"
            f"- 20-Day SMA: ${sma_20:.2f} | 50-Day SMA: ${sma_50:.2f} | 200-Day SMA: ${sma_200:.2f}\n"
            f"- Moving Average Extensions: vs 50 SMA: {ext_50:+.2f}% | vs 200 SMA: {ext_200:+.2f}%\n"
            f"- 14-Day RSI: {rsi_14:.2f} ({timing_condition})\n"
            f"- MACD (12,26,9): MACD={macd_val:.2f}, Signal={signal_val:.2f}, Histogram={macd_hist:.2f} "
            f"({'Bullish Momentum Expanding' if macd_hist > 0 else 'Bearish/Consolidation Momentum'})\n"
            f"- Bollinger Bands (20-day, 2σ): Lower=${bb_lower:.2f} | Upper=${bb_upper:.2f} | %B={pct_b:.2f} | Bandwidth={bb_bandwidth:.2f}%\n"
            f"- 14-Day ATR: ${atr_14:.2f} (~{(atr_14 / current_price)*100:.2f}% daily volatility buffer)\n"
            f"- Key Support Levels: S1 (50 SMA)=${sma_50:.2f}, S2 (200 SMA)=${sma_200:.2f}, S3 (60d Low)=${swing_low_60:.2f}\n"
            f"- Key Resistance Levels: R1 (60d High)=${swing_high_60:.2f}, R2 (52w High)=${high_52w:.2f}"
        )
    except Exception as e:
        return f"Error analyzing timing and technical structure for {ticker}: {str(e)}"


@tool
def assess_valuation_and_margin_of_safety(ticker: str) -> str:
    """
    Evaluates valuation multiples (P/E, Forward P/E, PEG, P/S, EV/EBITDA), profitability margins,
    balance sheet strength (Cash vs Debt), Free Cash Flow, and Wall Street consensus price targets 
    with upside/downside spread to calculate the Margin of Safety.
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

        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose", 0)
        target_mean = info.get("targetMeanPrice")
        target_high = info.get("targetHighPrice")
        target_low = info.get("targetLowPrice")
        recommendation = info.get("recommendationKey", "N/A").capitalize()
        num_analysts = info.get("numberOfAnalystOpinions", "N/A")

        # Calculated spread to consensus target
        if current_price and target_mean and isinstance(target_mean, (int, float)):
            consensus_upside = ((target_mean - current_price) / current_price) * 100
            upside_str = f"{consensus_upside:+.2f}%"
        else:
            upside_str = "N/A"

        trailing_pe = info.get("trailingPE")
        forward_pe = info.get("forwardPE")
        peg_ratio = info.get("pegRatio")
        price_to_sales = info.get("priceToSalesTrailing12Months")
        ev_to_ebitda = info.get("enterpriseToEbitda")

        return (
            f"Valuation & Margin of Safety Profile for {ticker.upper()}:\n"
            f"- Company Name & Sector: {info.get('shortName', ticker)} | {info.get('sector', 'N/A')} ({info.get('industry', 'N/A')})\n"
            f"- Market Cap: {fmt_curr(info.get('marketCap'))} | Enterprise Value: {fmt_curr(info.get('enterpriseValue'))}\n"
            f"- Valuation Multiples: Trailing P/E: {fmt_num(trailing_pe)} | Forward P/E: {fmt_num(forward_pe)} | PEG Ratio: {fmt_num(peg_ratio)} | P/S: {fmt_num(price_to_sales)} | EV/EBITDA: {fmt_num(ev_to_ebitda)}\n"
            f"- Profitability & Returns: Gross Margin: {fmt_pct(info.get('grossMargins'))} | Operating Margin: {fmt_pct(info.get('operatingMargins'))} | Profit Margin: {fmt_pct(info.get('profitMargins'))} | ROE: {fmt_pct(info.get('returnOnEquity'))}\n"
            f"- Growth Metrics (YoY): Revenue Growth: {fmt_pct(info.get('revenueGrowth'))} | Earnings Growth: {fmt_pct(info.get('earningsGrowth'))}\n"
            f"- Balance Sheet & Cash Flow: Total Cash: {fmt_curr(info.get('totalCash'))} | Total Debt: {fmt_curr(info.get('totalDebt'))} | Free Cash Flow: {fmt_curr(info.get('freeCashflow'))}\n"
            f"- Wall Street Consensus ({num_analysts} Analysts): Rating: {recommendation} | Mean Target: ${fmt_num(target_mean)} (Implied Upside: {upside_str}) | Low: ${fmt_num(target_low)} | High: ${fmt_num(target_high)}"
        )
    except Exception as e:
        return f"Error assessing valuation for {ticker}: {str(e)}"


@tool
def check_catalysts_and_risk_events(ticker: str) -> str:
    """
    Identifies upcoming binary risk events and catalysts: next earnings release date, 
    days until earnings, EPS/Revenue consensus forecasts, dividend dates, short interest % of float,
    and systematic beta risk.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        calendar = stock.calendar

        # Parse earnings date
        earnings_date_str = "N/A"
        days_to_earnings_str = "N/A"
        earnings_risk_flag = "No immediate earnings risk detected"

        if calendar and isinstance(calendar, dict):
            earnings_dates = calendar.get("Earnings Date")
            if earnings_dates:
                if isinstance(earnings_dates, list) and len(earnings_dates) > 0:
                    next_e_date = earnings_dates[0]
                else:
                    next_e_date = earnings_dates

                if isinstance(next_e_date, (datetime, date)):
                    earnings_date_str = str(next_e_date)
                    today = date.today()
                    if isinstance(next_e_date, datetime):
                        target_d = next_e_date.date()
                    else:
                        target_d = next_e_date
                    days_diff = (target_d - today).days
                    days_to_earnings_str = f"{days_diff} days"
                    if 0 <= days_diff <= 14:
                        earnings_risk_flag = f"⚠️ HIGH BINARY RISK: Earnings release in {days_diff} days! Elevated gap risk."
                    elif days_diff < 0:
                        days_to_earnings_str = f"{abs(days_diff)} days ago (Recently reported)"
                else:
                    earnings_date_str = str(next_e_date)

        def fmt_pct(val):
            return f"{val * 100:.2f}%" if isinstance(val, (int, float)) else "N/A"

        def fmt_num(val):
            return f"{val:.2f}" if isinstance(val, (int, float)) else "N/A"

        short_float = info.get("shortPercentOfFloat")
        short_ratio = info.get("shortRatio")
        beta = info.get("beta")
        div_yield = info.get("dividendYield")
        payout_ratio = info.get("payoutRatio")

        return (
            f"Catalyst & Event Risk Assessment for {ticker.upper()}:\n"
            f"- Next Earnings Date: {earnings_date_str} (Countdown: {days_to_earnings_str})\n"
            f"- Event Risk Notice: {earnings_risk_flag}\n"
            f"- Short Interest: {fmt_pct(short_float)} of float (Short Ratio: {fmt_num(short_ratio)} days to cover)\n"
            f"- Market Beta: {fmt_num(beta)} ({'High volatility vs market' if isinstance(beta, (int, float)) and beta > 1.3 else 'Moderate / Low volatility vs market'})\n"
            f"- Dividend Profile: Yield: {fmt_pct(div_yield)} | Payout Ratio: {fmt_pct(payout_ratio)}\n"
            f"- Earnings Estimates: Avg EPS Est: ${fmt_num(calendar.get('Earnings Average') if isinstance(calendar, dict) else None)} | Avg Revenue Est: ${calendar.get('Revenue Average', 'N/A') if isinstance(calendar, dict) else 'N/A'}"
        )
    except Exception as e:
        return f"Error checking catalysts for {ticker}: {str(e)}"


@tool
def fetch_sentiment_and_news_catalysts(ticker: str) -> str:
    """
    Fetches the latest news headlines, summaries, and publishers to gauge market sentiment 
    and identify emerging company-specific catalysts.
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


# ==========================================================
# 2. Agent Configuration & Institutional Decision Rubric
# ==========================================================

tools = [
    analyze_timing_and_technical_structure,
    assess_valuation_and_margin_of_safety,
    check_catalysts_and_risk_events,
    fetch_sentiment_and_news_catalysts,
]

SYSTEM_PROMPT = (
    "Role: You are a Senior Portfolio Manager and Chief Investment Officer (CIO) leading an institutional investment committee.\n\n"
    "Primary Objective: You are tasked with answering the critical capital allocation question for a given ticker and timeframe: "
    "'SHOULD THE INVESTOR INVEST NOW OR INVEST LATER?'\n\n"
    "Decision Framework & Categorization:\n"
    "You MUST choose exactly ONE of the following definitive verdicts:\n"
    "1. 🟢 INVEST NOW (HIGH CONVICTION) - Immediate capital deployment. Technicals are attractive (oversold or breakout confirmed), "
    "valuation offers solid margin of safety, and no high-risk binary events loom within the timeframe.\n"
    "2. 🟡 INVEST NOW (TRANCHE / DCA) - Bullish fundamental thesis intact, but elevated near-term volatility suggests scaling in. "
    "Deploy 30–50% now and reserve remaining capital for pullbacks to designated support levels.\n"
    "3. 🟠 INVEST LATER (WAIT FOR PULLBACK / SUPPORT) - Great asset, but currently extended/overbought (RSI high, stretched above 50 SMA, "
    "or at heavy resistance). Specify the exact price zone to wait for before buying.\n"
    "4. 🔵 INVEST LATER (WAIT FOR CATALYST / EARNINGS) - High binary risk (e.g. imminent earnings in < 14 days, regulatory review). "
    "Recommend waiting until after the event to confirm guidance/results.\n"
    "5. 🔴 AVOID / DO NOT INVEST - Deteriorating fundamentals, poor risk/reward ratio (< 1.5:1), or broken secular trend.\n\n"
    "Crucial Guidelines:\n"
    "- Timeframe Alignment: You must tailor your decision directly to the user's requested timeframe. Short timeframes (e.g. 1-4 weeks) "
    "depend heavily on technical entry timing, RSI, and earnings proximity. Long timeframes (e.g. 1-5 years) prioritize valuation, moat, "
    "and cash flow over short-term noise.\n"
    "- Devil's Advocate / Bear-Bull Balance: Actively challenge your own verdict. State what would prove this recommendation wrong.\n"
    "- Be Concrete: Provide exact price levels (Ideal Entry Zone, Profit Target, Invalidation/Stop Level, and Risk-to-Reward Ratio).\n\n"
    "Required Output Format in Markdown:\n"
    "### 1. 🎯 Executive Investment Verdict\n"
    "- **Decision Verdict:** [Choose 1 exact verdict from the 5 categories above]\n"
    "- **Conviction Level:** [High / Medium / Low]\n"
    "- **Time Horizon:** [User's timeframe]\n"
    "- **Executive Summary:** [2-3 concise sentences detailing why NOW or why LATER]\n\n"
    "### 2. 📐 Tactical Execution Blueprint\n"
    "| Parameter | Target Level / Value | Tactical Rationale |\n"
    "| :--- | :--- | :--- |\n"
    "| **Current Price** | $X.XX | Market reference |\n"
    "| **Ideal Buy Entry Zone** | $X.XX – $Y.YY | Optimal risk-adjusted accumulation zone |\n"
    "| **Upside Target (Take Profit)** | $Z.ZZ | Resistance / Fair value objective |\n"
    "| **Downside Invalidation (Stop)** | $W.WW | Thesis broken / structural breakdown level |\n"
    "| **Risk-to-Reward Ratio** | e.g. 3.2 : 1 | Asymmetry calculation |\n\n"
    "### 3. ⚖️ Core Thesis: Why Now vs. Why Later\n"
    "[Deep-dive analytical reasoning combining valuation, timing, and catalysts. Cite specific numbers from tools.]\n\n"
    "### 4. 🔍 Valuation, Financial Health & Margin of Safety\n"
    "[Analyze P/E, PEG, Free Cash Flow, Profitability, and Wall Street Consensus upside.]\n\n"
    "### 5. 📊 Technical Timing & Event Risk Profile\n"
    "[Analyze RSI, moving average distance, ATR volatility buffer, support/resistance, and upcoming earnings calendar countdown.]\n\n"
    "### 6. 🔄 Actionable Triggers to Flip / Invalidate Decision\n"
    "- **Conditions to Upgrade/Buy:** [Exact triggers if verdict is Invest Later]\n"
    "- **Conditions to Exit/Invalidate:** [Exact triggers that invalidate the bullish case]"
)

MODEL_NAME = "gemini-3.6-flash"
llm = ChatGoogleGenerativeAI(model=MODEL_NAME)

decision_agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
)

# ==========================================================
# 3. Report Generation & Deduplication Engine
# ==========================================================

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
    """Computes SHA-256 hash of normalized text content to detect duplicate reports."""
    normalized = "".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def save_decision_report(
    analysis_text: str,
    ticker: str,
    timeframe: str,
    output_dir: str = "reports",
    model_name: str = MODEL_NAME,
) -> tuple[Path | None, bool]:
    """
    Saves the investment decision analysis into a structured Markdown report
    in the specified directory, with SHA-256 deduplication and auto-versioning.

    Returns:
        tuple[Path | None, bool]: (File path, was_created)
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

    # 1. Check if identical report already exists
    for existing_file in target_dir.glob(f"DECISION_{sanitized_ticker}_*.md"):
        try:
            existing_text = existing_file.read_text(encoding="utf-8")
            if compute_content_hash(existing_text) == new_content_hash or analysis_text.strip() in existing_text:
                return existing_file, False
        except Exception:
            continue

    # 2. Format institutional Markdown decision report
    report_markdown = (
        f"# 🧭 Institutional Investment Decision: {sanitized_ticker}\n\n"
        f"| Metric / Parameter | Value |\n"
        f"| :--- | :--- |\n"
        f"| **Target Ticker** | `{sanitized_ticker}` |\n"
        f"| **Investment Horizon** | `{timeframe}` |\n"
        f"| **Decision Generated** | `{timestamp_str}` |\n"
        f"| **Intelligence Model** | `{model_name}` |\n\n"
        f"---\n\n"
        f"{analysis_text.strip()}\n\n"
        f"---\n"
        f"*Disclaimer: This report is generated by an automated quantitative AI agent for informational and analytical purposes only. It does not constitute binding financial advice or a solicitous offer to buy or sell securities. Always conduct your own due diligence.*"
    )

    # 3. Determine unique filename with versioning
    base_filename = f"DECISION_{sanitized_ticker}_{sanitized_timeframe}_{today_str}"
    target_file = target_dir / f"{base_filename}.md"

    version = 2
    while target_file.exists():
        target_file = target_dir / f"{base_filename}_v{version}.md"
        version += 1

    target_file.write_text(report_markdown, encoding="utf-8")
    return target_file, True


# ==========================================================
# 4. Interactive Execution Runner
# ==========================================================

def run_decision_agent(ticker: str, timeframe: str):
    """Executes the investment decision workflow for the given ticker and timeframe."""
    user_query = (
        f"Evaluate ticker: {ticker.upper()} for an investment timeframe of: {timeframe}. "
        f"Perform a comprehensive quantitative analysis and determine whether to INVEST NOW or INVEST LATER."
    )

    print(f"\n🧠 Convening Investment Committee for {ticker.upper()} (Horizon: {timeframe})...\n")
    response = decision_agent.invoke({"messages": [{"role": "user", "content": user_query}]})
    analysis_text = extract_response_text(response)

    print("\n" + "=" * 60)
    print(f"📋 FINAL INVESTMENT DECISION & BLUEPRINT: {ticker.upper()}")
    print("=" * 60 + "\n")
    print(analysis_text)

    report_path, created = save_decision_report(analysis_text, ticker, timeframe)
    if report_path:
        if created:
            print(f"\n✅ Investment Decision Report saved to: {report_path}")
        else:
            print(f"\nℹ️ Identical decision report already exists at: {report_path} (Skipped duplicate creation)")
    return analysis_text, report_path


if __name__ == "__main__":
    print("💎 AI Investment Decision & Timing Agent ('Invest Now vs. Invest Later')")
    print("=" * 70)

    raw_ticker = input("Enter Stock Ticker (e.g., NVDA, AAPL, TSLA, MSFT) [default: NVDA]: ").strip()
    ticker = raw_ticker.upper() if raw_ticker else "NVDA"

    raw_timeframe = input("Enter Timeframe (e.g., 2 weeks, 1 month, 6 months, 1 year) [default: 1 month]: ").strip()
    timeframe = raw_timeframe if raw_timeframe else "1 month"

    run_decision_agent(ticker, timeframe)
