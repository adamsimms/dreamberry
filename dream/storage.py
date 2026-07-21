"""Cloudflare R2 delivery for Dreamberry hourly artifacts (M5 / issues #16–#17).

Layout (flat, dedicated bucket `art-adamsimms-xyz-dreamberry` — never Cloudberry):

  archive/<TIMESTAMP>_DREAM###.png   + .json   (PNG lossless — print / InDesign)
  current/current.webp               + .json   (WebP lossless — public window)
  current/status.json
  current/signal_lost.webp                     (channel dead only)

Hold (weather silence / gate exhaustion): update `current/status.json` only —
never overwrite `current/current.webp` (DREAMBERRY.md §7).
"""

from __future__ import annotations

import io
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml
from PIL import Image

from dream.config import REPO_ROOT

__all__ = [
    "R2Config",
    "R2Store",
    "encode_archive_png",
    "encode_current_webp",
    "next_dream_number_from_names",
    "load_r2_config",
    "r2_config_from_env",
]

_DREAM_RE = re.compile(r"_DREAM(\d+)\.(?:png|PNG|jpg|JPG|jpeg|JPEG|webp|WEBP)$")

ARCHIVE_PREFIX = "archive/"
CURRENT_PREFIX = "current/"
CURRENT_IMAGE_KEY = f"{CURRENT_PREFIX}current.webp"
CURRENT_JSON_KEY = f"{CURRENT_PREFIX}current.json"
STATUS_KEY = f"{CURRENT_PREFIX}status.json"
SIGNAL_LOST_KEY = f"{CURRENT_PREFIX}signal_lost.webp"


@dataclass(frozen=True)
class R2Config:
    """S3-compatible credentials for the dedicated Dreamberry bucket."""

    bucket: str
    endpoint_url: str
    access_key_id: str
    secret_access_key: str
    public_base_url: str | None = None
    region_name: str = "auto"

    def public_url(self, key: str) -> str | None:
        if not self.public_base_url:
            return None
        return f"{self.public_base_url.rstrip('/')}/{key.lstrip('/')}"


def load_r2_config(path: Path | str | None = None) -> dict[str, Any]:
    p = Path(path) if path else REPO_ROOT / "config" / "platform.yaml"
    with open(p) as f:
        return yaml.safe_load(f) or {}


def r2_config_from_env(
    *,
    platform_cfg: Mapping[str, Any] | None = None,
) -> R2Config:
    """Build R2Config from process env (Modal secrets / local `.env`)."""
    from dream.config import _load_dotenv

    _load_dotenv()
    if platform_cfg is None:
        try:
            platform_cfg = load_r2_config()
        except FileNotFoundError:
            platform_cfg = {}
    r2 = (platform_cfg.get("r2") or {}) if platform_cfg else {}

    bucket = os.environ.get("CF_R2_BUCKET") or r2.get("bucket")
    endpoint = os.environ.get("CF_R2_ENDPOINT") or r2.get("endpoint")
    access = os.environ.get("CF_R2_ACCESS_KEY_ID")
    secret = os.environ.get("CF_R2_SECRET")
    public = os.environ.get("CF_R2_PUBLIC_BASE_URL") or r2.get("public_base_url")

    missing = [
        name
        for name, val in (
            ("CF_R2_BUCKET", bucket),
            ("CF_R2_ENDPOINT", endpoint),
            ("CF_R2_ACCESS_KEY_ID", access),
            ("CF_R2_SECRET", secret),
        )
        if not val
    ]
    if missing:
        raise ValueError("missing R2 env: " + ", ".join(missing))

    if "r2.cloudflarestorage.com" not in str(endpoint):
        raise ValueError(
            "CF_R2_ENDPOINT must be the S3 API host "
            "(https://<ACCOUNT_ID>.r2.cloudflarestorage.com), "
            "not the public custom domain — put that in CF_R2_PUBLIC_BASE_URL"
        )

    return R2Config(
        bucket=str(bucket),
        endpoint_url=str(endpoint).rstrip("/"),
        access_key_id=str(access),
        secret_access_key=str(secret),
        public_base_url=(str(public).rstrip("/") if public else None),
    )


def encode_archive_png(image: Image.Image) -> bytes:
    """Lossless PNG for the private hourly archive (print / InDesign path)."""
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def encode_current_webp(image: Image.Image) -> bytes:
    """Lossless WebP for the public window pointer."""
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="WEBP", lossless=True, method=6)
    return buf.getvalue()


def next_dream_number_from_names(names: list[str]) -> int:
    """Next roll counter from archive filenames (local or R2 keys)."""
    mx = 0
    for name in names:
        base = Path(name).name
        m = _DREAM_RE.search(base)
        if m:
            mx = max(mx, int(m.group(1)))
    return mx + 1


