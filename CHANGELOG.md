# Changelog

All notable changes to this project are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed
- **HWP Aspect Size** (README): remove the leftover `Qwen2.1, Ideogram` row from the preset table — leftover from the v0.9.10 split; the alias is already explained in the note under the table, and it stays in the node menu so old workflows keep working.

## [0.9.10] - 2026-10-05

### Added
- **HWP Aspect Size**: per-preset **max side** baked into the size math. Each model preset now carries a max side in pixels in addition to its pixel budget: at extreme aspect ratios the constant budget makes the long side grow past what the model family handles (Qwen-Image-2512 starts duplicating content at 2656 = 2× native 1328, while 2400 renders clean), so the long side is scaled down to the cap before rounding. The resolved size shows a `(capped)` suffix below the node when the cap engaged. Caps: `SD 1.5` 1024 (2× native), `SD 2.1` 1152 (1.5× native), `SDXL` 1536 (documented optimal buckets, 1536×640 @ 2.4:1), `QWEN` 2048 (measured, applied as the long-side cap at all ratios — the official Qwen-Image specs are native 1328 with the published size list topping out at 1664, 16:9 = 1664×928; at 5:1, 2400 was clean with a 3-field concatenated prompt but duplicated with a single prompt field, 2048 was clean in both, 2656 = 2× native duplicated in both), `WAN22` 1440 (hosted T2I 512–1440 per side), `Qwen2.1` 2752 (model card widescreen 2752×1536), `Ideogram` 2048 (256–2048 per side, ratios up to 6:1).

### Changed
- **HWP Aspect Size**: the `SDXL, FLUX` preset splits into `SDXL` (cap 1536) and `FLUX.1` (uncapped — no documented limit), and `Qwen2.1, Ideogram` splits into `Qwen2.1` (cap 2752) and `Ideogram` (cap 2048) — the max sides of the families differ, so they can no longer share one entry. The old combined names are kept as aliases (conservative common cap) so existing saved workflows keep working unchanged. The generic `1440x`/`4K`/`3072x`/`8K`/`16K` budgets stay uncapped — the escape hatch for going past a family cap.

## [0.9.9] - 2026-10-04

### Added
- **HWP Aspect Size**: hover tooltips on all widgets and the `model` input (shown on mouse-over, like the built-in node tooltips), explaining the pixel-budget logic, the downscale-factor choice per model family, and when the model input is needed.
- **HWP Aspect Size**: new optional `model` (MODEL) input. When connected (to the same MODEL chain that feeds your sampler), the `latent` output is emitted in that model's **native layout** — channel count and spatial downscale ratio are read from the model itself via the same conversion the built-in `KSampler` applies (`comfy.sample.fix_empty_latent_channels`), and the `downscale_ratio_spacial` tag is dropped so nothing rescales a second time. This makes the latent work with **custom samplers** (e.g. RES4LYF `ClownsharKSampler`) that do not rescale empty latents themselves — on 1/16-VAE models (Flux 2: 128 ch, Qwen-Image 2.x: 64 ch) a canonical /8 latent would otherwise decode at 2× the intended size. Unconnected, the output is byte-for-byte the built-in `Empty Latent Image` layout as before, so existing workflows are unchanged. Verified against the Flux 2 / Qwen-Image 2.1 / SD3 / SDXL latent formats.

## [0.9.8] - 2026-09-30

### Added
- **HWP Aspect Size** — new node that computes `width`/`height` from a model's base pixel budget and a free-form aspect ratio (two integers, e.g. 5×2 for a Discord banner), rounding both dimensions up to multiples of a `downscale_factor` (VAE-safe output; the resolved size is shown below the node after a run). Modelled on Drift's Aspect Size V2 (DJZ-Nodes) with the preset list renamed/extended and sorted by ascending pixel budget: `SD 1.5` (512²), `SD 2.1` (768²), `SDXL, FLUX` (1024² — also Krea 2), `QWEN` (1328² — Qwen-Image/2512, matches the official README table), `1440x`, `WAN22` (1536²), `Qwen2.1, Ideogram` (2048² — Ideogram 4 / 4.5, Qwen-Image 2.x, Ming-Image 0.1 and Kandinsky Cascade, all native 2K), plus the generic 4K/3072x/8K/16K budgets. Preset names use ", " instead of "/" because the combo widget renders "/" as a submenu separator.
- **HWP Aspect Size** also outputs an empty **`LATENT`** at the resolved size (new `batch_size` input), so a workflow can skip that node entirely — the `width`/`height` INT outputs are unchanged and still there for anything that needs them. The latent matches the built-in Empty Latent Image exactly, including the `downscale_ratio_spacial` tag, so 16×-VAE models (Qwen-Image, FLUX, …) decode at the intended size.

### Changed
- **Documentation (HWP Global Seed / HWP Seed Node)**: made the README explicit about **broadcast vs. wired** — the *seed value* of HWP Global Seed is broadcast to every `seed` / `seed_num` / `noise_seed` int widget, but a `noise` (`NOISE`) output is **not** broadcast and must always be **wired** to a `NOISE` input (e.g. `SamplerCustomAdvanced` in Flux.2 workflows). Documentation only — no code change.

## [0.9.7] - 2026-09-23

### Added
- Release automation: GitHub Actions workflow (`.github/workflows/publish-comfy-registry.yml`) that publishes the pack to the Comfy Registry automatically on every `v*` tag push, using the pushed commit message as the version changelog; can also be triggered manually via `workflow_dispatch`. Manual publishing with `comfy node publish` continues to work unchanged (dev tooling only — no node or code changes).

