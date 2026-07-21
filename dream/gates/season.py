"""Season-lock validator: calibrated CLIP zero-shot (issue #10).

Layer 1 (hard) is already enforced upstream by same-season retrieval (M1). This
is layer 2: a CLIP zero-shot check on the *rendered* frame that trips a refusal
when the output looks like the wrong thermal regime — specifically the
"summer-green February" failure the brief forbids (DREAMBERRY.md §Season ethics,
§Container). The refusal is intentionally **asymmetric**: warm-in-a-cold-season
is refused (climate teleport out of the cold maritime container), while
cold-in-a-warm-season is only a soft warning (dreaming colder stays *within* the
container).

`season_verdict` is pure logic (testable without CLIP); `classify_season` runs
the model lazily.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

__all__ = ["SeasonVerdict", "season_verdict", "expected_coarse_season", "COARSE_SEASONS"]

COARSE_SEASONS = ("winter", "spring", "summer", "autumn")

# Warmth / greenness rank — the axis the container ethic cares about.
_WARMTH = {"winter": 0, "spring": 1, "autumn": 1, "summer": 2}


def expected_coarse_season(month: int) -> str:
    """NL thermal regime by month (winter bleeds into spring; short summer)."""
    m = int(month)
    if m in (12, 1, 2, 3, 4):  # deep + late winter are wintry in NL
        return "winter"
    if m == 5:
        return "spring"
    if m in (6, 7, 8):
        return "summer"
    return "autumn"  # 9, 10, 11


@dataclass(frozen=True)
class SeasonVerdict:
    expected: str
    predicted: str
    action: str  # "pass" | "warn" | "refuse"
    margin: float
    reason: str
    scores: dict[str, float]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def season_verdict(
    scores: Mapping[str, float],
    month: int,
    cfg: Mapping[str, Any],
) -> SeasonVerdict:
    """Decide pass/warn/refuse from coarse-season scores (already calibrated)."""
    expected = expected_coarse_season(month)
    predicted = max(COARSE_SEASONS, key=lambda s: scores.get(s, float("-inf")))
    margin = float(scores.get(predicted, 0.0) - scores.get(expected, 0.0))
    refuse_margin = float(cfg.get("refuse_margin", 0.05))

    warmth_gap = _WARMTH[predicted] - _WARMTH[expected]

    if predicted == expected:
        return SeasonVerdict(
            expected, predicted, "pass", margin, "matches expected regime", dict(scores)
        )
    # Warm hallucination in a cold season → climate teleport → refuse.
    if warmth_gap >= 2 and margin > refuse_margin:
        return SeasonVerdict(
            expected,
            predicted,
            "refuse",
            margin,
            f"warm '{predicted}' in cold '{expected}' season (margin {margin:.3f})",
            dict(scores),
        )
    # Any other mismatch stays within the container → soft warning.
    return SeasonVerdict(
        expected,
        predicted,
        "warn",
        margin,
        f"predicted '{predicted}' vs expected '{expected}'",
        dict(scores),
    )


# --- CLIP inference (lazy) --------------------------------------------------

_MODEL = None
_PROCESSOR = None
_DEVICE = None


def _load_clip(model_id: str, device: str | None = None):
    global _MODEL, _PROCESSOR, _DEVICE
    if _MODEL is not None:
        return _MODEL, _PROCESSOR, _DEVICE
    import torch
    from transformers import CLIPModel, CLIPProcessor

    if device is None:
        if torch.cuda.is_available():
            device = "cuda"
        elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
    _MODEL = CLIPModel.from_pretrained(model_id).to(device).eval()
    _PROCESSOR = CLIPProcessor.from_pretrained(model_id)
    _DEVICE = device
    return _MODEL, _PROCESSOR, _DEVICE


def classify_season(
    image,
    cfg: Mapping[str, Any],
    *,
    calibration: Mapping[str, float] | None = None,
) -> dict[str, float]:
    """CLIP zero-shot coarse-season log-probs (optionally debiased)."""
    import torch

    models = cfg.get("models", {})
    model_id = models.get("clip", "openai/clip-vit-base-patch32")
    template = cfg.get("season_lock", cfg).get(
        "prompt_template", "a photo of a {season} coastal landscape in Newfoundland"
    )
    prompts = [template.format(season=s) for s in COARSE_SEASONS]

    model, processor, device = _load_clip(model_id)
    inputs = processor(
        text=prompts, images=image.convert("RGB"), return_tensors="pt", padding=True
    ).to(device)
    with torch.no_grad():
        out = model(**inputs)
    logits = out.logits_per_image.squeeze(0)
    logprobs = torch.log_softmax(logits, dim=-1).float().cpu().numpy()

    scores = {s: float(logprobs[i]) for i, s in enumerate(COARSE_SEASONS)}
    if calibration:
        scores = {s: scores[s] - float(calibration.get(s, 0.0)) for s in scores}
    return scores
