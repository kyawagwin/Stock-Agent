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
# 1. Custom Quantitative Tools for Forensic Due Diligence
# ==========================================================

@tool
def audit_share_dilution_and_float(ticker: str) -> str:
    """
    Audits 3-year split-adjusted shares outstanding CAGR, float expansion,
    and determines whether the company is diluting shareholders or buying back shares.
    """
    try:
        stock = yf.Ticker(ticker)
        start_date = (pd.Timestamp.now(tz="UTC") - pd.DateOffset(years=3))
        sh = stock.get_shares_full(start=start_date.strftime("%Y-%m-%d"))

        info = stock.info
        shares_out = info.get("sharesOutstanding")
        float_shares = info.get("floatShares")
        rev_growth = info.get("revenueGrowth")

        if sh is not None and len(sh) >= 2:
            splits = stock.splits
            adj_sh = sh.copy().astype(float)

            # Ensure UTC timezone alignment for accurate split adjustment
            if not splits.empty:
                if splits.index.tz is None:
                    splits.index = splits.index.tz_localize("UTC")
                else:
                    splits.index = splits.index.tz_convert("UTC")

                if adj_sh.index.tz is None:
                    adj_sh.index = adj_sh.index.tz_localize("UTC")
                else:
                    adj_sh.index = adj_sh.index.tz_convert("UTC")

                for d in adj_sh.index:
                    subsequent_splits = splits[(splits.index > d) & (splits.index <= adj_sh.index[-1])]
                    factor = subsequent_splits.prod() if not subsequent_splits.empty else 1.0
                    adj_sh.loc[d] = adj_sh.loc[d] * factor

            initial_shares = adj_sh.iloc[0]
            latest_shares = adj_sh.iloc[-1]
            span_years = max((adj_sh.index[-1] - adj_sh.index[0]).days / 365.25, 0.5)
            cagr = ((latest_shares / initial_shares) ** (1 / span_years) - 1) * 100 if span_years > 0 else 0
            total_change = ((latest_shares - initial_shares) / initial_shares) * 100

            if cagr < -0.5:
                dilution_status = "SHAREHOLDER-FRIENDLY (Active Share Repurchase / Net Buybacks)"
            elif cagr <= 2.5:
                dilution_status = "EXCELLENT CAPITAL HYGIENE (Minimal / Negligible Share Expansion)"
            elif cagr <= 7.0:
                if rev_growth and rev_growth > 0.20:
                    dilution_status = "ACCEPTABLE TECH GROWTH DILUTION (Justified by >20% YoY Revenue Growth)"
                else:
                    dilution_status = "MODERATE DILUTION (Warning: Share count expanding faster than revenue)"
            else:
                dilution_status = "CRITICAL RED FLAG: AGGRESSIVE SHARE DILUTION (>7% Annualized CAGR)"

            float_str = f"{(float_shares / shares_out)*100:.1f}% float" if (float_shares and shares_out) else "N/A"
            rev_str = f"{rev_growth*100:+.1f}%" if rev_growth else "N/A"

            return (
                f"Share Dilution & Capital Hygiene Audit for {ticker.upper()}:\n"
                f"- Dilution Verdict: {dilution_status}\n"
                f"- Initial Split-Adjusted Shares (~{span_years:.1f}y ago): {initial_shares:,.0f}\n"
                f"- Current Shares Outstanding: {latest_shares:,.0f}\n"
                f"- 3-Year Total Share Count Change: {total_change:+.2f}%\n"
                f"- Annualized Dilution CAGR: {cagr:+.2f}% per year\n"
                f"- Float Ratio: {float_str}\n"
                f"- YoY Revenue Growth Reference: {rev_str}"
            )
        elif shares_out:
            float_str = f"{float_shares:,.0f}" if float_shares else "N/A"
            return (
                f"Share Dilution Audit for {ticker.upper()}:\n"
                f"- Historical share series unavailable in yfinance. Current shares: {shares_out:,.0f}.\n"
                f"- Float Shares: {float_str}.\n"
                f"- Status: Insufficient historical granular series; baseline neutral."
            )
        else:
            return f"Error: No share count data retrieved for {ticker}."
    except Exception as e:
        return f"Error auditing share dilution for {ticker}: {str(e)}"


