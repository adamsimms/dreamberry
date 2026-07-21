"""SUPIR upscale to Cloudberry resolution (~4000×3000) — M4 / issue #12.

Gates run on SDXL-native frames (1024×768). Accepted frames are upscaled here
*before* archive PNG / public WebP publish so the window is sharp at full bleed.

Backend:
  - ``supir`` — Fanghua-Yu/SUPIR (no LLaVA; weather prompt is the caption)
  - ``lanczos`` — deterministic resize for tests / CPU-only smoke
  - ``auto`` — SUPIR on CUDA when the code + weights are present, else Lanczos

Default sign is **F** (light degradation / fidelity): dial-0 frames are already
held by ControlNet; we want sharpness without inventing a live-camera look.
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Mapping

from PIL import Image

from dream.config import REPO_ROOT, resolve_path

__all__ = [
    "UpscaleResult",
    "upscale_for_publish",
    "target_size",
    "unload_torch_cuda",
]

log = logging.getLogger(__name__)

# Cloudberry archive native size (DREAMBERRY.md §8).
DEFAULT_TARGET = (4000, 3000)


class UpscaleResult:
    """Upscaled image plus provenance fields for the sidecar."""

    __slots__ = ("image", "meta")

    def __init__(self, image: Image.Image, meta: dict[str, Any]):
        self.image = image
        self.meta = meta


def target_size(dream_cfg: Mapping[str, Any] | None = None) -> tuple[int, int]:
    up = (dream_cfg or {}).get("upscale") or {}
    return (
        int(up.get("target_width", DEFAULT_TARGET[0])),
        int(up.get("target_height", DEFAULT_TARGET[1])),
    )


def unload_torch_cuda() -> None:
    """Free GPU memory before loading SUPIR (dream stack + SUPIR cannot coexist)."""
    try:
        import gc

        import torch

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except Exception:  # noqa: BLE001
        pass


def upscale_for_publish(
    image: Image.Image,
    dream_cfg: Mapping[str, Any],
    *,
    prompt: str | None = None,
    seed: int = 0,
) -> UpscaleResult:
    """Upscale a generated frame to the public/archive target size."""
    up = dict(dream_cfg.get("upscale") or {})
    if not up.get("enabled", True):
        w, h = image.size
        return UpscaleResult(
            image.convert("RGB"),
            {"upscale": {"enabled": False, "width": w, "height": h}},
        )

    tw, th = target_size(dream_cfg)
    backend = str(up.get("backend", "auto")).lower()
    rgb = image.convert("RGB")

    if backend == "auto":
        backend = "supir" if _supir_available(up) else "lanczos"

    err: str | None = None
    if backend == "supir":
        try:
            return _upscale_supir(rgb, up, prompt=prompt, seed=seed, target=(tw, th))
        except Exception as exc:  # noqa: BLE001
            log.exception("SUPIR failed; falling back to Lanczos: %s", exc)
            backend = "lanczos"
            err = f"{type(exc).__name__}: {exc}"

    if backend != "lanczos":
        raise ValueError(f"unknown upscale.backend: {backend}")

    out_img = rgb.resize((tw, th), Image.LANCZOS)
    meta: dict[str, Any] = {
        "upscale": {
            "enabled": True,
            "backend": "lanczos",
            "width": tw,
            "height": th,
            "native_width": rgb.size[0],
            "native_height": rgb.size[1],
        }
    }
    if err:
        meta["upscale"]["supir_error"] = err
    return UpscaleResult(out_img, meta)


def _supir_available(up: Mapping[str, Any]) -> bool:
    try:
        import torch

        if not torch.cuda.is_available():
            return False
    except Exception:  # noqa: BLE001
        return False
    root = _supir_root(up)
    if not (root / "SUPIR" / "util.py").exists():
        return False
    try:
        _resolve_weights(up)
    except FileNotFoundError:
        return False
    return True


def _supir_root(up: Mapping[str, Any]) -> Path:
    env = os.environ.get("SUPIR_ROOT")
    if env:
        return Path(env)
    if up.get("repo_dir"):
        return resolve_path(up["repo_dir"])
    for candidate in (
        Path("/opt/SUPIR"),
        REPO_ROOT / "third_party" / "SUPIR",
    ):
        if (candidate / "SUPIR" / "util.py").exists():
            return candidate
    return Path("/opt/SUPIR")


def _weights_dir(up: Mapping[str, Any]) -> Path:
    if up.get("weights_dir"):
        return resolve_path(up["weights_dir"])
    hf = os.environ.get("HF_HOME") or os.environ.get("HUGGINGFACE_HUB_CACHE")
    if hf:
        return Path(hf) / "supir"
    return REPO_ROOT / "data" / "models" / "supir"


def _resolve_weights(up: Mapping[str, Any]) -> tuple[Path, Path, Path]:
    """Return (sdxl_ckpt, supir_f, supir_q) paths; download if missing and allowed."""
    wdir = _weights_dir(up)
    wdir.mkdir(parents=True, exist_ok=True)

    sdxl_name = up.get("sdxl_ckpt_file", "sd_xl_base_1.0_0.9vae.safetensors")
    f_name = up.get("supir_ckpt_f_file", "SUPIR-v0F.ckpt")
    q_name = up.get("supir_ckpt_q_file", "SUPIR-v0Q.ckpt")
    repo = up.get("ckpt_repo", "camenduru/SUPIR")

    sdxl = wdir / sdxl_name
    ckpt_f = wdir / f_name
    ckpt_q = wdir / q_name

    if up.get("download_weights", True):
        _hf_download(repo, sdxl_name, sdxl)
        _hf_download(repo, f_name, ckpt_f)
        # Q is optional for sign=F; download when requested or already configured.
        if up.get("sign", "F") == "Q" or up.get("download_q", False):
            _hf_download(repo, q_name, ckpt_q)
        elif not ckpt_q.exists():
            # create_SUPIR_model only loads the selected sign; point Q at F.
            ckpt_q = ckpt_f

    missing = [p for p in (sdxl, ckpt_f) if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "SUPIR weights missing: " + ", ".join(str(p) for p in missing)
        )
    if not ckpt_q.exists():
        ckpt_q = ckpt_f
    return sdxl, ckpt_f, ckpt_q


def _hf_download(repo: str, filename: str, dest: Path) -> None:
    if dest.exists():
        return
    from huggingface_hub import hf_hub_download

    log.info("Downloading %s/%s → %s", repo, filename, dest)
    cached = hf_hub_download(repo_id=repo, filename=filename)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if Path(cached).resolve() != dest.resolve():
        shutil.copy2(cached, dest)


def _write_runtime_yaml(
    *,
    template: Path,
    out: Path,
    sdxl: Path,
    ckpt_f: Path,
    ckpt_q: Path,
    use_xformers: bool,
) -> Path:
    text = template.read_text()
    if not use_xformers:
        text = text.replace("softmax-xformers", "softmax")
    # Absolute checkpoint paths (override the authors' private paths).
    import re

    def _set(key: str, value: Path) -> None:
        nonlocal text
        text = re.sub(
            rf"^{key}:\s*.*$",
            f"{key}: {value}",
            text,
            count=1,
            flags=re.M,
        )

    _set("SDXL_CKPT", sdxl)
    _set("SUPIR_CKPT_F", ckpt_f)
    _set("SUPIR_CKPT_Q", ckpt_q)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    return out


def _upscale_supir(
    image: Image.Image,
    up: Mapping[str, Any],
    *,
    prompt: str | None,
    seed: int,
    target: tuple[int, int],
) -> UpscaleResult:
    import sys

    import torch

    unload_torch_cuda()

    root = _supir_root(up)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    # Authors expect CLIP paths as None → auto-download from HF.
    import CKPT_PTH  # type: ignore  # noqa: E402

    CKPT_PTH.LLAVA_CLIP_PATH = None
    CKPT_PTH.LLAVA_MODEL_PATH = None
    CKPT_PTH.SDXL_CLIP1_PATH = None
    CKPT_PTH.SDXL_CLIP2_CKPT_PTH = None

    from SUPIR.util import (  # type: ignore  # noqa: E402
        PIL2Tensor,
        Tensor2PIL,
        convert_dtype,
        create_SUPIR_model,
    )

    sdxl, ckpt_f, ckpt_q = _resolve_weights(up)
    template = root / "options" / "SUPIR_v0.yaml"
    if not template.exists():
        raise FileNotFoundError(f"missing SUPIR config at {template}")

    use_xformers = True
    try:
        import xformers  # noqa: F401
    except Exception:  # noqa: BLE001
        use_xformers = False

    with tempfile.TemporaryDirectory(prefix="dreamberry-supir-") as tmp:
        opt_path = _write_runtime_yaml(
            template=template,
            out=Path(tmp) / "SUPIR_v0.yaml",
            sdxl=sdxl,
            ckpt_f=ckpt_f,
            ckpt_q=ckpt_q,
            use_xformers=use_xformers,
        )

        sign = str(up.get("sign", "F")).upper()
        if sign not in ("F", "Q"):
            raise ValueError(f"upscale.sign must be F or Q, got {sign}")

        model = create_SUPIR_model(str(opt_path), SUPIR_sign=sign)
        if up.get("loading_half_params", True):
            model = model.half()
        if up.get("use_tile_vae", True):
            model.init_tile_vae(
                encoder_tile_size=int(up.get("encoder_tile_size", 512)),
                decoder_tile_size=int(up.get("decoder_tile_size", 64)),
            )
        model.ae_dtype = convert_dtype(str(up.get("ae_dtype", "bf16")))
        model.model.dtype = convert_dtype(str(up.get("diff_dtype", "fp16")))
        device = "cuda"
        model = model.to(device)

        factor = int(up.get("factor", 4))
        min_size = int(up.get("min_size", 1024))
        LQ_img, h0, w0 = PIL2Tensor(image, upsacle=factor, min_size=min_size)
        LQ_img = LQ_img.unsqueeze(0).to(device)[:, :3, :, :]

        # No LLaVA — the dream's weather prompt is the only honest caption.
        captions = [prompt or ""]
        # Restrained aesthetic — avoid "Canon / skin pores" live-camera fiction.
        a_prompt = up.get(
            "a_prompt",
            "photograph, natural outdoor light, sharp rocks and horizon, "
            "authentic wide-angle window view, fine natural detail",
        )
        n_prompt = up.get(
            "n_prompt",
            "painting, illustration, cartoon, CGI, over-smooth, plastic, "
            "watermark, text, people, boats, deformed, lowres, blur",
        )

        samples = model.batchify_sample(
            LQ_img,
            captions,
            num_steps=int(up.get("edm_steps", 50)),
            restoration_scale=float(up.get("s_stage1", -1)),
            s_churn=int(up.get("s_churn", 5)),
            s_noise=float(up.get("s_noise", 1.01)),
            cfg_scale=float(up.get("s_cfg", 4.0)),
            control_scale=float(up.get("s_stage2", 1.0)),
            seed=int(seed),
            num_samples=1,
            p_p=a_prompt,
            n_p=n_prompt,
            color_fix_type=str(up.get("color_fix_type", "Wavelet")),
            linear_CFG=bool(up.get("linear_CFG", True)),
            linear_s_stage2=bool(up.get("linear_s_stage2", False)),
            spt_linear_CFG=float(up.get("spt_linear_CFG", 1.0)),
            spt_linear_s_stage2=float(up.get("spt_linear_s_stage2", 0.0)),
        )
        out = Tensor2PIL(samples[0], h0, w0)

        # Free SUPIR before returning so the next hour can reload the dream stack.
        del model, samples, LQ_img
        unload_torch_cuda()

    tw, th = target
    if out.size != (tw, th):
        out = out.resize((tw, th), Image.LANCZOS)

    return UpscaleResult(
        out.convert("RGB"),
        {
            "upscale": {
                "enabled": True,
                "backend": "supir",
                "sign": sign,
                "factor": factor,
                "edm_steps": int(up.get("edm_steps", 50)),
                "s_cfg": float(up.get("s_cfg", 4.0)),
                "width": tw,
                "height": th,
                "native_width": image.size[0],
                "native_height": image.size[1],
                "supir_size": [w0, h0],
            }
        },
    )
