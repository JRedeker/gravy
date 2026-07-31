# Executive Summary: Add pairwise revision navigation

## Outcome
The pairwise surface now lets a reviewer revisit and revise any previously-decided pair — the last holdout after `allowSurfaceDecisionRevision` brought revision to gallery, form, and checklist. Previously, once a reviewer chose Left/Right/Tie/Skip on a pair, the surface advanced and offered no way back; a misclick or a reconsidered comparison was unrecoverable. A reviewer can now navigate to any decided pair, see their current effective choice, and change it.

## Value / why it matters
Pairwise ranking is the surface most prone to second thoughts: a reviewer's judgment on pair (a,b) often shifts after seeing (a,c) and (b,c). Forbidding revision forced premature, frozen decisions. Pairwise is now at parity with the other three surfaces — last-submission-wins per pair, full append-only audit preserved — so the reviewer's final, considered ranking is what reaches the agent.

## What changed
- **Surface (`pairwise.py`):** added `choose_pair(left, right, choice)` for targeted revision (exact-match pair validation against the canonical combinations tuple). `choose`, `current_pair`, and `complete` are unchanged — their `decided` set dedupes, so revisions don't disturb forward flow or completion.
- **Controller (`gradio_runtime.py`):** added `pairwise_choose_pair`; rebuilt `_build_pairwise` with a pair-selector dropdown showing every pair and its effective choice, defaulting to `current_pair`. Choice buttons operate on the active pair and reset to `current_pair` after each decision so forward progress stays the default.
- **Tests:** 4 new regression tests (revision + latest-wins, reversed-order rejection, skip↔real transition, forward-flow preservation) plus a controller wiring test.

## Verification
- TDD: red (4 fail) → green (81 pass). 13 surface tests + 81 full suite pass.
- Design independently validated by adv-researcher (CONCERN→resolved): exact-match pair validation fixes a correctness trap where reversed-order input would write non-canonical rows; explicit dropdown-as-input-and-output wiring.
- Append-only invariant held; no row ever mutated or deleted.

## Risks / follow-ups
- Manual live UI smoke of the dropdown deferred to post-merge (runtime wiring tests cover the controller path).
- The pairwise builder grew in complexity; a future refactor could extract a shared navigation-surface base, out of scope here.