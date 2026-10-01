# ComfyUI-HWP-Nodes

A small collection of custom [ComfyUI](https://github.com/comfyanonymous/ComfyUI) nodes by [hwprinz](https://github.com/hwprinz), covering seed/noise control, simple latent/size utilities, and an advanced multi-format image save node.

![Preview](screenshots/nodes.png)
<!-- TODO: add a screenshot showing the nodes in a workflow, then update the path above -->

## Nodes

| Node | File | Purpose |
|---|---|---|
| [HWP Global Seed](nodes/global_seed.py) | `global_seed.py` | Broadcasts one seed **value** to every `seed` / `noise_seed` int widget in the workflow |
| [HWP Seed Node](nodes/seed_node.py) | `seed_node.py` | Local (non-broadcasting) seed + noise source for a single sampler |
| [HWP Get Side (Latent)](nodes/get_side_from_latent.py) | `get_side_from_latent.py` | Returns the longest/shortest pixel-space dimension of a `LATENT` |
| [HWP Get Side (X/Y)](nodes/get_side_from_xy.py) | `get_side_from_xy.py` | Returns the longest/shortest of a `width`/`height` pair |
| [HWP Save Image (Advanced)](nodes/image_save.py) | `image_save.py` | Multi-format save (PNG/JPG/WEBP/TIFF/ICO) with timestamps, metadata, blind watermark and per-file logging |
| [HWP Aspect Size](nodes/aspect_size.py) | `aspect_size.py` | `width`/`height` from a model's pixel budget + free aspect ratio (e.g. 5:2), rounded to a VAE-safe multiple |

---

## Finding the nodes

All nodes are registered under the `HWP` category. To find them, just type `HWP` into the node search (right-click canvas → Add Node):

![Preview](screenshots/search_nodes.png)

---

## HWP Global Seed

**File:** `nodes/global_seed.py` · **Category:** HWP

Global seed controller for ComfyUI workflows. Distributes a single seed **value** to every other `seed` / `seed_num` / `noise_seed` **int widget** in the workflow, so you only need to manage one seed control instead of one per sampler. This is the seed *value* only — the node's `noise` output is a separate `NOISE` object that you **wire** like any other output; it is **not** broadcast (see Outputs below).

![Preview](screenshots/global_seed.png)
<!-- TODO: screenshot of the node + the 🎲 button -->

### Inputs

| Input | Type | Default | Description |
|---|---|---|---|
| `value` | INT | `0` | The base seed |
| `mode` | ENUM | `control_before_generate` | `control_before_generate` computes the next seed before this run's prompt is sent (this run uses the new value); `control_after_generate` uses the current value now and prepares the next one for the following queue |
| `action` | ENUM | `fixed` | `fixed`, `increment`, `decrement`, `randomize`, or their `... for each node` variants (see below) |
| `max_seed` | INT | `0` (→ `1125899906842624`) | Ceiling that increment/decrement wraps at |
| `logging` | ENUM | `default` | `default` logs one summary line per run; `verbose` also logs per-node seed updates |

The plain `action` variants advance one shared value for every node. The `... for each node` variants give each downstream seed widget its own successive value — e.g. `increment for each node` hands out `value`, `value+1`, `value+2`, …

### Outputs

| Output | Type | Description |
|---|---|---|
| `seed` | INT | The resolved seed value. On this (global) node it is also **broadcast** to every `seed` / `seed_num` / `noise_seed` int widget in the workflow — or wired to a single `INT` input like any other output |
| `noise` | NOISE | The same seed wrapped as a ready-to-use noise object (via ComfyUI's own `Noise_RandomNoise`) — useful for workflows (e.g. Flux.2 / `SamplerCustomAdvanced`) that need a `NOISE` input directly, without a separate `RandomNoise` converter node. **Wired, not broadcast**: connect it to a `NOISE` input — unlike the `seed` value it is never auto-applied, so it must always be connected |

---

## HWP Seed Node

**File:** `nodes/seed_node.py` · **Category:** HWP

A **local** seed + noise source — the non-global counterpart of HWP Global Seed. It looks and behaves like HWP Global Seed (see screenshot above) — the only difference is that it does **not** broadcast anything: the outputs only reach the node(s) you explicitly wire them to. It exposes the same `seed`/`noise` outputs and the same `fixed`/`increment`/`decrement`/`randomize` actions. Use it when you want a controllable seed for one specific sampler without touching the rest of the workflow.

### Inputs

| Input | Type | Default | Description |
|---|---|---|---|
| `value` | INT | `0` | The base seed |
| `mode` | ENUM | `control_before_generate` | Same semantics as HWP Global Seed |
| `action` | ENUM | `fixed` | `fixed`, `increment`, `decrement`, or `randomize` |
| `max_seed` | INT | `0` (→ `1125899906842624`) | Ceiling that increment/decrement wraps at, and cap for randomize |
| `logging` | ENUM | `default` | `default` logs one summary line per run; `verbose` also logs per-run seed detail |

### Outputs

| Output | Type | Description |
|---|---|---|
| `seed` | INT | The resolved seed value — applied **only** to the node(s) you wire it to (this node broadcasts nothing) |
| `noise` | NOISE | The same seed wrapped as a ready-to-use noise object (via ComfyUI's own `Noise_RandomNoise`) — **wired, not broadcast**: connect it to a `NOISE` input, like this node's `seed` |

---

## HWP Get Side (Latent)

**File:** `nodes/get_side_from_latent.py` · **Category:** HWP

Takes a `LATENT` input and returns either its longest or shortest pixel-space dimension (auto-converted from latent space via ×8), selected with a longest/shortest toggle.

The computed value is also displayed below the node after a run (bare number, like the built-in `Get Image Size` node).

### Inputs

| Input | Type | Default | Description |
|---|---|---|---|
| `latent` | LATENT | — | The latent to measure |
| `side` | ENUM | `longest` | `longest` or `shortest` |

### Outputs

| Output | Type | Description |
|---|---|---|
| `side` | INT | The selected pixel-space dimension |

---

## HWP Get Side (X/Y)

**File:** `nodes/get_side_from_xy.py` · **Category:** HWP

Takes `width`/`height` integers and returns either the longest or shortest of the two, selected with the same longest/shortest toggle.

The computed value is also displayed below the node after a run (bare number, like the built-in `Get Image Size` node).

### Inputs

| Input | Type | Default | Description |
|---|---|---|---|
| `width` | INT | — | Width value |
| `height` | INT | — | Height value |
| `side` | ENUM | `longest` | `longest` or `shortest` |

### Outputs

| Output | Type | Description |
|---|---|---|
| `side` | INT | The selected value |

---

## HWP Save Image (Advanced)

**File:** `nodes/image_save.py` · **Category:** HWP

An advanced terminal save node modeled on LayerStyle's `SaveImage Plus (Advanced)`, extended with **TIFF**, **WEBP** and **multi-resolution ICO** output. Unlike the core `Save Image` node it writes exactly the file the widget says, keeps a per-file `-> Saved image to <full path>` log line for every written file, and supports timestamped filenames, workflow metadata and an invisible blind watermark.

![Preview](screenshots/image_save.png)
<!-- TODO: screenshot of the node in a workflow -->

### Inputs

| Input | Type | Default | Description |
|---|---|---|---|
| `images` | IMAGE | — | The image batch to save (one file per image) |
| `custom_path` | STRING | `""` | Directory to save into (created if missing); empty = ComfyUI's `output/` folder. Supports `%date` and `%time` tokens |
| `filename_prefix` | STRING | `comfyui` | Base filename; also supports `%date` and `%time` tokens |
| `timestamp` | ENUM | `None` | Appends `_NNNNN` (counter), `_YYYY-MM-DD_HH-MM-SS` (second) or `_YYYY-MM-DD_HH-MM-SS-mmm` (millisecond) to the filename |
| `format` | ENUM | `png` | `png`, `jpg`, `webp`, `webp (lossless)`, `tiff`, `ico` |
| `quality` | INT | `100` | See the per-format table below — hidden in the UI when the format ignores it (`webp (lossless)`, `tiff`, `ico`) |
| `ico_sizes` | ENUM | `Medium (64, 128, 256)` | ICO resolution preset — hidden in the UI until `format` is `ico` (the value is still sent and ignored for other formats) |
| `meta_data` | BOOLEAN | `False` | Embed the workflow prompt + metadata (PNG text chunks, or EXIF `UserComment` JSON for jpg/webp/tiff). Honours the core `--disable-metadata` flag. ICO cannot store metadata (a warning is logged) |
| `blind_watermark` | STRING | `""` | Text to embed invisibly (QR payload spread across the full RGB image — lossless PNG output preserves it). Extractable with the [`blind_watermark`](https://pypi.org/project/blind-watermark/) library using `password_img=1`, `password_wm=1`; images too small to carry the payload are saved without it (a warning is logged) |
| `preview` | BOOLEAN | `True` | Show a result image in the UI. When saving to a `custom_path` the real files land there and a PNG preview is shown instead (saved to temp) |

**No output.** This is a terminal node.

### Formats and quality

| Format | Extension | Quality widget | Encoding |
|---|---|---|---|
| `png` | `.png` | compression level `(100 − q) // 10` (q 100 → level 0) | lossless, alpha preserved |
| `jpg` | `.jpg` | JPEG quality | 4:4:4 (`subsampling=0`); RGBA is composited over white |
| `webp` | `.webp` | WEBP quality | lossy, `method=6` (slowest, best ratio), alpha preserved |
| `webp (lossless)` | `.webp` | ignored | lossless, `method=6`, alpha preserved |
| `tiff` | `.tiff` | ignored | LZW — lossless, suited for final archive quality, alpha preserved |
| `ico` | `.ico` | ignored | multi-resolution ICO, 32-bit RGBA |

**ICO multi-resolution:** the `ico_sizes` preset picks the embedded sizes (e.g. `Small (32, 48, 64)`). Every size is resampled by PIL directly from the **full-resolution source image** — some other packs pre-resize the frames first and end up upscaling from the smallest entry, which is why their "multi-resolution" output looks soft; that defect does not apply here.

**Metadata layout:** PNG files get the prompt and each `extra_pnginfo` key as text chunks; JPG/WEBP/TIFF get a JSON blob `{"prompt": …, …extra_pnginfo}` in the EXIF `UserComment` tag (same layout as the other HWP-ecosystem save nodes).

---

## HWP Aspect Size

**File:** `nodes/aspect_size.py` · **Category:** HWP

Computes a `width` × `height` pair for a text-to-image model. Pick the model preset (its base pixel budget stays constant), enter a free-form aspect ratio as two integers — e.g. `5` × `2` for a Discord banner — and the node returns both dimensions rounded **up** to multiples of a `downscale_factor`, so the result is always VAE-safe. The resolved size is also shown below the node after a run.

Modelled on Drift's [Aspect Size V2](https://github.com/MushroomFleet/DJZ-Nodes/blob/main/AspectSizeV2.py) (DJZ-Nodes), with the preset list renamed/extended so entries name the models they actually fit.

### Inputs

| Input | Type | Default | Description |
|---|---|---|---|
| `model_type` | ENUM | `SD 1.5` | The base pixel budget (see presets below) |
| `aspect_ratio_width` | INT | `1` | Aspect ratio, width part (free integer) |
| `aspect_ratio_height` | INT | `1` | Aspect ratio, height part (free integer) |
| `downscale_factor` | INT | `32` | Both output dimensions are rounded up to multiples of this (1–128) |

### Outputs

| Output | Type | Description |
|---|---|---|
| `width` | INT | Pixel width, multiple of `downscale_factor` |
| `height` | INT | Pixel height, multiple of `downscale_factor` |

### Presets

The `model_type` preset sets the **total pixel budget** (width × height). The aspect ratio you choose decides how that area is split into width and height. Several models share a pixel budget, so one preset can name several of them — that is deliberate (no double entries for the same budget). The menu is sorted by ascending base budget.

MP uses ComfyUI's convention: 1 MP = 1024 × 1024 = 1,048,576 pixels.

| Preset | Square equivalent | Pixels | MP |
|---|---|---|---|
| `SD 1.5` | 512 × 512 | 262,144 | 0.25 |
| `SD 2.1` | 768 × 768 | 589,824 | 0.56 |
| `SDXL, FLUX` | 1024 × 1024 | 1,048,576 | 1.0 |
| `QWEN` | 1328 × 1328 | 1,763,584 | 1.68 |
| `1440x` | 1440 × 1440 | 2,073,600 | 1.98 |
| `WAN22` | 1536 × 1536 | 2,359,296 | 2.25 |
| `Qwen2.1, Ming` | 2048 × 2048 | 4,194,304 | 4.0 |
| `4K` | 2880 × 2880 | 8,294,400 | 7.91 |
| `3072x` | 3072 × 3072 | 9,437,184 | 9.0 |
| `8K` | 5760 × 5760 | 33,177,600 | 31.64 |
| `16K` | 11520 × 11520 | 132,710,400 | 126.56 |

"4K" and "8K" match the pixel area of 3840 × 2160 and 7680 × 4320 respectively, not a literal square of that width.

Which model fits which preset:

- `SD 1.5` — Stable Diffusion 1.5 · `SD 2.1` — Stable Diffusion 2.x (768)
- `SDXL, FLUX` — SDXL, FLUX.1, SD3, Kolors, HunyuanImage 3.0, [Krea 2](https://huggingface.co/krea/Krea-2-Raw) (its model card examples run at 1024×1024), …
- `QWEN` — Qwen-Image / Qwen-Image-2512 — the budget of the official [README](https://github.com/QwenLM/Qwen-Image) resolution table (1:1 → 1328×1328; non-square ratios keep the full budget, so they land a touch above the table's per-ratio values)
- `WAN22` — Wan 2.2
- `Qwen2.1, Ming` — Qwen-Image 2.x (native 2K), [Ming-Image 0.1](https://huggingface.co/inclusionAI/Ming-Image-0.1-Design) (2048×2048 recommended), Kandinsky Cascade, [Ideogram 4](https://huggingface.co/ideogram-ai/ideogram-4-fp8) (native 2K, 256–2048 per side)
- `1440x`, `4K`, `3072x`, `8K`, `16K` — generic budgets

**Ideogram 4 note:** its 2048 limit is *per side*, and wide ratios are capped at 6:1 — for very wide shapes the full 4.0 MP budget cannot be kept (e.g. 5:2 → 3264×1312 exceeds the 2048 side limit; drop the factor/budget or accept a smaller output for that model).

### Downscale factor

Pick the smallest multiple the model actually requires — a larger factor narrows the possible dimensions:

| Model | Factor |
|---|---|
| SD 1.5, SD 2.1, SDXL | 8 (16 works too) |
| FLUX.1, SD3 | 16 |
| Qwen-Image / 2512 | 16 (every dimension in the official table is a multiple of 16) |
| Qwen-Image 2.x, GLM-Image | 32 |
| Ming-Image 0.1, Ideogram 4 | 16 (Ming's 1024/2048 buckets are multiples of 32, so 32 works for it too) |

Example: `Qwen2.1, Ming`, ratio `5` × `2`, factor `32` → **3264 × 1312** (4.0 MP at 5:2).

---

## Shared Behaviour

- **Seed/noise pairing**: HWP Global Seed and HWP Seed Node both emit `seed` (INT) and `noise` (NOISE, via ComfyUI's `Noise_RandomNoise`), so either can feed a `SamplerCustomAdvanced`-style graph directly with no extra converter node.
- **Broadcast vs. wired (the key distinction)**: the *seed value* of **HWP Global Seed** is broadcast to every `seed` / `seed_num` / `noise_seed` **int widget** in the workflow — that is the "global" part. A `noise` output, on **either** node, is a `NOISE` object and is **not** broadcast: it always has to be **wired** to a `NOISE` input such as `SamplerCustomAdvanced`. **HWP Seed Node** is fully local — both its `seed` and its `noise` reach only the node(s) you wire them to.
- **Manual randomize**: both seed nodes get a client-side 🎲 "Manual Random Seed" button and live `value`/`last_seed` widget updates from the bundled JS extensions (`web/global_seed.js`, `web/seed_node.js`). They coexist in the same workflow without interfering with each other.
- **Logging**: both seed nodes support `default` (one summary line per run) and `verbose` (adds per-node/per-run seed detail) logging modes.

## Installation

```
cd ComfyUI/custom_nodes
git clone https://github.com/hwprinz/ComfyUI-HWP-Nodes
```

The blind watermark of HWP Save Image (Advanced) needs two extra Python packages that ComfyUI does not install automatically for clone installs. Run this once from the clone folder:

```
cd ComfyUI-HWP-Nodes
python -m pip install -r requirements.txt
```

Restart ComfyUI.

## License

MIT