class R2Store:
    """Thin S3 client for Dreamberry's dedicated R2 bucket."""

    def __init__(self, cfg: R2Config):
        import boto3
        from botocore.config import Config

        self.cfg = cfg
        self._client = boto3.client(
            "s3",
            endpoint_url=cfg.endpoint_url,
            aws_access_key_id=cfg.access_key_id,
            aws_secret_access_key=cfg.secret_access_key,
            region_name=cfg.region_name,
            config=Config(signature_version="s3v4"),
        )

    # -- primitives ----------------------------------------------------------

    def put_bytes(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str,
        cache_control: str | None = None,
    ) -> None:
        # Live pointer under current/ changes hourly — short edge cache so a
        # hard refresh never keeps a stale hour (client also busts with ?v=).
        if cache_control is None and key.startswith(CURRENT_PREFIX):
            cache_control = "public, max-age=300"
        kwargs: dict[str, Any] = {
            "Bucket": self.cfg.bucket,
            "Key": key,
            "Body": data,
            "ContentType": content_type,
        }
        if cache_control:
            kwargs["CacheControl"] = cache_control
        self._client.put_object(**kwargs)

    def put_json(self, key: str, obj: Mapping[str, Any]) -> None:
        body = (json.dumps(dict(obj), ensure_ascii=False, indent=2) + "\n").encode(
            "utf-8"
        )
        self.put_bytes(key, body, content_type="application/json")

    def get_json(self, key: str) -> dict[str, Any] | None:
        try:
            resp = self._client.get_object(Bucket=self.cfg.bucket, Key=key)
        except self._client.exceptions.NoSuchKey:
            return None
        except Exception as exc:  # noqa: BLE001
            # botocore ClientError 404
            code = getattr(exc, "response", {}).get("Error", {}).get("Code")
            if code in ("404", "NoSuchKey", "NotFound"):
                return None
            raise
        return json.loads(resp["Body"].read().decode("utf-8"))

    def list_keys(self, prefix: str) -> list[str]:
        keys: list[str] = []
        token = None
        while True:
            kwargs: dict[str, Any] = {
                "Bucket": self.cfg.bucket,
                "Prefix": prefix,
            }
            if token:
                kwargs["ContinuationToken"] = token
            resp = self._client.list_objects_v2(**kwargs)
            for item in resp.get("Contents") or []:
                keys.append(item["Key"])
            if not resp.get("IsTruncated"):
                break
            token = resp.get("NextContinuationToken")
        return keys

    def next_dream_number(self) -> int:
        names = [
            k
            for k in self.list_keys(ARCHIVE_PREFIX)
            if k.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
        ]
        return next_dream_number_from_names(names)

    def read_status(self) -> dict[str, Any]:
        return self.get_json(STATUS_KEY) or {}

    # -- outcome writers -----------------------------------------------------

    def publish_frame(
        self,
        *,
        dream_id: str,
        image: Image.Image,
        sidecar: Mapping[str, Any],
        status: Mapping[str, Any],
    ) -> dict[str, str]:
        """Archive PNG + public WebP + status. Pointer moves."""
        archive_png = f"{ARCHIVE_PREFIX}{dream_id}.png"
        archive_json = f"{ARCHIVE_PREFIX}{dream_id}.json"
        self.put_bytes(archive_png, encode_archive_png(image), content_type="image/png")
        self.put_json(archive_json, sidecar)
        self.put_bytes(
            CURRENT_IMAGE_KEY, encode_current_webp(image), content_type="image/webp"
        )
        self.put_json(CURRENT_JSON_KEY, sidecar)
        status_out = dict(status)
        status_out["current"] = "current.webp"
        status_out["archive_key"] = archive_png
        if self.cfg.public_base_url:
            status_out["current_url"] = self.cfg.public_url(CURRENT_IMAGE_KEY)
        self.put_json(STATUS_KEY, status_out)
        return {
            "archive_png": archive_png,
            "archive_json": archive_json,
            "current": CURRENT_IMAGE_KEY,
            "status": STATUS_KEY,
        }

    def publish_hold(self, status: Mapping[str, Any]) -> dict[str, str]:
        """Weather silence / gate hold — status only; leave current.webp untouched.

        The pointer stays on the last successful dream (`current.webp`), so the
        public URL is refreshed to match — a hold must never keep a stale
        signal_lost URL from the previous hour.
        """
        status_out = dict(status)
        if self.cfg.public_base_url:
            if status_out.get("current") == "current.webp":
                status_out["current_url"] = self.cfg.public_url(CURRENT_IMAGE_KEY)
            else:
                status_out.pop("current_url", None)
        self.put_json(STATUS_KEY, status_out)
        return {"status": STATUS_KEY}

    def publish_signal_lost(
        self,
        *,
        image: Image.Image,
        status: Mapping[str, Any],
    ) -> dict[str, str]:
        """Channel dead — noise field as current pointer."""
        self.put_bytes(
            SIGNAL_LOST_KEY, encode_current_webp(image), content_type="image/webp"
        )
        status_out = dict(status)
        status_out["current"] = "signal_lost.webp"
        if self.cfg.public_base_url:
            status_out["current_url"] = self.cfg.public_url(SIGNAL_LOST_KEY)
        self.put_json(STATUS_KEY, status_out)
        return {"signal_lost": SIGNAL_LOST_KEY, "status": STATUS_KEY}


def save_local_publish(
    *,
    image: Image.Image,
    sidecar: Mapping[str, Any],
    status: Mapping[str, Any],
    dream_id: str,
    public_dir: Path,
    archive_dir: Path,
) -> None:
    """Mirror R2 layout on disk (dev / Modal scratch before upload)."""
    from dream.sidecar import write_sidecar

    archive_dir.mkdir(parents=True, exist_ok=True)
    public_dir.mkdir(parents=True, exist_ok=True)

    image.convert("RGB").save(archive_dir / f"{dream_id}.png", format="PNG", optimize=True)
    write_sidecar(archive_dir / f"{dream_id}.json", sidecar)

    image.convert("RGB").save(
        public_dir / "current.webp", format="WEBP", lossless=True, method=6
    )
    write_sidecar(public_dir / "current.json", sidecar)

    status_path = public_dir / "status.json"
    with open(status_path, "w") as f:
        json.dump(dict(status), f, ensure_ascii=False, indent=2)
        f.write("\n")


def save_local_signal_lost(
    *,
    image: Image.Image,
    status: Mapping[str, Any],
    public_dir: Path,
) -> None:
    public_dir.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(
        public_dir / "signal_lost.webp", format="WEBP", lossless=True, method=6
    )
    with open(public_dir / "status.json", "w") as f:
        json.dump(dict(status), f, ensure_ascii=False, indent=2)
        f.write("\n")
