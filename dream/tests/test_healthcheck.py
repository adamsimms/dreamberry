"""Unit tests for healthchecks.io ping helper."""

from __future__ import annotations

from dream.healthcheck import ping_healthcheck


def test_ping_skipped_when_unset(monkeypatch):
    monkeypatch.delenv("HEALTH_PING_URL", raising=False)
    out = ping_healthcheck(url=None)
    assert out["skipped"] is True


def test_ping_success(monkeypatch):
    class Resp:
        ok = True
        status_code = 200

    def fake_get(url, timeout=15.0):
        assert url.endswith("/abc")
        return Resp()

    monkeypatch.setattr("dream.healthcheck.requests.get", fake_get)
    out = ping_healthcheck(url="https://hc-ping.com/abc")
    assert out["ok"] is True


def test_ping_fail_suffix(monkeypatch):
    seen = {}

    class Resp:
        ok = True
        status_code = 200

    def fake_get(url, timeout=15.0):
        seen["url"] = url
        return Resp()

    monkeypatch.setattr("dream.healthcheck.requests.get", fake_get)
    ping_healthcheck(url="https://hc-ping.com/abc", failed=True)
    assert seen["url"] == "https://hc-ping.com/abc/fail"