@tool
def screen_insider_transactions(ticker: str) -> str:
    """
    Screens open-market insider buying vs selling over trailing 12 months,
    measuring management conviction, insider alignment, and dumping activity.
    """
    try:
        stock = yf.Ticker(ticker)
        it = stock.insider_transactions
        if it is None or it.empty:
            return (
                f"Insider Transaction Screening for {ticker.upper()}:\n"
                f"- No SEC Form 4 insider transactions recorded in yfinance database for this ticker.\n"
                f"- Insider Sentiment: NEUTRAL / INSUFFICIENT SEC DATA"
            )

        purchases = []
        sales = []
        grants = []

        total_bought_shares = 0
        total_bought_val = 0
        total_sold_shares = 0
        total_sold_val = 0

        for _, row in it.iterrows():
            text = str(row.get("Text", "")).lower()
            shares = row.get("Shares", 0)
            val = row.get("Value", 0)
            insider = row.get("Insider", "Unknown")
            pos = row.get("Position", "Insider")
            s_date = str(row.get("Start Date", ""))[:10]

            if not isinstance(shares, (int, float)) or np.isnan(shares):
                shares = 0
            if not isinstance(val, (int, float)) or np.isnan(val):
                val = 0

            if "purchase" in text or "buy" in text:
                purchases.append((s_date, insider, pos, shares, val))
                total_bought_shares += shares
                total_bought_val += val
            elif "sale" in text or "sold" in text:
                sales.append((s_date, insider, pos, shares, val))
                total_sold_shares += shares
                total_sold_val += val
            elif "grant" in text or "award" in text:
                grants.append((s_date, insider, pos, shares))

        if total_bought_val > 500_000 and total_bought_val > (total_sold_val * 0.5):
            insider_sentiment = "BULLISH INSIDER CONVICTION (Significant open-market cash buying)"
        elif total_sold_val > 50_000_000 and total_bought_val == 0:
            insider_sentiment = "BEARISH HEAVY DUMPING (High executive selling with ZERO open-market buying)"
        elif total_bought_val > 0:
            insider_sentiment = "MIXED / MODERATE BUYING (Some open-market accumulation detected)"
        else:
            insider_sentiment = "ROUTINE SELLING / EXERCISES (Standard 10b5-1 executive diversification)"

        noteworthy = []
        if purchases:
            for p in purchases[:3]:
                noteworthy.append(f"  • BUY: {p[1]} ({p[2]}) purchased {p[3]:,.0f} shares (${p[4]:,.0f}) on {p[0]}")
        if sales:
            for s in sales[:3]:
                noteworthy.append(f"  • SELL: {s[1]} ({s[2]}) sold {s[3]:,.0f} shares (${s[4]:,.0f}) on {s[0]}")

        return (
            f"Insider Conviction & Alignment for {ticker.upper()}:\n"
            f"- Net Insider Sentiment: {insider_sentiment}\n"
            f"- Open-Market Purchases (12m): {len(purchases)} transactions | Total: {total_bought_shares:,.0f} shares (${total_bought_val:,.0f})\n"
            f"- Open-Market Sales (12m): {len(sales)} transactions | Total: {total_sold_shares:,.0f} shares (${total_sold_val:,.0f})\n"
            f"- Stock Awards / Grants Logged: {len(grants)} events\n"
            f"- Noteworthy Recent Transactions:\n" + ("\n".join(noteworthy) if noteworthy else "  • No major recent open-market filings")
        )
    except Exception as e:
        return f"Error screening insider transactions for {ticker}: {str(e)}"


