from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Split:
    train_start: int
    train_end: int
    test_start: int
    test_end: int
    embargo: int

def purged_walk_forward_splits(n: int, train_size: int, test_size: int, step: int, embargo: int = 0) -> list[Split]:
    if min(n, train_size, test_size, step) <= 0 or embargo < 0:
        raise ValueError("invalid split parameters")
    out=[]; start=0
    while start + train_size + embargo + test_size <= n:
        train_end=start+train_size
        test_start=train_end+embargo
        out.append(Split(start, train_end, test_start, test_start+test_size, embargo))
        start += step
    return out

def assert_no_future_leakage(splits: list[Split]) -> None:
    for s in splits:
        if s.train_end > s.test_start:
            raise AssertionError("training data overlaps future test window")
