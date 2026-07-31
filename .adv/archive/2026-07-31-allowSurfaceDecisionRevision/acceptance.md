# Acceptance

Reviewed at: 2026-07-31T21:53:30.419Z

## Contract Review Matrix

| ID | Kind | Requirement | Status | Evidence |
|---|---|---|---|---|
| AC1 | acceptance_criterion | **AC1 (Gallery revision):** A reviewer can submit, then revise and resubmit on the gallery surface without error; `decisions.jsonl` contains both rows; the surface reports complete after each. | pass | test_gallery_allows_revision_and_preserves_history: submit gallery twice (revise selection/ranking/notes), no SurfaceValidationError, decisions.jsonl has 2 rows, result.complete True after both. runId tr_ms9h8yyx_8566a091 |
| AC2 | acceptance_criterion | **AC2 (Form revision):** Same as AC1 for the form surface (field values). | pass | test_form_allows_revision_and_preserves_history: submit form twice (revise values), no error, 2 rows, complete after both. runId tr_ms9h8yyx_8566a091 |
| AC3 | acceptance_criterion | **AC3 (Checklist revision):** Re-submitting an already-decided criterion succeeds; the latest row for that criterion is effective; completion counts each criterion exactly once regardless of revision count. | pass | test_checklist_allows_criterion_revision_and_counts_once: revise criterion 'Has title' twice, no error, 2 rows for criterion, remaining unchanged on revise, final.complete after all criteria. runId tr_ms9h8yyx_8566a091 |
| AC4 | acceptance_criterion | **AC4 (Pairwise disposition):** Pairwise is either fixed with a documented revision mechanism, or explicitly scoped out with rationale recorded in design.md. | pass | Pairwise scoped out with rationale in design.md §D4 and pairwise.py module docstring. Pairwise does not exhibit the reported immutability dead-end; advancing model is correct sequential behavior. Past-pair revision requires new navigation feature (out of boundary). |
| AC5 | acceptance_criterion | **AC5 (Append-only invariant):** No existing row in `decisions.jsonl` is ever mutated or deleted in place; revision appends only. | pass | No mutate/delete of decision rows; ArtifactStore.append_decision opens mode 'a' (verified by adv-researcher against artifacts.py L21-27). Revision tests assert both rows preserved in decisions.jsonl. |
| AC6 | acceptance_criterion | **AC6 (Recovery fidelity):** Reconstructing a surface from `decisions.jsonl` after recycle treats the latest row per key as the effective decision. | pass | latest_decision() and latest_per_key(key_fn) added to DecisionSurface (common.py). test_latest_decision_returns_last_row and test_latest_per_key_dedupes_to_last verify None/{} on empty and last-row-wins semantics. runId tr_ms9h8yyx_8566a091 |
| AC7 | acceptance_criterion | **AC7 (Regression tests):** Tests prove revision semantics for each in-scope surface and verify the append-only audit history is preserved. | pass | 5 new revision tests (gallery/form/checklist revision + latest_decision + latest_per_key) + 4 existing tests = 9/9 pass. Full collectable suite 42/42 pass. runId tr_ms9h9omo_26813089 |
| SC1 | success_criterion | A reviewer can revise any decision on any in-scope surface until the review is closed without encountering a dead-end error. | pass | Gallery/form/checklist immutability guards removed; reviewers can revise without dead-end error until review close. |
| SC2 | success_criterion | The durable decision log preserves the full revision history for audit. | pass | Append-only log preserved; revision tests assert both original and revised rows present in decisions.jsonl. |
| C1 | constraint | No changes to review lifecycle, MCP boundary, or Vision wiring. | respected | Diff confined to src/gravy/surfaces/{common,gallery,form,checklist,pairwise}.py + tests/test_surfaces.py. No changes to lifecycle.py, mcp_boundary.py, mcp_entry.py, or Vision wiring. |
| C2 | constraint | No new surfaces or product features. | respected | Change is guard removal + 2 additive accessors + pairwise comment. No new surfaces or product features. |
| C3 | constraint | Decision history remains append-only for audit; revision changes the effective/latest decision only. | respected | _append path unchanged; decisions.jsonl schema unchanged; revision appends only. |
| DONT1 | avoidance | Do not mutate or delete existing decision-log rows in place. | respected | No in-place mutation or deletion of decision rows anywhere in the diff. |
| DONT2 | avoidance | Do not disable the submit button after first decision (revision must remain possible until close). | respected | No submit-button disable logic added or modified in gradio_runtime.py (unchanged). |
| DONT3 | avoidance | Do not change the durable decision-log schema in a way that breaks recovery from persisted artifacts. | respected | decisions.jsonl row schema unchanged; recovery path (decisions()) unchanged. |

