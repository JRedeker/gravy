# Acceptance

Reviewed at: 2026-07-31T23:14:37.128Z

## Contract Review Matrix

| ID | Kind | Requirement | Status | Evidence |
|---|---|---|---|---|
| AC1 | acceptance_criterion | **AC1 (Gallery pre-population):** Opening a gallery review that already has a decision shows the prior selection/ranking/notes in the inputs. | pass | test_gallery_prior_returns_latest_decision: gallery_prior() returns {selection, ranking, notes} from latest decision; None when undecided. runId tr_ms9k756q_9a345692 |
| AC2 | acceptance_criterion | **AC2 (Form pre-population):** Opening a form review that already has a decision shows the prior field values. | pass | test_form_prior_returns_latest_values: form_prior() returns {field: value} from latest decision; {} when undecided. runId tr_ms9k756q_9a345692 |
| AC3 | acceptance_criterion | **AC3 (Checklist pre-population):** Selecting a decided criterion in the checklist dropdown populates pass/comment from that criterion's latest decision. | pass | test_checklist_prior_returns_decided_criterion: checklist_prior(criterion) returns (passed, comment) from latest_per_key; (False,'') when undecided. Builder wires criterion.change(populate). runId tr_ms9k756q_9a345692 |
| AC4 | acceptance_criterion | **AC4 (No-decision case):** When no decision exists, fields render blank (no regression). | pass | test_no_decision_renders_blank_values: gallery_prior()=None, form_prior()={}, checklist_prior()=(False,'') when no decision. runId tr_ms9k756q_9a345692 |
| AC5 | acceptance_criterion | **AC5 (Tests):** Assertions that initial values reflect a prior decision for each surface. | pass | 4 new controller-level tests covering gallery/form/checklist prior + no-decision case. 12 gradio_runtime tests pass. |
| AC6 | acceptance_criterion | **AC6 (No semantic change):** Pre-population does not alter submission, validation, or append-only behavior. | pass | Purely additive initial-value population; submit handlers and surface classes unmodified; accessors read-only. 85 full suite pass (no submission/validation regressions). |
| SC1 | success_criterion | A reviewer revising a decision sees their prior submission in the fields and edits in place rather than re-entering from scratch. | pass | Reviewer sees prior submission in fields and edits in place rather than re-entering. |
| C1 | constraint | No changes to surface semantics, persistence, lifecycle, MCP boundary, or Vision wiring. | respected | Diff confined to gradio_runtime.py + test_gradio_runtime.py. No surface/persistence/lifecycle/MCP/Vision changes. |
| C2 | constraint | No new surfaces; pre-population is confined to initial-value population in the Gradio builders. | respected | No new surfaces; initial-value population only. |
| DONT1 | avoidance | Do not mutate or delete existing decision rows. | respected | No mutation/deletion of decision rows. |
| DONT2 | avoidance | Do not block submission or change validation rules. | respected | No submission blocking or validation rule changes. |
| DONT3 | avoidance | Do not re-architect the Gradio builders beyond initial-value population. | respected | Builders unchanged beyond initial-value population (no re-architecture). |

