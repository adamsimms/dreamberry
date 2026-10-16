#!/usr/bin/env python3
"""Build / upload the private archive studio index (issue #37).

Writes ``archive/studio/index.json`` on R2 (newest-first summaries).

  PYTHONPATH=. .venv/bin/python scripts/build_archive_index.py
  PYTHONPATH=. .venv/bin/python scripts/build_archive_index.py --limit 200
  PYTHONPATH=. .venv/bin/python scripts/build_archive_index.py --upload-ui
"""

from __future__ import annotations

import argparse
import mimetypes
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from dream.archive_index import INDEX_KEY, STUDIO_PREFIX, rebuild_archive_index  # noqa: E402
from dream.storage import R2Store, r2_config_from_env  # noqa: E402

UI_DIR = REPO / "studio" / "archive"
UI_FILES = ("index.html", "studio.css", "studio.js")


def upload_ui(store: R2Store) -> list[str]:
    keys: list[str] = []
    for name in UI_FILES:
        path = UI_DIR / name
        data = path.read_bytes()
        ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
        if name.endswith(".html"):
            ctype = "text/html; charset=utf-8"
        elif name.endswith(".js"):
            ctype = "text/javascript; charset=utf-8"
        elif name.endswith(".css"):
            ctype = "text/css; charset=utf-8"
        key = f"{STUDIO_PREFIX}{name}"
        store.put_bytes(
            key,
            data,
            content_type=ctype,
            cache_control="private, max-age=60",
        )
        keys.append(key)
    return keys


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only index the newest N dreams (faster smoke)",
    )
    ap.add_argument(
        "--enrich",
        action="store_true",
        help="Fetch every sidecar into the index (slow; detail view already loads sidecars)",
    )
    ap.add_argument(
        "--upload-ui",
        action="store_true",
        help="Also upload studio/archive/{index.html,studio.css,studio.js}",
    )
    ap.add_argument(
        "--ui-only",
        action="store_true",
        help="Upload UI assets only (skip index rebuild)",
    )
    args = ap.parse_args()

    cfg = r2_config_from_env()
    store = R2Store(cfg)
    print(f"bucket: {cfg.bucket}")
    print(f"public: {cfg.public_base_url}")

    if args.upload_ui or args.ui_only:
        keys = upload_ui(store)
        for k in keys:
            print(f"ui: {cfg.public_url(k) if cfg.public_base_url else k}")

    if not args.ui_only:
        doc = rebuild_archive_index(store, limit=args.limit, enrich=args.enrich)
        print(f"index: {INDEX_KEY} ({doc['count']} entries)")
        if cfg.public_base_url:
            print(f"studio: {cfg.public_base_url.rstrip('/')}/archive/studio/")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
