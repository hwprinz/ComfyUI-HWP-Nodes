"""
ComfyUI Custom Node - Get Side from X/Y
Returns either the longest or shortest of WIDTH and HEIGHT, selected via
a toggle.

The computed value is also shown below the node after a run
(bare number, like the built-in "Get Image Size" node).
"""

import server


class GetSideFromXY:
    CATEGORY = "HWP"
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("side",)
    FUNCTION = "get_side"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width":  ("INT", {"default": 512, "min": 1, "max": 32768}),
                "height": ("INT", {"default": 512, "min": 1, "max": 32768}),
                "side": ("BOOLEAN", {"default": True, "label_on": "longest", "label_off": "shortest"}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    def get_side(self, width, height, side, unique_id):
        side_value = max(width, height) if side else min(width, height)

        # Show the bare value below the node (needs recent ComfyUI; older
        # versions simply skip it instead of erroring)
        if hasattr(server.PromptServer.instance, "send_progress_text"):
            server.PromptServer.instance.send_progress_text(str(side_value), unique_id)

        return (side_value,), {"result": side_value}


NODE_CLASS_MAPPINGS = {
    "GetSideFromXY": GetSideFromXY,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GetSideFromXY": "HWP Get Side (X/Y)",
}
