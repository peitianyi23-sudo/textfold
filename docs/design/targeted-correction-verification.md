# Targeted extraction correction verification

Implementation and isolated evaluation, 2026-10-20, from `personal` revision `fda97f5` in the managed
`targeted-correction` worktree, branch `codex/targeted-correction`. Implementation commits are signed off:
`ba499d5`, `33a32e3` and `5574245`. The [agreed design](targeted-extraction-correction-discussion.md) and
[exact sample manifest](targeted-correction-sample-manifest.md) define the scope.

## Result

The final validated trials take **2042.63 -> 1106.33 seconds** (34.0 -> 18.4 minutes), a **45.8% observed reduction**.
HTTP requests fall **168 -> 141**, submitted images **197 -> 151**, and HTTP-body payload **107.79 -> 48.34 MiB**.
Both versions encounter two HTTP 500s and ten seconds of retry waits. This is a single paired corpus experiment,
not a guaranteed speed multiplier.

There is a coverage trade-off: of 38 independently referenced error locations, exhaustive checking fixes 38;
targeted correction fixes **34**, flags **3** without resolving them, and misses **1** flattened table exponent.
All 15 reference display labels are restored. A discovered partial-footnote mis-edit was fixed and the affected
paper rerun; no further accepted mis-edit was found in the inspected final evaluation output. This does not certify
zero recognition errors. Delivery status is recorded below after the local merge and service check.

## Implemented behavior

New imported PDFs of at most 30 physical pages use text-first screening of MinerU Markdown alongside the original
PDF's existing text layer, in groups of up to six pages. The model identifies suspicious exact passages and literal
PDF anchors, without proposing text-only corrections. The observed discovery patterns include corrupted fractions,
exponents, math/prose boundaries, control-character residue, fragmented/duplicated paragraphs and omitted passages
or numbered displays. Syntactically valid formulas can still be candidates; scientific plausibility is not authority.

PDFium locates exact unique anchors in the original text layer and reuses their character rectangles. Context grows
to complete same-column lines so a short anchor cannot clip paragraph edges or equation numbers. Overlapping context
rectangles merge before rendering. Same-page candidates share an image-backed proposal request and an independent
review request; every proposed edit receives its own decision. Printed author notation must survive, including
scientifically inconsistent notation. Nonunique, absent or unreadable source locations remain explicitly unresolved.
Scans retain the missing-text-layer limitation; they do not start whole-document OCR or a full-page vision fallback.

Successful screening replies use the existing model cache. `targeted-work.json` retains discovery, reviewed draft,
completed candidate groups and unreviewed local proposals. A provider failure during independent review reuses the
successful unchanged proposal on resume. Overlapping edits are resolved in draft order before review; stale overlaps
remain issues instead of repeatedly failing publication. No hashes or new service are introduced.

Full is readable immediately. Derived layers start after the current targeted workflow finishes, using its corrected
reading copy and relevant uncertainties. Reconciliation retains healthy layers, translations, notes and original
geometry through the existing publication path. Questions and generation explicitly distinguish targeted investigation
from exhaustive PDF verification. A targeted receipt leaves physical `checked` coverage empty.

The document menu contains **Check whole document**, **Choose checking scope** and **Correction records**. The range
form stays collapsed until requested. Running work uses the existing lightweight job toast; completion reloads the
reader and removes progress. Resuming targeted correction does not convert its saved document selection into explicit
full-page checking. Explicit document/range/chapter requests retain the serial exhaustive workflow, bounded 30-page
batches, physical coverage and resumable selection. Longer imports require explicit scope and never auto-enqueue a
whole book or generate unchecked summaries on opening/scrolling.

Only TextFold reading copies are published. Original PDFs and Zotero/MinerU producer caches are read-only inputs.

## Automated and browser checks

`PYTHONUTF8=1 python -X utf8 -m unittest discover tests`: **195 tests run: 192 passed, 3 skipped**. The skipped tests use a fake
Unix-shell `npx` and are disabled on Windows. Existing socket/subprocess `ResourceWarning`s remain non-failing.
The daily service uses the same Python 3.12 installation as these checks.

