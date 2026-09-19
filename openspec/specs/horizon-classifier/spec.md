# Capability: Horizon Classifier

## Purpose
Classifies analyzed tickers into definitive investment timeframes (`LONG-TERM COMPOUNDER`, `SHORT-TERM TACTICAL SWING`, `ALL-WEATHER`, `AVOID / TOXIC`) and automates routing to tactical execution or short-circuiting on toxic assets.

## Requirements

### Requirement: Deterministic Horizon Classification
The system SHALL classify any analyzed ticker into exactly one of four definitive investment horizons based on the forensic audit results: `LONG-TERM COMPOUNDER`, `SHORT-TERM TACTICAL SWING`, `ALL-WEATHER`, or `AVOID / TOXIC`.

#### Scenario: High quality business classified as long-term compounder
- **WHEN** an asset demonstrates low dilution, positive free cash flow, stable or expanding margins, and manageable debt
- **THEN** the system SHALL assign the verdict `LONG-TERM COMPOUNDER` with a recommended horizon of 1 to 3+ years

#### Scenario: Cyclical or high-beta asset classified as short-term swing
- **WHEN** an asset has high volatility/beta or cyclical margins, but healthy liquidity and clear near-term catalysts
- **THEN** the system SHALL assign the verdict `SHORT-TERM TACTICAL SWING` with a recommended horizon of 30 to 60 days

#### Scenario: Broken balance sheet or hyper-dilution triggers avoid verdict
- **WHEN** an asset exhibits predatory dilution, severe debt distress, or persistent cash burn with no viable runway
- **THEN** the system SHALL assign the verdict `AVOID / TOXIC`

### Requirement: Automated Pipeline Routing and Short-Circuiting
The system SHALL orchestrate the handoff between Stage 1 forensic classification and Stage 2 tactical execution.

#### Scenario: Short-circuit execution on uninvestable assets
- **WHEN** the horizon verdict is `AVOID / TOXIC`
- **THEN** the system SHALL immediately halt execution, bypass the Stage 2 entry blueprint, and output a Forensic Risk Audit report

#### Scenario: Automated handoff for viable assets
- **WHEN** the horizon verdict is `LONG-TERM COMPOUNDER`, `SHORT-TERM TACTICAL SWING`, or `ALL-WEATHER`
- **THEN** the system SHALL pass the ticker and the diagnosed timeframe directly to the Stage 2 execution agent to compute entry zones, stops, and risk-to-reward ratios

### Requirement: Structured Dossier Export and Content Deduplication
The system SHALL export the combined forensic audit and execution analysis into an institutional Markdown report with SHA-256 hash deduplication.

#### Scenario: Saving a new intelligence report
- **WHEN** a pipeline run completes
- **THEN** the system SHALL write a formatted report to the `reports/` directory with a timestamped filename and versioning if modified
