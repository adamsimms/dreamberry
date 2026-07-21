"""Perceptual metrics for the eval harness (issue #11).

CLIP image-image similarity (is the dream near the real morning?) and LPIPS
(perceptual distance). Both lazy-imported. Horizon stability comes from
dream/gates/horizon.py.
"""

from __future__ import annotations

import numpy as np

_CLIP = None
_CLIP_PROC = None
_CLIP_DEVICE = None
_LPIPS = None
_LPIPS_DEVICE = None


def _load_clip(model_id: str):
    global _CLIP, _CLIP_PROC, _CLIP_DEVICE
    if _CLIP is not None:
        return _CLIP, _CLIP_PROC, _CLIP_DEVICE
    import torch
    from transformers import CLIPModel, CLIPProcessor

    if torch.cuda.is_available():
        device = "cuda"
    elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    _CLIP = CLIPModel.from_pretrained(model_id).to(device).eval()
    _CLIP_PROC = CLIPProcessor.from_pretrained(model_id)
    _CLIP_DEVICE = device
    return _CLIP, _CLIP_PROC, _CLIP_DEVICE


def clip_similarity(
    image_a, image_b, model_id: str = "openai/clip-vit-base-patch32"
) -> float:
    """Cosine similarity of CLIP image embeddings (−1..1)."""
    import torch

    model, processor, device = _load_clip(model_id)
    inputs = processor(
        images=[image_a.convert("RGB"), image_b.convert("RGB")], return_tensors="pt"
    ).to(device)
    with torch.no_grad():
        out = model.get_image_features(pixel_values=inputs["pixel_values"])
        # transformers >=5 returns an output object whose pooler_output is the
        # already-projected CLIP image embedding (image_embeds on older versions).
        if torch.is_tensor(out):
            feats = out
        else:
            feats = getattr(out, "image_embeds", None)
            if feats is None:
                feats = out.pooler_output
    feats = feats / feats.norm(dim=-1, keepdim=True)
    return float((feats[0] @ feats[1]).item())


def _load_lpips(net: str):
    global _LPIPS, _LPIPS_DEVICE
    if _LPIPS is not None:
        return _LPIPS, _LPIPS_DEVICE
    import lpips
    import torch

    if torch.cuda.is_available():
        device = "cuda"
    elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    _LPIPS = lpips.LPIPS(net=net).to(device).eval()
    _LPIPS_DEVICE = device
    return _LPIPS, _LPIPS_DEVICE


def _to_lpips_tensor(image, size, device):
    import torch

    arr = np.asarray(image.convert("RGB").resize(size), dtype=np.float32) / 255.0
    t = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)
    return (t * 2.0 - 1.0).to(device)  # LPIPS expects [-1, 1]


def lpips_distance(image_a, image_b, net: str = "alex") -> float:
    """LPIPS perceptual distance (lower = more similar)."""
    import torch

    model, device = _load_lpips(net)
    size = (256, 256)
    ta = _to_lpips_tensor(image_a, size, device)
    tb = _to_lpips_tensor(image_b, size, device)
    with torch.no_grad():
        d = model(ta, tb)
    return float(d.item())