@tool
def analyze_solvency_and_cash_runway(ticker: str) -> str:
    """
    Evaluates balance sheet leverage, comparing cash and equivalents vs total debt,
    current ratio, quick ratio, and operational cash burn/runway.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        def fmt_curr(val):
            return f"${val:,.0f}" if isinstance(val, (int, float)) else "N/A"

        def fmt_num(val):
            return f"{val:.2f}" if isinstance(val, (int, float)) else "N/A"

        total_cash = info.get("totalCash")
        total_debt = info.get("totalDebt")
        current_ratio = info.get("currentRatio")
        quick_ratio = info.get("quickRatio")
        fcf = info.get("freeCashflow")
        ebitda = info.get("ebitda")

        net_cash = (total_cash - total_debt) if (isinstance(total_cash, (int, float)) and isinstance(total_debt, (int, float))) else None

        # Cash Runway calculation if cash burning
        runway_str = "Self-funding (Positive Free Cash Flow)"
        solvency_status = "HEALTHY"

        if isinstance(fcf, (int, float)) and fcf < 0:
            if isinstance(total_cash, (int, float)) and total_cash > 0:
                years_runway = total_cash / abs(fcf)
                months_runway = years_runway * 12
                runway_str = f"⚠️ CASH BURN: ~{months_runway:.1f} months of cash runway remaining"
                if months_runway < 12:
                    solvency_status = "CRITICAL DISTRESS: Imminent financing / dilution risk (< 12 months runway)"
                else:
                    solvency_status = "ELEVATED BURN: Cash burning but >12 months runway available"
            else:
                runway_str = "CRITICAL: Negative FCF with minimal / no cash reported"
                solvency_status = "INSOLVENCY RISK"
        elif isinstance(net_cash, (int, float)) and net_cash > 0:
            solvency_status = "FORTRESS BALANCE SHEET: Net Cash Positive (Cash exceeds Total Debt)"
        elif isinstance(total_debt, (int, float)) and isinstance(fcf, (int, float)) and fcf > 0:
            debt_to_fcf = total_debt / fcf
            if debt_to_fcf <= 3.0:
                solvency_status = f"MANAGEABLE LEVERAGE (Total Debt is {debt_to_fcf:.1f}x annual FCF)"
            else:
                solvency_status = f"HEAVY LEVERAGE (Total Debt is {debt_to_fcf:.1f}x annual FCF - vulnerable to macro shocks)"

        return (
            f"Solvency, Liquidity & Balance Sheet Audit for {ticker.upper()}:\n"
            f"- Solvency Condition: {solvency_status}\n"
            f"- Total Cash & Equivalents: {fmt_curr(total_cash)}\n"
            f"- Total Outstanding Debt: {fmt_curr(total_debt)}\n"
            f"- Net Cash / (Net Debt): {fmt_curr(net_cash) if net_cash is not None else 'N/A'}\n"
            f"- Current Ratio: {fmt_num(current_ratio)} | Quick Ratio: {fmt_num(quick_ratio)}\n"
            f"- Annual Free Cash Flow (FCF): {fmt_curr(fcf)}\n"
            f"- EBITDA: {fmt_curr(ebitda)}\n"
            f"- Operational Runway Assessment: {runway_str}"
        )
    except Exception as e:
        return f"Error analyzing solvency for {ticker}: {str(e)}"


@tool
def track_margin_durability_and_moat(ticker: str) -> str:
    """
    Evaluates historical operating margins and gross margins over up to 4 years
    to determine pricing power, economic moat strength, and cyclical vulnerability.
    """
    try:
        stock = yf.Ticker(ticker)
        f = stock.financials

        if f is not None and not f.empty and "Total Revenue" in f.index and "Operating Income" in f.index:
            rev_series = f.loc["Total Revenue"].dropna()
            op_series = f.loc["Operating Income"].dropna()
            gross_series = f.loc["Gross Profit"].dropna() if "Gross Profit" in f.index else None

            common_dates = sorted(list(set(rev_series.index).intersection(op_series.index)))
            margin_records = []
            for dt in common_dates:
                r = rev_series.loc[dt]
                op = op_series.loc[dt]
                if r != 0:
                    op_margin = (op / r) * 100
                    gp_margin = (gross_series.loc[dt] / r) * 100 if gross_series is not None and dt in gross_series.index else None
                    dt_str = dt.strftime("%Y") if hasattr(dt, "strftime") else str(dt)[:4]
                    margin_records.append((dt_str, op_margin, gp_margin))

            if len(margin_records) >= 2:
                earliest = margin_records[0]
                latest = margin_records[-1]
                op_delta = latest[1] - earliest[1]

                if latest[1] > 20 and op_delta >= -2.0:
                    moat_profile = "ELITE SECULAR MOAT (Consistently high operating margins >20%, high pricing power)"
                elif latest[1] > 10 and op_delta > 5.0:
                    moat_profile = "EXPANDING OPERATING LEVERAGE (Strong margin expansion trajectory)"
                elif latest[1] > 0 and (max([m[1] for m in margin_records]) - min([m[1] for m in margin_records]) > 15):
                    moat_profile = "CYCLICAL MARGIN STRUCTURE (Wide swings across business cycles; poor for buy-and-hold)"
                elif latest[1] <= 0:
                    moat_profile = "UNPROFITABLE / CHRONIC MARGIN DEFICIT (Operating at a loss)"
                else:
                    moat_profile = "STABLE / MODERATE MOAT (Single-digit to low-double-digit margins)"

                history_str = " | ".join([f"{m[0]}: Op={m[1]:.1f}%" + (f", Gross={m[2]:.1f}%" if m[2] else "") for m in margin_records])

                roe_val = stock.info.get("returnOnEquity")
                roe_str = f"{roe_val * 100:.2f}%" if isinstance(roe_val, (int, float)) else "N/A"

                return (
                    f"Margin Durability & Moat Profile for {ticker.upper()}:\n"
                    f"- Moat Classification: {moat_profile}\n"
                    f"- Latest Operating Margin: {latest[1]:.2f}%\n"
                    f"- Multi-Year Margin Progression: {history_str}\n"
                    f"- Multi-Year Margin Delta: {op_delta:+.2f} percentage points\n"
                    f"- ROE: {roe_str}"
                )

        info = stock.info
        op_margin = info.get("operatingMargins")
        gross_margin = info.get("grossMargins")
        op_str = f"{op_margin * 100:.2f}%" if isinstance(op_margin, (int, float)) else "N/A"
        gross_str = f"{gross_margin * 100:.2f}%" if isinstance(gross_margin, (int, float)) else "N/A"
        return (
            f"Margin Profile for {ticker.upper()} (TTM Fallback):\n"
            f"- Operating Margin: {op_str}\n"
            f"- Gross Margin: {gross_str}\n"
            f"- Multi-year financials not fully populated; baseline assessment relied on TTM."
        )
    except Exception as e:
        return f"Error tracking margin durability for {ticker}: {str(e)}"


@tool
def evaluate_volatility_and_cyclicality(ticker: str) -> str:
    """
    Evaluates market beta, historical volatility, and maximum 52-week drawdown
    to distinguish steady compounders from high-beta tactical swing vehicles.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")

        beta = info.get("beta", 1.0)
        sector = info.get("sector", "N/A")
        industry = info.get("industry", "N/A")

        if not hist.empty and len(hist) >= 30:
            returns = hist["Close"].pct_change().dropna()
            annualized_vol = returns.std() * np.sqrt(252) * 100
            high_52 = hist["High"].max()
            current_p = hist["Close"].iloc[-1]
            drawdown_52 = ((current_p - high_52) / high_52) * 100 if high_52 else 0

            if annualized_vol > 50 or (isinstance(beta, (int, float)) and beta > 1.8):
                vol_class = "HIGH-BETA / TACTICAL SWING PROFILE (High volatility, requires tight risk management)"
            elif annualized_vol < 30 and (isinstance(beta, (int, float)) and 0.6 <= beta <= 1.3):
                vol_class = "STEADY COMPOUNDER PROFILE (Low-to-moderate volatility, defensive secular stability)"
            else:
                vol_class = "MODERATE VOLATILITY PROFILE (Balanced beta)"

            return (
                f"Volatility & Cyclicality Profile for {ticker.upper()}:\n"
                f"- Classification: {vol_class}\n"
                f"- Sector / Industry: {sector} ({industry})\n"
                f"- Market Beta: {f'{beta:.2f}' if isinstance(beta, (int, float)) else 'N/A'}\n"
                f"- Annualized Historical Volatility: {annualized_vol:.2f}%\n"
                f"- Current Price vs 52-Week High: {drawdown_52:+.2f}% drawdown\n"
                f"- 52-Week High / Low: ${high_52:.2f} / ${hist['Low'].min():.2f}"
            )
        return f"Volatility Profile for {ticker.upper()}: Beta: {beta}, Sector: {sector}"
    except Exception as e:
        return f"Error evaluating volatility for {ticker}: {str(e)}"


