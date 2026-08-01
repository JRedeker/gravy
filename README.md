# Gravy

Gravy is a local-first review kit for coding agents. It spins up temporary,
structured human-review pages — served over your Tailnet — so an agent can ask
a human to pick a variant, triage items, fill a form, or check criteria, then
receive the decision back through normal chat.

It is a standalone Python + Gradio service with a small MCP control surface.
Agents discover review templates, create a page, and close it when done.

## Review surfaces

Each surface captures a distinct decision shape:

| Surface | Decision | Example request |
|---|---|---|
| **gallery** | Select one, rank, add notes | `{"surface": "gallery", "items": ["a.png", "b.png"]}` |
| **pairwise** | Compare pairs: left / right / tie / skip | `{"surface": "pairwise", "items": ["x", "y", "z"]}` |
| **form** | Fill typed fields (text, toggle, option, image) | `{"surface": "form", "fields": ["summary", "approved"]}` |
| **checklist** | Pass/fail + comment per criterion | `{"surface": "checklist", "criteria": ["title is visible"]}` |
| **queue** | Triage every item into an outcome bucket | `{"surface": "queue", "items": ["card-a", "card-b"], "options": ["accept", "reject", "defer"]}` |

All surfaces support **revision** — a reviewer can resubmit a changed decision
and the latest one wins. Prior decisions are reflected in the UI on re-open.
The decision log is append-only; no revision mutates or deletes history.

The catalog is closed. `annotation`, `document`, and `preview` are deferred and
unimplemented. There is no `custom` surface, generic renderer, or agent-supplied
executable UI path.

## MCP tools

| Tool | Purpose |
|---|---|
| `catalog` | List supported surfaces, schemas, and examples |
| `create` | Create a review page and return its Tailnet URL |
| `update` | Patch metadata on an active review |
| `close` | Close a review and release its resources |

`create` also serves the page — there is no separate serve step. A human visits
the Tailnet URL, makes their decision, and replies to the agent in chat. Gravy
does not poll, notify, or auto-resume agent sessions.

## Prerequisites

- Python 3.11+
- [Tailscale](https://tailscale.com) with HTTPS/Serve enabled on the host
- An MCP-compatible agent runtime (e.g. OpenCode with an MCP client)

## Installation

```bash
git clone https://github.com/JRedeker/gravy.git
cd gravy
uv sync                  # runtime dependencies
uv sync --group test     # add test dependencies (pytest)
```

## Running

Gravy is designed to run as a foreground MCP server supervised by a process
manager. The entry point never daemonizes or forks:

```bash
uv run python -m gravy.mcp_entry
```

The server binds `127.0.0.1:7654/mcp` by default. A `GET /ready` endpoint
returns `{"status": "ready"}` once the server is accepting requests.

### Configuration (environment variables)

All non-secret; no credentials required:

| Variable | Default | Purpose |
|---|---|---|
| `GRAVY_INTERNAL_HOST` | `127.0.0.1` | Loopback bind address (keep default) |
| `GRAVY_INTERNAL_PORT` | `7654` | MCP listener port (outside 6276–6325) |
| `GRAVY_EXTERNAL_PORT` | `6281` | External published port (within 6276–6325) |
| `GRAVY_PATH` | `/mcp` | MCP endpoint path (keep default) |
| `GRAVY_STATE_DIR` | `~/.local/share/gravy` | Durable lifecycle + artifact storage |

Invalid settings fail validation before the server binds.

## Testing

```bash
bin/oc-test                                # full suite (smoke tier)
bin/oc-test targeted -- tests/test_surfaces.py   # specific files
```

`bin/oc-test` routes through `uv run --group test pytest`, ensuring the project
venv (with Gradio + pytest) is used. The full suite covers surfaces, runtime
wiring, lifecycle, registry, artifacts, MCP boundary, schemas, and Tailscale
Serve integration.

## How it works

1. An agent calls `create` with a surface + payload.
2. Gravy reserves a bounded port, starts an in-process Gradio `Blocks` server,
   creates a Tailnet Serve mapping, and returns the review URL.
3. The human visits the URL, makes their decision, and tells the agent in chat.
4. The agent calls `close` to release the port and Tailnet mapping.

Decisions append atomically to review-scoped artifacts before the UI advances.
If the service recycles, active reviews are terminalized with a recovery
pointer; decision artifacts are preserved. Gravy reconciles only its own
Tailnet mappings — it never runs a global `tailscale serve reset`.

Capacity defaults to 10 simultaneous reviews with bounded Gradio queue/thread
limits.

## Project layout

```
src/gravy/
  mcp_entry.py          Foreground MCP server entry point
  mcp_boundary.py       MCP tool boundary (catalog/create/update/close)
  control_plane.py      Review lifecycle orchestration
  lifecycle.py          Create/close/recycle/recovery adapter
  registry.py           Bounded review registry
  gradio_runtime.py     Gradio Blocks builders + surface controllers
  schemas.py            Closed request validation (discriminated union)
  catalog.py            Surface catalog + deferred-surface metadata
  artifacts.py          Append-only decision artifact store
  ports.py              Bounded port pool
  config.py             Runtime config validation
  tailscale_serve.py    Tailnet Serve mapping management
  surfaces/
    common.py           DecisionSurface base (append, latest_decision, revision)
    gallery.py          Select + rank + notes
    pairwise.py         Pair comparison with revision navigation
    form.py             Typed fields
    checklist.py        Per-criterion pass/fail
    queue.py            Bulk triage into buckets
```

See [architecture](docs/architecture.md) and [operations](docs/operations.md)
for the full design and operational reference.

## License

[MIT](LICENSE) — Copyright (c) 2026 Sharper Flow LLC
