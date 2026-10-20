# Document-wide batched correction verification

Implementation delivered on 2026-10-20. Final complete corpus performance and quality revalidation was stopped at the user's request to finish immediately. No final aggregate speedup or exhaustive correction claim is made.

## Changes

Correction first reads coherent document text and repairs supported text/symbol extraction errors. Residual PDF questions are grouped across pages by image capacity, with explicit physical-page and candidate attribution. Retained geometry and unique literal PDF anchors locate evidence; independent review decides publication. Original producer caches remain read-only. Full remains immediately readable; existing layers, notes, translation, equations, menus and scoped reading behavior are retained.

Fixes found during real-paper trials include caption relocation atomicity, mathematical delimiter atomicity, preservation of printed author notation, dependent edit ordering, legacy resume indexes, actual control characters in model JSON, cross-page cache geometry errors, and literal bibliography spelling checks.

## Completed validation

- Latest implementation: ba17375. Full unittest suite: 216 tests, 213 passed, 3 existing platform skips. Log: launch/batched/delivery-tests.log.
- Real reader checks covered 30 input/baseline/intermediate corrected documents: Full readable, expected images loaded, no JavaScript or reported formula rendering errors, no background jobs. These checks do not establish mathematical correctness.
- Live boundary fixtures covered clean text, deliberate author notation, numeric extraction errors requiring PDF evidence, and missing formulas.
- Ten known regression papers (84 physical pages) were used, not a fresh holdout. Nine retained structured layouts; one had Markdown only. Original PDF/Markdown/layout identity and input image alias equivalence were recorded. No producer-cache rebuild or write was performed. A later cache availability check found one cache removed externally; frozen inputs were retained.

## Timing and quality limits

The valid frozen baseline completed in 1481.02 s: 142 logical requests, 145 HTTP attempts, 171 images, 52.12 MB wire payload. Three HTTP errors are included. Two excluded initial baseline attempts and their reruns are recorded in the raw evidence.

An intermediate complete run at b91e4f1 took 1206.18 s: 34 logical/HTTP requests, 186 images, 51.92 MB wire payload, no HTTP errors. Model wait dominated both runs (1448.10 s baseline; 1192.02 s intermediate). This intermediate timing is NOT a validated final-release speedup: subsequent PDF quality inspection found a partial mathematical delimiter edit and a normalized journal abbreviation that differed from the printed source. Both led to the latest fixes. An earlier faster trial also failed quality and is excluded from delivery claims.

Latest affected-paper rechecks completed: Boffetta 138.09 s / 3 HTTP attempts; Takaoka 101.47 s / 3; Chong 400.69 s / 6 attempts (5 logical calls). Chong includes an HTTP 500 taking 118.10 s plus retry/backoff; it is not replaced with a favorable rerun. Boffetta's delimiter output is balanced. Takaoka no longer publishes the wrong journal spelling, but its first partial bibliography entry remains unrestored. Detection is therefore incomplete. Earlier baseline PDF inspection also found a substantive duplicated-paragraph edit in Xia; the intermediate new pipeline did not repeat it.

The remaining latest-version measurement was interrupted during Yarom after text screening; it and the unstarted remaining papers are excluded. No final complete 38-case quality score or aggregate latest-version speedup is claimed. Original files and raw measurements remain under the managed worktree's ignored launch/batched directory.

## Delivery

Signed-off commits are merged into personal locally. No push or upstream PR is authorized. The daily service refresh receipt, when successful, is launch/batched/daily-service.json in the evidence worktree. Unrelated primary-checkout changes are preserved.
