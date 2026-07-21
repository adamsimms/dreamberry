"""Weather nearest-neighbor retrieval index — schema §4."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from weather_schema.buckets import season_token
from weather_schema.vector import (
    DEFAULT_THETA_SHORE_DEG,
    FEATURE_NAMES,
    FEATURE_WEIGHTS,
    feature_vector,
    season_family,
    weighted_distance,
)

INDEX_VERSION = 1


@dataclass(frozen=True)
class IndexEntry:
    filename: str
    month: int
    feature_vector: list[float | None]
    prompt: str | None = None


class WeatherNNIndex:
    """Season-gated weighted-Euclidean NN index over archive feature vectors."""

    def __init__(
        self,
        entries: Sequence[IndexEntry],
        *,
        theta_shore_deg: float = DEFAULT_THETA_SHORE_DEG,
    ) -> None:
        self.entries = list(entries)
        self.theta_shore_deg = theta_shore_deg
        self.weights = list(FEATURE_WEIGHTS)

    def __len__(self) -> int:
        return len(self.entries)

    @classmethod
    def build_from_captions(cls, captions_path: Path | str) -> WeatherNNIndex:
        """Build index from caption JSONL (preferred — reuses stored vectors)."""
        path = Path(captions_path)
        entries: list[IndexEntry] = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                entries.append(
                    IndexEntry(
                        filename=row["filename"],
                        month=int(row["month"]),
                        feature_vector=row["feature_vector"],
                        prompt=row.get("prompt"),
                    )
                )
        return cls(entries)

    @classmethod
    def build_from_weather(
        cls,
        weather_dir: Path | str,
        *,
        curated_paths: Sequence[Path | str],
        theta_shore_deg: float = DEFAULT_THETA_SHORE_DEG,
    ) -> WeatherNNIndex:
        """Rebuild index from weather packets (fallback when captions lack vectors)."""
        weather_path = Path(weather_dir)
        entries: list[IndexEntry] = []
        seen: set[str] = set()

        for curated in curated_paths:
            with open(curated) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    fn = row["filename"]
                    if fn in seen:
                        continue
                    wpath = weather_path / f"{fn}.json"
                    if not wpath.exists():
                        continue
                    with open(wpath) as wf:
                        pkt = json.load(wf)
                    vals, _ = feature_vector(pkt, theta_shore_deg=theta_shore_deg)
                    entries.append(
                        IndexEntry(
                            filename=fn,
                            month=int(pkt["month"]),
                            feature_vector=vals,
                        )
                    )
                    seen.add(fn)
        return cls(entries, theta_shore_deg=theta_shore_deg)

    def _season_allowed(self, query_month: int, anchor_month: int) -> bool:
        allowed = season_family(query_month)
        return season_token(anchor_month) in allowed

    def query(
        self,
        pkt: Mapping[str, Any],
        k: int = 5,
        *,
        include_prompt: bool = False,
    ) -> list[dict[str, Any]]:
        """Return top-k same-season anchors sorted by weighted distance."""
        if k <= 0:
            return []

        query_month = int(pkt["month"])
        q_vals, _ = feature_vector(pkt, theta_shore_deg=self.theta_shore_deg)

        scored: list[tuple[float, IndexEntry]] = []
        for entry in self.entries:
            if not self._season_allowed(query_month, entry.month):
                continue
            dist = weighted_distance(q_vals, entry.feature_vector, self.weights)
            scored.append((dist, entry))

        scored.sort(key=lambda item: item[0])
        results: list[dict[str, Any]] = []
        for dist, entry in scored[:k]:
            row: dict[str, Any] = {
                "filename": entry.filename,
                "distance": dist,
            }
            if include_prompt and entry.prompt is not None:
                row["prompt"] = entry.prompt
            results.append(row)
        return results

    def save(self, path: Path | str) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": INDEX_VERSION,
            "feature_names": list(FEATURE_NAMES),
            "feature_weights": list(FEATURE_WEIGHTS),
            "theta_shore_deg": self.theta_shore_deg,
            "entries": [
                {
                    "filename": e.filename,
                    "month": e.month,
                    "feature_vector": e.feature_vector,
                    **({"prompt": e.prompt} if e.prompt is not None else {}),
                }
                for e in self.entries
            ],
        }
        with open(path, "w") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")

    @classmethod
    def load(cls, path: Path | str) -> WeatherNNIndex:
        with open(path) as f:
            payload = json.load(f)
        if payload.get("version") != INDEX_VERSION:
            raise ValueError(
                f"unsupported index version {payload.get('version')!r}, "
                f"expected {INDEX_VERSION}"
            )
        entries = [
            IndexEntry(
                filename=row["filename"],
                month=int(row["month"]),
                feature_vector=row["feature_vector"],
                prompt=row.get("prompt"),
            )
            for row in payload["entries"]
        ]
        return cls(
            entries,
            theta_shore_deg=float(
                payload.get("theta_shore_deg", DEFAULT_THETA_SHORE_DEG)
            ),
        )
