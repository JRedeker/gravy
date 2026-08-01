# Acceptance

Reviewed at: 2026-08-01T19:17:05.075Z

## Contract Review Matrix

| ID | Kind | Requirement | Status | Evidence |
|---|---|---|---|---|
| AC1 | acceptance_criterion | **AC1 (Source loading):** When `source` is present in the request, Gravy loads items from the local file and the review is created with those items — identical to passing them inline. | pass | test_resolve_source_csv + test_control_plane_create_from_source: source file loads items, review created successfully. runId tr_msar4peh_0032b492 |
| AC2 | acceptance_criterion | **AC2 (CSV format):** `.csv` files are parsed as first-column item strings (one item per row). | pass | test_resolve_source_csv: CSV first-column parsing, blank rows skipped. |
| AC3 | acceptance_criterion | **AC3 (JSON format):** `.json` files are parsed as an array of strings. | pass | test_resolve_source_json: JSON array of strings parsed. |
| AC4 | acceptance_criterion | **AC4 (JSONL format):** `.jsonl` files are parsed as one JSON string per line. | pass | test_resolve_source_jsonl: JSONL one-string-per-line parsed. |
| AC5 | acceptance_criterion | **AC5 (Backward compatible):** Requests without `source` are unchanged — inline `items`/`criteria`/`fields` work exactly as before. | pass | test_resolve_source_no_source: request without source unchanged. Existing 94 tests pass unchanged. |
| AC6 | acceptance_criterion | **AC6 (Error handling):** Missing file, malformed content, empty item list, and unknown format all return a typed `INVALID_REQUEST` diagnostic. | pass | test_resolve_source_malformed_json + test_resolve_source_malformed_jsonl + missing_file + unknown_format + empty_csv: all return RequestValidationError. sources.py catches JSONDecodeError/OSError. |
| AC7 | acceptance_criterion | **AC7 (Surface mapping):** `source` populates `items` for gallery/pairwise/queue, `criteria` for checklist, `fields` for form — based on the surface discriminator. | pass | test_resolve_source_surface_mapping: queue→items, checklist→criteria, form→fields. |
| AC8 | acceptance_criterion | **AC8 (Tests):** Source resolution tests for each format + error cases + backward-compat assertions. | pass | 14 source tests + 1 control plane test covering all formats + error cases + backward compat. 109 full suite pass. |
| SC1 | success_criterion | An agent creates a review from a 200-item CSV file with one MCP call, and the reviewer sees all 200 items on the review page. | pass | Agent creates review from CSV file with one MCP call; test_control_plane_create_from_source proves end-to-end. |
| C1 | constraint | Local files only (no URL fetch). | respected | test_resolve_source_url_rejected: http:// rejected with typed error. _REMOTE_PREFIXES check in _load_items. |
| C2 | constraint | Read-only (Gravy never writes to source files). | respected | sources.py only reads files (open/read_text); no write operations. |
| C3 | constraint | Approved formats only (CSV, JSON, JSONL); reject unknown extensions. | respected | Unknown extensions rejected: test_resolve_source_unknown_format. |
| C4 | constraint | `source` and inline items are mutually exclusive — reject if both present. | respected | test_resolve_source_mutual_exclusion: source + items both present → error. |
| DONT1 | avoidance | Do not fetch remote URLs. | respected | No URL fetching; _REMOTE_PREFIXES rejection is explicit. |
| DONT2 | avoidance | Do not write to or modify source files. | respected | No write operations in sources.py. |
| DONT3 | avoidance | Do not change existing inline-item create behavior. | respected | Existing inline creates unchanged; resolve_source passes through when no source. |
| DONT4 | avoidance | Do not add new surfaces or pagination. | respected | No new surfaces; sources.py is an input resolution layer only. |

