# Executive Summary: Reflect prior decision on revision

## Outcome
Gallery, form, and checklist surfaces now show the reviewer's prior submission in the input fields when a review is opened or re-opened with an existing decision. Previously, revision rendered blank fields — the reviewer had to re-enter their entire prior selection/ranking/notes/values from scratch even to change one field. Revision now happens in place: change only what you want, untouched fields retain their prior value.

## Value / why it matters
Revision was technically possible after `allowSurfaceDecisionRevision` but practically painful — the prior decision existed in the log but was invisible in the UI. Pre-population closes that gap, making the revision feature actually usable for the common case (tweak one field, keep the rest).

## What changed
- Added `gallery_prior()`, `form_prior()`, and `checklist_prior(criterion)` to `ReviewPageController`, surfacing the latest decision for UI consumption.
- Gallery/form builders set initial component values from the prior decision at construction.
- Checklist builder adds a `.change()` handler on the criterion dropdown that populates pass/comment from the selected criterion's latest decision.
- Pairwise already showed effective choices via its dropdown (no change needed).

## Verification
- TDD: 4 new controller-level tests (red→green). 12 gradio_runtime + 85 full suite pass.
- Design validated by adv-researcher (CONFIRM, high confidence, low risk).
- No surface/persistence/semantic changes — purely initial-value population.

## Risks / follow-ups
- None material. Builder-level Gradio component introspection is intentionally avoided (fragile); controller-level tests cover the pre-population data, and the builder wiring follows the proven pairwise pattern.