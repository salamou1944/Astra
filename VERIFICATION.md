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

### Untouched holdout evidence

`evidence/holdout_validation_ci.json` records a 100-bar holdout excluded from candidate selection. The selected candidate was positive on all four assets, but the equal-weight compounded result (**26.8301%**) remained below the same-period buy-and-hold benchmark (**40.5521%**) and max drawdown reached **16.7243%**. Profitability/alpha remains unverified.

## Binance empty-response regression — 2026-10-28

- Status: **TEST ADDED; BRANCH VERIFICATION PENDING**.
- Branch: `test/binance-empty-response-2026-10-28`.
- Test: `tests/test_v08.py::test_binance_empty_response_raises_value_error`.
- Scope: an empty first Binance response must raise `ValueError` matching `no bars returned for BTCUSDT`.
- Local isolated result: **1 passed (reported)**; this was not a run from a checkout of the actual GitHub branch.
- GitHub branch execution: **NOT VERIFIED**; no CI check/run was found for the test commit at the time of recording.
- Production changes: **NONE**.
- Merge: **NOT APPROVED**; do not merge until the test is executed against the actual branch and its result is reviewed.
