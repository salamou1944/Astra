# ASTRA Verification

## v1.7.0

- Local regression: **49/49 PASS**.
- REAL_DATA: **PROVEN** through a GitHub-hosted runner.
- Source verification: **Kraken public REST API**.
- Dataset: **721 non-synthetic BTC/USD daily rows**.
- Multi-asset REAL_DATA: **4 verified markets × 721 daily rows** (BTC/USD, ETH/USD, SOL/USD, LTC/USD).
- Dataset SHA-256: `fb3598099d2beef502a8a34dedf21cebd64236917780fd6b55821c9082993060`.
- Provenance persisted: **YES**.
- Local OHLCV/timestamp validation: **PASS**.
- Walk-forward/OOS: **4 folds, research gate FAIL**.
- Robustness: adversarial survival **0.0**; cost stress executed.
- Risk/shadow: **PROVEN**, with max-drawdown halt and **0 broker orders**.
- Candidate tournament: **123 candidates**, BTC-only gate **FAIL**.
- Cross-asset research: **4 folds**, equal-weight aggregate **-6.8715%**, positive asset-fold ratio **25%**, max asset drawdown **37.3515%**, gate **FAIL**.
- Profitability/alpha: **UNVERIFIED**.
- Live execution: **OFF**.

### Real-data acquisition evidence

`evidence/real_data_ci.json` records source access, successful retrieval, 721 rows, provenance, SHA-256, non-synthetic status, and local validation.

### Research evidence

`evidence/real_data_research_ci.json` records the actual real-data research result. It is negative/failed research evidence, not a profitability claim.

### Risk/shadow evidence

`evidence/real_data_risk_shadow_ci.json` records the risk guardian halt and zero broker orders.

### Previous barrier evidence

The earlier 2026-09-23 local barrier remains valid as a local-environment finding: the original sandbox lacked outbound network access. The GitHub-hosted runner supplied a distinct authorized execution boundary. Binance returned HTTP 451 there, while Kraken supplied the verified dataset.

### Cross-asset evidence

`evidence/multi_asset_real_data_ci.json` records successful Kraken retrieval and validation for four non-synthetic markets. `evidence/cross_asset_research_ci.json` records the cross-asset walk-forward result and its failed gate. No candidate is promoted to profitability or live execution on this evidence.
