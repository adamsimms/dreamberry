#!/usr/bin/env python3
"""Download Cloudberry catalog JPEGs from CDN into data/raw/."""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

from dataset_common import REPO_ROOT, ensure_dirs, load_catalog, load_config, resolve_path

sys.path.insert(0, str(REPO_ROOT / "scripts"))


def download_one(
    session: requests.Session,
    url: str,
    dest: Path,
    user_agent: str,
    retries: int,
) -> tuple[str, bool, str | None]:
    if dest.exists() and dest.stat().st_size > 0:
        return dest.name, True, "cached"

    headers = {"User-Agent": user_agent}
    last_err: str | None = None
    for attempt in range(retries):
        try:
            resp = session.get(url, headers=headers, timeout=120, stream=True)
            resp.raise_for_status()
            tmp = dest.with_suffix(dest.suffix + ".part")
            with open(tmp, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        f.write(chunk)
            tmp.rename(dest)
            return dest.name, True, None
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)
            time.sleep(1.5 * (attempt + 1))
    return dest.name, False, last_err


def main() -> int:
    parser = argparse.ArgumentParser(description="Download catalog images")
    parser.add_argument("--limit", type=int, default=0, help="Download only N images (0=all)")
    args = parser.parse_args()

    cfg = load_config()
    raw_dir = resolve_path(cfg["paths"]["raw_dir"])
    ensure_dirs(raw_dir)

    photos = load_catalog(cfg)
    if args.limit:
        photos = photos[: args.limit]

    cdn_base = cfg["catalog"]["cdn_base"].rstrip("/") + "/"
    ua = cfg["download"]["user_agent"]
    workers = int(cfg["download"]["workers"])
    retries = int(cfg["download"]["retries"])

    tasks: list[tuple[str, Path]] = []
    for p in photos:
        fn = p["filename"]
        tasks.append((cdn_base + fn, raw_dir / fn))

    total = len(tasks)
    ok = 0
    failed: list[tuple[str, str]] = []
    cached = 0

    print(f"Downloading {total} images to {raw_dir} ({workers} workers)...")

    with requests.Session() as session, ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(download_one, session, url, dest, ua, retries): (url, dest)
            for url, dest in tasks
        }
        for i, fut in enumerate(as_completed(futures), 1):
            name, success, err = fut.result()
            if success:
                ok += 1
                if err == "cached":
                    cached += 1
            else:
                failed.append((name, err or "unknown"))
            if i % 50 == 0 or i == total:
                print(f"  [{i}/{total}] ok={ok} cached={cached} failed={len(failed)}")

    if failed:
        print(f"\nFailed downloads ({len(failed)}):")
        for name, err in failed[:20]:
            print(f"  {name}: {err}")
        if len(failed) > 20:
            print(f"  ... and {len(failed) - 20} more")
        return 1

    print(f"Done: {ok}/{total} ({cached} cached)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