Twelve new targeted tests cover text-first discovery, separate image review, author-symbol rejection, unlocatable
candidates, stop/resume, successful-proposal reuse after review failure, generation after publication, same-page
batching, merged crop geometry, clipped source lines, explicit full coverage reset and overlapping edit proposals.
The existing long-scope test additionally asserts zero text-model calls above the automatic boundary. Existing
scope, source/image, annotation, atom/layer reconciliation and essential-equation tests continue to pass.

A headed Chrome browser on isolated port 3027 verified immediate Full access, the closed-at-rest menu, explicit
full checking and completion, noncontiguous physical pages 2-3 and 38-39, stopping, long-document scrolling without
new jobs, and 390-pixel scope controls without horizontal overflow. A separate interrupted targeted fixture resumed
without a `scope` field and completed with method `targeted`, rather than invoking full-page checking. Zero JavaScript
errors were recorded. Model replies for these scheduling tests are controlled, not production jobs.

Two isolated copies of the existing Galtier and Johnson readers retained Key/Takeaway equation selections **8/4**
and **8/2**. Actual equation captions and figure captions still use the existing click-to-open/Escape behavior.
Formula bodies remain identical across Full, Key, Takeaway and Topic; selected Takeaway formulas remain visible,
Topic hides them, and the 390-pixel reader has no horizontal document overflow. These checks use actual stored
reading layers, with no regeneration or writes to the daily papers.

The final corrected Takaoka copy was also opened in a real reader: all five figures load, no raw `[^1]` marker
appears, unverified text-screen observations are labeled separately, and no model job is queued. Its raw-Markdown
figure layout has a pre-existing horizontal overflow: 1398 pixels in a 1200-pixel viewport, identical in the original
extraction control and corrected copy. This isolated figure-layout limitation remains; it is not a new correction
regression and is not a repair of the separate cache-opening incident.

## Model comparison protocol

Use exactly the manifest's five discovery attachments (2951, 3354, 3506, 3145, 3836) and five evaluation attachments
(2982, 2793, 2878, 3206, 148): 84 physical pages. Both versions start from the same original `full.md` and selected
PDF in isolated folders. The existing selected `gpt-6.1-sol` subscription bridge is used; no account/service is bought
and no provider settings are changed. Requests are serial within each correction workflow.

The baseline is the actual prior full-page comparison plus independent edit review from `fda97f5`. Correction time
includes PDF text mapping, rendering, network/model wait, retries, source validation and publication. Building the
isolated input copies and resolving the model are outside the paper timer. HTTP-body byte counts include schema,
text and base64 image payloads; HTTP counts include retries. Request-stage receipts distinguish image count, model
wait, local work and backoff. The first six baseline papers retain combined wire bytes and image counts; the last
four and all final targeted requests additionally retain raw image-byte and non-image string-byte breakdowns.

Initial preparation accidentally dropped image references in four isolated HTML copies. Their pre-request consistency
failures are retained and excluded from valid comparison times. Preparation was corrected and those four baselines
were rerun from the original Markdown/PDF. A diagnostic targeted run using the initial clipped-anchor crop was stopped
after the first discovery paper; it is retained separately and excluded. The final targeted run uniformly uses complete
column context and merged crops. No detector patterns were tuned from held-out failures; crop and proposal-overlap
changes concern localization/orchestration. The clipped-column bug was demonstrated on Chen's evaluation PDF;
that layout was used to verify the geometry repair before the timed final run. Thus the five papers are held out
for error-pattern selection, not a completely blind end-to-end engineering test. The independent source reference
still examines all pages rather than only detector candidates. There is one final run per paper, not a statistical
latency estimate.

Follow-up verification exposed two bookkeeping gaps and one real publication error. Existing unenrolled PDFs now
have the explicit menu action without being enrolled on opening. Locally inventoried missing display labels remain
explicitly unresolved after a rejected restoration. Text-only batch-boundary cautions are retained as qualified
`screen_notes`, rather than asserted as unresolved PDF findings; derived agents receive that distinction.

