# PDF checking and essential-equation verification

Validated 2026-10-19 on the two agreed papers, using isolated copies of their original extraction, selected PDFs,
and the existing ChatGPT subscription bridge with model `gpt-6.1-sol`. No Zotero cache was written.

## Live correction measurements

| Paper | Serial baseline | Page-local comparison and region review | Vision calls |
|---|---:|---:|---:|
| Galtier, Weak inertial-wave turbulence theory, 4 pages | 291.28 s | 185.93 s | 18 -> 11 |
| Johnson, Energy transfer…, 6 pages | 320.52 s | 91.66 s | 25 -> 12 |
| Total | 611.80 s | 277.58 s | 43 -> 23 |

These samples were 54.6% faster overall, not a promised speed multiplier. Neither run reported a provider error.
Baseline and new runs overlap in wall-clock time and share the subscription provider; model sampling and service
load remain sources of variation. Request wall time includes request serialization and provider/network time.
Summed call durations are 586.85 s before and 430.48 s after; the latter overlaps because of bounded concurrency.
Full Markdown normalization fell from 114 calls / 16.65 s to 10 / 1.25 s; image-map parsing fell from 114 / 4.47 s
to 4 / 0.13 s. A separate no-network replay measures page preparation rather than inferring it from residual time:
the baseline renders 26 page images and eagerly saves 66 PNGs across both papers; the new first comparisons render
10 pages and save 10 PNGs, with edit crops produced only when needed. This replay excludes live review crops.

The first faster trial (130.83 s / 89.69 s) failed quality acceptance because it omitted equation (10) and several
labels. It was not delivered. The numbered-display inventory and region-restoration pass fixed that failure.
The table above is the subsequent accepted run. Rendering-only fixes for aligned rows were then verified without
additional model calls: the original LaTeX, tokens, atom identities and equation ids remain unchanged.

## Content and presentation

- All 4 and 6 physical pages receive a full first comparison, including the finalized-Markdown case without blocks.
  Galtier retains 12 display blocks, including restored equation (10) and all labels (1)–(11). Johnson retains 13
  display blocks, labels (1)–(12), and all 3 figures. Final reading copies contain 34 and 46 units; correction merges
  OCR fragments back into paragraphs, rather than preserving the damaged segmentation for its own sake.
- Direct PDF inspection verified the printed velocity **v** is retained, equation (10)'s prefactor is
  $\Omega^2\epsilon^2/4$, the energy/helicity spectral exponents match equation (11), and Johnson's mean kinetic
  energy and vorticity definitions match the PDF. Galtier equation (9)'s mismatched bracket is actually printed in
  the PDF and is preserved. The model's reason is never treated as evidence on its own.
- Key selects 8 equations in each paper. Takeaway independently retains 4 Galtier and 2 Johnson blocks. Core results
  appear directly, with meanings, validity conditions, original equation identity and access to the original PDF.
  Topic does not retain them. English and Chinese share selection but have translated explanations.
- `aligned` previously rendered literal ampersands and flattened rows in the installed converter. Layout now uses
  its array path, preserving all source symbols, rows and original LaTeX. The displayed equation's body scrolls
  independently of its meaning and conditions; no algebraic shortening is performed.
- 139 automated tests pass. They include overlap relocation in a changed draft, resume and provider failure,
  independent rejection of a plausible author-symbol rewrite, omitted numbered equations, layer/translation
  identity, notes, images, and faithful aligned rows. Browser checks cover actual Full/Key/Takeaway/Topic views in
  English and Chinese and 390-pixel viewports, comparing the rendered mathematics with the stored originals.

## Remaining limits

Checking completion does not certify perfect OCR. Both trials explicitly report missing reference-list content
already absent from the extraction; Johnson also reports an omitted author contact footnote. Some model reports
are merely “already proposed” or out-of-page context notices and should not be read as additional source damage.
The independent evidence and original reports are retained. No mandatory human approval is added.

The JAUYGCML / J2CRW9DP cache-opening incident remains a separate unresolved problem. No cache identity was inferred
from titles, and this change does not claim to fix that incident. Other library papers are outside the rollout.

Raw timings, original/corrected copies, scripts, page images, screenshots and Chrome frame traces remain under
`C:/Users/admin/.codex/worktrees/pdf-speed-equations/textfold/launch/pdf-speed-equations/`.

## GPU and deployment

Headed Chrome, NVIDIA RTX 4060 Ti, GPU compositing/rasterization enabled, 1512x982 CSS pixels at 2x. Chrome
`PipelineReporter` traces measure presented/dropped frames, not headless rAF intervals. The documented dense paper
2512.23916 was available locally and used without substitution; Galtier additionally exercises retained long formulas.

| Paper / gesture | Presented before -> after | Dropped before -> after | Longest gap before -> after, ms |
|---|---:|---:|---:|
| 2512.23916 pinch out | 540 -> 575 | 1 -> 1 | 83 -> 83 |
| 2512.23916 pinch in | 475 -> 477 | 3 -> 2 | 83 -> 83 |
| 2512.23916 drag | 150 -> 169 | 1 -> 3 | 400 -> 33 |
| 2512.23916 click Full | 56 -> 60 | 3 -> 7 | 38 -> 200 |
| Galtier pinch out | 571 -> 598 | 17 -> 8 | 2286 -> 83 |
| Galtier pinch in | 526 -> 507 | 53 -> 2 | 484 -> 67 |
| Galtier drag | 202 -> 161 | 14 -> 0 | 67 -> 33 |
| Galtier click Full | 53 -> 58 | 13 -> 2 | 87 -> 50 |

The dense-paper click result prompted a focused follow-up, in alternating order: before drop counts 3 and 46
(50/334 ms worst gaps), after 2, 3 and 7 (33/50/83 ms). Another before sample had zero presented frames and is
invalid for a smoothness comparison. There is substantial run-to-run variation, including baseline outliers;
these traces do not establish a repeatable slowdown or a universal smoothness guarantee. Animation logic is
unchanged. All valid and invalid raw traces are retained rather than hiding the noisy samples.

18 actual-page checks passed across Full/Key/Takeaway/Topic, English/Chinese, and narrow viewports. Additional
checks opened the original PDF, followed a real stored note anchor, and scrolled the longest retained equations.
At 390 CSS pixels Galtier's formula viewport is 356 pixels wide with 1032 pixels of content, Johnson's 356/436;
both scroll locally, both keep the meaning at x=17, and document width remains 390. Original rows and labels survive,
with no literal alignment ampersands. The isolated note fixture is not copied into the daily library.

Daily service application receipts are retained with the raw evidence; deployment follows the idle queue and
existing scheduled-task ownership checks after the tested commit is merged into `personal`.
