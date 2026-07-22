"""DINOv2 embeddings + real-frame reference index.

Identity collapse is measured as distance from a generated frame to the *real*
Cloudberry-frame distribution. We embed archive frames once (DINOv2 CLS token,
L2-normalized) into a reference index, then score a generated frame by its mean
cosine distance to the k nearest real neighbors.

The model is imported lazily; only NumPy is needed to load/query a built index.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

_MODEL = None
_PROCESSOR = None
_DEVICE = None


def _load_model(model_id: str, device: str | None = None):
    global _MODEL, _PROCESSOR, _DEVICE
    if _MODEL is not None:
        return _MODEL, _PROCESSOR, _DEVICE
    import torch
    from transformers import AutoImageProcessor, AutoModel

    if device is None:
        if torch.cuda.is_available():
            device = "cuda"
        elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
    _PROCESSOR = AutoImageProcessor.from_pretrained(model_id)
    _MODEL = AutoModel.from_pretrained(model_id).to(device).eval()
    _DEVICE = device
    return _MODEL, _PROCESSOR, _DEVICE


def embed_image(image, model_id: str = "facebook/dinov2-base") -> np.ndarray:
    """L2-normalized DINOv2 CLS embedding for a PIL image."""
    import torch

    model, processor, device = _load_model(model_id)
    inputs = processor(images=image.convert("RGB"), return_tensors="pt").to(device)
    with torch.no_grad():
        out = model(**inputs)
    cls = out.last_hidden_state[:, 0, :].squeeze(0).float().cpu().numpy()
    norm = np.linalg.norm(cls)
    return cls / norm if norm > 0 else cls


@dataclass
class DinoReference:
    """L2-normalized reference embeddings keyed by archive filename."""

    filenames: list[str]
    embeddings: np.ndarray  # (N, D), row-normalized

    def __len__(self) -> int:
        return len(self.filenames)

    def save(self, path: Path | str) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            filenames=np.array(self.filenames, dtype=object),
            embeddings=self.embeddings.astype(np.float32),
        )

    @classmethod
    def load(cls, path: Path | str) -> "DinoReference":
        data = np.load(Path(path), allow_pickle=True)
        return cls(
            filenames=list(data["filenames"]),
            embeddings=data["embeddings"].astype(np.float32),
        )

    def knn_distance(
        self,
        embedding: np.ndarray,
        *,
        k: int = 3,
        exclude: set[str] | None = None,
    ) -> tuple[float, list[str]]:
        """Mean cosine distance (1 - cos) to the k nearest real neighbors.

        `exclude` drops filenames (leave-one-out for held-out eval).
        """
        excluded = exclude or set()
        mask = np.array(
            [fn not in excluded for fn in self.filenames], dtype=bool
        )
        if not mask.any():
            return float("nan"), []
        embs = self.embeddings[mask]
        names = [fn for fn, m in zip(self.filenames, mask) if m]
        sims = embs @ embedding  # both L2-normalized → cosine similarity
        dists = 1.0 - sims
        order = np.argsort(dists)[: max(1, k)]
        nearest = [names[i] for i in order]
        return float(np.mean(dists[order])), nearest
