# addGravyReviewKit: Add Gravy review kit

**Status:** cancelled
**Branch:** main (merged at 01de60c1e70408b41d375c46f41fa76e3d21fd14)
**Timeline:** 2026-07-30T00:52:17.128Z → 2026-07-31T22:08:56.745Z

## Outcome
Completed 9 task(s): Build typed foundation and durable review state; Implement isolated Gradio and Tailnet lifecycle adapter; Render four typed review surfaces and append decision…

## Why
Agents need a fast, reusable way to create Tailnet-reachable human review pages for images, forms, and structured choices. Gravy supplies a small typed MCP sur…

## Surface
- Build typed foundation and durable review state
- Implement isolated Gradio and Tailnet lifecycle adapter
- Render four typed review surfaces and append decisions
- Expose closed MCP control plane and recovery behavior
- Document supported operation and recovery boundaries
- Run contract-complete verification and lifecycle regression suite
- …3 more task(s)

## Acceptance Criteria
- ✓ `catalog()` returns schema-validated descriptions and one example request for exactly `gallery`, `pairwise`, `form`, an…
- ✓ A valid discriminated `create()` returns a unique `review_id` and Tailnet URL; invalid schema, unavailable Tailnet HTTP…
- ✓ Ten simultaneous creates yield ten distinct IDs, ports/URLs, and artifact namespaces, and every active review progresse…
- ✓ Gallery supports visual select/rank plus notes; pairwise records left/right/tie/skip and resumes partial queues without…
- ✓ Every decision is persisted before UI advance; reconstruction duplicates no prior decisions; backend recycle leaves act…
- ✓ `update` and `close` use review identity rather than MCP-session identity; unknown or terminal IDs cannot affect anothe…
- ✓ A lifecycle test proves close/recycle leaves no review listener or child subprocess, preserves recoverable artifacts, a…
- ✓ Regression coverage proves port release, queue close, historical Gradio instance cleanup, and launch-thread termination.

## Spec Deltas
- None

## Wisdom Prom

<!-- summary truncated to stay under 2KB -->
