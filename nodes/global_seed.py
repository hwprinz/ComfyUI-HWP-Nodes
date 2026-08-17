import random
import server
import logging
from enum import Enum

try:
    from comfy_extras.nodes_custom_sampler import Noise_RandomNoise
except ImportError:
    Noise_RandomNoise = None

# ANSI color helpers
_P = "\033[38;5;141m[HWP Global Seed]\033[38;5;41m "
_R = "\033[0m"

def _log(msg, verbose=False, is_verbose=False):
    """Print a log line. If is_verbose=True, only prints when verbose=True."""
    if is_verbose and not verbose:
        return
    logging.info(f"{_P}{msg}{_R}")

# Tracks the last dispatched seed across runs for changed/unchanged detection
_last_dispatched_seed = None

class SGmode(Enum):
    FIX = 1
    INCR = 2
    DECR = 3
    RAND = 4


class SeedGenerator:
    def __init__(self, base_value, action, max_seed=0):
        self.base_value = base_value
        self.max_seed = max_seed if max_seed > 0 else 1125899906842624

        if action in ("fixed", "increment", "decrement", "randomize"):
            self.action = SGmode.FIX
        elif action == 'increment for each node':
            self.action = SGmode.INCR
        elif action == 'decrement for each node':
            self.action = SGmode.DECR
        elif action == 'randomize for each node':
            self.action = SGmode.RAND

    def next(self):
        seed = self.base_value

        if self.action == SGmode.INCR:
            self.base_value += 1
            if self.base_value > self.max_seed:
                self.base_value = 0
        elif self.action == SGmode.DECR:
            self.base_value -= 1
            if self.base_value < 0:
                self.base_value = self.max_seed
        elif self.action == SGmode.RAND:
            self.base_value = random.randint(0, self.max_seed)

        return seed


def control_seed(v, action, seed_is_global, max_seed=0):
    action = v['inputs']['action'] if seed_is_global else action
    value = v['inputs']['value'] if seed_is_global else v['inputs'].get('seed_num', v['inputs'].get('seed', 0))
    max_seed_val = max_seed if max_seed > 0 else 1125899906842624

    if action in ('increment', 'increment for each node'):
        value = value + 1
        if value > max_seed_val:
            value = 0
    elif action in ('decrement', 'decrement for each node'):
        value = value - 1
        if value < 0:
            value = max_seed_val
    elif action in ('randomize', 'randomize for each node'):
        value = random.randint(0, max_seed_val)

    if seed_is_global:
        v['inputs']['value'] = value

    return value


def prompt_seed_update(json_data):
    try:
        seed_widget_map = json_data['extra_data']['extra_pnginfo']['workflow']['seed_widgets']
    except:
        seed_widget_map = {}

    value = None
    mode = None
    node = None
    action = None
    max_seed = 0
    seed_is_global = False
    verbose = False

    for k, v in json_data['prompt'].items():
        if 'class_type' not in v:
            continue

        if v['class_type'] == 'CustomGlobalSeed':
            mode = v['inputs']['mode']
            action = v['inputs']['action']
            value = v['inputs']['value']
            max_seed = v['inputs'].get('max_seed', 0)
            verbose = v['inputs'].get('logging', False)
            node = k, v
            seed_is_global = True
            _log(f"Found CustomGlobalSeed node: {k}", verbose, is_verbose=True)
            _log(f"Settings - mode: {mode}, action: {action}, value: {value}, max_seed: {max_seed}", verbose, is_verbose=True)
            break

    if not seed_is_global:
        _log("no GlobalSeed node in workflow, skipping")
        return None, False

    used_seed = value

    if mode is not None and mode:
        used_seed = control_seed(node[1], action, seed_is_global, max_seed)
        _log(f"control_before_generate - new value: {used_seed}", verbose, is_verbose=True)

    nodes_updated = 0
    seed_generator = SeedGenerator(used_seed, action, max_seed)

    for k, v in json_data['prompt'].items():
        for k2, v2 in v['inputs'].items():
            if isinstance(v2, str) and '$GlobalSeed.value$' in v2:
                v['inputs'][k2] = v2.replace('$GlobalSeed.value$', str(used_seed))

        if 'seed_num' in v['inputs'] and isinstance(v['inputs']['seed_num'], int):
            old = v['inputs']['seed_num']
            v['inputs']['seed_num'] = seed_generator.next()
            _log(f"Updated seed_num in node {k}: {old} -> {v['inputs']['seed_num']}", verbose, is_verbose=True)
            nodes_updated += 1

        if 'seed' in v['inputs'] and isinstance(v['inputs']['seed'], int):
            old = v['inputs']['seed']
            v['inputs']['seed'] = seed_generator.next()
            _log(f"Updated seed in node {k}: {old} -> {v['inputs']['seed']}", verbose, is_verbose=True)
            nodes_updated += 1

        if 'noise_seed' in v['inputs'] and isinstance(v['inputs']['noise_seed'], int):
            old = v['inputs']['noise_seed']
            v['inputs']['noise_seed'] = seed_generator.next()
            _log(f"Updated noise_seed in node {k}: {old} -> {v['inputs']['noise_seed']}", verbose, is_verbose=True)
            nodes_updated += 1

    if mode is not None and not mode:
        control_seed(node[1], action, seed_is_global, max_seed)
        _log("control_after_generate - next seed prepared", verbose, is_verbose=True)

    global _last_dispatched_seed
    seed_changed = (_last_dispatched_seed is not None) and (used_seed != _last_dispatched_seed)
    prev_seed = _last_dispatched_seed
    _last_dispatched_seed = used_seed
    state_word = "updated" if seed_changed else "unchanged"
    _log(f"seed dispatched: {used_seed} -> {nodes_updated} node(s) {state_word}")
    if seed_changed:
        _log(f"last/changed seed was: {prev_seed}")

    return used_seed, verbose


