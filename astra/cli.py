import argparse
from .core import market, backtest, adversary, PaperBroker
from .research import demo_research
from .evidence import EvidenceLedger

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--alpaca-check', action='store_true', help='attempt public Alpaca crypto historical data fetch')
    args=parser.parse_args()
    bars=market(); bt=backtest(bars); adv=adversary(bars)
    broker=PaperBroker(); broker.order(1); ranked=demo_research(); top=ranked[0]
    ledger=EvidenceLedger()
    ledger.add('deterministic_core', 'PROVEN', 'local test suite covers deterministic market, backtest, risk cap, adversary and research tournament', 'TESTED')
    ledger.add('real_market_adapter', 'IMPLEMENTED', 'Alpaca public crypto historical adapter implemented; network/provider verification is separate', 'IMPLEMENTED')
    print('ASTRA QUANT LAB — RESEARCH ENGINE')
    print(f'baseline_return_pct={bt["return_pct"]} max_drawdown_pct={bt["max_drawdown_pct"]} trades={bt["trades"]}')
    print(f'adversary_survival={adv["survival_ratio"]:.2f} adversary_passed={adv["passed"]}')
    print(f'walk_forward_folds={top.folds} top_candidate=fast:{top.fast}/slow:{top.slow} mean_test_return_pct={top.mean_return_pct} positive_fold_ratio={top.positive_fold_ratio} passed={top.passed}')
    print(f'paper_position={broker.position} live_money_execution=False')
    if args.alpaca_check:
        from .alpaca import fetch_crypto_bars
        try:
            fetched=fetch_crypto_bars(start='2026-01-01T00:00:00Z', end='2026-03-01T00:00:00Z', limit=100)
            print(f'alpaca_provider=VERIFIED symbol={fetched.symbol} bars={len(fetched.bars)}')
        except Exception as e:
            print(f'alpaca_provider=BLOCKED reason={type(e).__name__}: {e}')
if __name__ == '__main__': main()
