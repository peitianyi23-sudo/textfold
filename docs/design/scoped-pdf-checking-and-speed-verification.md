# Scoped PDF checking and speed experiments

Validated 2026-10-19 in an isolated managed worktree from `personal` revision `3494aba`.
The agreed [scope design](scoped-pdf-checking-and-further-speed-discussion.md) remains the behavioral authority.

## Implemented behavior

- At most 30 **physical** pages: automatic whole-PDF checking. At 31 or more: readable extraction and an explicit
  scope selector, without automatic vision or summary calls. Front matter, references and appendices count.
- Page ranges may be noncontiguous. Reliably bounded author sections are selectable; missing chapter structure is
  not invented. A long section starts at the chosen reading position and initially covers at most 30 pages.
  Explicit whole-document/range requests continue in batches of at most 30, generating checked content between batches.
- Physical coverage, the latest explicit request, and unreviewed proposals are separate persisted records. Replacing
  a scope stops new scheduling in the previous job. The single worker serializes publication; completed reviewed
  pages survive stops, errors and scope changes. A late proposal cannot publish itself or overwrite the newer request.
  Exact matching extraction context permits proposal reuse, followed by independent edit review.
- Scoped generation uses only paragraphs bounded by both PDF-text anchors and fully covered pages, plus covered
  display blocks. A paragraph spanning pages requires every page. Unknown/ambiguous boundaries wait for full coverage.
  Partial aggregates display **Selected-range summary**. Available outside text/displays are explicitly unchecked
  dependency context; they cannot recursively enqueue checking. Whole-document argument links wait for full coverage.
- Existing reconciliation retains healthy ladders/translations and remaps source/atom references and annotations.
  A changed section aggregate is rebuilt; notes, original quotes, conversations, original PDF and producer caches remain.
  Restarting the service does not automatically resume model work; the reader explicitly continues the saved selection.

## Automated and browser acceptance

`python -X utf8 -m unittest discover tests` passes **154 tests**, with `PYTHONUTF8=1` inherited by subprocesses and the
existing TextFold Python environment. Fifteen scope tests cover the inclusive 30/31 boundary, 100-page import with
zero automatic vision/generation, HTTP `needs:correction-scope`, >30-page sections, noncontiguous ranges, in-flight
replacement, bounded batches, stop/resume, proposal reuse, partial generation, unchecked dependencies and retained layers.
Existing source/atom, translation, notes, independent-rejection and aligned-equation tests continue to pass.
Some existing server tests emit socket `ResourceWarning`s on teardown; they do not fail the suite.

A real browser against isolated port 3026 submitted physical pages 2–3 and 38–39 of a controlled 40-page PDF.
The result retained precisely those four pages, generated four units, displayed the selected-range summary marker,
and said that the whole document was unfinished. Selecting the same 40-page section from page 5 checked only pages
5–34 and preserved the previous noncontiguous work: 34 total checked pages, with the chapter still incomplete.
These scheduling/UI checks use mocked model replies, not real-book content validation. No 100-page live book was run.
The 390-pixel control panel and Key view were inspected visually; controls remain reachable in its scrollable panel.
Eighteen actual-paper checks pass across English/Chinese Full, Key, Takeaway and Topic views, with zero JavaScript
errors. Fresh trial generation selects 8/2 Key/Takeaway equations in Galtier and 5/2 in Johnson; equation selection
has no quota. Their central results retain original equation identity, meanings and explicit validity conditions.
The widest Takeaway formulas scroll locally: 356/1041 and 356/436 client/content pixels, with meaning text at x=17
and document width 390 in both. MathML bodies remain identical across level/language changes; no algebraic shortening
or loss of aligned rows is used. Older completed correction records also display their actual full physical coverage.

## Actual subscription-model experiments

Both named real papers started from the same retained original extraction and original PDF as the delivered
implementation. The existing subscription bridge and selected `gpt-6.1-sol` were reused. All trial data is isolated.
The following are **correction wall times** from stored request-stage receipts, including failed/resumed correction
and the extra physical-page quality recheck, but excluding separate model-discovery and summary-generation time.

| Paper | Delivered implementation, 2 in flight | New implementation, 2 in flight | Vision calls | Provider errors |
|---|---:|---:|---:|---:|
| Galtier, 4 physical pages | 247.01 s | 234.72 s | 11 → 10 | 0 → 0 |
| Johnson, 6 physical pages | 170.02 s | 207.57 s | 12 → 14 | 0 → 1 |
| Total | 417.03 s | 442.29 s | 23 → 24 | 0 → 1 |

There is **no demonstrated overall speedup** in this sample. The Johnson trial hit an HTTP 500 after three reviewed
pages, then resumed the remaining pages in 41.25 s of harness time. A subsequent quality check found the missing
number (4), prompting the targeted page recheck included above. Harness-level recheck time was 31.92 s, including
model resolution; its correction-only timer was 25.54 s. The failure and pre-fix reading copy are retained.

The initial proposal already supplied numbered restorations, reducing separate omission-restoration requests from
five across the baseline papers to zero in these new trials. Touching/overlapping independent-review crops reduced
submitted review images from 76 to 12 across the two papers, including the quality recheck. Every indexed edit still
receives an independent accept/reject/unresolved decision. Model proposals differ between runs, so these image/call
counts are observed outcomes, not a controlled causal estimate or a promised speed multiplier.

