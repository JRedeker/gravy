# Contract Traceability

**Change ID:** addFileSourceBatchLoading
**Contract Version:** 1
**Rigor:** standard
**Reviewed:** 2026-08-01T19:17:05.075Z

## Contract Items

| ID | Kind | Status | Evidence Policy | Evidence |
| --- | --- | --- | --- | --- |
| AC1 | acceptance_criterion | pass | test | test_resolve_source_csv + test_control_plane_create_from_source: source file loads items, review created successfully. runId tr_msar4peh_0032b492 |
| AC2 | acceptance_criterion | pass | test | test_resolve_source_csv: CSV first-column parsing, blank rows skipped. |
| AC3 | acceptance_criterion | pass | test | test_resolve_source_json: JSON array of strings parsed. |
| AC4 | acceptance_criterion | pass | test | test_resolve_source_jsonl: JSONL one-string-per-line parsed. |
| AC5 | acceptance_criterion | pass | test | test_resolve_source_no_source: request without source unchanged. Existing 94 tests pass unchanged. |
| AC6 | acceptance_criterion | pass | test | test_resolve_source_malformed_json + test_resolve_source_malformed_jsonl + missing_file + unknown_format + empty_csv: all return RequestValidationError. sources.py catches JSONDecodeError/OSError. |
| AC7 | acceptance_criterion | pass | test | test_resolve_source_surface_mapping: queue→items, checklist→criteria, form→fields. |
| AC8 | acceptance_criterion | pass | test | 14 source tests + 1 control plane test covering all formats + error cases + backward compat. 109 full suite pass. |
| SC1 | success_criterion | pass | review | Agent creates review from CSV file with one MCP call; test_control_plane_create_from_source proves end-to-end. |
| C1 | constraint | respected | static_check | test_resolve_source_url_rejected: http:// rejected with typed error. _REMOTE_PREFIXES check in _load_items. |
| C2 | constraint | respected | static_check | sources.py only reads files (open/read_text); no write operations. |
| C3 | constraint | respected | static_check | Unknown extensions rejected: test_resolve_source_unknown_format. |
| C4 | constraint | respected | static_check | test_resolve_source_mutual_exclusion: source + items both present → error. |
| DONT1 | avoidance | respected | review | No URL fetching; _REMOTE_PREFIXES rejection is explicit. |
| DONT2 | avoidance | respected | review | No write operations in sources.py. |
| DONT3 | avoidance | respected | review | Existing inline creates unchanged; resolve_source passes through when no source. |
| DONT4 | avoidance | respected | review | No new surfaces; sources.py is an input resolution layer only. |

## Task References

| Task | Implements | Verifies | Respects | N/A Reason |
| --- | --- | --- | --- | --- |
| tk-7ba1ba82b179 | AC1, AC2, AC3, AC4, AC5, AC6, AC7 | AC8 |  |  |
| tk-b8cdcf488658 |  | AC1, AC2, AC3, AC4, AC5, AC6, AC8 |  |  |
