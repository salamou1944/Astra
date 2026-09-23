# ASTRA Quant Lab v1.7.0

Evidence-first quantitative research system. Research-only; live-money execution is disabled.

## Current state

ASTRA v1.7.0 is the current transferred implementation. The local regression suite reached **49/49 passing**.

The system includes:
- deterministic market/backtest core
- risk controls and adversarial checks
- shadow/paper execution
- walk-forward and out-of-sample research
- research tournament and evidence ledger
- hard evidence gate for real research data
- Alpaca and Binance market-data adapters
- provenance and SHA-256 evidence handling
- CLI provider verification

## REAL_DATA barrier

The next objective is to cross the **REAL_DATA** boundary rather than inflate local test coverage.

The 2026-09-23 verification run established that the current execution environment has no usable outbound Internet egress: DNS resolution and direct HTTPS connectivity were blocked, including attempts against Alpaca, Binance, and an IP-direct HTTPS probe.

Therefore:
- REAL_DATA: **BLOCKED**
- profitability/alpha: **UNVERIFIED**
- local engineering regression: **49/49 PASS**
- live-money execution: **OFF**

The barrier is environmental, not a reason to treat synthetic or fixture data as real evidence.

See:
- VERIFICATION.md
- REAL_DATA_RUNBOOK.md
- evidence/real_data_barrier_evidence_2026-09-23.json

## Evidence rules

A dataset can qualify for research only when it is:
1. non-synthetic,
2. source-verified,
3. locally verified,
4. non-empty and at research scale (400+ rows by default),
5. accompanied by SHA-256 provenance.

The bundled six-row official Alpaca fixture is intentionally insufficient for profitability research.

## Safety

ASTRA does not claim profitability from synthetic, fixture, shadow, or paper results. Live-money execution remains disabled.