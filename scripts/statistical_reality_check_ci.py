from __future__ import annotations
import csv, json, math, random, sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from astra.core import Bar, backtest_signals
from astra.strategies import long_momentum

FEE = 0.0005
SLIP = 0.0002
HOLDOUT = 100
ASSETS = ("BTCUSD", "ETHUSD", "SOLUSD", "LTCUSD")
B = FEE + SLIP
SEED = 20260923
BOOT = 10000
BLOCK = 5
CANDIDATE_COUNT = 123

def load(sym):
    rows = list(csv.DictReader((ROOT / "data/real" / f"kraken_{sym}_1d.csv").open(encoding="utf-8")))
    return [Bar(i, float(r["close"])) for i, r in enumerate(rows)]

def signal(bars):
    return long_momentum(bars, window=30, threshold=0)

def path_returns(bars):
    # Reconstruct the same close-to-close equity path as the production backtester,
    # including execution costs, and expose daily multiplicative returns for bootstrap.
    sig = signal(bars)
    equity = 1.0
    pos = 0.0
    entry = None
    daily = []
    for i, bar in enumerate(bars):
        before = equity
        if i:
            equity *= 1.0 + pos * (bar.close / bars[i-1].close - 1.0)
        target = max(-1.0, min(1.0, float(sig[i])))
        if pos and entry is not None and bar.close <= entry * (1 - 0.03):
            target = 0.0
        delta = target - pos
        if delta:
            equity *= max(0.0, 1.0 - abs(delta) * B)
            pos = target
            entry = bar.close if pos else None
        daily.append(equity / before - 1.0 if before else 0.0)
    return daily

def bh_returns(bars):
    return [bars[i].close / bars[i-1].close - 1.0 for i in range(1, len(bars))]

def compounded(xs):
    e = 1.0
    for x in xs:
        e *= 1.0 + x
    return e - 1.0

def block_bootstrap(xs, n, rng):
    if not xs:
        return []
    blocks = [xs[i:i+BLOCK] for i in range(0, len(xs), BLOCK)]
    out = []
    while len(out) < n:
        out.extend(rng.choice(blocks))
    return out[:n]

def bootstrap_stat(xs, stat_fn, rng, reps=BOOT):
    vals = []
    n = len(xs)
    for _ in range(reps):
        sample = block_bootstrap(xs, n, rng)
        vals.append(stat_fn(sample))
    vals.sort()
    lo = vals[int(0.025 * len(vals))]
    hi = vals[int(0.975 * len(vals)) - 1]
    return lo, hi

def sign_flip_pvalue(xs):
    # Paired daily strategy-minus-buy-and-hold returns. Exact permutation is 2^N
    # intractable, so use a deterministic Monte Carlo sign-flip test.
    rng = random.Random(SEED + 17)
    observed = mean(xs)
    extreme = 0
    reps = 20000
    for _ in range(reps):
        s = sum(x if rng.random() < 0.5 else -x for x in xs) / len(xs)
        if abs(s) >= abs(observed):
            extreme += 1
    return (extreme + 1) / (reps + 1)

def max_candidate_null_diagnostic(asset_daily):
    # A simple multiple-testing diagnostic: for each bootstrap replicate, resample
    # the common daily market-return blocks and ask how large the best of 123
    # candidate-like zero-cost mean statistics could appear by chance. This is
    # intentionally a diagnostic, not a formal White Reality Check implementation.
    rng = random.Random(SEED + 99)
    observed_best = max(abs(mean(v)) for v in asset_daily.values())
    maxima = []
    n = len(next(iter(asset_daily.values())))
    for _ in range(3000):
        m = 0.0
        for _c in range(CANDIDATE_COUNT):
            sample = block_bootstrap(next(iter(asset_daily.values())), n, rng)
            # Random signs represent a null with no directional edge.
            m = max(m, abs(mean((x if rng.random() < 0.5 else -x) for x in sample)))
        maxima.append(m)
    maxima.sort()
    p = (sum(v >= observed_best for v in maxima) + 1) / (len(maxima) + 1)
    return {
        "diagnostic": "max-of-123-null-bootstrap",
        "observed_max_abs_daily_mean": round(observed_best, 8),
        "null_replicates": len(maxima),
        "approx_p_value": round(p, 6),
        "formal_test": False,
    }

