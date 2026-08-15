"""
ComfyUI Custom Node - Get Side from Latent
Takes a latent as input and returns either the longest or shortest
pixel-space dimension, selected via a toggle.

Install: Drop this file into ComfyUI/custom_nodes/ and restart ComfyUI.
"""

class GetSideFromLatent:
    CATEGORY = "HWP"
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("side",)
    FUNCTION = "get_side"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "latent": ("LATENT",),
                "side": ("BOOLEAN", {"default": True, "label_on": "longest", "label_off": "shortest"}),
            }
        }

    def get_side(self, latent, side):
        # latent["samples"] shape is (batch, channels, height, width)
        # multiply by 8 to get pixel-space dimensions
        samples = latent["samples"]
        height = samples.shape[2] * 8
        width  = samples.shape[3] * 8
        return (max(width, height) if side else min(width, height),)


NODE_CLASS_MAPPINGS = {
    "GetSideFromLatent": GetSideFromLatent,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GetSideFromLatent": "HWP Get Side (Latent)",
}
