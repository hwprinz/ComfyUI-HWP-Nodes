"""
ComfyUI Custom Node - Get Side from Latent
Takes a latent as input and returns either the longest or shortest
pixel-space dimension, selected via a toggle.

The computed value is also shown below the node after a run
(bare number, like the built-in "Get Image Size" node).
"""

import server


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
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    def get_side(self, latent, side, unique_id):
        # latent["samples"] shape is (batch, channels, height, width)
        # multiply by 8 to get pixel-space dimensions
        samples = latent["samples"]
        height = samples.shape[2] * 8
        width  = samples.shape[3] * 8
        side_value = max(width, height) if side else min(width, height)

        # Show the bare value below the node (needs recent ComfyUI; older
        # versions simply skip it instead of erroring)
        if hasattr(server.PromptServer.instance, "send_progress_text"):
            server.PromptServer.instance.send_progress_text(str(side_value), unique_id)

        return (side_value,), {"result": side_value}


NODE_CLASS_MAPPINGS = {
    "GetSideFromLatent": GetSideFromLatent,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GetSideFromLatent": "HWP Get Side (Latent)",
}