The **three-request** experiment failed on its first paper: HTTP 500, 83.23 s, four requests including one provider
failure, and zero pages marked checked. It produced no valid completed quality/latency sample. Default concurrency
remained **two** at the initial delivery. No provider or subscription configuration was changed.

### User-requested concurrency rollback

After reviewing these measurements, the user requested **single-request** checking. The page-comparison executor
and its prefetch window have been removed: the current page's comparison and all independent review/restoration
requests finish before the next page starts. Scope selection, 30-page batches, resumable coverage, merged crops and
omission-restoration reuse remain. This does not change the separate summary/translation generation worker settings.
The added regression test verifies that the next physical page cannot start during the current page's independent
review. The rollback suite passes 155 tests; no additional live model benchmark or zoom trace is needed for this
scheduler-only change. No speedup is claimed for the serial configuration.

Signed-off rollback commit `ec4ed8ae0f58e262992261f858c854c1bc6dffed` was fast-forward merged into `personal`.
After confirming both queues idle and the same launcher/data ownership, the daily service restarted PID 41236 as
12244. Model selection and the daily papers' PDF/source/notes/layer bytes are unchanged. The receipt is
`launch/scoped-pdf/daily-service-serial.json` in the retained managed worktree.

## Quality finding and correction

An initial proposal contained Johnson's missing label (4), causing the redundant-restoration request to be skipped.
Independent review then rejected that proposal, but the prior control flow did not restore the still-missing label.
The regression now follows rejected restorations with a request targeting the **specific remaining numbered display**,
using the review feedback and current text, followed by independent PDF review. A regression test reproduces this path.
Unresolved numbers are explicit issues after the existing bounded local rounds, never silently treated as restored.

The first reviewer also incorrectly claimed that the printed transport T required a calligraphic replacement.
Direct PDF inspection and its embedded font information show the equation's E and T in the same italic face,
distinct from the dissipation symbol. The final proposal preserves the original T and adds only the printed (4).
Model explanations alone were not accepted as evidence.

Final trial sources retain Galtier's labels (1)–(11), including equation (10)'s $\Omega^2\epsilon^2/4$ prefactor,
and Johnson's (1)–(12) and all three figures. The original mean-energy and vorticity definitions were compared with
the retained PDF. Printed author inconsistencies are preserved rather than scientifically rewritten. Missing
bibliography content and Johnson's author-contact footnote remain explicit issues; this is not error-free OCR.

## GPU / 2x zoom

The documented dense paper 2512.23916 uses the previous retained standalone export, with the current reader code
substituted for the after view. Headed Chrome, RTX 4060 Ti, enabled GPU compositing/rasterization, 1512×982 CSS
pixels at 2x. Chrome `PipelineReporter` records presented/dropped frames; no headless rAF proxy was used.

| Gesture | Before presented / dropped | After presented / dropped | Before / after longest gap |
|---|---:|---:|---:|
| Pinch out, initial baseline | 297 / 6935 | 504 / 2 | 17 / 83 ms |
| Pinch in, initial baseline | 145 / 10678 | 476 / 2 | 2135 / 83 ms |
| Drag, initial baseline | 196 / 52 | 156 / 1 | 1802 / 33 ms |
| Full click, initial baseline | 57 / 5 | 55 / 8 | 50 / 67 ms |
| Pinch out, baseline repeat | 576 / 1 | 504 / 2 | 83 / 83 ms |
| Pinch in, baseline repeat | 458 / 1638 | 476 / 2 | 33 / 83 ms |
| Drag, baseline repeat | 60 / 2648 | 156 / 1 | 26509 / 33 ms |
| Full click, baseline repeat | 85 / 52 | 55 / 8 | 1001 / 67 ms |

Baseline traces are highly unstable and sometimes do not reach the intended level; retain those traces as such,
not as evidence of a speedup. The after trace completes all gestures normally. This establishes no repeatable new
slowdown, but the noisy environment limits comparative conclusions. No animation algorithm changed; partial section
summaries add a label outside the word-token indices, retaining existing annotation identities.

## Evidence and rollout

Raw original/trial copies, model request timings, provider failures, proposal/checkpoint files, quality-failure and
recovery copies, UI screenshots, generation records and GPU traces remain in the managed worktree's ignored
`launch/scoped-pdf/` folder. Preserve the older `pdf-speed-equations` worktree and its evidence.

Signed-off implementation commit `c21e91ceb938181a3a869cd9ba078c554b874299` was fast-forward merged into `personal`.
The primary checkout stayed on `personal`. Its pre-existing glossary content and the two unrelated design drafts
were preserved byte for byte; only the agreed Correction scope entry is included in the implementation commit.

Immediately before refreshing the daily service, both generation and PDF-engine queues were empty. The listener
was the existing primary-checkout **TextFold Personal** scheduled-task launcher, using
`C:/Users/admin/AppData/Local/TextFold/personal`. That same owner restarted PID 85420 as 41236. Served reader/app JS
bytes match the merged source and the selected model is unchanged. The bridge on 10531 was reused and not restarted.
The daily selected papers' original PDF, source, notes and all layer files remain byte-identical across deployment.

An actual browser on **3017** confirmed existing Key/Takeaway selections 8/4 and 8/2, correct complete physical-page
coverage 4/4 and 6/6, zero JavaScript errors, and no queued/running jobs. `daily-service.json`, `daily-check.json` and
the daily screenshots retain the receipts. The controlled isolated server was stopped after validation.

This delivery updates code; it does not copy experimental sources/layers into the daily library. The separate
cache-opening incident is **unresolved**. No push or upstream PR was performed.
