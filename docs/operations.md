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

## Vision runtime wiring

Vision runs the foreground MCP entry point with `python -m gravy.mcp_entry`.
The entry point never daemonizes or forks. Its defaults are intentionally
separate: Gravy binds `127.0.0.1:7654/mcp`, while Vision's `managed-http` entry
publishes external port `6281` and forwards it to
`http://127.0.0.1:7654/mcp`. Vision must health-check `GET /ready`, which
returns `{"status":"ready"}` only after the MCP server is accepting requests.

The runtime accepts these non-secret environment variables:

- `GRAVY_INTERNAL_HOST` — must remain `127.0.0.1` (default).
- `GRAVY_INTERNAL_PORT` — loopback MCP listener port (default `7654`); it must
  be outside Vision's external `6276–6325` range.
- `GRAVY_EXTERNAL_PORT` — Vision `managed-http` port (default `6281`); it must
  be within `6276–6325` and differ from the internal port.
- `GRAVY_PATH` — must remain `/mcp` (default).
- `GRAVY_STATE_DIR` — durable local lifecycle/artifact directory (default
  `~/.local/share/gravy`).

Invalid runtime settings fail validation before the server binds. Keep Vision
configuration and these values synchronized; do not place secrets in Gravy
environment configuration or copy Vision's private environment file.

## Vision configuration rollout and rollback

1. Snapshot the known-good non-secret Vision server configuration.
2. Update the `managed-http` entry to run the foreground entry point, expose
   external port `6281`, target `http://127.0.0.1:7654/mcp`, and check
   `http://127.0.0.1:7654/ready`.
3. Run `vision config validate`, then restart only with
   `systemctl --user restart vision.service`.
4. Confirm Vision reports the Gravy backend ready and perform one
   `catalog`/`create`/`close` MCP round-trip.

If validation, startup, or readiness fails, restore the prior non-secret
configuration snapshot, run `vision config validate`, restart Vision with the
same command, and retain only secret-safe diagnostics. Do not hot-reload the
shared daemon.

## Supported catalog and control operations

The control plane exposes only `catalog`, `create`, `update`, and `close`.
`create` also serves the review page, so there is no separate serve operation.

`catalog` contains exactly `gallery`, `pairwise`, `form`, `checklist`, and `queue`.
`checklist` decisions include an explicit boolean status and comment for each
declared criterion. `queue` decisions assign every item to one of a closed set of
outcome buckets. `annotation`, `document`, and `preview` remain deferred and
unimplemented. Do not add a custom surface, generic renderer, or agent-provided
executable UI path.

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