# ==========================================================
# 2. Agent Configuration & Horizon Decision Rubric
# ==========================================================

forensic_tools = [
    audit_share_dilution_and_float,
    screen_insider_transactions,
    analyze_solvency_and_cash_runway,
    track_margin_durability_and_moat,
    evaluate_volatility_and_cyclicality,
]

SYSTEM_PROMPT = (
    "Role: You are a Forensic Investment Auditor and Chief Risk Officer (CRO) of an institutional investment firm.\n\n"
    "Primary Objective: You are tasked with performing an unsparing forensic background check on a stock's capital health "
    "and answering the core question: 'WHAT IS THE APPROPRIATE INVESTMENT TIMEFRAME FOR THIS ASSET?'\n\n"
    "Definitive Classification Categories (You MUST assign exactly ONE of these four):\n"
    "1. 🟢 LONG-TERM COMPOUNDER (Horizon: 1 to 3+ Years)\n"
    "   - Criteria: Low dilution (<2.5% CAGR or net buybacks), fortress or healthy balance sheet (positive FCF, net cash or debt <3x FCF), "
    "high and resilient operating margins (>15-20%), and strong business moat. Volatility can be endured because the fundamental engine compounds wealth.\n"
    "2. 🟡 SHORT-TERM TACTICAL SWING (Horizon: 30 to 60 Days)\n"
    "   - Criteria: Viable solvency and liquidity, but exhibits high beta (>1.5), cyclical margins, or high valuation that makes a 5-year hold dangerous. "
    "Best traded tactically on catalysts, momentum, and technical inflection points.\n"
    "3. 🟣 ALL-WEATHER / CORE ASSET (Horizon: Dual Long-Term & Short-Term)\n"
    "   - Criteria: World-class secular moat meeting all Long-Term criteria, but also displaying an immediate high-volatility technical or catalyst opportunity.\n"
    "4. 🔴 AVOID / TOXIC (Horizon: ZERO / DO NOT ALLOCATE)\n"
    "   - Criteria: Predatory share dilution (>10-15% CAGR), dangerous cash burn with <12 months runway, catastrophic debt cliff, or collapsing unit economics. "
    "Uninvestable for prudent capital preservation. Immediate short-circuit trigger!\n\n"
    "Guidelines:\n"
    "- Never be lenient on capital destruction. If a company is chronically diluting shareholders to pay executive bonuses or subsidize negative cash flow, flag it immediately.\n"
    "- High revenue growth (>25%) can forgive moderate dilution (3-6%), but nothing forgives a sub-12-month runway with zero cash.\n"
    "- Ground every conclusion in exact numbers retrieved from the tools (CAGR, shares, debt, cash, margins).\n\n"
    "Required Output Format in Markdown:\n"
    "### 1. 🧭 Executive Horizon Classification\n"
    "- **Assigned Verdict:** [🟢 LONG-TERM COMPOUNDER | 🟡 SHORT-TERM TACTICAL SWING | 🟣 ALL-WEATHER / CORE | 🔴 AVOID / TOXIC]\n"
    "- **Recommended Investment Timeframe:** [e.g. 1 to 3 Years | 30 to 60 Days | Immediate Avoidance]\n"
    "- **Pipeline Action:** [PROCEED TO TACTICAL EXECUTION | SHORT-CIRCUIT: CAPITAL PRESERVATION HALT]\n"
    "- **Executive Synthesis:** [2-3 sentences summarizing the forensic findings and horizon justification]\n\n"
    "### 2. 🧬 Forensic Health Scorecard\n"
    "| Forensic Vector | Metric / Value | Risk Assessment |\n"
    "| :--- | :--- | :--- |\n"
    "| **Share Dilution (3y CAGR)** | [Value] | [Low / Moderate / Red Flag] |\n"
    "| **Insider Conviction (12m)** | [Value] | [Bullish / Routine / Dumping] |\n"
    "| **Solvency & Cash Runway** | [Value] | [Fortress / Manageable / Distress] |\n"
    "| **Moat & Margin Persistence** | [Value] | [Expanding / Stable / Cyclical / Loss] |\n"
    "| **Beta & Volatility Profile** | [Value] | [Steady Compounder / High-Beta Swing] |\n\n"
    "### 3. 🔍 Detailed Forensic Audit\n"
    "- **Dilution & Share Count Drift:** [Analysis]\n"
    "- **Insider Conviction & Alignment:** [Analysis]\n"
    "- **Balance Sheet Strength & Cash Runway:** [Analysis]\n"
    "- **Pricing Power & Moat Durability:** [Analysis]\n\n"
    "### 4. ⚠️ Critical Red Flags & Structural Risks\n"
    "[Top 2-3 severe risks that could impair capital or break the business model]"
)