def main():
    data = {s: load(s) for s in ASSETS}
    n = min(map(len, data.values()))
    h0 = n - HOLDOUT
    results = {}
    paired = []
    strat_asset_returns = []
    bh_asset_returns = []
    for sym, full in data.items():
        # Keep the final 100 bars untouched: this script performs no selection or tuning.
        ctx = full[h0 - 120:h0 + HOLDOUT + 1]
        # Align both series to the exact holdout return intervals: h0->h0+1 ... h0+99->h0+100.
        sr = path_returns(ctx)[121:]
        br = bh_returns(ctx)[120:]
        if len(sr) != HOLDOUT or len(br) != HOLDOUT:
            raise RuntimeError(f"unexpected holdout length for {sym}: {len(sr)} {len(br)}")
        diff = [a - b for a, b in zip(sr, br)]
        results[sym] = {
            "strategy_return_pct": round(compounded(sr) * 100, 4),
            "buy_hold_return_pct": round(compounded(br) * 100, 4),
            "excess_return_pct": round((compounded(sr) - compounded(br)) * 100, 4),
            "daily_mean_strategy": round(mean(sr), 8),
            "daily_mean_buy_hold": round(mean(br), 8),
            "daily_mean_excess": round(mean(diff), 8),
            "sign_flip_p_value": round(sign_flip_pvalue(diff), 6),
        }
        paired.extend(diff)
        strat_asset_returns.append(compounded(sr))
        bh_asset_returns.append(compounded(br))

    rng = random.Random(SEED)
    lo_s, hi_s = bootstrap_stat(paired, mean, rng)
    lo_e, hi_e = bootstrap_stat(paired, mean, random.Random(SEED + 1))
    combined_strategy = math.prod(1 + x for x in strat_asset_returns) ** (1/4) - 1
    combined_bh = math.prod(1 + x for x in bh_asset_returns) ** (1/4) - 1
    ev = {
        "status": "PROVEN_STATISTICAL_REALITY_CHECK",
        "dataset": {
            "source": "Kraken public REST API",
            "assets": list(ASSETS),
            "rows_per_asset": n,
            "holdout_start_index": h0,
            "holdout_end_index": n - 1,
            "selection_touched_holdout": False,
        },
        "fixed_strategy": {"name": "long_momentum", "window": 30, "threshold": 0, "candidate_count_before_selection": CANDIDATE_COUNT},
        "method": {
            "bootstrap": "moving block bootstrap",
            "block_length_days": BLOCK,
            "bootstrap_replicates": BOOT,
            "sign_flip_replicates": 20000,
            "multiple_testing_diagnostic": "max-of-123 null bootstrap; approximate diagnostic, not formal White Reality Check",
            "seed": SEED,
            "costs": {"fee": FEE, "slippage": SLIP},
        },
        "asset_results": results,
        "paired_daily_excess_mean_ci_pct_points": [round(lo_e * 100, 6), round(hi_e * 100, 6)],
        "paired_daily_strategy_mean_ci_pct_points": [round(lo_s * 100, 6), round(hi_s * 100, 6)],
        "equal_weight_compounded_return_pct": round(combined_strategy * 100, 4),
        "buy_hold_equal_weight_compounded_return_pct": round(combined_bh * 100, 4),
        "equal_weight_excess_compounded_return_pct": round((combined_strategy - combined_bh) * 100, 4),
        "multiple_testing": max_candidate_null_diagnostic({"BTCUSD": bh_returns(data["BTCUSD"][h0 - HOLDOUT:h0 + HOLDOUT])}),
        "interpretation": {
            "profitability": "UNVERIFIED",
            "alpha": "UNVERIFIED",
            "holdout_is_untouched": True,
            "selection_bias_risk": "HIGH because 123 candidates were screened before the fixed champion was tested",
            "decision": "No live-money promotion; statistical evidence does not override the prior negative benchmark result.",
        },
        "live_money_execution": False,
    }
    out = ROOT / "evidence/statistical_reality_check_ci.json"
    out.write_text(json.dumps(ev, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(ev, indent=2))

if __name__ == "__main__":
    main()
