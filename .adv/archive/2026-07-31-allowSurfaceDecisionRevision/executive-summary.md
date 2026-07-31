# Executive Summary: Allow surface decision revision

## Outcome
Gravy's gallery, form, and checklist surfaces no longer block reviewers from revising a decision after their first submission. Previously, any resubmission hit a dead-end error (`gallery already has a decision`) while the Gradio UI kept the submit button enabled — leaving the reviewer unable to correct a selection, ranking, notes, field values, or checklist answers before the agent collected their final feedback. Reviewers can now revise freely until the review closes.

## Value / why it matters
Gravy's whole purpose is to capture a human's final, considered judgment for a coding agent. Forcing one-shot immutability contradicted that: a misclick or second thought became unrecoverable. Last-submission-wins semantics align the surfaces with how review actually works — people revise their minds — while preserving a full append-only audit trail of every revision.

## What changed
- **Gallery / Form:** removed the one-shot immutability guard. Any submission completes the surface; the latest appended row is the effective decision.
- **Checklist:** removed the per-criterion re-submit guard. A criterion can be revised; completion still counts each criterion exactly once.
- **Pairwise:** scoped out (documented rationale). Pairwise's advancing model is correct sequential ranking behavior and does not exhibit the reported immutability dead-end; past-pair revision would require a new navigation feature outside this change's boundary.
- **Recovery support:** added `latest_decision()` and `latest_per_key()` accessors to the shared surface base class so "latest-wins" effective-decision semantics are explicit and testable for reconstruction after recycle.

## Verification
- TDD: 5 new revision tests written first (red), then implementation made them pass (green). 9/9 surface tests pass; 42/42 collectable suite tests pass.
- Design independently validated by adv-researcher (CONFIRM, high confidence, low risk).
- 4 gradio-dependent test modules fail only at collection (gradio not installed in this environment) — pre-existing, unrelated to the change.

## Risks / follow-ups
- Pairwise past-pair revision remains a known navigation limitation; a future change could add a previous-pair control if ranking tasks need it.
- UI pre-population of prior decisions on revision is a possible UX follow-up, not required by any acceptance criterion.
- Concurrent revision from two tabs: append is atomic; last write wins; both rows persist. Acceptable for the single-reviewer model.