MODEL_NAME = "gemini-3.6-flash"
llm = ChatGoogleGenerativeAI(model=MODEL_NAME)

forensic_agent = create_agent(
    model=llm,
    tools=forensic_tools,
    system_prompt=SYSTEM_PROMPT,
)


# ==========================================================
# 3. Report Generation & Content Deduplication
# ==========================================================

def extract_response_text(response: dict) -> str:
    """Extracts text content from agent response dict."""
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


def save_forensic_report(
    analysis_text: str,
    ticker: str,
    output_dir: str = "reports",
    model_name: str = MODEL_NAME,
) -> tuple[Path | None, bool]:
    """
    Saves the forensic audit into a structured Markdown report in reports/
    with SHA-256 deduplication and auto-versioning.
    """
    if not analysis_text or not analysis_text.strip():
        return None, False

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    sanitized_ticker = re.sub(r"[^A-Za-z0-9_-]", "", ticker).upper()
    today_str = datetime.now().strftime("%Y-%m-%d")
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_hash = compute_content_hash(analysis_text)

    for existing in target_dir.glob(f"FORENSIC_{sanitized_ticker}_*.md"):
        try:
            existing_text = existing.read_text(encoding="utf-8")
            if compute_content_hash(existing_text) == new_hash or analysis_text.strip() in existing_text:
                return existing, False
        except Exception:
            continue

    report_markdown = (
        f"# 🔍 Forensic Due Diligence & Horizon Audit: {sanitized_ticker}\n\n"
        f"| Metric / Parameter | Value |\n"
        f"| :--- | :--- |\n"
        f"| **Target Ticker** | `{sanitized_ticker}` |\n"
        f"| **Audit Generated** | `{timestamp_str}` |\n"
        f"| **Intelligence Model** | `{model_name}` |\n\n"
        f"---\n\n"
        f"{analysis_text.strip()}\n\n"
        f"---\n"
        f"*Disclaimer: This forensic report is generated by an automated quantitative AI agent for informational purposes only. It does not constitute investment advice.*"
    )

    base_filename = f"FORENSIC_{sanitized_ticker}_{today_str}"
    target_file = target_dir / f"{base_filename}.md"

    version = 2
    while target_file.exists():
        target_file = target_dir / f"{base_filename}_v{version}.md"
        version += 1

    target_file.write_text(report_markdown, encoding="utf-8")
    return target_file, True


