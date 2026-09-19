## 1. Forensic Analysis Tools

- [x] 1.1 Implement share dilution tool analyzing 3-year shares outstanding CAGR and float expansion
- [x] 1.2 Implement insider transaction screening tool analyzing net buying vs dumping over trailing 12 months
- [x] 1.3 Implement balance sheet solvency and cash runway tool (Cash vs Debt, Current Ratio, FCF burn)
- [x] 1.4 Implement 3-year operating and gross margin persistence tracking tool with graceful degradation for missing data

## 2. Horizon Classifier Agent

- [x] 2.1 Define deterministic horizon classification rubric (`LONG-TERM COMPOUNDER`, `SHORT-TERM TACTICAL SWING`, `ALL-WEATHER`, `AVOID / TOXIC`)
- [x] 2.2 Construct `forensic_agent.py` using `ChatGoogleGenerativeAI` and the custom quantitative forensic tools
- [x] 2.3 Implement Markdown forensic report generation with SHA-256 content hashing and versioning

## 3. Two-Stage Orchestration Pipeline

- [x] 3.1 Export programmatic `run_decision_agent` interface from `decision_agent.py` for seamless import
- [x] 3.2 Build `pipeline.py` orchestrator to run Stage 1 (Forensic Audit) with user input
- [x] 3.3 Implement routing logic to short-circuit on `AVOID / TOXIC` or forward diagnosed horizon to Stage 2 (`decision_agent.py`)
- [x] 3.4 Generate unified institutional intelligence reports combining forensic audit and tactical execution blueprint

## 4. Verification and Documentation

- [x] 4.1 Verify pipeline execution against benchmark tickers (e.g. megacap compounder vs high-beta swing)
- [x] 4.2 Validate short-circuit behavior and report deduplication in `reports/`
- [x] 4.3 Update `README.md` with quickstart instructions for `pipeline.py` and the two-stage diligence workflow
