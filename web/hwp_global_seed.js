import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// ---------------------------------------------------------------------------
// Helper: retrieve a LiteGraph node by id, nodes2.0 safe
// ---------------------------------------------------------------------------
function getNode(id) {
    try {
        return app.graph?.getNodeById(Number(id)) ?? null;
    } catch (e) {
        console.warn("[HWP Global Seed] getNode error:", e);
        return null;
    }
}

// ---------------------------------------------------------------------------
// Helper: find a named widget, null-safe
// ---------------------------------------------------------------------------
function findWidget(node, ...names) {
    if (!node?.widgets) return null;
    for (const name of names) {
        const w = node.widgets.find(w => w.name === name);
        if (w) return w;
    }
    return null;
}

// ---------------------------------------------------------------------------
// Helper: set widget value and trigger redraw (nodes2.0 safe)
// ---------------------------------------------------------------------------
function setWidgetValue(widget, value) {
    if (!widget) return;
    widget.value = value;
    app.graph?.setDirtyCanvas(true, true);
}

// ---------------------------------------------------------------------------
// Max seed value — must match __init__.py (1125899906842624)
// Intentionally lower than 0xffffffffffffffff to stay within JS safe integer
// range (Number.MAX_SAFE_INTEGER ~= 9 quadrillion).
// ---------------------------------------------------------------------------
const HWP_MAX_SEED = 1125899906842624;

function randomSeed(maxSeed) {
    const max = (maxSeed && maxSeed > 0) ? maxSeed : HWP_MAX_SEED;
    return Math.floor(Math.random() * (max + 1));
}

// ---------------------------------------------------------------------------
// When the button is used we capture the seed that was in value BEFORE the
// new random seed overwrites it. This lets us correctly populate last_seed
// in fixed mode, where the server sends next_value == used_seed (both the
// same number) and can't tell us what the previous seed was.
// null means the last queue was NOT triggered by the button.
// ---------------------------------------------------------------------------
let _previousSeedBeforeButton = null;

// ---------------------------------------------------------------------------
// Tracks the seed that ran most recently. last_seed is only updated when
// the incoming seed differs from this value — so repeated runs of the same
// seed never alter last_seed.
// ---------------------------------------------------------------------------
let _lastKnownSeed = null;

// ---------------------------------------------------------------------------
// Extension
// ---------------------------------------------------------------------------
app.registerExtension({
    name: "HWP.GlobalSeed",

    // -----------------------------------------------------------------------
    // Inject the "🎲 Manual Random Seed" button onto the CustomGlobalSeed node
    // -----------------------------------------------------------------------
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "CustomGlobalSeed") return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            onNodeCreated?.apply(this, arguments);

            this.addWidget(
                "button",
                "🎲 Manual Random Seed",
                "manual_random_seed",
                () => {
                    const valueWidget   = findWidget(this, "value");
                    const maxSeedWidget = findWidget(this, "max_seed");

                    if (valueWidget) {
                        const cap = maxSeedWidget?.value > 0 ? maxSeedWidget.value : HWP_MAX_SEED;
                        const newSeed = randomSeed(cap);
                        // Save the seed that is about to run BEFORE overwriting value.
                        // In fixed mode the server can't tell us the previous seed
                        // because next_value == used_seed, so we capture it here.
                        const previousSeed = valueWidget.value;
                        setWidgetValue(valueWidget, newSeed);
                        _previousSeedBeforeButton = previousSeed;
                        console.log("[HWP Global Seed] Manual random seed →", newSeed, "(previous:", previousSeed, ")");
                        // Defer queue by one tick so widget value is committed
                        // before ComfyUI serializes the prompt
                        setTimeout(() => app.queuePrompt(0), 0);
                    }
                }
            );
        };
    },

    // -----------------------------------------------------------------------
    // Handle server-side seed update events
    // -----------------------------------------------------------------------
    async setup() {
        api.addEventListener("custom-global-seed", ({ detail }) => {
            const { id, value, seed_map, extended_logging } = detail;

            // Track whether the seed changed this run, and what the previous seed was.
            let _seedChanged = false;
            let _prevSeed    = null;

            // ---------------------------------------------------------------
            // Update the HWP Global Seed node itself
            // ---------------------------------------------------------------
            if (id != null && value != null) {
                const node = getNode(id);

                if (node) {
                    const valueWidget    = findWidget(node, "value");
                    const lastSeedWidget = findWidget(node, "last_seed");

                    if (_previousSeedBeforeButton !== null) {
                        // Button-triggered run: seed captured before button overwrote value.
                        // Only update last_seed if it actually differs.
                        const prevSeed = _previousSeedBeforeButton;
                        _previousSeedBeforeButton = null;
                        if (prevSeed !== value) {
                            _seedChanged = true;
                            _prevSeed    = prevSeed;
                            if (lastSeedWidget) lastSeedWidget.value = String(prevSeed);
                        }
                        if (valueWidget) setWidgetValue(valueWidget, value);
                        _lastKnownSeed = value;
                    } else {
                        // Normal run: only update last_seed when seed actually changed.
                        const seedChanged = (_lastKnownSeed !== null) && (value !== _lastKnownSeed);
                        if (seedChanged) {
                            _seedChanged = true;
                            _prevSeed    = _lastKnownSeed;
                            if (lastSeedWidget) lastSeedWidget.value = String(_lastKnownSeed);
                        }
                        if (valueWidget) setWidgetValue(valueWidget, value);
                        _lastKnownSeed = value;
                    }

                    if (extended_logging) {
                        console.log("[HWP Global Seed] global seed node updated:", node);
                    }
                } else {
                    console.warn("[HWP Global Seed] global seed node not found (id=" + id + ")");
                }
            }

            // ---------------------------------------------------------------
            // Update all sampler nodes in seed_map
            // ---------------------------------------------------------------
            if (seed_map) {
                for (const [nodeId, seedValue] of Object.entries(seed_map)) {
                    const node = getNode(nodeId);
                    if (node) {
                        const seedWidget = findWidget(node, "seed", "seed_num", "noise_seed");
                        if (seedWidget) {
                            setWidgetValue(seedWidget, seedValue);
                            if (extended_logging) {
                                console.log(`[HWP Global Seed] node ${nodeId} ${seedWidget.name} →`, seedValue);
                            }
                        } else {
                            console.warn(`[HWP Global Seed] no seed widget on node ${nodeId}`);
                        }
                    } else {
                        console.warn(`[HWP Global Seed] node not found (id=${nodeId})`);
                    }
                }
            }

            // ---------------------------------------------------------------
            // Minimal log — one line always, second line only when seed changed
            // ---------------------------------------------------------------
            const nodeCount = 1 + (seed_map ? Object.keys(seed_map).length : 0);
            const stateWord = _seedChanged ? "updated" : "unchanged";
            console.log(`[HWP Global Seed] seed dispatched: ${value} -> ${nodeCount} node(s) ${stateWord}`);
            if (_seedChanged) {
                console.log(`[HWP Global Seed] last/changed seed was: ${_prevSeed}`);
            }

            app.graph?.setDirtyCanvas(true, true);
        });
    }
});
