# Gravy

Gravy gives coding agents small, temporary human-review pages over the Tailnet.

It is a standalone Python and Gradio service, supervised by Vision. Agents use
a small MCP surface to discover a review template, create a page, update an
active review when permitted, and close it.

## Initial review surfaces

- **Gallery** — inspect, rank, or select visual variants and add notes.
- **Pairwise** — record left, right, tie, or skip decisions for a resumable
  comparison queue.
- **Form** — collect structured options, toggles, text, and image feedback.
- **Checklist** — record an explicit pass/fail result and comment for each
  declared criterion.

The catalog is closed: `gallery`, `pairwise`, `form`, and `checklist` are the
only implemented surfaces. `annotation`, `queue`, `document`, and `preview`
are deferred and unimplemented. Gravy does not accept custom renderers,
agent-provided executable UI code, or arbitrary generated applications.

## Operating model

- Gravy serves human pages only on the Tailnet.
- Vision supervises Gravy's loopback MCP control backend.
- Each review has an opaque review ID, a bounded port, and a separate Tailnet
  origin.
- Decisions append to review-scoped artifacts before the UI advances.
- A human replies to the agent in normal chat after review; Gravy does not poll
  or resume agent sessions.
- `create` serves the page; there is no separate serve operation.
- Recovery terminalizes pages lost to a service recycle and preserves an
  artifact recovery pointer. It removes only recorded Gravy-owned mappings and
  never runs `tailscale serve reset` against shared Tailnet Serve configuration.

See [architecture](docs/architecture.md) and [operations](docs/operations.md).
