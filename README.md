# ASTRA Quant Lab v1.7.0

Evidence-first quantitative research system. Research-only; live-money execution is disabled.

## Current state

ASTRA now has a reproducibly verified real-data boundary through a GitHub-hosted execution runner.

- Local regression: **49/49 PASS**.
- REAL_DATA: **PROVEN**.
- Source: Kraken public REST API.
- Dataset: BTC/USD daily OHLCV, **721 rows**, 2024-10-03 through 2026-09-23.
- Multi-asset REAL_DATA: **PROVEN** for BTC/USD, ETH/USD, SOL/USD, LTC/USD; **721 rows each**.
- Dataset SHA-256: `fb3598099d2beef502a8a34dedf21cebd64236917780fd6b55821c9082993060`.
- Research/OOS: executed on the verified real dataset.
- Candidate tournament: **123 candidates**; single-asset gate **FAIL**.
- Cross-asset research: **4 assets × 4 chronological folds**; gate **FAIL**.
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

Therefore profitability/alpha remains **UNVERIFIED**. The real datasets are genuine evidence; the strategy results are negative evidence, not a success claim.

### Cross-asset result

The same candidate families were evaluated without per-asset parameter selection across four verified Kraken markets. The equal-weight fold aggregate was **-6.8715%**, the positive asset-fold ratio was **25%**, and the worst asset-level drawdown was **37.3515%**. The gate failed. This is a stronger rejection signal than the BTC-only tournament and prevents treating a single favorable asset/regime as sufficient evidence.

## Safety

Live-money execution is **OFF**. The real-data risk/shadow run submitted **0 broker orders** and triggered the configured max-drawdown halt.

See `VERIFICATION.md`, `REAL_DATA_RUNBOOK.md`, and the persisted evidence under `evidence/`.


## Untouched holdout validation

A final 100-bar period (indices 621-720) was reserved and not used for candidate selection. The repeatedly selected `long_momentum(window=30, threshold=0)` was evaluated on that holdout across BTC/USD, ETH/USD, SOL/USD, and LTC/USD. The equal-weight compounded strategy return was **26.8301%**, versus **40.5521%** for buy-and-hold over the same asset holdout; maximum asset drawdown was **16.7243%**. This is validation evidence, not a profitability claim.
