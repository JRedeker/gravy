# Contract Traceability

**Change ID:** addGravyRuntimeWiring
**Contract Version:** 1
**Rigor:** strict
**Reviewed:** 2026-07-31T21:20:00.000Z

## Contract Items

| ID | Kind | Status | Evidence Policy | Evidence |
| --- | --- | --- | --- | --- |
| SC1 | success_criterion | pass | review | Foreground MCP entry on 127.0.0.1:7654/mcp, internal port outside 6276-6325; uvicorn Server blocks, no fork; config validation tests (tr_ms9ev4nu_daa17856). |
| SC2 | success_criterion | pass | review | Vision managed-http entry on external port 6281, internal URL http://127.0.0.1:7654/mcp; backend_state ready confirmed via vision_list. |
| SC3 | success_criterion | pass | review | Typed GravyRuntimeConfig rejects non-loopback host, path other than /mcp, internal port in 6276-6325, and internal==external; tests in test_runtime_config.py. |
| SC4 | success_criterion | pass | review | vision config validate passed; systemctl restart succeeded; backend_state ready; live catalog/create/close round-trip passed (tr_ms9fajuf_9b7e795d). |
| SC5 | success_criterion | pass | review | Pre-change snapshot retained at /tmp/opencode/gravy-servers.yaml.pre-change; documented restore procedure in design.md; secret-safe diagnostics added for exposure failures. |
| SC6 | success_criterion | pass | review | Non-secret servers.yaml synced to Toolbox backup (PR #123 merged); environment file never copied; cmp verified identical. |
| AC1 | acceptance_criterion | pass | test | Entry-point tests prove loopback-only binding and reject invalid config; tr_ms9ev4nu_daa17856 passed. |
| AC2 | acceptance_criterion | pass | test | Live managed catalog/create/close round-trip succeeded through Vision endpoint; tr_ms9fajuf_9b7e795d, tr_ms9fdp78_4b037372, tr_ms9fxfnp_f7f81172. |
| AC3 | acceptance_criterion | pass | test | Config validation tests reject mismatched internal port, path, and host before any restart attempt. |
| AC4 | acceptance_criterion | pass | test | vision config validate passed after final configuration; post-restart vision_list reports gravy backend_state ready. |
| AC5 | acceptance_criterion | pass | test | Live and backup servers.yaml verified identical via cmp; Toolbox PR #123 merged with manifest. |
| C1 | constraint | respected | static_check | Existing review-kit runtime imported unchanged; only thin MCP boundary and entry point added. |
| C2 | constraint | respected | static_check | All restarts used systemctl --user restart vision.service; no hot reload attempted. |
| C3 | constraint | respected | static_check | No dynamic proxy, generic UI, subprocess-per-review, hosted deployment, or secret copying found. |
| C4 | constraint | respected | static_check | Shared Vision restart is bounded; pre-change snapshot retained; documented rollback procedure in design.md. |

## Task References

| Task | Implements | Verifies | Respects | N/A Reason |
| --- | --- | --- | --- | --- |
| tk-ce7679584f97 | SC1, SC3 | AC1, AC2 | C1, C3 |  |
| tk-8b25edf7f95f | SC2, SC5, SC6 | AC3, AC4, AC5 | C2, C4 |  |
| tk-cefd8dc542a5 |  | AC1, AC2, AC3, AC4, AC5 | C1, C2, C3, C4 |  |
