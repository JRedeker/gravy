# Contract Traceability

**Change ID:** addPairwiseRevisionNavigation
**Contract Version:** 1
**Rigor:** standard
**Reviewed:** 2026-07-31T22:54:04.344Z

## Contract Items

| ID | Kind | Status | Evidence Policy | Evidence |
| --- | --- | --- | --- | --- |
| AC1 | acceptance_criterion | pass | test | test_pairwise_allows_pair_revision_and_latest_wins: choose_pair revises (a,b) left->right; latest_per_key returns choice=right; 2 rows in decisions.jsonl. runId tr_ms9jccm8_ca77ee32 |
| AC2 | acceptance_criterion | pass | test | _build_pairwise dropdown pair-selector loads any pair into comparison view via .change(); choice buttons call choose_pair on active pair via controller.pairwise_choose_pair. Controller wiring test in test_gradio_runtime.py. |
| AC3 | acceptance_criterion | pass | test | _build_choices labels each pair with effective choice via latest_per_key: 'a vs b - left' or 'a vs b - pending'. gradio_runtime.py |
| AC4 | acceptance_criterion | pass | test | test_pairwise_forward_flow_unchanged_after_revision: revise past pair; current_pair returns next undecided; complete False until all decided. runId tr_ms9jccm8_ca77ee32 |
| AC5 | acceptance_criterion | pass | test | test_pairwise_skip_to_real_choice_revision: skip->left via choose_pair; effective=left; completion unchanged. runId tr_ms9jccm8_ca77ee32 |
| AC6 | acceptance_criterion | pass | test | Only _append/choose_pair append rows; ArtifactStore.append_decision opens mode 'a'. No mutate/delete path in diff. |
| AC7 | acceptance_criterion | pass | test | 4 new pairwise revision tests + controller wiring test; 13 surface + 81 full suite pass. runId tr_ms9jfy0v_3c1a0bbf |
| SC1 | success_criterion | pass | review | Pairwise now at parity with gallery/form/checklist revision semantics. |
| SC2 | success_criterion | pass | review | Append-only log preserved; revision tests assert both rows present in decisions.jsonl. |
| C1 | constraint | respected | static_check | Diff confined to src/gravy/surfaces/pairwise.py + gradio_runtime.py + tests. No lifecycle/mcp_boundary/mcp_entry/Vision changes. |
| C2 | constraint | respected | static_check | Pair-selector dropdown is the in-scope navigation feature; no other new surfaces/features. |
| C3 | constraint | respected | static_check | _append path unchanged; decisions.jsonl schema unchanged; revision appends only. |
| DONT1 | avoidance | respected | review | No in-place mutation/deletion of decision rows in diff. |
| DONT2 | avoidance | respected | review | combinations tuple unchanged; pair order preserved; choose_pair validates exact match against canonical tuples. |
| DONT3 | avoidance | respected | review | Forward navigation preserved; dropdown defaults to current_pair; buttons reset to current_pair after choice. |

## Task References

| Task | Implements | Verifies | Respects | N/A Reason |
| --- | --- | --- | --- | --- |
| tk-6321b7836b43 | AC1, AC2, AC3, AC4, AC5, AC6 | AC6, AC7 |  |  |
| tk-5be51dea90c4 |  | AC1, AC4, AC5, AC6, AC7 |  |  |
| tk-a3fd102c4c36 |  | AC7, SC1, SC2 |  |  |
