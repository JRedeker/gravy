# Gravy Agent Context

Gravy is a standalone, local-first review-kit for coding agents. It provides
temporary Tailnet-reachable Gradio pages for structured human review.

## Boundaries

- Keep Gravy independent of Advance runtime code. Advance may reference review
  evidence but does not own Gravy processes or artifacts.
- Vision owns supervision of Gravy's loopback MCP backend. Do not add a second
  process manager, daemonization, or double-forking.
- Gravy owns review IDs, active-review capacity, review ports, Tailnet Serve
  mappings, and review artifacts.
- The supported catalog is closed: `gallery`, `pairwise`, `form`, `checklist`, and
  `queue`. Treat `annotation`, `document`, and `preview` as deferred and
  unimplemented.
- Human feedback returns to the agent through normal chat. Do not add polling,
  notifications, or automatic agent-resume behavior.

## Concurrency and persistence

- Treat review-registry and Tailscale ServeConfig updates as serialized state
  transitions. Do not hold the lifecycle lock while user interaction runs.
- Keep Vision MCP-session admission separate from Gravy active-review capacity.
- Persist review metadata atomically and append decisions before UI advance.
- Never replay a lifecycle mutation after uncertain execution. Return a typed
  terminal result with the artifact recovery pointer instead.
- Reconcile only Gravy-owned stale Serve mappings during startup. Never run a
  global `tailscale serve reset`; unrelated mappings are outside Gravy's
  authority.

## Scope

Do not implement a `custom` surface, arbitrary/generated renderer,
agent-provided executable UI code, SaaS hosting, accounts, multi-reviewer
workflows, browser automation, or automatic agent resume without a new
approved change.

## Verification

- Preserve a version floor containing Gradio's `close()` thread-cleanup fix.
- Test 10 simultaneous review creates, bounded-capacity rejection, distinct
  artifact namespaces, progress under active reviews, close/recycle cleanup,
  and recovery from persisted artifacts.
- Before changing Vision configuration, validate it and sync its non-secret
  backup per the Toolbox instructions.

See `docs/architecture.md` and `docs/operations.md` for the durable design.
