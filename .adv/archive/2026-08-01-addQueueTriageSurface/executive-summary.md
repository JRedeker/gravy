# Executive Summary: Add queue triage surface

## Outcome
Gravy now has a 5th review surface: **queue** — purpose-built for bulk triage. An agent creates a review with `{"surface": "queue", "items": [...], "options": [...]}` and a reviewer sorts every item into an outcome bucket (accept/reject/defer, or any custom buckets) in a single view. The decision is a clean `{item: bucket}` mapping. Previously, bulk triage required constructing an awkward N-field form that obscured intent and produced undifferentiated decisions.

## Value / why it matters
Triage is one of the most common review tasks (sort candidates, filter submissions, prioritize work items). A dedicated surface gives the agent a minimal, one-call setup and gives the reviewer a clean worklist UI. The catalog now covers five distinct decision shapes: pick-one (gallery), compare-pairs (pairwise), fill-fields (form), check-criteria (checklist), triage-into-buckets (queue).

## What changed
- New `QueueSurface` (whole-surface single decision, like gallery/form) with frozenset item/bucket validation.
- New `QueueRequest` schema with items + options (>=2 required).
- Queue entry in MCP catalog; removed from DEFERRED_SURFACES.
- `_build_queue` Gradio builder (per-item Radio + single Submit, pre-population on revision).
- Controller `queue_submit` + `queue_prior` methods.
- 4 boundary docs updated (AGENTS.md, README.md, architecture.md, operations.md).

## Verification
- TDD red→green. 94/94 tests pass (was 85; +9 new queue tests + existing catalog/schema/mcp tests updated).
- Design validated by adv-researcher (CONCERN→resolved; 6 plan gaps applied).
- Append-only invariant held; revision semantics consistent with all other surfaces.

## Risks / follow-ups
- None material. The three remaining deferred surfaces (annotation, document, preview) are intentionally skipped — covered by existing surfaces or too complex for the value.