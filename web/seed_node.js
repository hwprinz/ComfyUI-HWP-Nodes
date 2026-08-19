import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// ---------------------------------------------------------------------------
// HWP Seed Node (local) — client-side niceties
//
// This is a SEPARATE extension from web/global_seed.js (HWP.GlobalSeed). It
// targets only the local "HWPSeedNode" and listens on the distinct
// "hwp-seed-node" event, so it does not touch the global node's behaviour.
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Helper: retrieve a LiteGraph node by id, nodes2.0 safe
// ---------------------------------------------------------------------------
function getNode(id) {
    try {
        return app.graph?.getNodeById(Number(id)) ?? null;
    } catch (e) {
        console.warn("[HWP Seed Node] getNode error:", e);
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
// Max seed value — must match nodes/seed_node.py (1125899906842624)
// Intentionally lower than 0xffffffffffffffff to stay within JS safe integer
// range (Number.MAX_SAFE_INTEGER ~= 9 quadrillion).
// ---------------------------------------------------------------------------
const HWP_MAX_SEED = 1125899906842624;

function randomSeed(maxSeed) {
    const max = (maxSeed && maxSeed > 0) ? maxSeed : HWP_MAX_SEED;
    return Math.floor(Math.random() * (max + 1));
}

// ---------------------------------------------------------------------------
// last_seed is derived client-side, exactly like the global node: it holds the
// seed from the run BEFORE the current one and is only rewritten when the seed
// actually changed — so the first run (and any run that reuses the same seed)
// leaves it at its default of 0.
//
// The local node is per-instance, so these are maps keyed by node id (a graph
// may hold several HWPSeedNodes).
// ---------------------------------------------------------------------------
const _lastKnownSeed = {};  // node id -> seed that ran most recently
const _prevBeforeButton = {}; // node id -> seed captured just before a manual-random queue

// ---------------------------------------------------------------------------
// Extension
// ---------------------------------------------------------------------------
app.registerExtension({
    name: "HWP.SeedNode",

    // -----------------------------------------------------------------------
    // Inject the "🎲 Manual Random Seed" button onto the local HWPSeedNode
    // -----------------------------------------------------------------------
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "HWPSeedNode") return;

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
                        // Capture the seed that was in value before overwriting it,
                        // so the event handler can store it as last_seed (mirrors the
                        // global node's button capture).
                        _prevBeforeButton[this.id] = valueWidget.value;
                        setWidgetValue(valueWidget, newSeed);
                        console.log("[HWP Seed Node] Manual random seed →", newSeed,
                                    "(previous:", _prevBeforeButton[this.id], ")");
                        // Defer queue by one tick so widget value is committed
                        // before ComfyUI serializes the prompt
                        setTimeout(() => app.queuePrompt(0), 0);
                    }
                }
            );
        };
    },

    // -----------------------------------------------------------------------
    // Handle server-side value updates from nodes/seed_node.py
    // -----------------------------------------------------------------------
    async setup() {
        api.addEventListener("hwp-seed-node", ({ detail }) => {
            const { id, value, node_count, logging: verbose } = detail;
            // Hoisted so the summary log below (outer scope) can read them;
            // set only when the node is found and the seed changed.
            let seedChanged = false;
            let prevSeed    = null;

            if (id != null) {
                const node = getNode(id);
                if (node) {
                    const valueWidget    = findWidget(node, "value");
                    const lastSeedWidget = findWidget(node, "last_seed");

                    // last_seed = the seed from the previous run, written only
                    // when the seed actually changed (mirrors the global node).
                    // First run: _lastKnownSeed[id] is undefined → no write,
                    // so it stays at its default of 0.
                    if (value != null) {
                        if (_prevBeforeButton[id] !== undefined) {
                            const btnPrev = _prevBeforeButton[id];
                            delete _prevBeforeButton[id];
                            if (btnPrev !== value) {
                                seedChanged = true;
                                prevSeed    = btnPrev;
                                if (lastSeedWidget) lastSeedWidget.value = String(btnPrev);
                            }
                        } else if (_lastKnownSeed[id] !== undefined && _lastKnownSeed[id] !== value) {
                            seedChanged = true;
                            prevSeed    = _lastKnownSeed[id];
                            if (lastSeedWidget) lastSeedWidget.value = String(prevSeed);
                        }
                        if (valueWidget) setWidgetValue(valueWidget, value);
                        _lastKnownSeed[id] = value;
                    }

                    if (verbose) {
                        console.log("[HWP Seed Node] node updated:", node);
                    }
                } else {
                    console.warn("[HWP Seed Node] seed node not found (id=" + id + ")");
                }
            }

            const nodeCount = (node_count != null) ? node_count : 0;
            const stateWord = seedChanged ? "updated" : "unchanged";
            console.log(`[HWP Seed Node] seed dispatched: ${value} -> ${nodeCount} node(s) ${stateWord}`);
            if (seedChanged) {
                console.log(`[HWP Seed Node] last/changed seed was: ${prevSeed}`);
            }
            app.graph?.setDirtyCanvas(true, true);
        });
    }
});