In the first Takaoka targeted trial, independent review accepted a `[^1]` marker but rejected its footnote definition,
leaving literal Markdown in the reader. The final publication check withholds edits that introduce a dangling footnote
when only part of the repair passes review. A test reproduces this failure, and replaying the actual recorded proposal
and verdicts confirms the incomplete marker is withheld with **zero provider requests**. Takaoka was then rerun from
the same original input at `5574245`: 102.50 seconds, no new dangling marker, and the unlocatable footnote remains
explicitly unresolved. The original 97.57-second quality-failed trial is retained and excluded from the validated
comparison, regardless of its faster time. The diagnostic clipped-crop trial is also excluded.

Nine final timed papers use `33a32e3`; the affected Takaoka paper uses `5574245`. Subsequent changes on the other nine
concern the menu and uncertainty bookkeeping, not model requests or accepted source edits. Checking every final
reading copy finds no other newly introduced dangling footnote. The original receipts are not rewritten.
All ten compared PDFs match the exact manifest attachments byte for byte, and each retained original Markdown
matches the same producer `full.md` in both versions (`input-identity.json`).

## Actual correction measurements

| Attachment | Before / after seconds | HTTP requests | Submitted images | HTTP-body MiB | Provider errors |
|---|---:|---:|---:|---:|---:|
| 2951 | 113.31 / 70.56 | 8 / 9 | 9 / 12 | 7.42 / 4.08 | 0 / 0 |
| 3354 | 107.32 / 75.39 | 10 / 8 | 11 / 7 | 8.64 / 4.76 | 0 / 1 |
| 3506 | 154.45 / 120.07 | 14 / 14 | 20 / 16 | 6.25 / 4.20 | 0 / 0 |
| 3145 | 466.91 / 157.87 | 23 / 21 | 26 / 23 | 21.89 / 8.47 | 1 / 0 |
| 3836 | 260.46 / 135.77 | 25 / 18 | 31 / 22 | 11.03 / 4.85 | 0 / 0 |
| 2982 | 89.92 / 40.56 | 8 / 5 | 8 / 4 | 7.21 / 3.01 | 0 / 0 |
| 2793 | 103.92 / 60.93 | 13 / 8 | 16 / 8 | 6.52 / 1.45 | 0 / 0 |
| 2878 | 213.90 / 102.50 | 20 / 13 | 22 / 15 | 9.76 / 4.36 | 1 / 1 |
| 3206 | 203.44 / 123.70 | 20 / 18 | 25 / 16 | 13.04 / 4.90 | 0 / 0 |
| 148 | 329.01 / 218.98 | 27 / 27 | 29 / 28 | 16.03 / 8.27 | 0 / 0 |
| **Total** | **2042.63 / 1106.33** | **168 / 141** | **197 / 151** | **107.79 / 48.34** | **2 / 2** |

The discovery subset takes 1102.44 -> 559.66 seconds; evaluation takes 940.19 -> 546.67 seconds. Counts are mixed
per paper: Clercx adds a screening request (8 -> 9 HTTP requests), and Chong remains at 27. More images are submitted
for Clercx (9 -> 12), although their combined payload is smaller. There is no claim that every count improves.

| Time component | Before | After |
|---|---:|---:|
| HTTP response/model wait | 2002.37 s | 1076.51 s |
| Retry backoff | 10.00 s | 10.00 s |
| Remaining local correction work | 30.25 s | 19.82 s |

The final new requests additionally contain 35.36 MiB of raw PNG data and
1.11 MiB of non-image string values. Those values exclude JSON-key/syntax overhead;
the wire-body column is the complete serialized request body. A complete raw-image/text split was not captured for
the first six baselines, so no reconstructed before/after byte split is invented.

## Independent quality reference

The evaluation reference uses original publisher-page renders for every physical page, raw MinerU input and a separate
full-page baseline pass, independently of targeted candidates. Baseline findings are reference leads, not unquestionable
truth. Direct PDF inspection confirms **38 reference error locations**, including **15 missing printed display labels**.
The inventory distinguishes scientific passages and display labels; multiple labels in one edited paragraph remain
separate reference locations. It excludes metadata icon styling from the scientific-passage count.

