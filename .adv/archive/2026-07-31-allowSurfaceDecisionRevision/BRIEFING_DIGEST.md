# Archive Briefing Digest

**Change ID:** allowSurfaceDecisionRevision
**Title:** Allow surface decision revision
**Status:** archived
**Generated:** 2026-07-31T21:54:44.354Z

## Identity Anchors

- CHANGE
- STATUS
- TERMINAL_GATE_SUMMARY
- Origin: discovery

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

- **[report_follow_up]** follow_ups: Pre-existing (NOT design-introduced): append_decision is not atomic against a mid-write crash producing a partial JSON line; decisions() would raise SurfaceValidationError('cannot reconstruct corrupt decision history') on such a line. Out of scope for this change but worth a future hardening note.
- **[report_follow_up]** follow_ups: Execution: ensure AC7 tests exercise latest_per_key for the revised criterion (not just completion counting) to prove AC6 recovery fidelity at the effective-decision level.
- **[research_citation]** sources: src/gravy/surfaces/common.py: DecisionSurface base; _surface_decisions() filters by surface name (L51-52); _append delegates to artifacts.append_decision (L54-55); decisions() reads jsonl, raises SurfaceValidationError on corrupt/non-object rows (L38-49). (file:///home/jon/dev/gravy/src/gravy/surfaces/common.py)
- **[research_citation]** sources: src/gravy/surfaces/gallery.py: Immutability guard L17-18 (if self._surface_decisions(): raise 'gallery already has a decision'); append + SurfaceProgress(complete=True, remaining=0) L25-26. Design D2 line refs EXACT. (file:///home/jon/dev/gravy/src/gravy/surfaces/gallery.py)
- **[research_citation]** sources: src/gravy/surfaces/form.py: Immutability guard L21-22 (if self._surface_decisions(): raise 'form already has a submission'); append + complete=True L30-31. Design D2 line refs EXACT. (file:///home/jon/dev/gravy/src/gravy/surfaces/form.py)
- **[research_citation]** sources.omitted: 6 additional sources omitted (bounded to first 3)
- **[archive_only_evidence]** architecture_assessment: Design is accurate, minimal, and contract-aligned. Every claim verified against source: (1) guard line refs EXACT for gallery L17-18, form L21-22, checklist L20-21; (2) D2 completion invariant holds — gallery/form hardcode complete=True, unaffected by revision; (3) D3 traced precisely: when criterion already in decided and resubmitted, decided|{criterion} == decided so remaining = len(criteria - decided) is UNCHANGED — counts each criterion once regardless of revision count; (4) D4 sound: pairwise has no resubmit-block guard (only 'complete' raise), the cannot-return-to-past-pair behavior is navigation-based via current_pair (first undecided), correctly classified as a navigation gap not an immutability dead-end, and AC4 explicitly permits scope-out with rationale; (5) latest_decision() returns None and latest_per_key() returns {} on empty decisions — graceful; (6) artifacts.append_decision is append-only with fsync, no mutate/delete path exists; (7) MCP boundary (4 tools) and lifecycle.recover_after_recycle reference only artifact_path pointer (str(namespace)), never decision contents — claim 7 CONFIRMED. No existing test asserts the removed guards, so guard removal breaks nothing. Change is correctly confined to src/gravy/surfaces/ + tests/test_surfaces.py. One non-blocking clarification: proposal In Scope lists 'Update UI state so the surface reflects the latest decision after revision' but design D2 only removes guards (no input pre-fill); all ACs (AC1-AC7) are satisfiable without pre-fill since they require resubmit-without-error + both-rows + complete-after-each, not input population — design should state explicitly that 'reflects latest decision' means completion-status reflection, not input pre-fill.

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
| SC2 | success_criterion | pass |
| C1 | constraint | respected |
| C2 | constraint | respected |
| C3 | constraint | respected |
| DONT1 | avoidance | respected |
| DONT2 | avoidance | respected |
| DONT3 | avoidance | respected |

## Unresolved Actions

None
