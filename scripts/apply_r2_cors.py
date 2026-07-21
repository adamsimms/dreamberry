#!/usr/bin/env python3
"""Apply CORS on the Dreamberry R2 bucket so art.adamsimms.xyz can fetch JSON (M6 / #20).

Prefer Wrangler (account auth) — S3 API tokens often lack PutBucketCors:

  # from art.adamsimms.xyz (Node ≥22):
  npx wrangler r2 bucket cors set art-adamsimms-xyz-dreamberry \\
    --file ../dreamberry/config/r2-cors.json

Fallback via S3 API (needs a token with CORS write):

  PYTHONPATH=. .venv/bin/python scripts/apply_r2_cors.py
  PYTHONPATH=. .venv/bin/python scripts/apply_r2_cors.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from dream.storage import r2_config_from_env  # noqa: E402

CORS_JSON = REPO / "config" / "r2-cors.json"


def _rules_from_wrangler_file() -> list[dict]:
    """Map config/r2-cors.json (Wrangler shape) → S3 PutBucketCors rules."""
    doc = json.loads(CORS_JSON.read_text())
    out: list[dict] = []
    for rule in doc.get("rules") or []:
        allowed = rule.get("allowed") or {}
        out.append(
            {
                "AllowedOrigins": list(allowed.get("origins") or []),
                "AllowedMethods": list(allowed.get("methods") or ["GET", "HEAD"]),
                "AllowedHeaders": list(allowed.get("headers") or ["*"]),
                "ExposeHeaders": list(rule.get("exposeHeaders") or []),
                "MaxAgeSeconds": int(rule.get("maxAgeSeconds") or 3600),
            }
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rules = _rules_from_wrangler_file()
    cfg = r2_config_from_env()
    print(f"bucket: {cfg.bucket}")
    print(json.dumps(rules, indent=2))
    print(
        "tip: if AccessDenied, use:\n"
        "  npx wrangler r2 bucket cors set art-adamsimms-xyz-dreamberry "
        f"--file {CORS_JSON}"
    )

    if args.dry_run:
        print("dry-run — not applying")
        return 0

    import boto3
    from botocore.config import Config

    client = boto3.client(
        "s3",
        endpoint_url=cfg.endpoint_url,
        aws_access_key_id=cfg.access_key_id,
        aws_secret_access_key=cfg.secret_access_key,
        region_name=cfg.region_name,
        config=Config(signature_version="s3v4"),
    )
    client.put_bucket_cors(Bucket=cfg.bucket, CORSConfiguration={"CORSRules": rules})
    got = client.get_bucket_cors(Bucket=cfg.bucket)
    print("applied:", json.dumps(got.get("CORSRules", []), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