### Changed
- **HWP Save Image (Advanced)**: the `-> Saved image to <path>` log lines are yellow by default again (as in LayerStyle's `SaveImage Plus`), which stands out better than the green shipped in 0.9.6.

### Fixed
- **HWP Save Image (Advanced)**: the blind watermark silently didn't work on manual git-clone installs — `qrcode` and `blind-watermark` are not installed automatically for clones (only when the pack is installed via Comfy Manager / registry). The pack now ships a `requirements.txt` (run `python -m pip install -r requirements.txt` from the clone folder; also documented in the README), and the node already warned in the log and saved without the watermark instead of failing.
- **HWP Global Seed**: the `no GlobalSeed node in workflow, skipping` log line is suppressed — the prompt hook runs on every run of every workflow, so the line showed up for users who don't use the node. Detection is unchanged: as soon as a Global Seed node is in the workflow, the node kicks in and logs as before.

## [0.9.6] - 2026-09-11

### Added
- **HWP Save Image (Advanced)** — terminal save node modeled on LayerStyle's `SaveImage Plus (Advanced)`, extended with TIFF, WEBP and multi-resolution ICO output:
  - Formats: `png`, `jpg`, `webp`, `webp (lossless)`, `tiff` (LZW lossless), `ico` (multi-resolution presets 32/48/64, 64/128/256, 128/256/512)
  - ICO entries are resampled by PIL from the **full-resolution source image** (other packs pre-resize and end up upscaling from the smallest entry — broken multi-resolution output)
  - The `ico_sizes` widget is hidden until `format` is set to `ico`, so the node never looks like it wants an ICO preset for non-ICO output
  - The `quality` widget is hidden for the formats that ignore it (`webp (lossless)`, `tiff`, `ico`) — only `png` (as compression level), `jpg` and `webp` use it
  - Sensible defaults when a node opens: `quality` 100, `ico_sizes` `Medium (64, 128, 256)`
  - `%date` / `%time` tokens in `custom_path` and `filename_prefix`
  - Optional filename timestamp: none, second, or millisecond
  - Per-format quality control (PNG compression level, JPG quality 4:4:4, WEBP quality; TIFF/ICO use lossless encoding)
  - Optional workflow metadata (PNG text chunks / EXIF `UserComment` JSON, same layout as Apolonia's save nodes) — honours the core `--disable-metadata` flag; ICO cannot store metadata and logs a warning if requested
  - Optional invisible **blind watermark** (QR payload spread across the full RGB image, so lossless PNG output preserves it; extractable with the `blind_watermark` library using `password_img=1`, `password_wm=1` — compatible with the watermarks already used in the Apolonia ecosystem; images too small to carry the payload are saved without it, with a warning)
  - Optional UI preview image when saving to a `custom_path` (batch bug fixed: the preview temp dir is created once, so multi-image batches keep every preview)
  - JPEG alpha is composited over white instead of discarded to black
  - Per-file `-> Saved image to <full path>` log lines via `logging` (no `print`)

## [0.9.5] - 2026-09-07

### Added
- **HWP Get Side (Latent)** and **HWP Get Side (X/Y)** now display their output value below the node (bare number, no label) after a run, like the built-in `Get Image Size` node. Older ComfyUI versions without this feature are unaffected — the display is skipped instead of erroring.

### Changed
- Startup banner now reads `[ComfyUI-HWP-Nodes] <n> node(s) v<version> registered.` — the node count is derived from `NODE_CLASS_MAPPINGS` and the rainbow gradient is generated at runtime, so both stay in sync automatically with no manual re-styling when nodes or the version change.
- **HWP Get Side (Latent)** and **HWP Get Side (X/Y)**: removed a leftover "drop this file into custom_nodes" install note from the docstrings (leftover from before the nodes were consolidated into this pack).

## [0.9.4] - 2026-08-27

### Changed
- README updated (reworked node documentation with tables and a node-search section), screenshots added.

## [0.9.3] - 2026-08-25

### Added
- `CHANGELOG.md` — persistent in-repo record of releases (Keep a Changelog format), reconstructed from the v0.9.0 and v0.9.2 GitHub release notes.

## [0.9.2] - 2026-08-19

### Added
- **HWP Seed Node** — per-node seed control (fixed / increment / decrement / randomize), applied to wired outputs only.

### Changed
- Registration banner now reads its version from `pyproject.toml` instead of a hardcoded string, so it can't drift from the actual release version.

## [0.9.0] - 2026-08-17

Initial release.

### Added
- **HWP Global Seed** — distributes a single seed to every `seed` / `seed_num` / `noise_seed` widget in the workflow.
  - `mode`: `control_before_generate` / `control_after_generate`
  - `action`: `fixed`, `increment`, `decrement`, `randomize`, plus `... for each node` variants giving each downstream sampler its own successive value
  - `max_seed`: configurable wrap ceiling for increment/decrement
  - `logging`: `default` or `verbose`
  - Outputs both `seed` (`INT`) and `noise` (`NOISE`) — the `NOISE` output plugs directly into `SamplerCustomAdvanced` (e.g. Flux.2 workflows) without a separate `RandomNoise` converter node
- **HWP Get Side (Latent)** — returns the longest or shortest pixel-space dimension of a `LATENT` input (auto-converted from latent space).
- **HWP Get Side (X/Y)** — returns the longest or shortest of a `width`/`height` pair.
