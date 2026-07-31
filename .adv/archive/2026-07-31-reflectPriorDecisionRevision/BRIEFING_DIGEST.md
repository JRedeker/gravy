# Archive Briefing Digest

**Change ID:** reflectPriorDecisionRevision
**Title:** Reflect prior decision on revision
**Status:** archived
**Generated:** 2026-07-31T23:15:55.475Z

## Identity Anchors

- CHANGE
- STATUS
- TERMINAL_GATE_SUMMARY
- Origin: adhoc

## Archive Digest

**Status:** archived

| Gate | Status |
| --- | --- |
| proposal | done |
| discovery | done |
| design | done |
| planning | done |
| execution | done |
| acceptance | done |
| release | pending |

## Epic Context

No Epic membership

## Durable Facts

Showing 7 of 7 durable facts.

- **[report_follow_up]** follow_ups: AC5 tests should assert ranking-list ORDER preservation on gallery round-trip (advisory #1).
- **[report_follow_up]** follow_ups: Confirm gr.Image filepath pre-population graceful degradation when source file absent (advisory #2).
- **[research_citation]** sources: DecisionSurface accessors: latest_decision() returns rows[-1] or None (surface-filtered); latest_per_key(key_fn) returns {key->row} or {} (surface-filtered). Both filter via _surface_decisions() at common.py:52-53. (src/gravy/surfaces/common.py:55-75)
- **[research_citation]** sources: Gallery submit row shape: Appends {surface, selection(str), ranking(list), notes(str)}. Confirmed by test_latest_decision_returns_last_row (tests/test_surfaces.py:135-140). (src/gravy/surfaces/gallery.py:23)
- **[research_citation]** sources: Form submit row shape: Appends {surface, values(dict)}. values validated JSON-serializable at form.py:25 but stored as original dict; JSON round-trip preserves native types (bool stays bool, str stays str). (src/gravy/surfaces/form.py:28)
- **[research_citation]** sources.omitted: 5 additional sources omitted (bounded to first 3)
- **[archive_only_evidence]** architecture_assessment: Design is accurate and contract-aligned. All three accessor/row-shape claims verified against source + existing tests. D1 (gallery/form value= at construction) is type-correct: gr.Radio accepts str selection; gr.Dropdown(multiselect=True) accepts a list value for ranking per Gradio docs; gr.Textbox accepts str notes; form fields map cleanly (text/free_text->Textbox str, toggle->Checkbox bool, option->Radio str, image->Image filepath). D2 (checklist .change() handler) correctly targets AC3 (populate on criterion SELECTION, not load) and reads fresh from latest_per_key each event so post-revision state is always current. D3 (None/{} => blank) is sound: latest_decision() returns None, constructors omit value= and Gradio defaults to blank. AC6 preserved: pre-population is additive (constructor values + one change handler); submit handlers and surface classes are untouched. Surface filtering in _surface_decisions() guarantees no cross-surface contamination if a review_id log ever held mixed rows. No contract item compromised.

## Contract / AC Coverage

| ID | Kind | Status |
| --- | --- | --- |
| AC1 | acceptance_criterion | pass |
| AC2 | acceptance_criterion | pass |
| AC3 | acceptance_criterion | pass |
| AC4 | acceptance_criterion | pass |
| AC5 | acceptance_criterion | pass |
| AC6 | acceptance_criterion | pass |
| SC1 | success_criterion | pass |
| C1 | constraint | respected |
| C2 | constraint | respected |
| DONT1 | avoidance | respected |
| DONT2 | avoidance | respected |
| DONT3 | avoidance | respected |

## Unresolved Actions

None
