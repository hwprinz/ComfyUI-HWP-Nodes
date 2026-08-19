# ComfyUI-HWP-Nodes

Custom node pack for ComfyUI by [hwprinz](https://github.com/hwprinz).

## Nodes

### HWP Global Seed
Global seed controller for ComfyUI workflows. Distributes a single seed value
to every other seed / seed_num / noise_seed widget in the workflow, so you
only need to manage one seed control instead of one per sampler.

Inputs:
- `value` (`INT`) — the base seed.
- `mode` (`control_before_generate` / `control_after_generate`) — whether the
  next seed is computed before this run's prompt is sent (so this run uses
  the new value) or after (so this run uses the current value, and the next
  one is prepared for the following queue).
- `action` — `fixed`, `increment`, `decrement`, `randomize`, or their
  `... for each node` variants. The plain variants advance one shared value
  for every node; the `for each node` variants give each downstream seed
  widget its own successive value (e.g. `increment for each node` hands out
  `value`, `value+1`, `value+2`, ...).
- `max_seed` — wraps increment/decrement at this ceiling (default
  `1125899906842624` when left at `0`).
- `logging` — `default` logs one summary line per run; `verbose` also logs
  per-node seed updates.

Outputs:
- `seed` (`INT`) — the resolved seed value.
- `noise` (`NOISE`) — the same seed wrapped as a ready-to-use noise object
  (via ComfyUI's own `Noise_RandomNoise`), for workflows (e.g. Flux.2 /
  `SamplerCustomAdvanced`) that need a `NOISE` input directly — no separate
  `RandomNoise` converter node required.

### HWP Seed Node
A **local** seed + noise source — the non-global counterpart of HWP Global
Seed. It exposes the same `seed` (`INT`) and `noise` (`NOISE`) outputs and the
same `fixed` / `increment` / `decrement` / `randomize` actions, but it does
**not** broadcast anything: the outputs are only applied to the node(s) you
explicitly wire them to. Use it when you want a controllable seed for a
specific sampler without touching the rest of the workflow.

Inputs:
- `value` (`INT`) — the base seed.
- `mode` (`control_before_generate` / `control_after_generate`) — whether the
  next seed is computed before this run's prompt is sent (so this run uses
  the new value) or after (so this run uses the current value, and the next
  one is prepared for the following queue).
- `action` — `fixed`, `increment`, `decrement`, or `randomize`.
- `max_seed` — wraps increment/decrement at this ceiling and caps randomize
  (default `1125899906842624` when left at `0`).
- `logging` — `default` logs one summary line per run; `verbose` also logs
  per-run seed detail.

Outputs:
- `seed` (`INT`) — the resolved seed value.
- `noise` (`NOISE`) — the same seed wrapped as a ready-to-use noise object
  (via ComfyUI's own `Noise_RandomNoise`).

As with HWP Global Seed, the 🎲 Manual Random Seed button and the live
value/last_seed widget updates are provided by the client-side extension
(`web/seed_node.js`). It coexists with HWP Global Seed in the same workflow
without the two interfering.

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
