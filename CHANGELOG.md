# Changelog

All notable changes to this project are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
