# Contract Traceability

**Change ID:** allowSurfaceDecisionRevision
**Contract Version:** 1
**Rigor:** standard
**Reviewed:** 2026-07-31T21:53:30.419Z

## Contract Items

| ID | Kind | Status | Evidence Policy | Evidence |
| --- | --- | --- | --- | --- |
| AC1 | acceptance_criterion | pass | test | test_gallery_allows_revision_and_preserves_history: submit gallery twice (revise selection/ranking/notes), no SurfaceValidationError, decisions.jsonl has 2 rows, result.complete True after both. runId tr_ms9h8yyx_8566a091 |
| AC2 | acceptance_criterion | pass | test | test_form_allows_revision_and_preserves_history: submit form twice (revise values), no error, 2 rows, complete after both. runId tr_ms9h8yyx_8566a091 |
| AC3 | acceptance_criterion | pass | test | test_checklist_allows_criterion_revision_and_counts_once: revise criterion 'Has title' twice, no error, 2 rows for criterion, remaining unchanged on revise, final.complete after all criteria. runId tr_ms9h8yyx_8566a091 |
| AC4 | acceptance_criterion | pass | test | Pairwise scoped out with rationale in design.md §D4 and pairwise.py module docstring. Pairwise does not exhibit the reported immutability dead-end; advancing model is correct sequential behavior. Past-pair revision requires new navigation feature (out of boundary). |
| AC5 | acceptance_criterion | pass | test | No mutate/delete of decision rows; ArtifactStore.append_decision opens mode 'a' (verified by adv-researcher against artifacts.py L21-27). Revision tests assert both rows preserved in decisions.jsonl. |
| AC6 | acceptance_criterion | pass | test | latest_decision() and latest_per_key(key_fn) added to DecisionSurface (common.py). test_latest_decision_returns_last_row and test_latest_per_key_dedupes_to_last verify None/{} on empty and last-row-wins semantics. runId tr_ms9h8yyx_8566a091 |
| AC7 | acceptance_criterion | pass | test | 5 new revision tests (gallery/form/checklist revision + latest_decision + latest_per_key) + 4 existing tests = 9/9 pass. Full collectable suite 42/42 pass. runId tr_ms9h9omo_26813089 |
| SC1 | success_criterion | pass | review | Gallery/form/checklist immutability guards removed; reviewers can revise without dead-end error until review close. |
| SC2 | success_criterion | pass | review | Append-only log preserved; revision tests assert both original and revised rows present in decisions.jsonl. |
| C1 | constraint | respected | static_check | Diff confined to src/gravy/surfaces/{common,gallery,form,checklist,pairwise}.py + tests/test_surfaces.py. No changes to lifecycle.py, mcp_boundary.py, mcp_entry.py, or Vision wiring. |
| C2 | constraint | respected | static_check | Change is guard removal + 2 additive accessors + pairwise comment. No new surfaces or product features. |
| C3 | constraint | respected | static_check | _append path unchanged; decisions.jsonl schema unchanged; revision appends only. |
| DONT1 | avoidance | respected | review | No in-place mutation or deletion of decision rows anywhere in the diff. |
| DONT2 | avoidance | respected | review | No submit-button disable logic added or modified in gradio_runtime.py (unchanged). |
| DONT3 | avoidance | respected | review | decisions.jsonl row schema unchanged; recovery path (decisions()) unchanged. |

## Task References

| Task | Implements | Verifies | Respects | N/A Reason |
| --- | --- | --- | --- | --- |
| tk-6900ea688744 |  | AC1, AC2, AC3, AC6, AC7 |  |  |
| tk-f09d0499b5bc | AC1, AC2, AC3, AC4, AC5, AC6 | AC5, AC7 |  |  |
| tk-f444334fb318 |  | AC7, SC1, SC2 |  |  |
