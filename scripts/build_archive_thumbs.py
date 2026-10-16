#!/usr/bin/env python3
"""Backfill ``archive/thumbs/<id>.webp`` for the studio gallery (issue #37).

  PYTHONPATH=. .venv/bin/python scripts/build_archive_thumbs.py
  PYTHONPATH=. .venv/bin/python scripts/build_archive_thumbs.py --limit 50
  PYTHONPATH=. .venv/bin/python scripts/build_archive_thumbs.py --rebuild-index
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from dream.archive_index import list_archive_dream_ids, rebuild_archive_index  # noqa: E402
from dream.storage import ARCHIVE_PREFIX, R2Store, r2_config_from_env  # noqa: E402
from dream.thumbs import put_archive_thumb_from_png_bytes, thumb_key  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true", help="Overwrite existing thumbs")
    ap.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Rewrite archive/studio/index.json after thumbs",
    )
    args = ap.parse_args()

    store = R2Store(r2_config_from_env())
    ids = list_archive_dream_ids(store)
    ids.sort(reverse=True)
    if args.limit is not None:
        ids = ids[: max(0, args.limit)]

    existing = set()
    if not args.force:
        existing = {k for k in store.list_keys("archive/thumbs/") if k.endswith(".webp")}

    done = 0
    skipped = 0
    failed = 0
    for i, dream_id in enumerate(ids, 1):
        key = thumb_key(dream_id)
        if key in existing:
            skipped += 1
            continue
        png = store.get_bytes(f"{ARCHIVE_PREFIX}{dream_id}.png")
        if not png:
            failed += 1
            print(f"[{i}/{len(ids)}] missing png {dream_id}", flush=True)
            continue
        try:
            put_archive_thumb_from_png_bytes(store, dream_id=dream_id, png=png)
            done += 1
            if done % 25 == 0 or i == len(ids):
                print(f"[{i}/{len(ids)}] wrote {done} thumbs (+{skipped} skip)", flush=True)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"[{i}/{len(ids)}] fail {dream_id}: {exc}", flush=True)

    print(f"done={done} skipped={skipped} failed={failed}")
    if args.rebuild_index:
        doc = rebuild_archive_index(store)
        print(f"index: {doc['count']} entries")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
