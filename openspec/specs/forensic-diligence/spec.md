# Capability: Forensic Diligence

## Purpose
Provides institutional-grade quantitative screening across key capital preservation metrics: multi-year share dilution, insider conviction, balance sheet solvency/cash runway, and margin durability.

## Requirements

### Requirement: Share Dilution and Float Expansion Audit
The system SHALL calculate historical share count changes over a multi-year lookback to identify predatory equity dilution and float expansion.

#### Scenario: Predatory dilution detected
- **WHEN** a company exhibits an annualized shares outstanding growth rate exceeding 15% accompanied by negative free cash flow
- **THEN** the system SHALL flag the stock with a High Dilution Warning and disqualify it from Long-Term Compounder classification

#### Scenario: Share count stability or net buybacks
- **WHEN** a company exhibits flat or decreasing shares outstanding over 3 years
- **THEN** the system SHALL score the dilution metric positively as shareholder-friendly

### Requirement: Insider Conviction and Transaction Screening
The system SHALL analyze open-market insider buying and selling transactions over the trailing 12 months to measure management skin-in-the-game.

#### Scenario: Heavy net insider liquidation
- **WHEN** executives and directors exhibit substantial open-market selling with zero open-market purchases over 12 months
- **THEN** the system SHALL flag insider alignment as weak and document the net share volume liquidated

#### Scenario: Cluster open-market insider buying
- **WHEN** key corporate insiders purchase shares on the open market using personal capital
- **THEN** the system SHALL highlight the transaction as strong insider conviction

### Requirement: Solvency and Cash Runway Analysis
The system SHALL evaluate balance sheet leverage, comparing cash and liquid equivalents against total debt, current ratios, and operational cash burn rates.

#### Scenario: Imminent debt maturity or severe cash burn
- **WHEN** total debt substantially exceeds cash and free cash flow is negative with less than 12 months of operating runway
- **THEN** the system SHALL classify the balance sheet as high distress risk

#### Scenario: Fortress balance sheet
- **WHEN** cash and equivalents exceed total debt or free cash flow reliably covers interest payments by more than 4x
- **THEN** the system SHALL confirm solvency strength suitable for long-term holding

### Requirement: Moat and Margin Durability Evaluation
The system SHALL track 3-year operating and gross margin trends to evaluate business model defensibility and pricing power.

#### Scenario: Deteriorating margins
- **WHEN** operating margins contract consecutively over 3 years
- **THEN** the system SHALL flag margin erosion and competitive moat degradation

#### Scenario: Expanding or resilient margins
- **WHEN** operating margins remain stable or expand above industry medians
- **THEN** the system SHALL validate the presence of pricing power and economic moat
