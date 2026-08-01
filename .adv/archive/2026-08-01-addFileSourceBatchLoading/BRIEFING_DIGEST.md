# Archive Briefing Digest

**Change ID:** addFileSourceBatchLoading
**Title:** Add file-source batch loading
**Status:** archived
**Generated:** 2026-08-01T19:18:06.075Z

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

Showing 16 of 16 durable facts.

- **[archive_only_evidence]** decisions: Added resolve_source() in a new sources.py module — Keeps file I/O separate from the pure schema validator and makes error handling testable in isolation
- **[archive_only_evidence]** decisions: Called resolve_source in control_plane.create before validate_request — Downstream validation and lifecycle continue to see a normal inline request; no surface/schema/builder changes needed
- **[archive_only_evidence]** decisions: Rejected URLs by prefix and required non-empty local path — Agreement constraint: local files only; explicit guard is static-checkable and produces clear INVALID_REQUEST diagnostics
- **[archive_only_evidence]** decisions: Mapped source to surface-appropriate field (items/criteria/fields) — Matches AC7 and avoids ambiguity across gallery/pairwise/queue/checklist/form
- **[archive_only_evidence]** verification: uv run --group test pytest tests/test_sources.py tests/test_control_plane.py -v (0) — GREEN iteration: 18 passed (14 source + 4 control plane)
- **[archive_only_evidence]** verification: uv run --group test pytest (0) — Full suite: 109 passed in ~76s
- **[unresolved_action]** consumer_warnings: verification_missing: No durable adv_run_test evidence found for run_id: tr_msaqy8xq_0e5330e5
- **[unresolved_action]** consumer_warnings: verification_missing: No durable adv_run_test evidence found for run_id: tr_msar0kz6_a4c7151c
- **[report_follow_up]** follow_ups: Scope anchors (TASK_SCOPE/IN_SCOPE/OUT_OF_SCOPE/DONE_WHEN/STOP_WHEN/VERIFICATION) were not present verbatim in the spawn prompt; identity anchors (WORKDIR/CHANGE/SCOPE KEY/ATTEMPT=1) were present and used. Scope inferred from the 'What to validate' section.
- **[report_follow_up]** follow_ups: AC8 test plan must explicitly include malformed .json and .jsonl cases to lock the AC6 fix.
- **[research_citation]** sources: control_plane.py create(): create() catches ONLY RequestValidationError (L30-33) -> INVALID_REQUEST; then surface != parsed.surface check. No broader catch. resolve_source must run inside this try. (src/gravy/control_plane.py:28-36)
- **[research_citation]** sources: schemas.py _require_exact_keys: Strict set equality: set(request) must equal {'surface', *keys}. Any extra key (e.g. leftover 'source') is rejected - resolution MUST precede validation. (src/gravy/schemas.py:78-80)
- **[research_citation]** sources: schemas.py RequestValidationError: class RequestValidationError(ValueError) - sibling of json.JSONDecodeError, NOT a parent. (src/gravy/schemas.py:12-13)
- **[research_citation]** sources.omitted: 4 additional sources omitted (bounded to first 3)
- **[archive_only_evidence]** architecture_assessment: The architectural approach is sound and minimal: resolve_source() transforms the optional 'source' field into the surface-appropriate inline field BEFORE validate_request, so the closed schema validator and all downstream code see a normal inline request. This is the correct and only placement: _require_exact_keys (schemas.py:78-80) rejects any key outside {surface, <expected>}, so 'source' MUST be removed before validate_request runs. The surface-discriminator map, extension-based format detection, and mutual-exclusion check all trace cleanly to AC1-AC8, C1-C4, DONT1-4. HOWEVER the shown implementation code has one hard contract violation (AC6 malformed-content) and one code/prose mismatch (D5 URL rejection). The AC6 violation: _load_json and _load_jsonl call json.loads without converting json.JSONDecodeError -> RequestValidationError. Per Python docs (https://docs.python.org/3/library/json.html) json.JSONDecodeError is a subclass of ValueError and thus a SIBLING of RequestValidationError (schemas.py:12), not a child. control_plane.create catches ONLY RequestValidationError (control_plane.py:32) and mcp_boundary.handle (mcp_boundary.py:40-60) has no surrounding try/except, so malformed JSON/JSONL raises an UNCAUGHT exception instead of the typed INVALID_REQUEST AC6 requires. The design's own 'cleaner: catch RequestValidationError only' note makes this worse; only the dirty 'except (RequestValidationError, Exception)' variant would mask it, at the cost of hiding real bugs.
- **[unresolved_action]** validation.blockers: Malformed .json or .jsonl content raises json.JSONDecodeError, which is NOT a RequestValidationError (both are sibling subclasses of ValueError per https://docs.python.org/3/library/json.html and schemas.py:12). control_plane.create's 'except RequestValidationError' (control_plane.py:32) will not catch it, and mcp_boundary.handle (mcp_boundary.py:40-60) has no surrounding catch, so the exception propagates uncaught instead of returning a typed INVALID_REQUEST. AC6 explicitly requires 'malformed content ... return a typed INVALID_REQUEST diagnostic.' The design's own 'cleaner: catch RequestValidationError only' note makes this unavoidable; only the dirty broad-Exception variant would mask it (while hiding real bugs).

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
| AC8 | acceptance_criterion | pass |
| SC1 | success_criterion | pass |
| C1 | constraint | respected |
| C2 | constraint | respected |
| C3 | constraint | respected |
| C4 | constraint | respected |
| DONT1 | avoidance | respected |
| DONT2 | avoidance | respected |
| DONT3 | avoidance | respected |
| DONT4 | avoidance | respected |

## Unresolved Actions

- verification_missing: No durable adv_run_test evidence found for run_id: tr_msaqy8xq_0e5330e5
- verification_missing: No durable adv_run_test evidence found for run_id: tr_msar0kz6_a4c7151c
- Malformed .json or .jsonl content raises json.JSONDecodeError, which is NOT a RequestValidationError (both are sibling subclasses of ValueError per https://docs.python.org/3/library/json.html and schemas.py:12). control_plane.create's 'except RequestValidationError' (control_plane.py:32) will not catch it, and mcp_boundary.handle (mcp_boundary.py:40-60) has no surrounding catch, so the exception propagates uncaught instead of returning a typed INVALID_REQUEST. AC6 explicitly requires 'malformed content ... return a typed INVALID_REQUEST diagnostic.' The design's own 'cleaner: catch RequestValidationError only' note makes this unavoidable; only the dirty broad-Exception variant would mask it (while hiding real bugs).
