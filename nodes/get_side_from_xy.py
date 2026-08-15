"""
ComfyUI Custom Node - Get Side from X/Y
Returns either the longest or shortest of WIDTH and HEIGHT, selected via
a toggle.

Install: Drop this file into ComfyUI/custom_nodes/ and restart ComfyUI.
"""

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
            }
        }

    def get_side(self, width, height, side):
        return (max(width, height) if side else min(width, height),)


NODE_CLASS_MAPPINGS = {
    "GetSideFromXY": GetSideFromXY,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GetSideFromXY": "HWP Get Side (X/Y)",
}
