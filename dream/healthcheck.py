"""Healthchecks.io dead-man ping (M5 / issue #16)."""

from __future__ import annotations

import os
from typing import Any

import requests


def ping_healthcheck(
    *,
    url: str | None = None,
    failed: bool = False,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """Ping the configured check. No-op when HEALTH_PING_URL is unset.

    On hard failures pass `failed=True` to hit the `/fail` endpoint so the
    dead-man switch pages even if the process exits 0 after recording noise.
    """
    base = (url or os.environ.get("HEALTH_PING_URL") or "").rstrip("/")
    if not base:
        return {"skipped": True, "reason": "HEALTH_PING_URL unset"}
    target = f"{base}/fail" if failed else base
    try:
        resp = requests.get(target, timeout=timeout)
        return {"ok": resp.ok, "status_code": resp.status_code, "url": target}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "url": target}
