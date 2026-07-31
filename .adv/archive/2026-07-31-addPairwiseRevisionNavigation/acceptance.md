# Acceptance

Reviewed at: 2026-07-31T22:54:04.344Z

## Contract Review Matrix

| ID | Kind | Requirement | Status | Evidence |
|---|---|---|---|---|
| AC1 | acceptance_criterion | **AC1 (Pair revision):** Re-deciding a previously-decided pair succeeds; the latest choice per pair is effective; `decisions.jsonl` preserves all rows. | pass | test_pairwise_allows_pair_revision_and_latest_wins: choose_pair revises (a,b) left->right; latest_per_key returns choice=right; 2 rows in decisions.jsonl. runId tr_ms9jccm8_ca77ee32 |
| AC2 | acceptance_criterion | **AC2 (Navigation):** A reviewer can select any decided pair via a navigation affordance and the comparison view loads it for revision. | pass | _build_pairwise dropdown pair-selector loads any pair into comparison view via .change(); choice buttons call choose_pair on active pair via controller.pairwise_choose_pair. Controller wiring test in test_gradio_runtime.py. |
| AC3 | acceptance_criterion | **AC3 (Visibility):** The reviewer can see which pairs are decided and their current effective choice. | pass | _build_choices labels each pair with effective choice via latest_per_key: 'a vs b - left' or 'a vs b - pending'. gradio_runtime.py |
| AC4 | acceptance_criterion | **AC4 (Forward flow preserved):** Advancing through undecided pairs still works; completion counting is unchanged by revisions. | pass | test_pairwise_forward_flow_unchanged_after_revision: revise past pair; current_pair returns next undecided; complete False until all decided. runId tr_ms9jccm8_ca77ee32 |
| AC5 | acceptance_criterion | **AC5 (Skip transition):** Revising a pair between "skip" and a real choice (or vice versa) updates the effective choice and completion correctly. | pass | test_pairwise_skip_to_real_choice_revision: skip->left via choose_pair; effective=left; completion unchanged. runId tr_ms9jccm8_ca77ee32 |
| AC6 | acceptance_criterion | **AC6 (Append-only invariant):** No row mutated/deleted in place; revision appends only. | pass | Only _append/choose_pair append rows; ArtifactStore.append_decision opens mode 'a'. No mutate/delete path in diff. |
| AC7 | acceptance_criterion | **AC7 (Regression tests):** Tests prove revision, navigation, skip-transition, and append-only audit preservation. | pass | 4 new pairwise revision tests + controller wiring test; 13 surface + 81 full suite pass. runId tr_ms9jfy0v_3c1a0bbf |
| SC1 | success_criterion | A reviewer can revise any pairwise decision until the review closes without losing forward progress. | pass | Pairwise now at parity with gallery/form/checklist revision semantics. |
| SC2 | success_criterion | The durable decision log preserves the full revision history per pair. | pass | Append-only log preserved; revision tests assert both rows present in decisions.jsonl. |
| C1 | constraint | No changes to review lifecycle, MCP boundary, or Vision wiring. | respected | Diff confined to src/gravy/surfaces/pairwise.py + gradio_runtime.py + tests. No lifecycle/mcp_boundary/mcp_entry/Vision changes. |
| C2 | constraint | No new surfaces or product features beyond pairwise navigation. | respected | Pair-selector dropdown is the in-scope navigation feature; no other new surfaces/features. |
| C3 | constraint | Decision history remains append-only for audit; revision changes the effective/latest choice per pair only. | respected | _append path unchanged; decisions.jsonl schema unchanged; revision appends only. |
| DONT1 | avoidance | Do not mutate or delete existing decision-log rows in place. | respected | No in-place mutation/deletion of decision rows in diff. |
| DONT2 | avoidance | Do not change the pair combination order (`itertools.combinations` sequence is canonical). | respected | combinations tuple unchanged; pair order preserved; choose_pair validates exact match against canonical tuples. |
| DONT3 | avoidance | Do not disable forward navigation through undecided pairs. | respected | Forward navigation preserved; dropdown defaults to current_pair; buttons reset to current_pair after choice. |

