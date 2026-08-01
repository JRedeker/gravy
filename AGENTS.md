# Gravy Agent Context

Gravy is a standalone, local-first review-kit for coding agents. It provides
temporary Tailnet-reachable Gradio pages for structured human review.

## Development commands

- **Tests:** `bin/oc-test` (smoke/full) or `bin/oc-test targeted -- tests/test_surfaces.py` (specific files). This routes through `uv run --group test pytest` — do not run bare `python -m pytest` (resolves to system python, missing gradio + pytest).
- **Sync deps:** `uv sync --group test` in a fresh worktree (bin/oc-test handles this automatically).
- **Run locally:** `uv run python -m gravy.mcp_entry` (binds `127.0.0.1:7654/mcp`).
- Python ≥3.11; uv-managed project (`uv.lock`).

## Adding a review surface

Six integration points — all required, follow the existing pattern exactly:

1. `schemas.py` — add a `@dataclass(frozen=True, slots=True)` Request type; extend the `ReviewRequest` union; add a branch in `validate_request`; update the error message.
2. `surfaces/<name>.py` — subclass `DecisionSurface`; set `surface = "<name>"`; implement `submit()`.
3. `surfaces/__init__.py` — export the new class.
4. `gradio_runtime.py` — import the surface + request; add a `_surface_for_request` branch; add controller methods (`<name>_submit`, `<name>_prior`); add a `_build_<name>` function; register in `_BUILDERS`.
5. `catalog.py` — add an entry to `_SURFACES`; remove from `DEFERRED_SURFACES` if present.
6. Tests — surface tests in `test_surfaces.py`; schema tests in `test_schemas.py`; controller tests in `test_gradio_runtime.py`. Update the catalog-count assertion in `test_schemas.py` and the surface-set assertion in `test_mcp_boundary.py`.

## Revision semantics

All surfaces support revision (resubmit; latest wins). The decision log is
append-only. Effective decisions derive from:
- `latest_decision()` — whole-surface surfaces (gallery, form, queue).
- `latest_per_key(key_fn)` — keyed surfaces (checklist by criterion, pairwise by pair).

When adding pre-population, expose a `<name>_prior()` controller method reading
the appropriate accessor — do not introspect Gradio component internals.

## Boundaries

- Keep Gravy independent of Advance runtime code. Advance may reference review evidence but does not own Gravy processes or artifacts.
- Vision owns supervision of Gravy's loopback MCP backend. Do not add a second process manager, daemonization, or double-forking.
- Gravy owns review IDs, active-review capacity, review ports, Tailnet Serve mappings, and review artifacts.
- The supported catalog is closed: `gallery`, `pairwise`, `form`, `checklist`, and `queue`. Treat `annotation`, `document`, and `preview` as deferred and unimplemented.
- Human feedback returns to the agent through normal chat. Do not add polling, notifications, or automatic agent-resume behavior.

## Concurrency and persistence

- Treat review-registry and Tailscale ServeConfig updates as serialized state transitions. Do not hold the lifecycle lock while user interaction runs.
- Keep Vision MCP-session admission separate from Gravy active-review capacity.
- Persist review metadata atomically and append decisions before UI advance.
- Never replay a lifecycle mutation after uncertain execution. Return a typed terminal result with the artifact recovery pointer instead.
- Reconcile only Gravy-owned stale Serve mappings during startup. Never run a global `tailscale serve reset`; unrelated mappings are outside Gravy's authority.

## Scope

Do not implement a `custom` surface, arbitrary/generated renderer, agent-provided executable UI code, SaaS hosting, accounts, multi-reviewer workflows, browser automation, or automatic agent resume without a new approved change.

## Verification

- Test 10 simultaneous review creates, bounded-capacity rejection, distinct artifact namespaces, progress under active reviews, close/recycle cleanup, and recovery from persisted artifacts.
- Before changing Vision configuration, validate it and sync its non-secret backup per the Toolbox instructions.

See `docs/architecture.md` and `docs/operations.md` for the durable design.
