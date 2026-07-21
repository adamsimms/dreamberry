#!/usr/bin/env python3
"""Prefetch SUPIR + SDXL checkpoint weights into HF_HOME/supir (issue #12).

On Modal the HF volume is mounted at /models (= HF_HOME). Run once after deploy
or from a GPU machine with HF_TOKEN set:

  HF_HOME=/models PYTHONPATH=. .venv/bin/python scripts/download_supir_weights.py

Local:

  PYTHONPATH=. .venv/bin/python scripts/download_supir_weights.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from dream.config import load_dream_config  # noqa: E402
from dream.upscale import _resolve_weights  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sign", choices=("F", "Q"), default=None)
    args = ap.parse_args()

    cfg = load_dream_config()
    up = dict(cfg.get("upscale") or {})
    up["download_weights"] = True
    if args.sign:
        up["sign"] = args.sign
        if args.sign == "Q":
            up["download_q"] = True

    sdxl, f_ckpt, q_ckpt = _resolve_weights(up)
    print("sdxl:", sdxl, "bytes=", sdxl.stat().st_size if sdxl.exists() else 0)
    print("supir F:", f_ckpt, "bytes=", f_ckpt.stat().st_size if f_ckpt.exists() else 0)
    print("supir Q:", q_ckpt, "bytes=", q_ckpt.stat().st_size if q_ckpt.exists() else 0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
