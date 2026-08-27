import server
import logging
import colorsys
try:
    import tomllib
except ImportError:  # Python < 3.11
    tomllib = None
from pathlib import Path

from .nodes.global_seed import (
    CustomGlobalSeed,
    onprompt,
)
from .nodes.seed_node import (
    HWPSeedNode,
    on_prompt,
)
from .nodes.get_side_from_latent import GetSideFromLatent
from .nodes.get_side_from_xy import GetSideFromXY

# ---------------------------------------------------------------------------
# Node registration
# ---------------------------------------------------------------------------
NODE_CLASS_MAPPINGS = {
    "CustomGlobalSeed": CustomGlobalSeed,
    "HWPSeedNode": HWPSeedNode,
    "GetSideFromLatent": GetSideFromLatent,
    "GetSideFromXY": GetSideFromXY,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CustomGlobalSeed": "HWP Global Seed",
    "HWPSeedNode": "HWP Seed Node",
    "GetSideFromLatent": "HWP Get Side (Latent)",
    "GetSideFromXY": "HWP Get Side (X/Y)",
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

# ---------------------------------------------------------------------------
# Prompt handler
# ---------------------------------------------------------------------------
server.PromptServer.instance.add_on_prompt_handler(onprompt)
server.PromptServer.instance.add_on_prompt_handler(on_prompt)


# ---------------------------------------------------------------------------
# Registration banner
# ---------------------------------------------------------------------------
def _get_version():
    """Read the package version straight from pyproject.toml so the banner
    can never drift from the real version."""
    try:
        if tomllib is None:
            return "unknown"
        with open(Path(__file__).resolve().parent / "pyproject.toml", "rb") as f:
            return tomllib.load(f)["project"]["version"]
    except Exception:
        return "unknown"


__version__ = _get_version()


def _rainbow(text, white=""):
    """Render *text* with a full red → green → blue → red gradient sweep so the
    rainbow always fits the message length. The substring given as *white*
    (the version number) is painted white instead of following the sweep."""
    head, _, tail = text.partition(white) if white else (text, "", "")
    plain_len = max(len(head) + len(tail) - 1, 1)
    idx = 0  # position of this char within the non-white character stream
    out = []
    for part, is_white in ((head, False), (white, True), (tail, False)):
        for ch in part:
            if is_white:
                out.append("\033[38;2;255;255;255m" + ch)
            else:
                r, g, b = (int(c * 255) for c in colorsys.hsv_to_rgb(idx / plain_len, 1, 1))
                out.append(f"\033[38;2;{r};{g};{b}m" + ch)
                idx += 1
    return "".join(out) + "\033[0m"


_node_count = len(NODE_CLASS_MAPPINGS)
_node_word = "node" if _node_count == 1 else "nodes"
logging.info(_rainbow(f"[ComfyUI-HWP] {_node_count} {_node_word} v{__version__} registered.", __version__))
