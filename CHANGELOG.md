# Changelog

All notable changes to this project are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed
- Startup banner now reads `[ComfyUI-HWP] <n> node(s) v<version> registered.` — the node count is derived from `NODE_CLASS_MAPPINGS` and the rainbow gradient is generated at runtime, so both stay in sync automatically with no manual re-styling when nodes or the version change.

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
