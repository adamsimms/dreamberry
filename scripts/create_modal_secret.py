#!/usr/bin/env python3
"""Create / update the Modal Secret `dreamberry` from local `.env`.

Reads only the keys Modal needs — never prints secret values.

Usage:
  PYTHONPATH=. .venv/bin/python scripts/create_modal_secret.py
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

REPO = Path(__file__).resolve().parent.parent

KEYS = (
    "HF_TOKEN",
    "CF_R2_BUCKET",
    "CF_R2_ENDPOINT",
    "CF_R2_ACCESS_KEY_ID",
    "CF_R2_SECRET",
    "CF_R2_PUBLIC_BASE_URL",
    "HEALTH_PING_URL",
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--name", default="dreamberry")
    ap.add_argument("--env-file", default=str(REPO / ".env"))
    args = ap.parse_args()

    vals = dotenv_values(args.env_file)
    missing = [k for k in KEYS if not vals.get(k)]
    if missing:
        print("missing keys in .env:", ", ".join(missing), file=sys.stderr)
        return 1

    modal = REPO / ".venv" / "bin" / "modal"
    if not modal.exists():
        modal = Path(sys.executable).parent / "modal"

    # modal secret create KEY=VAL ...  (re-create if exists)
    kv = [f"{k}={vals[k]}" for k in KEYS]
    # Delete existing then create — Modal has no upsert in older CLIs.
    subprocess.run(
        [str(modal), "secret", "delete", args.name],
        cwd=REPO,
        check=False,
        capture_output=True,
    )
    cmd = [str(modal), "secret", "create", args.name, *kv]
    print(f"creating Modal secret {args.name!r} with keys: {', '.join(KEYS)}")
    subprocess.check_call(cmd, cwd=REPO)
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
