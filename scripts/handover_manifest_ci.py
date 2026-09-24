from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "handover_manifest.json"

def main() -> None:
    sha = os.environ.get("GITHUB_SHA", "LOCAL")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    manifest = {
        "repository": "salamou1944/Astra",
        "verification_commit_sha": sha,
        "generated_at": now,
        "runtime_mode": "NON_LIVE",
        "live_trading_environment": "0",
        "automatic_live_orders": False,
        "private_order_submission": False,
        "withdrawal_capability": False,
        "human_approval": False,
        "strategy_status": "UNVERIFIED",
        "alpha_status": "UNVERIFIED",
        "profitability_status": "UNVERIFIED",
        "prospective_status": "ACCUMULATING_FORWARD_SAMPLE",
        "required_gates": {
            "DATA_VALID": True,
            "STRATEGY_VALID": False,
            "RISK_VALID": True,
            "EXECUTION_VALID": True,
            "RECONCILIATION_VALID": True,
            "KILL_SWITCH_VALID": True,
            "HUMAN_APPROVAL": False,
            "LIVE_ENABLED": False,
        },
        "completed_stages": [
            "REAL_DATA",
            "RESEARCH",
            "OUT_OF_SAMPLE",
            "WALK_FORWARD",
            "ROBUSTNESS",
            "STATISTICAL_REALITY_CHECK",
            "RISK_ENGINE",
            "PAPER_EXECUTION",
            "RECONCILIATION",
            "KILL_SWITCH",
            "ADVERSARIAL_EXECUTION",
            "EXCHANGE_TESTING",
            "HUMAN_APPROVAL_GATE",
            "LIVE_READINESS_ASSESSMENT",
            "PROSPECTIVE_PAPER_VALIDATION_MONITOR",
        ],
        "blockers": [
            "STRATEGY_VALID is not proven",
            "HUMAN_APPROVAL is intentionally false",
            "LIVE_ENABLED is intentionally false",
            "Prospective forward sample must accumulate before it becomes evidence",
        ],
        "next_required_action": "Continue scheduled prospective paper observation; do not enable live trading automatically.",
        "evidence_policy": "CI success is not trading success; profitability and alpha remain unverified until independently supported.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
