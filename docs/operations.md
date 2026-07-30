# Operations

## Startup

1. Vision starts the loopback Gravy MCP backend.
2. Gravy validates Tailnet HTTPS Serve availability.
3. Gravy atomically loads its registry and reconciles only mappings recorded as
   Gravy-owned stale mappings.
4. Gravy begins accepting bounded review creation requests.

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

## Observability

Emit bounded structured lifecycle fields only: review ID, state, age, port, and
terminal reason. Do not log review-page contents or submitted user data.
