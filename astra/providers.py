from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
from .alpaca import fetch_crypto_bars, MarketFetch
from .binance import fetch_klines, BinanceFetch

@dataclass(frozen=True)
class ProviderResult:
    provider: str
    status: str
    detail: str
    fetch: MarketFetch | None = None

class Provider(Protocol):
    name: str
    def fetch(self, symbol: str, timeframe: str, limit: int = 1000) -> ProviderResult: ...

class AlpacaProvider:
    name = "alpaca_crypto"
    def fetch(self, symbol: str, timeframe: str, limit: int = 1000) -> ProviderResult:
        try:
            f = fetch_crypto_bars(symbol=symbol, timeframe=timeframe, limit=limit)
            return ProviderResult(self.name, "PROVIDER_VERIFIED", "live provider request succeeded", f)
        except Exception as exc:
            return ProviderResult(self.name, "BLOCKED", f"{type(exc).__name__}: {exc}")

class ProviderRegistry:
    def __init__(self, providers: list[Provider]): self.providers = providers
    def fetch_first_verified(self, symbol: str, timeframe: str, limit: int = 1000) -> list[ProviderResult]:
        results=[]
        for p in self.providers:
            r=p.fetch(symbol,timeframe,limit); results.append(r)
            if r.status == "PROVIDER_VERIFIED": break
        return results

class BinanceProvider:
    name = "binance_public"
    def fetch(self, symbol: str, timeframe: str, limit: int = 1000) -> ProviderResult:
        try:
            normalized = symbol.replace("/", "")
            f = fetch_klines(symbol=normalized, interval=timeframe, limit=limit)
            return ProviderResult(self.name, "PROVIDER_VERIFIED", "live public market-data request succeeded", f)
        except Exception as exc:
            return ProviderResult(self.name, "BLOCKED", f"{type(exc).__name__}: {exc}")
