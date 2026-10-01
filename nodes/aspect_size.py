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
- Qwen2.1, Ming  2048x2048 (4.0 MP)  Qwen-Image 2.x (native 2K), Ming-Image 0.1, Kandinsky Cascade, Ideogram 4
- 4K             2880x2880 (7.91 MP)
- 3072x          3072x3072 (9.0 MP)
- 8K             5760x5760 (31.64 MP)
- 16K            11520x11520 (126.56 MP)

The pixel budget of the selected model stays constant; only the shape
changes. Pick the downscale factor the model's VAE/patch size requires
(e.g. 16 for FLUX.1 / Qwen-Image 1.x, 32 for Qwen-Image 2.x / GLM-Image).
"""

import math

import server


class HWPAspectSize:
    CATEGORY = "HWP"
    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("width", "height")
    FUNCTION = "run"

    # model_type -> base (square) pixel budget.
    # Names must not contain "/" (combo renders it as a submenu); use ", " instead.
    # Several entries share a budget (e.g. "Qwen2.1, Ming" covers Qwen-Image 2.x,
    # Ming-Image 0.1, Kandinsky Cascade and Ideogram 4 — all native 2K/2048x2048);
    # the README documents which model lives under which preset.
    # ordered by ascending base budget
    MODEL_PIXELS = {
        "SD 1.5": 512 * 512,
        "SD 2.1": 768 * 768,
        "SDXL, FLUX": 1024 * 1024,
        "QWEN": 1328 * 1328,
        "1440x": 1440 * 1440,
        "WAN22": 1536 * 1536,
        "Qwen2.1, Ming": 2048 * 2048,
        "4K": 2880 * 2880,
        "3072x": 3072 * 3072,
        "8K": 5760 * 5760,
        "16K": 11520 * 11520,
    }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_type": (list(cls.MODEL_PIXELS),),
                "aspect_ratio_width": ("INT", {"default": 1, "min": 1, "step": 1, "display": "number"}),
                "aspect_ratio_height": ("INT", {"default": 1, "min": 1, "step": 1, "display": "number"}),
                "downscale_factor": ("INT", {"default": 32, "min": 1, "max": 128, "step": 1, "display": "number"}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    def run(self, model_type, aspect_ratio_width, aspect_ratio_height, downscale_factor, unique_id):
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

        return (width, height)


NODE_CLASS_MAPPINGS = {
    "HWPAspectSize": HWPAspectSize,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HWPAspectSize": "HWP Aspect Size",
}
