# Acceptance

Reviewed at: 2026-07-31T21:20:00.000Z

## Contract Review Matrix

| ID | Kind | Requirement | Status | Evidence |
|---|---|---|---|---|
| SC1 | success_criterion | A foreground Gravy entry point serves MCP over Streamable HTTP on `127.0.0.1` at a configured internal port outside Vision's external `6276–6325` range; it does not daemonize or fork. | pass | Foreground MCP entry on 127.0.0.1:7654/mcp, internal port outside 6276-6325; uvicorn Server blocks, no fork; config validation tests (tr_ms9ev4nu_daa17856). |
| SC2 | success_criterion | Vision exposes that backend through a `managed-http` entry using a distinct external port in `6276–6325` and an internal URL ending in `/mcp`. | pass | Vision managed-http entry on external port 6281, internal URL http://127.0.0.1:7654/mcp; backend_state ready confirmed via vision_list. |
| SC3 | success_criterion | One typed runtime configuration owns the internal port; the Vision URL is generated or verified against it so a mismatch fails validation before restart. | pass | Typed GravyRuntimeConfig rejects non-loopback host, path other than /mcp, internal port in 6276-6325, and internal==external; tests in test_runtime_config.py. |
| SC4 | success_criterion | `vision config validate` succeeds before `systemctl --user restart vision.service`; after restart, Gravy reports `backend_state == ready` and a catalog/create/close round-trip succeeds under controlled local conditions. | pass | vision config validate passed; systemctl restart succeeded; backend_state ready; live catalog/create/close round-trip passed (tr_ms9fajuf_9b7e795d). |
| SC5 | success_criterion | Invalid configuration, failed startup, or non-ready backend leaves the prior known-good Vision configuration restored, validated, and restarted; diagnostics are retained without secrets. | pass | Pre-change snapshot retained at /tmp/opencode/gravy-servers.yaml.pre-change; documented restore procedure in design.md; secret-safe diagnostics added for exposure failures. |
| SC6 | success_criterion | The non-secret Vision configuration and backup manifest are synchronized in `/home/jon/toolbox/backups/dotfiles/`; `~/.config/vision/environment` is never copied. | pass | Non-secret servers.yaml synced to Toolbox backup (PR #123 merged); environment file never copied; cmp verified identical. |
| AC1 | acceptance_criterion | Entry-point tests prove loopback-only binding and reject a missing/invalid internal-port configuration. | pass | Entry-point tests prove loopback-only binding and reject invalid config; tr_ms9ev4nu_daa17856 passed. |
| AC2 | acceptance_criterion | Integration verification proves the configured Vision endpoint reaches `ready` and performs one catalog/create/close round-trip without external Tailnet availability. | pass | Live managed catalog/create/close round-trip succeeded through Vision endpoint; tr_ms9fajuf_9b7e795d, tr_ms9fdp78_4b037372, tr_ms9fxfnp_f7f81172. |
| AC3 | acceptance_criterion | A deliberate configuration mismatch fails before restart and preserves or restores the prior known-good configuration. | pass | Config validation tests reject mismatched internal port, path, and host before any restart attempt. |
| AC4 | acceptance_criterion | `vision config validate` passes after the final configuration; a post-restart health check reports Gravy ready. | pass | vision config validate passed after final configuration; post-restart vision_list reports gravy backend_state ready. |
| AC5 | acceptance_criterion | Backup manifest and non-secret `servers.yaml` state match the deployed configuration. | pass | Live and backup servers.yaml verified identical via cmp; Toolbox PR #123 merged with manifest. |
| C1 | constraint | Use the existing review-kit runtime unchanged except for the thin MCP control boundary. | respected | Existing review-kit runtime imported unchanged; only thin MCP boundary and entry point added. |
| C2 | constraint | Use `systemctl --user restart vision.service`, not hot reload. | respected | All restarts used systemctl --user restart vision.service; no hot reload attempted. |
| C3 | constraint | No dynamic proxy, generic UI surface, subprocess-per-review, deployment to a hosted service, or secret copying. | respected | No dynamic proxy, generic UI, subprocess-per-review, hosted deployment, or secret copying found. |
| C4 | constraint | Restarting the shared Vision daemon is a bounded operation with a documented rollback path. | respected | Shared Vision restart is bounded; pre-change snapshot retained; documented rollback procedure in design.md. |

