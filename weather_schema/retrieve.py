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

INDEX_VERSION = 2

# Same threshold as config curation.night_solar_elevation_deg / brief night bucket.
DEFAULT_NIGHT_SOLAR_ELEVATION_DEG = -6.0


def is_night_elevation(
    solar_elevation: float,
    *,
    night_solar_elevation_deg: float = DEFAULT_NIGHT_SOLAR_ELEVATION_DEG,
) -> bool:
    """True when elev is on the night/twilight side of the curation boundary."""
    return float(solar_elevation) < float(night_solar_elevation_deg)


@dataclass(frozen=True)
class IndexEntry:
    filename: str
    month: int
    feature_vector: list[float | None]
    prompt: str | None = None
    solar_elevation: float | None = None


class WeatherNNIndex:
    """Season- and day/night-gated weighted-Euclidean NN over archive vectors."""

    def __init__(
        self,
        entries: Sequence[IndexEntry],
        *,
        theta_shore_deg: float = DEFAULT_THETA_SHORE_DEG,
        night_solar_elevation_deg: float = DEFAULT_NIGHT_SOLAR_ELEVATION_DEG,
    ) -> None:
        self.entries = list(entries)
        self.theta_shore_deg = theta_shore_deg
        self.night_solar_elevation_deg = float(night_solar_elevation_deg)
        self.weights = list(FEATURE_WEIGHTS)

    def __len__(self) -> int:
        return len(self.entries)

    @classmethod
    def build_from_captions(
        cls,
        captions_path: Path | str,
        *,
        night_solar_elevation_deg: float = DEFAULT_NIGHT_SOLAR_ELEVATION_DEG,
    ) -> WeatherNNIndex:
        """Build index from caption JSONL (preferred — reuses stored vectors)."""
        path = Path(captions_path)
        entries: list[IndexEntry] = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                elev = row.get("solar_elevation")
                entries.append(
                    IndexEntry(
                        filename=row["filename"],
                        month=int(row["month"]),
                        feature_vector=row["feature_vector"],
                        prompt=row.get("prompt"),
                        solar_elevation=None if elev is None else float(elev),
                    )
                )
        return cls(entries, night_solar_elevation_deg=night_solar_elevation_deg)

    @classmethod
    def build_from_weather(
        cls,
        weather_dir: Path | str,
        *,
        curated_paths: Sequence[Path | str],
        theta_shore_deg: float = DEFAULT_THETA_SHORE_DEG,
        night_solar_elevation_deg: float = DEFAULT_NIGHT_SOLAR_ELEVATION_DEG,
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
                    elev = pkt.get("solar_elevation")
                    entries.append(
                        IndexEntry(
                            filename=fn,
                            month=int(pkt["month"]),
                            feature_vector=vals,
                            solar_elevation=None if elev is None else float(elev),
                        )
                    )
                    seen.add(fn)
        return cls(
            entries,
            theta_shore_deg=theta_shore_deg,
            night_solar_elevation_deg=night_solar_elevation_deg,
        )

    def _season_allowed(
        self, query_month: int, anchor_month: int, *, widen: bool
    ) -> bool:
        q = season_token(query_month)
        a = season_token(anchor_month)
        if not widen:
            return a == q
        return a in season_family(query_month)

    def _night_allowed(
        self, query_elevation: float | None, entry_elevation: float | None
    ) -> bool:
        """Hard day/night gate (§4.3) — never cross the curation boundary."""
        if query_elevation is None or entry_elevation is None:
            # Incomplete elev: keep candidate only for day-side queries so a
            # night packet cannot latch onto an unlabelled dawn frame.
            if query_elevation is None:
                return True
            return not is_night_elevation(
                query_elevation,
                night_solar_elevation_deg=self.night_solar_elevation_deg,
            )
        return is_night_elevation(
            query_elevation,
            night_solar_elevation_deg=self.night_solar_elevation_deg,
        ) == is_night_elevation(
            entry_elevation,
            night_solar_elevation_deg=self.night_solar_elevation_deg,
        )

    def query(
        self,
        pkt: Mapping[str, Any],
        k: int = 5,
        *,
        include_prompt: bool = False,
        exclude: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Return top-k same-season, same-day/night anchors by weighted distance.

        Same-season candidates are preferred. If that pool has fewer than `k`
        entries, widen to the adjacent season family (§4.3 thin-pool rule).
        Day/night is a hard gate (elev ↔ `night_solar_elevation_deg`); thin
        night pools do **not** widen into day.
        `exclude` drops candidate filenames (leave-one-out for held-out eval).
        """
        if k <= 0:
            return []

        query_month = int(pkt["month"])
        raw_elev = pkt.get("solar_elevation")
        query_elev = None if raw_elev is None else float(raw_elev)
        q_vals, _ = feature_vector(pkt, theta_shore_deg=self.theta_shore_deg)
        excluded = exclude or set()

        def _score(*, widen: bool) -> list[tuple[float, IndexEntry]]:
            scored: list[tuple[float, IndexEntry]] = []
            for entry in self.entries:
                if entry.filename in excluded:
                    continue
                if not self._season_allowed(query_month, entry.month, widen=widen):
                    continue
                if not self._night_allowed(query_elev, entry.solar_elevation):
                    continue
                dist = weighted_distance(q_vals, entry.feature_vector, self.weights)
                scored.append((dist, entry))
            scored.sort(key=lambda item: item[0])
            return scored

        scored = _score(widen=False)
        if len(scored) < k:
            scored = _score(widen=True)

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
            "night_solar_elevation_deg": self.night_solar_elevation_deg,
            "entries": [
                {
                    "filename": e.filename,
                    "month": e.month,
                    "feature_vector": e.feature_vector,
                    **(
                        {"solar_elevation": e.solar_elevation}
                        if e.solar_elevation is not None
                        else {}
                    ),
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
        version = payload.get("version")
        if version not in (1, INDEX_VERSION):
            raise ValueError(
                f"unsupported index version {version!r}, "
                f"expected 1 or {INDEX_VERSION}"
            )
        entries = [
            IndexEntry(
                filename=row["filename"],
                month=int(row["month"]),
                feature_vector=row["feature_vector"],
                prompt=row.get("prompt"),
                solar_elevation=(
                    None
                    if row.get("solar_elevation") is None
                    else float(row["solar_elevation"])
                ),
            )
            for row in payload["entries"]
        ]
        return cls(
            entries,
            theta_shore_deg=float(
                payload.get("theta_shore_deg", DEFAULT_THETA_SHORE_DEG)
            ),
            night_solar_elevation_deg=float(
                payload.get(
                    "night_solar_elevation_deg", DEFAULT_NIGHT_SOLAR_ELEVATION_DEG
                )
            ),
        )
