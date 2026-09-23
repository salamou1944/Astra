# ASTRA Real-Data Runbook

1. Acquire real historical market data from a permitted external source.
2. Persist raw data, source URL, retrieval status and SHA-256.
3. Validate CSV and audit timestamps/OHLCV integrity.
4. Require research-scale data (default 400+ rows).
5. Run purged/embargoed walk-forward and independent candidate tournament.
6. Apply fee/slippage stress and adversarial attacks.
7. Persist evidence and code fingerprint.
8. Only then evaluate paper/shadow behavior. Live execution remains disabled.

REAL_DATA is not satisfied by fixtures, mocks, synthetic data, provider-adapter existence, or local tests.