Concrete references include Chen's damaged energy denominator and `cos(2theta)`; Fang's reordered filtered-energy
definition; Takaoka's `In k space` misread as `ln k`, corrupted vector P and invariant accents; Ding's near-onset epsilon
misread as Pi; and Chong's Gamma/T confusions, corrupted scaling expressions and flattened table exponents. Correct
relations are recorded as correct. The PDF really prints beta in Chong's free-fall normalization despite alpha earlier,
and actually says “shown” in Fang's Reynolds-number sentence; these author inconsistencies must not be improved.

These reference locations allow concrete missed-error accounting outside detector candidates. They are not a perfectly
exhaustive character-level gold transcription, and no whole-document recall percentage is claimed. In particular,
bibliographic typography and all vector-font distinctions are not fully enumerated. Cross-page reading-order issues,
unresolved localization and provider failures must remain distinct from successful fixes and incorrect accepted edits.

## Reference outcomes and remaining errors

| Evaluation attachment | Reference locations | Baseline fixed | Targeted fixed | Detected, unresolved | Missed |
|---|---:|---:|---:|---:|---:|
| 2982 | 5 | 5 | 5 | 0 | 0 |
| 2793 | 6 | 6 | 5 | 1 | 0 |
| 2878 | 8 | 8 | 8 | 0 | 0 |
| 3206 | 5 | 5 | 5 | 0 | 0 |
| 148 | 14 | 14 | 11 | 2 | 1 |
| **Total** | **38** | **38** | **34** | **3** | **1** |

The three unresolved reference locations are Fang's Figure 3 filter-scale subscript, Chong's first abstract Gamma/T
inequality, and Chong's accented compensated Nu expression on physical page 9. Exact PDF anchors failed; the source
is retained. The undetected error is Chong's Table 1: `3 x 104` should be `3 x 10^4` (and similarly for the other
powers). No table candidate was returned. This is a real blind miss exposed by the independent PDF reference,
not a candidate-review success or a harmless formatting difference. Detector patterns were not tuned to remove
this held-out miss.

Other unresolved content exists outside the 38-location inventory, including omitted footnote/bibliography content
and cross-page caption/paragraph placement. Raw issue records can contain duplicate observations and, in earlier
receipts, generic text-screen cautions. They are not error counts; the final code labels such observations separately.
The publication safeguard addresses the actual dangling-footnote mis-edit, while the remaining missed/ambiguous
source stays explicit wherever detected. Targeted correction does not achieve exhaustive-check coverage parity.

## GPU / 2x zoom

Headed Chrome, NVIDIA RTX 4060 Ti, enabled GPU compositing/rasterization, 1512x982 CSS pixels at 2x. The same retained
dense paper `2512.23916v2` is built with before/after app code and a completed-correction metadata fixture to exercise
the new closed menu without changing its reading content. Chrome `PipelineReporter` counts screen-presented and dropped
frames; this is not a headless requestAnimationFrame proxy.

| Gesture | Before presented / dropped | After presented / dropped | Longest gap before / after |
|---|---:|---:|---:|
| Pinch out | 580 / 1 | 533 / 3 | 83 / 83 ms |
| Pinch in | 478 / 1 | 482 / 1 | 67 / 83 ms |
| Drag | 151 / 0 | 154 / 1 | 17 / 33 ms |
| Full click | 56 / 4 | 56 / 3 | 37 / 37 ms |

All gestures reach matching intended levels. Results are mixed: Full-click dropping improves from 6.67% to 5.08%,
while pinch-out rises from 0.17% to 0.56% and drag adds one dropped frame. This single pair establishes neither zoom
speedup nor a statistical no-regression guarantee. Reader animation, formula rendering and caption logic were unchanged.

## Evidence and delivery

Raw inputs, request and retry receipts, independent PDF renders/reference cases, reviewed proposals, UI screenshots,
real-reader checks and GPU traces remain in the managed worktree's ignored `launch/targeted/` directory. Keep that
worktree while these artifacts are needed. Test servers are stopped after checks.

Merge and daily-service verification are pending. No push or upstream PR is authorized or performed. The separate
cache-opening incident remains unresolved; this work does not claim to repair it.
