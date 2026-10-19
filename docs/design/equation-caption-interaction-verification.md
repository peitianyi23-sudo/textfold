# Equation explanation interaction and alignment

Validated on the feature branch `codex/equation-caption-interaction`, using an isolated copy of
`pdf-feb93e7749f4ecbb` served at port 3020. The daily service and library remained on `personal` during verification.

## Reproduction and fix

The actual daily Takeaway reader reproduced the report: clicking equation (20)'s generated explanation left its
text unchanged, and the explanation had zero inset beside the Takeaway spine. The browser assertion failed with
`RED: clicking equation explanation leaves summary unchanged`.

The explanation now uses a native disclosure, with the same 22px Takeaway inset as figure captions. A visible
Original control opens the adjacent author paragraphs within the same section, retaining their inline mathematics.
These are original explanatory context: equations generally do not have an authored caption. A second click or
Enter restores the short explanation. Global zoom closes the disclosure, and sandbox keyframes keep it closed.
Original paragraphs are populated only on opening, so hidden source copies do not burden every zoom frame.

Equation (20) already had Key and Takeaway selection, while equation (19) had Key only. Its chapter takeaway already
connects the sound spectrum to the energy spectrum and time correlation; the Topic map retains Lighthill’s theory.
The generation instruction now explicitly connects essential equation concepts to chapter Takeaway and Topic.
Topic keeps the existing concept-map presentation, without adding full formulas. Existing saved layers need no
regeneration for the interaction fix.

## Validation

The browser regression replay in `launch/equation-caption/check.cjs` passed on the feature service:

- Takeaway shows equation (20) and hides Key-only equation (19); Key shows both.
- Click opens real source prose; Enter closes it and restores exactly the previous short explanation.
- Takeaway inset is 22px, Key inset is zero; global level changes close the disclosure.
- Full retains the exact original formula HTML and hides generated equation explanations.
- Topic retains the chapter concept summary; figure captions still open independently.
- At 390px width, the page has no horizontal overflow and original formula HTML stays unchanged.
- No JavaScript exceptions occurred.

All 159 Python tests passed. JavaScript syntax and patch whitespace checks passed. Browser screenshots and raw
performance traces are retained under the ignored `launch/equation-caption/` evidence directory.

## GPU zoom comparison

Measured Chrome on NVIDIA GeForce RTX 4060 Ti with GPU compositing/rasterization enabled, at 1512×982 and device
scale factor 2. This uses the user's actual 14-page equation-heavy paper instead of the documented 2512.23916
benchmark, which is absent from this library. Both versions use identical saved layers and the same four gestures.
An initial run interrupted by other browser inspection is retained as `zoom-before.json` but excluded; the clean
comparison is `zoom-before-clean.json` versus `zoom-after.json`.

| Gesture | Before presented/dropped | After presented/dropped | Worst gap before/after (ms) |
| --- | --- | --- | --- |
| Pinch out | 567 / 0 | 453 / 0 | 50 / 83 |
| Pinch in | 348 / 1 | 456 / 2 | 284 / 284 |
| Slider drag | 160 / 6 | 166 / 2 | 183 / 233 |
| Click Full | 57 / 1 | 56 / 2 | 50 / 36 |

Aggregate dropped frames are 8/1140 (0.70%) before and 6/1137 (0.53%) after. Individual gestures vary by a small
number of frames; this run shows no overall smoothness regression and does not establish a performance improvement.
All four gestures reach the same intended levels in both versions (1, 4, 0, 4).

## Delivery

Signed-off commit `e6fca88bf0945fe9a1e362019de82ba498f2a7e6` was fast-forward merged into `personal` after the
feature-branch checks. Both queues were idle before restarting the existing daily service, PID 17256 → 73656.
Served `reader.js`, `reader.css` and `app.js` match the primary checkout. The model selection, affected paper and
previous validation papers' PDF/source/notes/layer bytes stayed unchanged. The existing bridge was retained.
Unrelated glossary edits and design drafts remain untouched. No push or upstream PR was made.
