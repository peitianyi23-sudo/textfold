# PDF check speed and essential equations

Status: design agreed and implementation validated, 2026-10-19. Implemented in the isolated `codex/pdf-speed-essential-equations` worktree after the user's handoff. See [verification](pdf-check-speed-and-essential-equations-verification.md) for measurements, quality evidence and rollout receipts. The decisions below retain the agreed scope.

## User needs

- Accelerate PDF-backed extraction correction algorithmically.
- Include important formulas in Key and Takeaway: definitions and central results, not intermediate derivation steps.
- Preserve the separate unresolved cache-opening bug: selected parent JAUYGCML / attachment J2CRW9DP waits for a cache. Current attachment numeric ID 17262 has no cache directory; matching paper text exists in older cache directories 11966 and 11958. Identity has NOT been established; do not reuse by title or assume the latest correction work reverted the previous fixes.

## Current code facts

correction.run checks pages serially, each with the whole evolving Markdown and up to three adjacent PDF images. Changed pages may take up to three correction rounds, each with a separate proposed-edit review. That review also receives four enlarged quadrants of the target page. Neighbor pages and full Markdown are repeatedly transmitted; full Markdown normalization/image checks are performed per edit. Full first-pass coverage and independent evidence-backed edit review remain accepted prior requirements until explicitly changed.

The current ladder receives displayed equations as context for corrected PDFs. Display equations are not reading units with their own importance decisions; merely putting an equation in the prompt does not establish that it remains visible at Key or Takeaway. The requested improvement therefore concerns both selection and reading presentation, not just prompt wording.

## Accepted decisions, round 1

- Q1 accepted: retain full first-pass PDF coverage; use page-local text/context, bounded parallel comparison, and region-only independent follow-up verification to remove redundant work. Measure actual elapsed time and quality against the baseline; no promised speed multiplier.
- Q2 accepted: an essential equation is necessary to understand this paper's argument: a necessary definition, a central result, or a governing relation essential to its claimed mechanism. Familiar definitions and intermediate derivations do not qualify solely because they are equations.
- Q3 user correction: Takeaway must directly display selected essential long formulas too, with a placement analogous to figures. Do not require expansion just to see a long essential formula. Line wrapping is acceptable where appropriate. Preserve mathematical meaning and original equation identity; permissible layout changes are distinct from algebraic rewriting. Detailed wrapping/fallback and explanatory context remain to settle below.

## Additional inspected facts

Read-only exploration confirmed the present reader hides every display equation at levels 2, 1 and 0. Actual UI levels are Full=4, Brief=3 (author sentence selections), Key=2 (written takeaway plus reason), Takeaway=1 (headline), Topic=0. Some ladder module prose swaps Key/Brief names; the handoff must follow the actual UI. Selected-equation visibility therefore requires changes to stored selection and reader behavior, not merely prompt instructions.

The current correction makes at most six vision calls per page, resends adjacent pages and whole Markdown, renders four detail crops eagerly, and validates each candidate by normalizing the entire document. Timing scripts printed elapsed durations but retained evidence does not contain a durable request-by-request timing breakdown. Benchmark new and baseline code on the same original extraction, recording model, call counts and durations; do not infer performance from file timestamps.

## Accepted decisions, round 2

- Q4 accepted: preserve the original equation number and PDF access, show a short meaning statement and necessary validity conditions, and directly display selected long formulas. Permit faithful layout line breaks at existing relations/additive terms/rows, preserving every term and symbol. Use formula-local horizontal scrolling where a readable, faithful layout cannot fit. Never algebraically rewrite an equation merely to fit the viewport.
- Q5 accepted with explicit rationale: Key and Takeaway select separately, following the author's existing progressive compression design; include equations within that same logic. Key can retain necessary definitions, governing relations and results; Takeaway retains the subset needed for the main message. Both directly show long formulas when selected. Agent selection is automatic, with no fixed numeric quota or routine confirmation. Topic remains the existing highest-compression view; no new formula-retention requirement there.

## Implementation judgment and acceptance

The product decisions above are settled. Page mapping, bounded concurrency, crop reuse, stable equation references and overlapping edit resolution are implementation decisions for the receiving agent, not another approval round. Preserve the accepted first full-PDF comparison and independent verification of changed symbols. Benchmark against the current implementation using original extraction copies, including the real finalized-Markdown case without block coordinates. Record wall time, request counts and provider errors; compare actual recovered/misread symbols and paragraph structure, not just speed. No numerical speed target has been agreed.

Keep original PDF and Zotero producer cache unchanged. Reading stays available during correction; derived layers consume the consistent corrected source. Preserve notes, translations, equation provenance and existing zoom behavior. Unresolved PDF content stays explicit and no mandatory human confirmation is added. Apply the agreed prior rollout boundary: validate on the two named papers in extraction-repair-discussion.md first, then future imports; do not rewrite the entire existing library. Reuse existing subscription/model configuration. Follow the personal -> codex/feature branch -> tested personal merge workflow; preserve unrelated dirty files.

For equation selection, validate that core definitions/results appear where needed in actual Key and Takeaway views, intermediate steps are omitted appropriately, conditions survive compression, original equation identities remain stable, and long equations fit or scroll locally on a narrow viewport. Exercise the existing languages, note anchors and zoom transitions affected by the change. Read CONTRIBUTING.md and its GPU/2x smoothness requirement before reader changes; report any benchmark-paper substitution explicitly.

The cache-opening incident remains a distinct unresolved bug, recorded under User needs. Its existing regression script is launch/cache-locality/repro.py. Resolve cache identity with evidence, never title matching. Keep any cache fix separate from performance/equation work unless a demonstrated dependency requires it.
