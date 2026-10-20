# Original display mathematics in local expansion

## Behavior and cause

On `pdf-cab09c60d336f652`, clicking the Key summary about the electron continuity equation opened
`u12` at Full but left the separate equation block `eq16` at Key, hidden by its normal importance selection.
The next passage, `u13`, had the same problem with equation (2). The formulas remained intact and visible
at global Brief/Full. The paragraph-only expansion path predates the equation-caption changes.

Local expansion restores the source passage using the existing card, original typography and token
transitions. A paragraph and its immediately following display equations now share that card. A new
paragraph, heading, figure, list, raw block or enclosing-container boundary ends the passage. Source units,
formula HTML, saved layers and Key/Takeaway importance decisions remain separate and unchanged.

The reader groups these existing blocks once at startup. Collapsed containers use `display: contents`.
Opening and closing update the associated equations; ordinary paragraph redraws do not perform extra
equation updates. The existing global-level block renderer handles zoom/reset, and the existing sandbox
closes local cards when constructing global zoom keyframes. Figure and equation captions retain their
existing independent interactions.

## Functional and layout evidence

- `python -m tests.browser_paragraph_equations` fails on pre-fix JavaScript with the paragraph at Full
  and its equation still hidden. It passes with the fix through real browser clicks.
- The regression covers consecutive equations, independent next passages, heading/figure boundaries,
  second click on the formula, Escape, global zoom reset, selected equations without duplicate formulas
  or generated captions, original formula HTML, figure-caption expansion and a 390px viewport.
- The actual daily reader at port 3017 passes clicks on `u12` and `u13`, collapse/Escape, exact unchanged
  equation (1) HTML, and no additional horizontal overflow on opening at 390px. No browser errors occurred.
- Before/after exports of the same saved paper have zero differences in visibility, typography or block
  geometry (0.6px tolerance) for 99 blocks at all five global levels, at 1200px and 390px widths.
- The Python suite runs 239 tests: OK, three skipped. It emits resource-cleanup warnings from its
  subprocess/socket tests. JavaScript syntax and patch whitespace checks pass.

The daily paper already has horizontal page overflow at 390px before this change (595px page width).
The before/after width is identical. This existing responsive-layout issue is outside this equation fix.

Screenshots and replay scripts are retained locally under the ignored `launch/paragraph-equations/`:
`daily-fixed.png`, `daily-mobile.png`, `check_daily.py`, `check_layout.py`, and `layout-results.json`.

## Zoom measurement

The comparison uses the prescribed dense paper `2512.23916`, identical saved layers, Chrome on Windows,
1512×982 at device scale factor 2, and Chrome's GPU frame trace. GPU compositing is enabled and rasterization
reports `enabled_force`. It reuses the upstream gesture sequence and frame parser, adapted for Windows
and retained under `launch/paragraph-equations/final-comparison/`.

Completed final-code samples comprise one baseline run and two feature runs. The last repeated baseline run
stalled during tracing, as did its fresh-browser retry; both incomplete controls are excluded. The initial
prototype's earlier measurements are also excluded: they prompted removal of redundant equation updates
from ordinary paragraph redraws. Raw completed final-code traces, `results.json` and `summary.json` are retained.

| Gesture | Before presented / dropped (1 run) | After presented / dropped (2 runs) | Before / after dropped | Worst gap before / after (ms) |
| --- | --- | --- | --- | --- |
| Pinch out | 534 / 4 | 1068 / 10 | 0.74% / 0.93% | 85 / 85 |
| Pinch in | 473 / 6 | 983 / 7 | 1.25% / 0.71% | 83 / 83 |
| Slider drag | 146 / 6 | 286 / 7 | 3.95% / 2.39% | 67 / 50 |
| Click Full | 53 / 8 | 108 / 18 | 13.11% / 14.29% | 55 / 83 |

All completed gestures reach the expected levels (1, 4, 0, 4). Overall drops are 24/1230 (1.95%) before
and 42/2487 (1.69%) after. Results vary by gesture: pinch-out and Click Full average one more dropped
frame per feature run, while pinch-in and drag improve. These bounded samples show no overall increase
in frame drops; they do not establish a general performance improvement or guarantee every gesture.
