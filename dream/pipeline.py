"""SDXL + ControlNet + IP-Adapter dream engine (brief §3, issue #7).

Dial-0 lock: a weather-nearest real frame is the img2img init; ControlNet
(depth + soft-edge) from the canonical geometry frame holds the rocks / horizon /
cabin edge; IP-Adapter carries the anchor's atmosphere. LoRA is an optional
mid-dial identity reservoir (follow-on) — not the lock.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from PIL import Image, ImageFilter

from dream.anchor import Anchor, select_anchor
from dream.sidecar import build_sidecar
from dream.config import (
    apply_edge_crop,
    canonical_frame_path,
    resolve_device,
    resolve_dtype,
    resolve_path,
)
from dream.controls import build_control_images
from dream.dial import DEFAULT_DIAL, DialParams, dial_schedule


@dataclass
class DreamResult:
    image: Image.Image
    sidecar: dict[str, Any]


def _seeded_defocus(image: Image.Image, strength: float) -> Image.Image:
    """Deliberate defocus for high-dial dissolve (brief §5). No-op at strength 0."""
    if strength <= 0:
        return image
    max_radius = 18.0
    radius = max_radius * float(strength)
    blurred = image.filter(ImageFilter.GaussianBlur(radius=radius))
    return Image.blend(image, blurred, alpha=min(1.0, float(strength)))


class DreamEngine:
    """Lazy-loaded SDXL control stack. Build once, generate many."""

    def __init__(self, dream_cfg: dict[str, Any]):
        self.cfg = dream_cfg
        self.models = dream_cfg["models"]
        self.gen = dream_cfg["generation"]
        self.runtime = dream_cfg["runtime"]
        self.device = resolve_device(self.runtime.get("device", "auto"))
        self._pipe = None
        self._dtype = None

    def unload(self) -> None:
        """Drop the SDXL stack from VRAM so SUPIR can load (issue #12)."""
        self._pipe = None
        from dream.upscale import unload_torch_cuda

        unload_torch_cuda()

    # -- model loading -------------------------------------------------------

    def load(self) -> None:
        if self._pipe is not None:
            return
        import torch
        from diffusers import (
            AutoencoderKL,
            ControlNetModel,
            StableDiffusionXLControlNetImg2ImgPipeline,
        )

        dtype = resolve_dtype(self.runtime.get("dtype", "auto"), self.device)
        self._dtype = dtype

        cn_depth = ControlNetModel.from_pretrained(
            self.models["controlnet_depth"], torch_dtype=dtype
        )
        cn_edge = ControlNetModel.from_pretrained(
            self.models["controlnet_softedge"], torch_dtype=dtype
        )
        vae = AutoencoderKL.from_pretrained(self.models["vae"], torch_dtype=dtype)

        pipe = StableDiffusionXLControlNetImg2ImgPipeline.from_pretrained(
            self.models["base"],
            controlnet=[cn_depth, cn_edge],
            vae=vae,
            torch_dtype=dtype,
            add_watermarker=False,
        )

        pipe = pipe.to(self.device)
        self._use_ip_adapter = bool(self.runtime.get("use_ip_adapter", True))

        # NOTE (diffusers 0.39): attention slicing is incompatible with IP-Adapter
        # loading — the IP-Adapter weight converter re-instantiates the active
        # SlicedAttnProcessor without slice_size. So slicing is only applied when
        # IP-Adapter is off. VAE slicing is always safe.
        if self.runtime.get("attention_slicing", False) and not self._use_ip_adapter:
            pipe.enable_attention_slicing()
        if self.runtime.get("vae_slicing", True):
            pipe.vae.enable_slicing()

        if self._use_ip_adapter:
            pipe.load_ip_adapter(
                self.models["ip_adapter_repo"],
                subfolder=self.models["ip_adapter_subfolder"],
                weight_name=self.models["ip_adapter_weight"],
            )

        lora_path = self.models.get("lora_path")
        self._has_lora = bool(lora_path)
        if lora_path:
            pipe.load_lora_weights(resolve_path(lora_path))

        pipe.set_progress_bar_config(disable=False)
        self._pipe = pipe

    # -- generation ----------------------------------------------------------

    def generate(
        self,
        pkt: Mapping[str, Any],
        *,
        dial: float = DEFAULT_DIAL,
        seed: int | None = None,
        prompt: str | None = None,
        anchor: Anchor | None = None,
        exclude_anchors: set[str] | None = None,
    ) -> DreamResult:
        import torch

        from weather_schema.compose import compose_prompt

        self.load()
        params = dial_schedule(dial)

        if prompt is None:
            prompt = compose_prompt(pkt)

        if anchor is None:
            anchor = select_anchor(pkt, self.cfg, exclude=exclude_anchors)

        w = int(self.gen["width"])
        h = int(self.gen["height"])
        size = (w, h)

        edge_crop = self.gen.get("edge_crop")
        init_image = Image.open(anchor.path).convert("RGB")
        init_image = apply_edge_crop(init_image, edge_crop)
        init_image = init_image.resize(size, Image.BICUBIC)

        depth_img, edge_img = build_control_images(
            canonical_frame_path(self.cfg),
            size,
            self.gen.get("controls_dir") or self.cfg["paths"]["controls_dir"],
            edge_crop=edge_crop,
        )

        depth_scale = float(self.gen["controlnet_depth_base"]) * params.controlnet_scale
        edge_scale = float(self.gen["controlnet_softedge_base"]) * params.controlnet_scale

        use_ip = getattr(self, "_use_ip_adapter", True)
        if use_ip:
            self._pipe.set_ip_adapter_scale(params.ip_adapter_scale)

        if seed is None:
            seed = 0
        generator = torch.Generator(device="cpu").manual_seed(int(seed))

        call_kwargs: dict[str, Any] = dict(
            prompt=prompt,
            negative_prompt=self.gen.get("negative_prompt"),
            image=init_image,
            control_image=[depth_img, edge_img],
            controlnet_conditioning_scale=[depth_scale, edge_scale],
            strength=params.denoise_strength,
            num_inference_steps=int(self.gen["steps"]),
            guidance_scale=float(self.gen["guidance_scale"]),
            width=w,
            height=h,
            generator=generator,
        )
        if use_ip:
            # IP-Adapter carries the weather anchor's palette/atmosphere.
            call_kwargs["ip_adapter_image"] = init_image

        out = self._pipe(**call_kwargs)
        image = out.images[0]
        image = _seeded_defocus(image, params.defocus_strength)

        sidecar = self._build_sidecar(
            pkt, params, prompt, anchor, seed, size
        )
        return DreamResult(image=image, sidecar=sidecar)

    def _build_sidecar(
        self,
        pkt: Mapping[str, Any],
        params: DialParams,
        prompt: str,
        anchor: Anchor,
        seed: int,
        size: tuple[int, int],
        *,
        validator_scores: Mapping[str, Any] | None = None,
        failure_mode: str | None = None,
    ) -> dict[str, Any]:
        models = dict(self.models)
        models["use_ip_adapter"] = getattr(self, "_use_ip_adapter", True)
        return build_sidecar(
            pkt=pkt,
            params=params,
            prompt=prompt,
            anchor=anchor,
            seed=seed,
            size=size,
            models=models,
            device=self.device,
            dtype=str(self._dtype),
            edge_crop=self.gen.get("edge_crop"),
            validator_scores=validator_scores,
            failure_mode=failure_mode,
        )
