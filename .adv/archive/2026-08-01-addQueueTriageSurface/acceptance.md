# Acceptance

Reviewed at: 2026-08-01T15:44:11.662Z

## Contract Review Matrix

| ID | Kind | Requirement | Status | Evidence |
|---|---|---|---|---|
| AC1 | acceptance_criterion | **AC1 (Queue triage):** Reviewer assigns each item to a bucket and submits; decision stores `{item: bucket}` for all items. | pass | test_queue_persists_item_bucket_assignments: submit {item:bucket} for all items; decision row has {surface:queue, assignments:{...}}; complete=True. 94/94 pass runId tr_msajjgzh_70690921 |
| AC2 | acceptance_criterion | **AC2 (Validation):** Submit rejects (SurfaceValidationError) if any item is missing or any bucket is not in the allowed options. | pass | test_queue_rejects_missing_item + test_queue_rejects_invalid_bucket: both raise SurfaceValidationError. 94/94 pass. |
| AC3 | acceptance_criterion | **AC3 (Revision):** Resubmit appends a new row; `latest_decision()` is effective (consistent with gallery/form). | pass | test_queue_allows_revision_and_latest_wins: submit twice; 2 rows; latest_decision() returns revised. 94/94 pass. |
| AC4 | acceptance_criterion | **AC4 (Pre-population):** On re-open, prior assignments populate the selectors (consistent with reflectPriorDecisionRevision). | pass | test_queue_prior_returns_latest: queue_prior() returns assignments from latest_decision; {} when undecided. _build_queue pre-populates Radio values from queue_prior(). 94/94 pass. |
| AC5 | acceptance_criterion | **AC5 (Catalog):** Queue appears in the MCP catalog with schema + example. | pass | catalog.py: queue entry in _SURFACES with schema+example; removed from DEFERRED_SURFACES. test_mcp_boundary + test_schemas catalog tests pass with 5 surfaces. |
| AC6 | acceptance_criterion | **AC6 (Append-only):** No row mutated/deleted; revision appends only. | pass | Only _append; ArtifactStore opens mode 'a'. No mutate/delete. 94/94 pass. |
| AC7 | acceptance_criterion | **AC7 (Tests):** Surface + runtime + schema validation tests. | pass | Surface tests (4) + schema tests (3) + runtime tests (2) + existing catalog/mcp test updates. 94/94 full suite pass. |
| SC1 | success_criterion | An agent creates a queue triage review with items + options and receives a clean {item: bucket} decision via one minimal create call. | pass | Agent creates queue review with items+options in one create call; receives clean {item:bucket} decision. |
| C1 | constraint | No changes to existing surfaces or schemas. | respected | Existing surfaces/schemas unchanged; queue is additive. 94/94 pass. |
| C2 | constraint | No per-item free-text notes (pure triage; use form for rich per-item feedback). | respected | No per-item free-text notes; pure bucket assignment. |
| C3 | constraint | No reordering within buckets (assignment, not ranking). | respected | No reordering/ranking within buckets; flat {item:bucket} mapping. |
| DONT1 | avoidance | Do not mutate or delete existing decision rows. | respected | No mutation/deletion of decision rows. |
| DONT2 | avoidance | Do not change existing surfaces or their schemas. | respected | Existing surfaces and schemas unchanged. |
| DONT3 | avoidance | Do not add reordering/ranking within buckets. | respected | No reordering within buckets. |

