"""
ComfyUI Custom Node - Aspect Size
Computes Width and Height from a model's base pixel budget and a free-form
aspect ratio (two integers), then caps the long side at the model family's
maximum and rounds both dimensions UP to multiples of a downscale factor.

Modelled on Drift's "Aspect Size V2" (DJZ-Nodes), with the preset list
renamed/extended so the entries name the models they actually fit:

Preset names must not contain "/" — the combo widget renders it as a submenu.

The pixel budget of the selected model stays constant; only the shape
changes. Every model preset additionally carries a max side in pixels
(0 = uncapped, the generic budgets): at extreme ratios the constant-budget
width grows without bound and models start repeating the content, so the
long side is scaled down to the cap before rounding. Caps:

- SD 1.5         512x512   (0.25 MP)   cap 1024  - 2x native, where duplication starts
- SD 2.1         768x768   (0.56 MP)   cap 1152  - 1.5x native, keeps 768x1152
- SDXL           1024x1024 (1.0 MP)    cap 1536  - documented optimal buckets (1536x640, 2.4:1)
- FLUX.1         1024x1024 (1.0 MP)    cap off   - no documented limit
- SDXL, FLUX     1024x1024 (1.0 MP)    cap 1536  - pre-split alias (existing workflows)
- QWEN           1328x1328 (1.68 MP)   cap 2048  - Qwen-Image/2512. Official specs: native 1328, published size
                                                  list tops at 1664 (16:9 = 1664x928). The cap is measured, not
                                                  documented, and depends on the prompt (at 5:1: 2400 clean with a
                                                  3-field concatenated prompt but duplicated with a single prompt
                                                  field; 2048 clean in both, 2656 = 2x native 1328 always
                                                  duplicates); it is the widest verified-clean width, applied as
                                                  the long-side cap at ALL ratios
- 1440x          1440x1440 (1.98 MP)   cap off
- WAN22          1536x1536 (2.25 MP)   cap 1440  - hosted T2I limit 512-1440 per side
- Qwen2.1        2048x2048 (4.0 MP)    cap 2752  - model card: 2752x1536 widescreen
- Ideogram       2048x2048 (4.0 MP)    cap 2048  - 256-2048 per side, ratios up to 6:1
- Qwen2.1, Ideogram  2048x2048 (4.0 MP)  cap 2048 - pre-split alias (existing workflows)
- 4K             2880x2880 (7.91 MP)   cap off
- 3072x          3072x3072 (9.0 MP)    cap off
- 8K             5760x5760 (31.64 MP)  cap off
- 16K            11520x11520 (126.56 MP) cap off

Pick the downscale factor the model's VAE/patch size requires
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

    # model_type -> (base (square) pixel budget, max side in px, 0 = uncapped).
    # The max side keeps the aspect-ratio math from stretching the long side
    # past what the model family handles: with the budget constant, extreme
    # ratios make the width grow without bound and the model starts repeating
    # the content. Caps are the documented limits per model family, except
    # QWEN, whose cap (2048) is measured rather than documented: the official
    # Qwen-Image/2512 sizes are native 1328 with the published list topping
    # out at 1664 (16:9 = 1664x928); at 5:1, 2400 was clean with a 3-field
    # concatenated prompt but duplicated with a single prompt field, 2048
    # was clean in both, and 2656 = 2x native 1328 always duplicates. 2048
    # (widest verified-clean width) is applied as the long-side cap at ALL
    # ratios - mild ratios never reach the cap anyway. The generic budgets
    # (1440x/4K/3072x/8K/16K) stay uncapped.
    # Names must not contain "/" (combo renders it as a submenu); use ", " instead.
    # The "SDXL, FLUX" and "Qwen2.1, Ideogram" entries are the pre-split names,
    # kept so existing workflows keep working (conservative common cap).
    # ordered by ascending base budget
    MODEL_SPECS = {
        "SD 1.5": (512 * 512, 1024),
        "SD 2.1": (768 * 768, 1152),
        "SDXL": (1024 * 1024, 1536),
        "FLUX.1": (1024 * 1024, 0),
        "SDXL, FLUX": (1024 * 1024, 1536),
        "QWEN": (1328 * 1328, 2048),
        "1440x": (1440 * 1440, 0),
        "WAN22": (1536 * 1536, 1440),
        "Qwen2.1": (2048 * 2048, 2752),
        "Ideogram": (2048 * 2048, 2048),
        "Qwen2.1, Ideogram": (2048 * 2048, 2048),
        "4K": (2880 * 2880, 0),
        "3072x": (3072 * 3072, 0),
        "8K": (5760 * 5760, 0),
        "16K": (11520 * 11520, 0),
    }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_type": (list(cls.MODEL_SPECS), {
                    "tooltip": "Base pixel budget (width × height at 1:1) plus the model family's max side — the aspect ratio only changes the shape, and extreme ratios get scaled down so the long side never exceeds the model's limit.",
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
        if model_type not in self.MODEL_SPECS:
            raise ValueError(f"Unknown model_type: {model_type!r}")
        if aspect_ratio_width < 1 or aspect_ratio_height < 1:
            raise ValueError("aspect ratio factors must be >= 1")
        if downscale_factor < 1:
            raise ValueError("downscale_factor must be >= 1")

        pixels, max_side = self.MODEL_SPECS[model_type]

        # Keep the model's total pixel budget, change only the shape
        ratio = aspect_ratio_width / aspect_ratio_height
        width = math.sqrt(pixels * ratio)
        height = pixels / width

        # Cap the long side: at extreme ratios the constant budget makes the
        # width grow past what the model family handles, and the content
        # starts repeating. Mild ratios never reach the cap.
        capped = False
        if max_side > 0 and max(width, height) > max_side:
            # Pin the long side to the cap and re-derive the short side from
            # the ratio: exact values land on the rounding grid instead of
            # drifting over it by float error (e.g. SDXL 24:10 -> 640.0000001
            # would round up to 648).
            capped = True
            if width >= height:
                width = max_side
                height = max_side / ratio
            else:
                height = max_side
                width = max_side * ratio

        # Round both dimensions UP to multiples of the downscale factor
        width = math.ceil(width / downscale_factor) * downscale_factor
        height = math.ceil(height / downscale_factor) * downscale_factor
        width, height = int(width), int(height)

        # Show the resolved size below the node after a run (needs recent
        # ComfyUI; older versions simply skip it instead of erroring)
        prompt_server = getattr(server.PromptServer, "instance", None)
        if prompt_server is not None and hasattr(prompt_server, "send_progress_text"):
            prompt_server.send_progress_text(f"{width}x{height} (capped)" if capped else f"{width}x{height}", unique_id)

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
