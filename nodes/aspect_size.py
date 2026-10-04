"""
ComfyUI Custom Node - Aspect Size
Computes Width and Height from a model's base pixel budget and a free-form
aspect ratio (two integers), rounding both dimensions UP to multiples of a
downscale factor.

Modelled on Drift's "Aspect Size V2" (DJZ-Nodes), with the preset list
renamed/extended so the entries name the models they actually fit:

Preset names must not contain "/" — the combo widget renders it as a submenu.

- SD 1.5         512x512   (0.25 MP)
- SD 2.1         768x768   (0.56 MP)
- SDXL, FLUX     1024x1024 (1.0 MP)  SDXL, FLUX.1, SD3, Kolors, HunyuanImage 3.0, Krea 2, ...
- QWEN           1328x1328 (1.68 MP) Qwen-Image / Qwen-Image-2512 (official README table)
- 1440x          1440x1440 (1.98 MP)
- WAN22          1536x1536 (2.25 MP)
- Qwen2.1, Ideogram  2048x2048 (4.0 MP)  Qwen-Image 2.x (native 2K), Ideogram 4 / 4.5, Ming-Image 0.1, Kandinsky Cascade
- 4K             2880x2880 (7.91 MP)
- 3072x          3072x3072 (9.0 MP)
- 8K             5760x5760 (31.64 MP)
- 16K            11520x11520 (126.56 MP)

The pixel budget of the selected model stays constant; only the shape
changes. Pick the downscale factor the model's VAE/patch size requires
(e.g. 16 for FLUX.1 / Qwen-Image 1.x, 32 for Qwen-Image 2.x / GLM-Image).

The optional `model` input (connect the same MODEL chain that feeds your
sampler) switches the latent output to that model's native layout — the
same conversion the built-in KSampler applies (channel count and spatial
downscale are read from the model itself). Custom samplers (e.g. RES4LYF
ClownsharKSampler) do not do that conversion, so on 1/16-VAE models such
as Flux 2 or Qwen-Image 2.x a canonical /8 latent would decode at 2x the
intended size. Unconnected, the latent matches the built-in Empty Latent
Image exactly, which is what the built-in samplers expect.
"""

import math

import server
import torch
import comfy.model_management
import comfy.sample


