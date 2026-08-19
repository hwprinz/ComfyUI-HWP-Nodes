import random
import server
import logging

try:
    from comfy_extras.nodes_custom_sampler import Noise_RandomNoise
except ImportError:
    Noise_RandomNoise = None

# ANSI color helpers
_P = "\033[38;5;141m[HWP Seed Node]\033[38;5;41m "
_R = "\033[0m"

def _log(msg, verbose=False, is_verbose=False):
    """Print a log line. If is_verbose=True, only prints when verbose=True."""
    if is_verbose and not verbose:
        return
    logging.info(f"{_P}{msg}{_R}")


# Default ceiling for random / wrap-around when max_seed is left at 0.
# Matches HWP_MAX_SEED in web/seed_node.js and the global node.
_DEFAULT_MAX_SEED = 1125899906842624

# Seed actions available on the local node (single output, so no
# "for each node" variants).
_ACTIONS = ("fixed", "increment", "decrement", "randomize")


def advance_seed(base, action, max_seed):
    """Return the value obtained by applying `action` to `base` once.

    This is the single source of truth for both the seed used at run time
    (in before-generate mode) and the value stored for the next run. It is
    pure — it never mutates its inputs — so calling it twice with the same
    arguments always yields the same result.
    """
    max_val = max_seed if max_seed > 0 else _DEFAULT_MAX_SEED
    if action == "increment":
        value = base + 1
        if value > max_val:
            value = 0
    elif action == "decrement":
        value = base - 1
        if value < 0:
            value = max_val
    elif action == "randomize":
        value = random.randint(0, max_val)
    else:  # fixed
        value = base
    return value


# Tracks the last dispatched seed per node across runs for changed/unchanged
# detection (mirrors the global node's _last_dispatched_seed, but keyed per
# node since a graph may hold several HWPSeedNode instances).
_last_dispatched_seeds = {}


def on_prompt(json_data):
    """Advance each HWPSeedNode's value across runs and mirror it to the UI.

    Fully independent of the global CustomGlobalSeed node: it only touches
    HWPSeedNode instances and never rewrites any other node's seed input, so
    the two nodes can coexist in one workflow.

    The seed reaches wired nodes through execute()'s return value (the
    downstream node's `seed` input is a link to this node); on_prompt only
    advances the stored widget value and mirrors it to the UI.
    """
    try:
        for node_id, v in json_data['prompt'].items():
            if v.get('class_type') != 'HWPSeedNode':
                continue

            base    = v['inputs'].get('value', 0)
            action  = v['inputs'].get('action', 'fixed')
            max_s   = v['inputs'].get('max_seed', 0)
            mode    = v['inputs'].get('mode', True)
            verbose = v['inputs'].get('logging', False)

            _log(f"Found HWPSeedNode: {node_id}", verbose, is_verbose=True)
            _log(f"Settings - mode: {mode}, action: {action}, value: {base}, max_seed: {max_s}",
                 verbose, is_verbose=True)

            next_value = advance_seed(base, action, max_s)
            # before-generate: this run already uses the advanced value
            # after-generate:  this run uses the current value; the advanced
            #                  one is prepared for the next queue
            used_seed = next_value if mode else base

            prev_seed = _last_dispatched_seeds.get(node_id)
            seed_changed = (prev_seed is not None) and (used_seed != prev_seed)
            _last_dispatched_seeds[node_id] = used_seed
            state_word = "updated" if seed_changed else "unchanged"

            # Count distinct downstream nodes wired to this node's outputs
            # (slot 0 = seed, slot 1 = noise), mirroring the global node's
            # "n node(s)" report. A wired input in the prompt is [node_id, slot].
            wired_nodes = set()
            for other_id, other in json_data['prompt'].items():
                if other_id == node_id:
                    continue
                for inp in (other.get('inputs') or {}).values():
                    # A wired input is [node_id, slot]; slot is always an int.
                    if (isinstance(inp, (list, tuple)) and len(inp) == 2
                            and str(inp[0]) == str(node_id) and isinstance(inp[1], int)):
                        wired_nodes.add(other_id)
            node_count = len(wired_nodes)

            _log(f"seed dispatched: {used_seed} -> {node_count} node(s) {state_word}")
            if seed_changed:
                _log(f"last/changed seed was: {prev_seed}")

            try:
                # The client computes the last_seed widget itself (previous
                # seed, only on change — mirrors the global node), so we only
                # push the value to persist for the next run.
                server.PromptServer.instance.send_sync("hwp-seed-node", {
                    "id": node_id,
                    "value": next_value,
                    "node_count": node_count,
                    "logging": verbose,
                })
            except Exception as e:
                _log(f"send_sync error: {e}")
    except Exception as e:
        _log(f"on_prompt error: {e}")
        import traceback
        traceback.print_exc()

    # on_prompt handlers are chained: server.py reassigns json_data to whatever
    # we return, so we MUST return it (possibly modified) or downstream handlers
    # (e.g. inspire-pack) receive None and crash.
    return json_data


class HWPSeedNode:
    """Local seed + noise source.

    Unlike HWP Global Seed, nothing is broadcast: the `seed` and `noise`
    outputs are only applied to the node(s) you wire them to.

    Named ``HWPSeedNode`` (not ``SeedNode``) because ComfyUI core already
    ships a node with the class_type ``SeedNode`` (``comfy_extras.nodes_seed``);
    registering under that name would be silently shadowed by the core node.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            },
            "optional": {
                "mode": ("BOOLEAN", {"default": True, "label_on": "control_before_generate", "label_off": "control_after_generate"}),
                "action": (_ACTIONS,),
                "last_seed": ("STRING", {"default": "", "multiline": False}),
                "max_seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Maximum seed value (0 = default: 1125899906842624)"}),
                "logging": ("BOOLEAN", {"default": False, "label_on": "verbose", "label_off": "default"}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "extra_pnginfo": "EXTRA_PNGINFO",
            }
        }

    RETURN_TYPES = ("INT", "NOISE")
    RETURN_NAMES = ("seed", "noise")
    OUTPUT_NODE = True
    FUNCTION = "execute"
    CATEGORY = "HWP"

    def execute(self, value, mode=True, action="fixed", last_seed="", max_seed=0, logging=False, unique_id=None, extra_pnginfo=None):
        seed = advance_seed(value, action, max_seed) if mode else value
        noise = Noise_RandomNoise(seed) if Noise_RandomNoise is not None else None
        if noise is None:
            _log("NOISE output unavailable - comfy_extras.nodes_custom_sampler.Noise_RandomNoise could not be imported")
        return {"ui": {"text": [str(seed)]}, "result": (seed, noise)}
