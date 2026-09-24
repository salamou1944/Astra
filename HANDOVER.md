# ASTRA Handover

Repository: salamou1944/Astra

## Current state

ASTRA is in a safety-first, non-live state.

- ASTRA_LIVE_TRADING=0
- Automatic live orders: disabled
- Private order submission: disabled in current validation stages
- Withdrawal capability: absent
- Human approval: not granted
- Strategy validity: UNVERIFIED
- Alpha: UNVERIFIED
- Profitability: UNVERIFIED
- Prospective sample: still accumulating after the untouched holdout

## Verified stages

- REAL DATA provenance
- Research / candidate evaluation
- Cross-asset research
- Untouched holdout validation
- Statistical reality check
- Principled hypothesis test
- Independent source validation
- Risk shadow
- Paper execution lifecycle
- Reconciliation
- Kill switch
- Adversarial execution
- Safe exchange testing
- Human approval gate
- Live-readiness assessment
- Prospective paper validation monitor

## Important evidence state

The latest prospective-paper workflow completed successfully as a workflow, but workflow success is not evidence that the required forward sample exists. The current prospective script reports INSUFFICIENT_FORWARD_SAMPLE until every asset has at least 30 post-holdout daily bars.

The final holdout must remain untouched for strategy selection.

## Required live gates

DATA_VALID
STRATEGY_VALID
RISK_VALID
EXECUTION_VALID
RECONCILIATION_VALID
KILL_SWITCH_VALID
HUMAN_APPROVAL
LIVE_ENABLED

All must be true before any live order could be authorized. Human approval must never be inferred automatically.

## Operational rule

Continue prospective observation and evidence accumulation. Fix real defects when found. Do not manufacture data, profitability, alpha, or readiness.

## Exact source of truth

The canonical implementation is this Git repository. CI artifacts are evidence snapshots; they are not permission to enable live trading.

A machine-generated handover manifest is produced by the ASTRA HANDOVER workflow and records the exact verification commit SHA at execution time.
