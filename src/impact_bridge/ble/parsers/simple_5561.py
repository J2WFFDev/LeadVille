"""Legacy 0x5561 parser stub.

The legacy multi-sample parser (`parse_5561`) has been retired from the active
bridge pipeline. Historical tooling that still needs it can import the archived
copy under `archive/legacy_parse_5561.py`. This stub remains only to provide a
clear failure message if stale imports linger in the runtime environment.
"""

from typing import Any


def parse_5561(*args: Any, **kwargs: Any) -> None:  # pragma: no cover - guard only
    raise RuntimeError(
        "parse_5561 has been retired. Use impact_bridge.ble.parsers.parse_bt50_frame "
        "or port callers to the archived implementation in archive/legacy_parse_5561.py."
    )