def parse_verdict_from_analysis(analysis_text: str) -> tuple[str, str]:
    """
    Parses the classified verdict and recommended timeframe from the agent's output.
    Returns (verdict_category, timeframe_string)
    verdict_category in: 'LONG_TERM', 'SHORT_TERM', 'ALL_WEATHER', 'AVOID'
    """
    text_upper = analysis_text.upper()
    if "AVOID" in text_upper or "TOXIC" in text_upper or "SHORT-CIRCUIT" in text_upper:
        return "AVOID", "0 days (Avoid)"
    elif "ALL-WEATHER" in text_upper:
        return "ALL_WEATHER", "1 year"
    elif "SHORT-TERM" in text_upper or "TACTICAL SWING" in text_upper:
        return "SHORT_TERM", "30 days"
    elif "LONG-TERM" in text_upper or "COMPOUNDER" in text_upper:
        return "LONG_TERM", "1 year"
    return "SHORT_TERM", "30 days"


# ==========================================================
# 4. Programmatic Audit Runner
# ==========================================================

def run_forensic_audit(ticker: str) -> tuple[str, str, str, Path | None]:
    """
    Executes the forensic diligence audit for the given ticker.
    Returns:
        tuple: (analysis_text, verdict_category, recommended_timeframe, report_path)
    """
    query = (
        f"Conduct a comprehensive quantitative forensic due diligence check on ticker: {ticker.upper()}. "
        f"Analyze 3-year share dilution, insider conviction, solvency and cash runway, margin durability, and volatility. "
        f"Assign a definitive Horizon Verdict: LONG-TERM COMPOUNDER, SHORT-TERM TACTICAL SWING, ALL-WEATHER, or AVOID / TOXIC."
    )

    print(f"\n🔍 Running Forensic Due Diligence & Horizon Audit for {ticker.upper()}...\n")
    response = forensic_agent.invoke({"messages": [{"role": "user", "content": query}]})
    analysis_text = extract_response_text(response)

    verdict_category, recommended_timeframe = parse_verdict_from_analysis(analysis_text)
    report_path, created = save_forensic_report(analysis_text, ticker)

    return analysis_text, verdict_category, recommended_timeframe, report_path


if __name__ == "__main__":
    print("🔬 Institutional Forensic Due Diligence & Horizon Classifier Agent")
    print("=" * 70)

    raw_ticker = input("Enter Stock Ticker (e.g., NVDA, PLTR, TSLA, GME) [default: NVDA]: ").strip()
    ticker = raw_ticker.upper() if raw_ticker else "NVDA"

    analysis_text, verdict, timeframe, report_path = run_forensic_audit(ticker)
    print("\n" + "=" * 60)
    print(f"📋 FORENSIC AUDIT DOSSIER: {ticker}")
    print(f"Assigned Verdict: {verdict} (Recommended Horizon: {timeframe})")
    print("=" * 60 + "\n")
    print(analysis_text)

    if report_path:
        print(f"\n✅ Forensic Report saved to: {report_path}")
