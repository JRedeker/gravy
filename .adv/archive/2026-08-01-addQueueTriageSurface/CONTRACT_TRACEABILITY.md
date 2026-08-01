# Contract Traceability

**Change ID:** addQueueTriageSurface
**Contract Version:** 1
**Rigor:** standard
**Reviewed:** 2026-08-01T15:44:11.662Z

## Contract Items

| ID | Kind | Status | Evidence Policy | Evidence |
| --- | --- | --- | --- | --- |
| AC1 | acceptance_criterion | pass | test | test_queue_persists_item_bucket_assignments: submit {item:bucket} for all items; decision row has {surface:queue, assignments:{...}}; complete=True. 94/94 pass runId tr_msajjgzh_70690921 |
| AC2 | acceptance_criterion | pass | test | test_queue_rejects_missing_item + test_queue_rejects_invalid_bucket: both raise SurfaceValidationError. 94/94 pass. |
| AC3 | acceptance_criterion | pass | test | test_queue_allows_revision_and_latest_wins: submit twice; 2 rows; latest_decision() returns revised. 94/94 pass. |
| AC4 | acceptance_criterion | pass | test | test_queue_prior_returns_latest: queue_prior() returns assignments from latest_decision; {} when undecided. _build_queue pre-populates Radio values from queue_prior(). 94/94 pass. |
| AC5 | acceptance_criterion | pass | test | catalog.py: queue entry in _SURFACES with schema+example; removed from DEFERRED_SURFACES. test_mcp_boundary + test_schemas catalog tests pass with 5 surfaces. |
| AC6 | acceptance_criterion | pass | test | Only _append; ArtifactStore opens mode 'a'. No mutate/delete. 94/94 pass. |
| AC7 | acceptance_criterion | pass | test | Surface tests (4) + schema tests (3) + runtime tests (2) + existing catalog/mcp test updates. 94/94 full suite pass. |
| SC1 | success_criterion | pass | review | Agent creates queue review with items+options in one create call; receives clean {item:bucket} decision. |
| C1 | constraint | respected | static_check | Existing surfaces/schemas unchanged; queue is additive. 94/94 pass. |
| C2 | constraint | respected | static_check | No per-item free-text notes; pure bucket assignment. |
| C3 | constraint | respected | static_check | No reordering/ranking within buckets; flat {item:bucket} mapping. |
| DONT1 | avoidance | respected | review | No mutation/deletion of decision rows. |
| DONT2 | avoidance | respected | review | Existing surfaces and schemas unchanged. |
| DONT3 | avoidance | respected | review | No reordering within buckets. |

## Task References

| Task | Implements | Verifies | Respects | N/A Reason |
| --- | --- | --- | --- | --- |
| tk-fa463f18b931 |  | AC1, AC2, AC3, AC6, AC7 |  |  |
| tk-ed0e8a3b1dff | AC1, AC2, AC3, AC4, AC5, AC6 | AC7 |  |  |
