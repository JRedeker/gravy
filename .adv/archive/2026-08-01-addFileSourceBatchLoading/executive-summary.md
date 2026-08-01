# Executive Summary: Add file-source batch loading

## Outcome
Agents can now create reviews from a local file (CSV/JSON/JSONL) instead of passing all items inline in the MCP call. For large batches (200+ card verifications), this eliminates the friction of serializing hundreds of items into a single create call. The agent generates a batch file using whatever domain logic it has, then points Gravy at the path.

## Value / why it matters
The inline-items pattern worked fine for small batches but created real friction at scale — a 200-item create call is a massive JSON payload that's awkward to construct and wasteful to transmit. The file-source option lets agents leverage existing batch-generation tooling (queries, CSV exports, JSONL generators) and hand Gravy the path. One MCP call regardless of batch size.

## What changed
- New `sources.py` module: `resolve_source(request)` loads items from a local file before schema validation. Supports CSV (first-column-per-row), JSON (array of strings), JSONL (one string per line). All errors convert to `RequestValidationError` → `INVALID_REQUEST`.
- Control plane calls `resolve_source` before `validate_request` — everything downstream sees a normal inline request. Backward compatible.
- URL rejection (local files only), type/non-empty guard, mutual exclusion (source + inline items can't coexist).

## Verification
- TDD red→green. 18 targeted tests pass (14 source resolution + 4 control plane). Engineer confirmed 109 full suite.
- Design validated by adv-researcher (CONFLICT→resolved: AC6 error conversion, URL rejection, type guard).
- All formats tested: CSV, JSON, JSONL, malformed content, missing file, unknown format, empty file, mutual exclusion, URL rejection, surface mapping.

## Risks / follow-ups
- Minimal risk: additive module, one call site, backward compatible.
- Future: support image URLs or object items in source files (second CSV column, JSON objects). Out of scope.