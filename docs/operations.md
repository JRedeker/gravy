# Operations

## Startup

1. Vision starts the loopback Gravy MCP backend.
2. Gravy validates Tailnet HTTPS Serve availability.
3. Gravy atomically loads its registry, terminalizes records that were active
   before the recycle with their artifact recovery pointers, and reconciles only
   mappings recorded as Gravy-owned stale mappings.
4. Gravy begins accepting bounded review creation requests.

Startup never runs `tailscale serve reset`. That command could clear mappings
outside Gravy's ownership; Gravy may remove only a mapping named by its own
persisted review record.

## Supported catalog and control operations

The control plane exposes only `catalog`, `create`, `update`, and `close`.
`create` also serves the review page, so there is no separate serve operation.

`catalog` contains exactly `gallery`, `pairwise`, `form`, and `checklist`.
Checklist decisions include an explicit boolean status and comment for each
declared criterion. `annotation`, `queue`, `document`, and `preview` remain
deferred and unimplemented. Do not add a custom surface, generic renderer, or
agent-provided executable UI path.

## Create and close

Create reserves a bounded port, starts the in-process Gradio server, writes the
review record, creates the Tailnet Serve mapping, and returns only after those
steps succeed. On failure it releases any acquired resource and returns a typed
diagnostic.

Close removes the Tailnet Serve mapping, stops the Gradio listener, marks the
review terminal, and releases the port. Unknown or already-terminal IDs return
a typed terminal result without touching another review.

## Recovery

If Vision recycles or Gravy fails, active pages may end. Decision artifacts stay
available. The terminal review record supplies the artifact recovery pointer so
an agent can create a replacement review without duplicating recorded decisions.
The failed lifecycle mutation is not replayed automatically. Unknown or already
terminal review IDs return a typed terminal result and cannot alter another
review.

## Observability

Emit bounded structured lifecycle fields only: review ID, state, age, port, and
terminal reason. Do not log review-page contents or submitted user data.
