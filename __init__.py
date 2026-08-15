import server
import logging

from .nodes.global_seed import (
    CustomGlobalSeed,
    onprompt,
)
from .nodes.get_side_from_latent import GetSideFromLatent
from .nodes.get_side_from_xy import GetSideFromXY

# ---------------------------------------------------------------------------
# Node registration
# ---------------------------------------------------------------------------
NODE_CLASS_MAPPINGS = {
    "CustomGlobalSeed": CustomGlobalSeed,
    "GetSideFromLatent": GetSideFromLatent,
    "GetSideFromXY": GetSideFromXY,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CustomGlobalSeed": "HWP Global Seed",
    "GetSideFromLatent": "HWP Get Side (Latent)",
    "GetSideFromXY": "HWP Get Side (X/Y)",
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

# ---------------------------------------------------------------------------
# Prompt handler
# ---------------------------------------------------------------------------
server.PromptServer.instance.add_on_prompt_handler(onprompt)

# ---------------------------------------------------------------------------
# Registration banner
# ---------------------------------------------------------------------------
logging.info("\033[38;2;255;0;0m[\033[38;2;255;40;0mH\033[38;2;255;80;0mW\033[38;2;255;120;0mP\033[38;2;255;161;0m-\033[38;2;255;201;0mG\033[38;2;255;241;0ml\033[38;2;229;255;0mo\033[38;2;188;255;0mb\033[38;2;148;255;0ma\033[38;2;108;255;0ml\033[38;2;68;255;0m-\033[38;2;27;255;0mS\033[38;2;0;255;13me\033[38;2;0;255;53me\033[38;2;0;255;93md\033[38;2;0;255;134m]\033[38;2;0;255;174m \033[38;2;0;255;214mn\033[38;2;0;255;255mo\033[38;2;0;215;255md\033[38;2;0;175;255me\033[38;2;0;135;255m \033[38;2;0;94;255mv\033[38;2;254;254;255m0\033[38;2;255;255;255m.\033[38;2;255;255;255m9\033[38;2;67;0;255m \033[38;2;107;0;255mr\033[38;2;147;0;255me\033[38;2;187;0;255mg\033[38;2;228;0;255mi\033[38;2;255;0;242ms\033[38;2;255;0;202mt\033[38;2;255;0;162me\033[38;2;255;0;121mr\033[38;2;255;0;81me\033[38;2;255;0;41md\033[38;2;255;0;0m.\033[0m")
