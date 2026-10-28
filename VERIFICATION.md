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

- Status: **GITHUB ACTIONS PR VALIDATION PASSED; VERIFICATION UPDATED TO LATEST RUN**.
- Branch: `test/binance-empty-response-2026-10-28`.
- PR: [#1](https://github.com/salamou1944/Astra/pull/1), still open and draft.
- HEAD commit: `55a5fea504dfcbf96fa7bc30bc2eab1be7fb94ba`.
- Test: `tests/test_v08.py::test_binance_empty_response_raises_value_error`.
- Scope: an empty first Binance response must raise `ValueError` matching `no bars returned for BTCUSDT`.
- Latest GitHub Actions run: [ASTRA CI #209](https://github.com/salamou1944/Astra/actions/runs/40629039202), run ID `40629039202`; completed successfully. Jobs `test`, `execution-boundary`, and `candidate-real-data` all passed.
- Test job output: `pytest -q` reported **88 passed, 4 subtests passed in 0.94s**.
- Execution boundary: Actions checked out PR merge ref `f8e675ee15c59cc0149d3be3abdad1d4b2600df2`, combining the current PR HEAD `55a5fea504dfcbf96fa7bc30bc2eab1be7fb94ba` with base commit `11a42643279e7323097cec4b845bf6d0cc179144`. This confirms successful CI on the current PR merge ref; it is **not** evidence of a separate direct branch-head checkout run.
- Local isolated result: **1 passed (reported)**; this was not a run from a checkout of the actual GitHub branch.
- Production changes: **NONE** in the PR diff; changed paths are `VERIFICATION.md` and `tests/test_v08.py`.
- Merge: **NOT APPROVED**; PR #1 remains open as a draft. Do not merge unless the user explicitly approves.
