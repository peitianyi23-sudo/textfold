# Local PDF checking slowdown and interruption

Incident: 2026-10-19, local upload `pdf-feb93e7749f4ecbb`, *On space and time correlations of isotropic and rotating
turbulence*, 14 physical pages. The user reported very slow checking, HTTP failure and an interrupted reader.

## Confirmed causes

The initial job took 664.90 seconds and failed during physical page 10's independent review with HTTP 500. Pages
1–9 were preserved. A later explicit resume spent another 61.88 seconds comparing page 10 before being stopped.
The image adapter lacked bounded transient-error retries, so the first 500 ended that job immediately.

Page localization also used the earliest and latest four-word matches anywhere in the extraction. On page 2,
the actual body anchors occupied source positions near 5515–11000, but the running-header names matched a distant
bibliography passage near 64068. This expanded that page's context to 62,979 of the extraction's 67,895 characters
(92.8%). Several other pages also received unrelated text from far away in the document. This was an actual
localization defect, not evidence that the whole source was needed for every page.

## Changes and regression evidence

- Localize using the main contiguous group of reading-order anchors. Keep surrounding paragraph context and retain
  the full-extraction fallback for unmapped pages. Every physical page still receives its original full-page image.
  Page 2's extraction context becomes 7,437 characters; across all 14 pages, 322,748 becomes 105,030 characters.
  This measures payload reduction, not a promised wall-time speedup.
- Retry transient HTTP 429/500/502/503/504/529 responses with the same prompt and original images, using the existing
  finite backoff. The Stop event interrupts the wait; no retry is sent after stopping. There is no text-only fallback.
  Request receipts retain retry count/status/wait, and progress identifies comparison, independent review or retry.
- Reuse an already returned comparison when the new, smaller local context is an unchanged substring of the saved
  context and every proposed edit's original anchor remains present. Proposed edits still require independent PDF
  review. For this paper's saved page-10 proposal, the new 8,257-character context is inside its saved 21,570-character
  context, and all nine edit anchors remain valid. It can continue at independent review rather than repeat comparison.
- Keep PDF checking strictly serial. Scope selection, 30-page limits, independent verification, source/annotation
  reconciliation, original PDF and other papers retain their existing behavior.

Before the fix, `tests.test_pdf_recovery` failed on both a distant-phrase localization fixture and a 500-then-success
image-provider fixture. After the fix, all **159 tests** pass, including cancellation during retry and reuse of a
smaller unchanged context with mandatory independent review. The real-paper localization assertion also changes
from failure to success. No new zoom trace is needed because reader rendering and animation code are unchanged.

## Delivery and recovery evidence

Signed-off implementation `af0aabf4f4fb9af554b2365bc782a1f988f35296` was merged into `personal`. Both model and PDF-engine
queues were idle before restarting the same primary-checkout TextFold Personal owner, PID 12244 → 17256. Model
selection and the daily papers' PDF/source/notes/layer bytes were unchanged during deployment. The bridge was not
restarted. Unrelated primary-checkout glossary and design drafts were preserved.

The affected paper's complete pre-recovery directory is retained in the managed worktree's ignored
`launch/pdf-checking-recovery/before-paper/`. Raw localization tables, failing/passing tests, deployment receipt and
the resumed job record are in that same evidence folder. Recovery uses the normal daily-service queue from the
existing 9/14 checkpoint, without rerunning completed pages.

Recovery job `c987804f44` completed successfully. Physical pages 10–14 took 183.71 seconds across eight visual
requests; page 10 reused its saved comparison and proceeded directly to independent review. No request revisited
pages 1–9, and this recovery encountered no HTTP failures or retries. The subsequent English generation completed
all 22 sections and argument links. The complete resumed job took 286.79 seconds including generation; this is not
a controlled comparison against the earlier failed run.

The daily paper now records completed coverage 1–14, with its English layer populated (124 units, 23 chunk entries
and 53 argument links). The actual reader displays the English document and “PDF 校对完成 · 有待核实位置”, with no
interrupted-job banner. Unresolved extraction observations remain explicit; completed coverage does not mean
perfect OCR. The original PDF and all pre-existing extracted image files are byte-identical to the backup.