def workflow_seed_update(json_data, used_seed, verbose):
    try:
        nodes = json_data['extra_data']['extra_pnginfo']['workflow']['nodes']
        seed_widget_map = json_data['extra_data']['extra_pnginfo']['workflow'].get('seed_widgets', {})
        prompt = json_data['prompt']

        updated_seed_map = {}
        next_value = None
        global_seed_node_id = None

        for node in nodes:
            node_id = str(node['id'])
            if node_id in prompt:
                if node['type'] == 'CustomGlobalSeed':
                    next_value = prompt[node_id]['inputs']['value']
                    global_seed_node_id = node_id
                    if len(node.get('widgets_values', [])) > 0:
                        node['widgets_values'][0] = next_value
                        if len(node['widgets_values']) > 3:
                            node['widgets_values'][3] = str(used_seed)
                elif node_id in seed_widget_map:
                    widget_idx = seed_widget_map[node_id]
                    if 'seed_num' in prompt[node_id]['inputs']:
                        seed = prompt[node_id]['inputs']['seed_num']
                    elif 'noise_seed' in prompt[node_id]['inputs']:
                        seed = prompt[node_id]['inputs']['noise_seed']
                    elif 'seed' in prompt[node_id]['inputs']:
                        seed = prompt[node_id]['inputs']['seed']
                    else:
                        continue

                    if widget_idx < len(node.get('widgets_values', [])):
                        node['widgets_values'][widget_idx] = seed
                    updated_seed_map[node_id] = seed

        if global_seed_node_id:
            _log(f"Sending update - Node: {global_seed_node_id}, used_seed: {used_seed}, next_value: {next_value}, Seeds: {updated_seed_map}", verbose, is_verbose=True)
            try:
                server.PromptServer.instance.send_sync("custom-global-seed", {
                    "id": global_seed_node_id,
                    "value": next_value,
                    "seed_map": updated_seed_map,
                    "logging": verbose
                })
                _log("send_sync called successfully", verbose, is_verbose=True)
            except Exception as e:
                _log(f"send_sync error: {e}")
    except Exception as e:
        _log(f"workflow_seed_update error: {e}")


def onprompt(json_data):
    try:
        used_seed, verbose = prompt_seed_update(json_data)
        if used_seed is not None:
            workflow_seed_update(json_data, used_seed, verbose)
    except Exception as e:
        _log(f"onprompt error: {e}")
        import traceback
        traceback.print_exc()

    return json_data


class CustomGlobalSeed:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            },
            "optional": {
                "mode": ("BOOLEAN", {"default": True, "label_on": "control_before_generate", "label_off": "control_after_generate"}),
                "action": (["fixed", "increment", "decrement", "randomize", "increment for each node", "decrement for each node", "randomize for each node"],),
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

    # 'logging' must match the input key; it shadows the module import, which is
    # fine here because execute() only logs via _log().
    def execute(self, value, mode=True, action="fixed", last_seed="", max_seed=0, logging=False, unique_id=None, extra_pnginfo=None):
        noise = Noise_RandomNoise(value) if Noise_RandomNoise is not None else None
        if noise is None:
            _log("NOISE output unavailable - comfy_extras.nodes_custom_sampler.Noise_RandomNoise could not be imported")
        return {"ui": {"text": [str(value)]}, "result": (value, noise)}