# ASTRA Quant Lab v1.7.0

Evidence-first quantitative research system. Research-only; live-money execution is disabled.

## Current state

ASTRA now has a reproducibly verified real-data boundary through a GitHub-hosted execution runner.

- Local regression: **49/49 PASS**.
- REAL_DATA: **PROVEN**.
- Source: Kraken public REST API.
- Dataset: BTC/USD daily OHLCV, **721 rows**, 2024-10-03 through 2026-09-23.
- Dataset SHA-256: `fb3598099d2beef502a8a34dedf21cebd64236917780fd6b55821c9082993060`.
- Research/OOS: executed on the verified real dataset.
- Robustness: adversarial and cost-stress executed.
- Risk/shadow: executed with live-money execution OFF.

## Research result

The real-data run did **not** pass ASTRA's research gate:

- Baseline return: **-7.4803%**
- Baseline max drawdown: **39.159%**
- Walk-forward: **4 folds**
- Aggregate walk-forward return: **-46.158%**
- Positive-fold ratio: **25%**
- Adversarial survival ratio: **0.0**
- Research gate: **FAIL**

Therefore profitability/alpha remains **UNVERIFIED**. The real dataset is genuine evidence; the strategy result is negative evidence, not a success claim.

## Safety

Live-money execution is **OFF**. The real-data risk/shadow run submitted **0 broker orders** and triggered the configured max-drawdown halt.

See `VERIFICATION.md`, `REAL_DATA_RUNBOOK.md`, and the persisted evidence under `evidence/`.
