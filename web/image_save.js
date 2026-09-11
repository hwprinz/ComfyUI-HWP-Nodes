import { app } from "../../scripts/app.js";

// ---------------------------------------------------------------------------
// HWP Save Image (Advanced) — client-side niceties
//
// The `ico_sizes` widget only makes sense when `format` is `ico`; leaving it
// visible at all times reads as if the output were always an ICO (or as if
// the field had to be filled in). Hide it until `format` is `ico`. The value
// is still serialized and sent to the backend, where it is simply ignored
// for every other format.
// ---------------------------------------------------------------------------

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
// Extension
// ---------------------------------------------------------------------------
app.registerExtension({
    name: "HWP.ImageSave",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "HWPImageSave") return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            onNodeCreated?.apply(this, arguments);

            const formatWidget = findWidget(this, "format");
            const icoWidget    = findWidget(this, "ico_sizes");
            if (!formatWidget || !icoWidget) return;

            const sync = () => {
                icoWidget.hide = formatWidget.value !== "ico";
                // Legacy frontends don't auto-resize when a widget is hidden;
                // in the new (Lit) frontend this is a harmless no-op.
                try {
                    this.setSize(this.computeSize());
                } catch (e) { /* non-fatal */ }
                app.graph?.setDirtyCanvas(true, true);
            };

            // Re-evaluate whenever the format changes. The callback argument
            // differs between frontend versions (raw value vs. event object),
            // so read formatWidget.value instead of trusting it.
            const oldCallback = formatWidget.callback;
            formatWidget.callback = (...args) => {
                oldCallback?.(...args);
                sync();
            };
            // Initial state: covers freshly created nodes and nodes restored
            // from a workflow file (onNodeCreated runs on load too).
            sync();
        };
    }
});
