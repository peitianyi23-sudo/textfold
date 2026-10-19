# Equation and Figure 1 caption rendering parity

This supersedes the earlier equation explanation presentation. The user asked for an actual Playwright comparison
of Figure 1's caption and equation (3)'s description on the uploaded Favier paper.

## Actual reproduction

`launch/equation-caption-parity/reproduce.cjs` clicked Figure 1 and equation (3) on the daily reader and saved both
screenshots before editing. The figure expanded in Inter with 21 token animation spans; the equation expanded in
Source Serif with zero token spans. Sharing only `morph` and a copied local-open style did not produce the same
text transition or typography. This was the missed defect in the earlier fixes.

## Fix

The reader payload now builds an ordinary caption unit from existing equation decisions and adjacent author prose,
using the same ladder token alignment as figure captions. It is attached with `unitNode` and goes through the same
`pieces`, `drawUnit`, `renderUnit` and `toggleUnit` path. The separate equation expansion renderer and click handler
were removed. Formula bodies remain independent animation pieces, so caption text is no longer captured as one
large bitmap. The caption uses the same sans font, full-caption size, local-open card and Takeaway inset as figures.
Existing translated prose and equation explanations form translated caption ladders too. This is a view-only copy;
source files and saved model layers are not rewritten or regenerated.

Full/Brief already contain the author prose and Topic hides equations, so hidden duplicate caption tokens are not
rendered at those levels or in their zoom sandboxes. The completed-check banner remains absent.

## Verification

Feature branch `codex/equation-caption-rendering`, isolated paper copy on port 3020. Playwright actually clicks
Figure 1 and equation (3) and asserts equal font, font size, line height, left padding, background, border radius
and shadow both closed and open. Captured values: closed 15.5px Inter / 22.475px line height; open 14.5px Inter /
21.75px line height; both keep the 22px Takeaway inset. Equation explanation now has individual token nodes.
Screenshots and `parity.json` are under `launch/equation-caption-parity/`.

Click again, Escape, Key/Takeaway/Topic/Full transitions and 390px horizontal overflow passed. Original formula HTML
stayed identical; Figure 1 retained its normal behavior; no JavaScript errors occurred. All 161 Python tests passed,
including source/layer input preservation and actual source-to-summary token alignment. Syntax and whitespace passed.

## GPU measurements

Used the actual equation-heavy 14-page Favier paper in place of the documented 2512.23916 benchmark (absent in this
library), Chrome on RTX 4060 Ti, GPU compositing/rasterization enabled, 1512×982, scale factor 2. Raw traces remain in
the evidence directory. The first comparison exposed unnecessary rendering of hidden duplicate captions; those
were excluded from Full/Brief/Topic and their sandboxes, then the same sequence was measured again:

| Gesture | Before presented/dropped | After presented/dropped | Worst gaps before/after ms |
| --- | --- | --- | --- |
| Pinch out | 442/3 | 455/0 | 150/83 |
| Pinch in | 459/3 | 360/0 | 284/67 |
| Slider drag | 167/11 | 153/0 | 300/270 |
| Click Full | 57/2 | 52/22 | 483/234 |

Because Click Full had different dropped-frame counts, a focused three-trial comparison then used the actual
old daily page and feature page, without other browser work. Presented/dropped frames were 58/2, 58/1, 58/1 before
and 57/4, 58/3, 58/2 after. Warm trials' worst gaps were 33/33ms before and 50/33ms after; the first trial in both
versions includes a roughly 1.5s idle/warm interval. The large Click Full difference in the full gesture sequence
was not reproduced consistently. These measurements show mixed small-frame variation and faster pinch sequences;
they do not establish a speedup or prove identical timing. The visual parity checks are separate from this evidence.

Feature validation completed before local personal delivery. No model regeneration is required.
