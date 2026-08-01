# Archive Briefing Digest

**Change ID:** addQueueTriageSurface
**Title:** Add queue triage surface
**Status:** archived
**Generated:** 2026-08-01T17:09:39.123Z

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

Showing 14 of 14 durable facts.

- **[archive_only_evidence]** decisions: Updated two additional existing tests (test_control_plane.py, test_mcp_entry.py) beyond the RED-phase list to remove 'queue' from deferred expected sets and include it in supported surfaces — Full-suite verification failed until those catalog assertions matched the new reality; they are part of the same surface rollout and safe to update.
- **[archive_only_evidence]** decisions: Used frozenset membership validation in QueueSurface.submit — Matches existing form/gallery pattern for closed-field whole-surface validation.
- **[archive_only_evidence]** decisions: Implemented queue_prior returning {} when no decision exists — Mirrors form_prior contract used by the builder for pre-population.
- **[archive_only_evidence]** verification: uv run --group test pytest tests/test_surfaces.py tests/test_schemas.py tests/test_gradio_runtime.py tests/test_mcp_boundary.py -v (0) — RED-phase targeted tests: 49 passed after implementation (new queue tests + updated existing tests)
- **[archive_only_evidence]** verification: uv run --group test pytest (0) — GREEN full suite: 94 passed in ~24s
- **[unresolved_action]** consumer_warnings: verification_missing: No durable adv_run_test evidence found for run_id: local-pytest-targeted-addQueueTriageSurface
- **[unresolved_action]** consumer_warnings: verification_missing: No durable adv_run_test evidence found for run_id: local-pytest-full-addQueueTriageSurface
- **[report_follow_up]** follow_ups: Packet provided WORKING DIRECTORY/CHANGE/SCOPE KEY/ATTEMPT/PHASE anchors but omitted explicit TASK_SCOPE/IN_SCOPE/OUT_OF_SCOPE/DONE_WHEN/STOP_WHEN/VERIFICATION blocks; scope inferred from 'What to validate' + 'Deliverable' sections.
- **[report_follow_up]** follow_ups: Consider whether duplicate item strings in a request (allowed by _string_list, which does not dedupe) need handling — pre-existing pattern shared with gallery/form, not queue-specific, but worth a decision if it matters for triage semantics.
- **[research_citation]** sources: src/gravy/surfaces/common.py (DecisionSurface base): DecisionSurface provides _append, latest_decision() (last row wins, returns None when undecided), _surface_decisions, decisions. Whole-surface pattern. Sufficient for QueueSurface. (src/gravy/surfaces/common.py:26-78)
- **[research_citation]** sources: src/gravy/surfaces/form.py (whole-surface single-decision reference): FormSurface validates set(values) != self._fields (frozenset) -> SurfaceValidationError; _append({surface, values}); complete=True. QueueSurface D2 mirrors this exactly. (src/gravy/surfaces/form.py:13-29)
- **[research_citation]** sources: src/gravy/surfaces/gallery.py (whole-surface reference): GallerySurface: set(ranking) == set(items) check, _append, complete=True. Confirms whole-surface revision pattern. (src/gravy/surfaces/gallery.py:9-24)
- **[research_citation]** sources.omitted: 7 additional sources omitted (bounded to first 3)
- **[archive_only_evidence]** architecture_assessment: QueueSurface D1-D3 correctly follows the gallery/form whole-surface single-decision pattern. DecisionSurface (common.py:26-78) provides every primitive needed: _append (append-only, artifacts.py opens 'a' mode), latest_decision() (last row wins, None when undecided), _surface_decisions (filters by surface). No new base-class capability required. D2 validation `set(assignments) != set(self._items)` is structurally identical to FormSurface's `set(values) != self._fields` (form.py:20-22): it catches missing keys AND extra keys in one check; duplicate keys are impossible in a Python dict so 'exactly once' is guaranteed by construction. The bucket-in-options check `any(b not in self._options ...)` correctly complements it. Schema approach reuses _string_list + _require_exact_keys identically to gallery/pairwise/checklist; the len(options)>=2 gate has precedent in FormField option type (schemas.py:56-59). Catalog entry shape and _BUILDERS/_surface_for_request registration match existing entries exactly. The CORE surface design is correct. The GAP: the design's '6 integration points' and 'Risks: None material' understate the real blast radius of promoting a deferred surface to real. queue appears in DEFERRED_SURFACES (catalog.py:8) and 4 boundary docs as deferred, and 3 tests assert the 4-surface closed catalog. These are not design errors but omissions in the integration plan that will cause red tests + stale/contradictory boundary docs if not addressed.

## Contract / AC Coverage

| ID | Kind | Status |
| --- | --- | --- |
| AC1 | acceptance_criterion | pass |
| AC2 | acceptance_criterion | pass |
| AC3 | acceptance_criterion | pass |
| AC4 | acceptance_criterion | pass |
| AC5 | acceptance_criterion | pass |
| AC6 | acceptance_criterion | pass |
| AC7 | acceptance_criterion | pass |
| SC1 | success_criterion | pass |
| C1 | constraint | respected |
| C2 | constraint | respected |
| C3 | constraint | respected |
| DONT1 | avoidance | respected |
| DONT2 | avoidance | respected |
| DONT3 | avoidance | respected |

## Unresolved Actions

- verification_missing: No durable adv_run_test evidence found for run_id: local-pytest-targeted-addQueueTriageSurface
- verification_missing: No durable adv_run_test evidence found for run_id: local-pytest-full-addQueueTriageSurface
