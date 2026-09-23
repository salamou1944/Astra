"""Guarded Kraken Spot execution adapter.

Live submission is fail-closed: ASTRA_LIVE_TRADING must be enabled *and* the
ExecutionGate must authorize the complete safety chain. Read-only private
queries support reconciliation but also remain disabled while live mode is OFF.
Withdrawal endpoints are intentionally absent.
"""
from __future__ import annotations

import base64, hashlib, hmac, json, os, time
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .safety import ExecutionGate


@dataclass(frozen=True)
class KrakenExecutionConfig:
    api_key: str
    api_secret: str
    live_enabled: bool = False
    base_url: str = "https://api.kraken.com"
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "KrakenExecutionConfig":
        return cls(
            api_key=os.getenv("ASTRA_KRAKEN_API_KEY", ""),
            api_secret=os.getenv("ASTRA_KRAKEN_API_SECRET", ""),
            live_enabled=os.getenv("ASTRA_LIVE_TRADING", "0") == "1",
        )


class KrakenExecutionError(RuntimeError):
    pass


class KrakenSpotExecutor:
    """Authenticated Spot boundary; no withdrawal capability by design."""

    def __init__(self, config: KrakenExecutionConfig):
        self.config = config
        if config.live_enabled and (not config.api_key or not config.api_secret):
            raise KrakenExecutionError(
                "live execution requires ASTRA_KRAKEN_API_KEY and ASTRA_KRAKEN_API_SECRET"
            )

    @staticmethod
    def _signature(path: str, nonce: str, payload: dict, secret: str) -> str:
        postdata = urlencode(payload)
        message = path.encode() + hashlib.sha256((nonce + postdata).encode()).digest()
        mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
        return base64.b64encode(mac.digest()).decode()

    def _private(self, path: str, payload: dict) -> dict:
        if not self.config.live_enabled:
            raise KrakenExecutionError("live execution is OFF")
        nonce = str(time.time_ns() // 1_000_000)
        body = dict(payload)
        body["nonce"] = nonce
        data = urlencode(body).encode()
        headers = {
            "API-Key": self.config.api_key,
            "API-Sign": self._signature(path, nonce, body, self.config.api_secret),
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        }
        req = Request(self.config.base_url + path, data=data, headers=headers, method="POST")
        with urlopen(req, timeout=self.config.timeout_seconds) as resp:
            result = json.loads(resp.read().decode())
        if result.get("error"):
            raise KrakenExecutionError("Kraken API error: " + "; ".join(map(str, result["error"])))
        return result.get("result", {})

    def build_add_order(self, *, pair: str, side: str, ordertype: str, volume: str,
                        price: str | None = None) -> dict:
        side = side.lower()
        ordertype = ordertype.lower()
        if side not in {"buy", "sell"}:
            raise ValueError("side must be buy or sell")
        if ordertype not in {"market", "limit"}:
            raise ValueError("ordertype must be market or limit")
        if not pair or float(volume) <= 0:
            raise ValueError("pair and positive volume are required")
        if ordertype == "limit" and (price is None or float(price) <= 0):
            raise ValueError("limit orders require a positive price")
        payload = {"ordertype": ordertype, "type": side, "volume": volume, "pair": pair}
        if price is not None:
            payload["price"] = price
        return payload

    def _submit_order(self, **order) -> dict:
        payload = self.build_add_order(**order)
        return self._private("/0/private/AddOrder", payload)

    def query_balance(self) -> dict:
        return self._private("/0/private/Balance", {})

    def query_open_orders(self) -> dict:
        return self._private("/0/private/OpenOrders", {})

    def query_orders(self, *, txid: str | None = None) -> dict:
        payload = {} if txid is None else {"txid": txid}
        return self._private("/0/private/QueryOrders", payload)

    def cancel_order(self, *, txid: str) -> dict:
        if not txid:
            raise ValueError("txid is required")
        return self._private("/0/private/CancelOrder", {"txid": txid})

    def submit_order(self, **order) -> dict:
        """Compatibility entry point that is fail-closed for live submission."""
        if self.config.live_enabled:
            raise KrakenExecutionError(
                "direct live submission is blocked; use submit_if_authorized with ExecutionGate"
            )
        return self._submit_order(**order)

    def submit_if_authorized(
        self, *, gate: ExecutionGate | None = None,
        data_valid: bool = False, strategy_valid: bool = False,
        risk_valid: bool = False, execution_valid: bool = False,
        reconciliation_valid: bool = False, human_approval: bool = False,
        **order,
    ) -> dict:
        if not self.config.live_enabled:
            return {"submitted": False, "mode": "OFF", "reason": "ASTRA_LIVE_TRADING is not enabled"}
        if gate is None:
            raise KrakenExecutionError("live submission requires an ExecutionGate")
        if not gate.authorize(
            data_valid=data_valid, strategy_valid=strategy_valid,
            risk_valid=risk_valid, execution_valid=execution_valid,
            reconciliation_valid=reconciliation_valid,
            human_approval=human_approval, live_enabled=self.config.live_enabled,
        ):
            return {"submitted": False, "mode": "LIVE_BLOCKED", "reason": "execution safety gate denied"}
        result = self._submit_order(**order)
        return {"submitted": True, "mode": "LIVE_SPOT", "result": result}
