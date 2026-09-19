import os
import re
import hashlib
from datetime import datetime
from pathlib import Path

from forensic_agent import run_forensic_audit, save_forensic_report
from decision_agent import run_decision_agent

def compute_content_hash(text: str) -> str:
    """Computes SHA-256 hash of normalized text content to detect duplicate reports."""
    normalized = "".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def save_unified_intelligence_report(
    ticker: str,
    verdict: str,
    timeframe: str,
    forensic_text: str,
    decision_text: str | None = None,
    output_dir: str = "reports",
) -> tuple[Path | None, bool]:
    """
    Saves the full institutional dossier combining Stage 1 forensic audit
    and Stage 2 tactical execution blueprint into a structured markdown report.
    """
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    sanitized_ticker = re.sub(r"[^A-Za-z0-9_-]", "", ticker).upper()
    sanitized_verdict = re.sub(r"[^A-Za-z0-9_-]", "", verdict).upper()
    today_str = datetime.now().strftime("%Y-%m-%d")
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Construct unified markdown
    if verdict == "AVOID":
        stage2_section = (
            "## 🛑 Stage 2: Tactical Execution Bypassed\n\n"
            "> [!CAUTION]\n"
            "> **CAPITAL PRESERVATION TRIGGERED**: The company failed fundamental forensic thresholds "
            "(aggressive dilution, debt distress, or unsustainable cash burn). Calculating technical buy zones "
            "or upside targets is strictly bypassed to prevent speculative capital destruction.\n"
        )
    else:
        stage2_section = (
            f"## 🎯 Stage 2: Tactical Execution Blueprint (Diagnosed Horizon: {timeframe})\n\n"
            f"{decision_text.strip() if decision_text else 'Tactical analysis pending.'}\n"
        )

    report_markdown = (
        f"# 🏛️ Institutional Intelligence Dossier: {sanitized_ticker}\n\n"
        f"| Dimension | Value |\n"
        f"| :--- | :--- |\n"
        f"| **Target Ticker** | `{sanitized_ticker}` |\n"
        f"| **Diagnosed Horizon Verdict** | `{verdict}` |\n"
        f"| **Recommended Timeframe** | `{timeframe}` |\n"
        f"| **Dossier Generated** | `{timestamp_str}` |\n\n"
        f"---\n\n"
        f"## 🔬 Stage 1: Forensic Due Diligence & Horizon Audit\n\n"
        f"{forensic_text.strip()}\n\n"
        f"---\n\n"
        f"{stage2_section}\n\n"
        f"---\n"
        f"*Disclaimer: This institutional dossier is synthesized by an autonomous multi-agent quantitative pipeline. "
        f"It is for analytical and educational purposes only and does not constitute financial advice.*"
    )

    new_hash = compute_content_hash(report_markdown)

    for existing in target_dir.glob(f"UNIFIED_{sanitized_ticker}_*.md"):
        try:
            existing_text = existing.read_text(encoding="utf-8")
            if compute_content_hash(existing_text) == new_hash:
                return existing, False
        except Exception:
            continue

    base_filename = f"UNIFIED_{sanitized_ticker}_{sanitized_verdict}_{today_str}"
    target_file = target_dir / f"{base_filename}.md"

    version = 2
    while target_file.exists():
        target_file = target_dir / f"{base_filename}_v{version}.md"
        version += 1

    target_file.write_text(report_markdown, encoding="utf-8")
    return target_file, True


def run_pipeline(ticker: str, custom_timeframe_override: str | None = None) -> Path | None:
    """
    Orchestrates the two-stage diligence and decision pipeline:
    1. Runs Stage 1: Forensic Background & Horizon Gatekeeper.
    2. Determines natural investment horizon.
    3. If AVOID, short-circuits execution.
    4. If viable, routes diagnosed horizon into Stage 2: Tactical Execution Blueprint.
    5. Saves unified dossier to reports/.
    """
    clean_ticker = ticker.strip().upper()
    print("=" * 70)
    print(f"🚀 INITIATING INSTITUTIONAL DILIGENCE & EXECUTION PIPELINE: {clean_ticker}")
    print("=" * 70)

    # --------------------------------------------------
    # Stage 1: Forensic Background & Horizon Gatekeeper
    # --------------------------------------------------
    forensic_text, verdict, diagnosed_timeframe, forensic_path = run_forensic_audit(clean_ticker)

    print("\n" + "-" * 60)
    print(f"📋 STAGE 1 AUDIT COMPLETE: {clean_ticker}")
    print(f"   • Assigned Verdict:    {verdict}")
    print(f"   • Diagnosed Timeframe: {diagnosed_timeframe}")
    print("-" * 60)

    # --------------------------------------------------
    # Stage 2: Routing Logic & Tactical Execution
    # --------------------------------------------------
    if verdict == "AVOID":
        print("\n🛑 CRITICAL RISK DETECTED: Asset classified as AVOID / TOXIC.")
        print("   Pipeline short-circuiting tactical blueprint to enforce capital preservation.")
        unified_path, created = save_unified_intelligence_report(
            ticker=clean_ticker,
            verdict=verdict,
            timeframe=diagnosed_timeframe,
            forensic_text=forensic_text,
            decision_text=None,
        )
    else:
        effective_timeframe = custom_timeframe_override if custom_timeframe_override else diagnosed_timeframe
        print(f"\n✅ Asset Passed Forensic Gatekeeper. Forwarding to Stage 2...")
        print(f"🎯 Execution Horizon Assigned: {effective_timeframe}\n")

        decision_text, _ = run_decision_agent(
            ticker=clean_ticker,
            timeframe=effective_timeframe,
            save_report=False,
        )

        unified_path, created = save_unified_intelligence_report(
            ticker=clean_ticker,
            verdict=verdict,
            timeframe=effective_timeframe,
            forensic_text=forensic_text,
            decision_text=decision_text,
        )

    print("\n" + "=" * 70)
    if unified_path:
        if created:
            print(f"🏛️ Unified Institutional Dossier saved to: {unified_path}")
        else:
            print(f"ℹ️ Identical dossier already exists at: {unified_path} (Skipped duplicate creation)")
    print("=" * 70 + "\n")
    return unified_path


if __name__ == "__main__":
    print("🏛️ AI Institutional Diligence & Execution Pipeline")
    print("   Stage 1: Forensic Diligence & Horizon Gatekeeper")
    print("   Stage 2: Tactical Timing & Capital Execution Blueprint")
    print("=" * 70)

    raw_ticker = input("Enter Stock Ticker (e.g., NVDA, PLTR, TSLA, AAPL) [default: NVDA]: ").strip()
    ticker = raw_ticker.upper() if raw_ticker else "NVDA"

    override = input("Custom Timeframe Override (Leave blank for autonomous diagnosis) []: ").strip()
    timeframe_override = override if override else None

    run_pipeline(ticker, timeframe_override)
