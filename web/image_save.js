import { app } from "../../scripts/app.js";

// ---------------------------------------------------------------------------
// HWP Save Image (Advanced) — client-side niceties
//
// Hide widgets that the selected `format` ignores:
// - `ico_sizes` only makes sense when `format` is `ico` (leaving it visible
//   at all times reads as if the output were always an ICO, or as if the
//   field had to be filled in)
// - `quality` is ignored by `webp (lossless)`, `tiff` and `ico` (lossless /
//   fixed compression) — only png (compression level), jpg and webp use it
//
// The hidden values are still serialized and sent to the backend, where
// they are simply ignored for the formats that don't use them.
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
// Helper: hide/show a widget in a way every frontend generation honours
// ---------------------------------------------------------------------------
// The current (Vue) frontend checks `widget.options.hidden` — that is what
// the core itself uses to hide widgets (e.g. the Painter node's preview
// widgets). Older frontends check `widget.hidden`. No frontend generation
// honours a bare `widget.hide`, so set both: the running frontend reads the
// one it knows, the other is just an ignored attribute.
function setWidgetHidden(widget, hidden) {
    if (!widget) return;
    widget.hidden = hidden;
    if (widget.options) {
        widget.options.hidden = hidden;
    }
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

            const formatWidget  = findWidget(this, "format");
            const qualityWidget = findWidget(this, "quality");
            const icoWidget     = findWidget(this, "ico_sizes");
            if (!formatWidget || !icoWidget) return;

            // formats whose encoding ignores the quality widget
            const qualityIgnored = ["webp (lossless)", "tiff", "ico"];

            const sync = () => {
                setWidgetHidden(icoWidget, formatWidget.value !== "ico");
                setWidgetHidden(
                    qualityWidget,
                    qualityIgnored.includes(formatWidget.value)
                );
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
