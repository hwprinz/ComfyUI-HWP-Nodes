# ComfyUI-HWP-Nodes

Custom node pack for ComfyUI by [hwprinz](https://github.com/hwprinz).

## Nodes

### HWP Global Seed
Global seed controller for ComfyUI workflows. Distributes a single seed value
to all sampler nodes, with increment / decrement / randomize modes and
per-node seed variants.

Outputs:
- `seed` (`INT`) — the resolved seed value.
- `noise` (`NOISE`) — the same seed wrapped as a ready-to-use noise object
  (via ComfyUI's own `Noise_RandomNoise`), for workflows (e.g. Flux.2 /
  `SamplerCustomAdvanced`) that need a `NOISE` input directly — no separate
  `RandomNoise` converter node required.

### HWP Get Side (Latent)
Takes a `LATENT` input and returns either its longest or shortest pixel-space
dimension (auto-converted from latent space via ×8), selected with a
longest/shortest toggle.

### HWP Get Side (X/Y)
Takes `width`/`height` integers and returns either the longest or shortest of
the two, selected with the same longest/shortest toggle.

## Installation
```
cd ComfyUI/custom_nodes
git clone https://github.com/hwprinz/ComfyUI-HWP-Nodes
```

Restart ComfyUI.

## License

MIT
