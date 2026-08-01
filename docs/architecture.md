# Architecture

## Topology

Vision supervises one loopback Gravy MCP backend through `managed-http`.
Gravy owns review lifecycle state. A created review starts an in-process Gradio
`Blocks` server on a unique port and exposes it with a Gravy-owned persistent
Tailnet Serve mapping.

This produces a distinct Tailnet origin per review. It intentionally avoids
runtime Gradio mounting, a shared-origin reverse proxy, subprocess-per-review
hosting, and daemonization.

## Agent surface

```text
catalog() -> supported surfaces, schemas, examples
create(surface, request) -> review_id, Tailnet URL, lifecycle metadata
update(review_id, patch) -> updated lifecycle state
close(review_id) -> terminal lifecycle state
```

`create` also serves the page. There is no separate serve operation.

## Closed review catalog

`catalog()` describes exactly five discriminated review surfaces, each with a
schema and example request:

- `gallery` for selecting or ranking visual variants with notes;
- `pairwise` for left/right/tie/skip decisions that resume from persisted
  decisions;
- `form` for images or text, options, toggles, fields, and free text;
- `checklist` for explicit pass/fail criteria and per-criterion comments; and
- `queue` for assigning every item to one of a closed set of outcome buckets.

`checklist` is independently discriminated and serialized even where it shares
field primitives with a form. `annotation`, `document`, and `preview` are catalog
roadmap metadata only: they are deferred and unimplemented. There is no
`custom` surface, generic renderer, or agent-supplied executable UI path.

## Correctness boundaries

- Review identity is independent of MCP session identity.
- Registry and Tailnet ServeConfig mutations share one narrow lifecycle lock.
- Review metadata is atomically replaced; decisions are append-only.
- A service recycle turns active reviews terminal and preserves a recovery
  pointer. No operation is replayed after uncertain execution.
- Startup/recycle reconciliation removes only mappings explicitly recorded as
  Gravy-owned. It never runs global `tailscale serve reset` or changes unrelated
  Serve configuration.
- Tailnet HTTPS capability is checked before a port or registry entry is
  allocated.

## Capacity

Vision MCP admission and Gravy review capacity are independent. Gravy's initial
default supports at least 10 simultaneous reviews, with a bounded configured
maximum and explicit per-review Gradio queue/thread limits.