class HWPAspectSize:
    CATEGORY = "HWP"
    RETURN_TYPES = ("INT", "INT", "LATENT")
    RETURN_NAMES = ("width", "height", "latent")
    FUNCTION = "run"

    # model_type -> base (square) pixel budget.
    # Names must not contain "/" (combo renders it as a submenu); use ", " instead.
    # Several entries share a budget (e.g. "Qwen2.1, Ideogram" covers Qwen-Image 2.x,
    # Ideogram 4 / 4.5, Ming-Image 0.1 and Kandinsky Cascade — all native 2K/2048x2048);
    # the README documents which model lives under which preset.
    # ordered by ascending base budget
    MODEL_PIXELS = {
        "SD 1.5": 512 * 512,
        "SD 2.1": 768 * 768,
        "SDXL, FLUX": 1024 * 1024,
        "QWEN": 1328 * 1328,
        "1440x": 1440 * 1440,
        "WAN22": 1536 * 1536,
        "Qwen2.1, Ideogram": 2048 * 2048,
        "4K": 2880 * 2880,
        "3072x": 3072 * 3072,
        "8K": 5760 * 5760,
        "16K": 11520 * 11520,
    }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_type": (list(cls.MODEL_PIXELS), {
                    "tooltip": "Base pixel budget (width × height at 1:1) — the aspect ratio only changes the shape, the total stays constant.",
                }),
                "aspect_ratio_width": ("INT", {"default": 1, "min": 1, "step": 1, "display": "number",
                    "tooltip": "Aspect ratio, width part (free integer, e.g. 5 for 5:2)."}),
                "aspect_ratio_height": ("INT", {"default": 1, "min": 1, "step": 1, "display": "number",
                    "tooltip": "Aspect ratio, height part (free integer, e.g. 2 for 5:2)."}),
                "downscale_factor": ("INT", {"default": 32, "min": 1, "max": 128, "step": 1, "display": "number",
                    "tooltip": "Both dimensions are rounded UP to multiples of this — pick what the model's VAE/patch size requires (8: SD 1.5 / 2.1 / SDXL, 16: FLUX.1 / SD3 / Qwen-Image 1.x, 32: Qwen-Image 2.x)."}),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 4096, "step": 1, "display": "number",
                    "tooltip": "Batch size of the latent output (1–4096)."}),
            },
            "optional": {
                # The model the latent will be sampled with (same MODEL chain
                # that feeds the sampler, e.g. the LoRA/loader output). When
                # connected, the latent output is built in that model's
                # native layout. Needed for custom samplers (RES4LYF
                # ClownsharKSampler, ...) that do not rescale empty latents
                # the way the built-in KSampler does. Unconnected: the latent
                # matches the built-in Empty Latent Image exactly.
                "model": ("MODEL", {
                    "tooltip": "Optional — the model the latent will be sampled with (same MODEL chain as your sampler). Connect it to get the latent in that model's native layout; needed for custom samplers (e.g. RES4LYF ClownsharKSampler) that do not rescale empty latents themselves.",
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    def run(self, model_type, aspect_ratio_width, aspect_ratio_height, downscale_factor, batch_size, unique_id, model=None):
        if model_type not in self.MODEL_PIXELS:
            raise ValueError(f"Unknown model_type: {model_type!r}")
        if aspect_ratio_width < 1 or aspect_ratio_height < 1:
            raise ValueError("aspect ratio factors must be >= 1")
        if downscale_factor < 1:
            raise ValueError("downscale_factor must be >= 1")

        pixels = self.MODEL_PIXELS[model_type]

        # Keep the model's total pixel budget, change only the shape
        ratio = aspect_ratio_width / aspect_ratio_height
        width = math.sqrt(pixels * ratio)
        height = pixels / width

        # Round both dimensions UP to multiples of the downscale factor
        width = math.ceil(width / downscale_factor) * downscale_factor
        height = math.ceil(height / downscale_factor) * downscale_factor
        width, height = int(width), int(height)

        # Show the resolved size below the node after a run (needs recent
        # ComfyUI; older versions simply skip it instead of erroring)
        prompt_server = getattr(server.PromptServer, "instance", None)
        if prompt_server is not None and hasattr(prompt_server, "send_progress_text"):
            prompt_server.send_progress_text(f"{width}x{height}", unique_id)

        # Also emit a ready-to-use empty LATENT at the resolved size.
        latent = torch.zeros(
            [batch_size, 4, height // 8, width // 8],
            device=comfy.model_management.intermediate_device(),
            dtype=comfy.model_management.intermediate_dtype(),
        )

        if model is None:
            # Match the built-in Empty Latent Image byte-for-byte, including
            # "downscale_ratio_spacial": 8. The built-in KSampler /
            # SamplerCustomAdvanced read that tag (comfy.sample.
            # fix_empty_latent_channels) and rescale the canonical /8 latent
            # to the model's native layout, so this works for every model —
            # as long as the sampler does that conversion itself.
            return (width, height, {"samples": latent, "downscale_ratio_spacial": 8})

        # Model connected: build the model's native layout directly, using
        # the exact conversion the built-in KSampler applies (channel count
        # and spatial ratio are read from the model itself: SD3 / FLUX.1 =
        # 16 ch / 8, Qwen-Image 2.x = 64 ch / 16, Flux 2 = 128 ch / 16, ...).
        # The "downscale_ratio_spacial" tag is dropped: the latent is already
        # native, and a sampler honouring the tag would rescale it a second
        # time.
        fix = getattr(comfy.sample, "fix_empty_latent_channels", None)
        if fix is None:
            print("[HWP Aspect Size] this ComfyUI is too old to convert the latent to the model layout - emitting the canonical /8 latent instead")
            return (width, height, {"samples": latent, "downscale_ratio_spacial": 8})
        try:
            try:
                native = fix(model, latent, 8)
            except TypeError:
                native = fix(model, latent)  # older ComfyUI without the ratio argument
        except Exception as e:
            print(f"[HWP Aspect Size] could not convert the latent to the model layout ({e}) - emitting the canonical /8 latent instead")
            return (width, height, {"samples": latent, "downscale_ratio_spacial": 8})
        return (width, height, {"samples": native})


NODE_CLASS_MAPPINGS = {
    "HWPAspectSize": HWPAspectSize,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HWPAspectSize": "HWP Aspect Size",
}
