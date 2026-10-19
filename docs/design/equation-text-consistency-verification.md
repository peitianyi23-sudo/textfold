# Consistent equation text interaction and completed-check banner

The user rejected the separate Original disclosure. This supersedes that presentation in
`equation-caption-interaction-verification.md`.

## Changes

Equation explanation text is clicked directly, like other reader text. The existing `morph` path and local-level
state switch between the short explanation and adjacent author prose, with the same local-open card appearance.
A second click or Escape restores the explanation; global zoom restores the current level. No disclosure, arrow,
Original label or extra control remains. Formula HTML and the 22px Takeaway inset remain unchanged.

A completed full-document correction no longer renders the fixed correction banner, including when observations
remain in its receipt. The receipt is retained unchanged. The existing completion watcher reopens the reader,
which removes the banner automatically; interrupted/error/scope-selection controls remain available when relevant.

## Feature validation

Feature branch `codex/equation-text-consistency`, isolated paper copy on port 3020. Browser replay
`launch/equation-consistency/check.cjs` passed direct-click expand/collapse, Escape reset, shared local-open styling,
unchanged figure-caption interaction, Key/Takeaway/Topic/Full transitions, exact formula HTML preservation, 390px
page overflow, no completed-check overlay and no separate disclosure controls. No JavaScript exceptions occurred.
Screenshots are retained in the same ignored evidence directory. All 160 Python tests passed, including completed
banner absence with retained observations and unfinished-state control preservation. JS syntax and whitespace passed.

GPU comparison used the actual equation-heavy 14-page paper (the documented 2512.23916 paper is absent here), Chrome
on RTX 4060 Ti, GPU compositing/rasterization enabled, 1512×982, scale factor 2. Same saved layers and four gestures:

| Gesture | Before presented / dropped | After presented / dropped | Worst gap before / after ms |
| --- | --- | --- | --- |
| pinchOut | 453 / 0 | 457 / 1 | 83 / 83 |
| pinchIn | 347 / 1 | 386 / 3 | 300 / 200 |
| drag | 211 / 15 | 220 / 14 | 284 / 217 |
| clickFull | 56 / 11 | 58 / 3 | 83 / 50 |

The same levels (1,4,0,4) were reached. Aggregate dropped frames: 27/1094 (2.47%) before, 21/1142 (1.84%) after.
No overall zoom regression is indicated; the measurement is not a claim of a performance improvement.

Signed-off implementation `5517c9286894500a23fbc05c9c52960fec368339` was merged into `personal` after feature
validation. The idle daily service was restarted (PID 73656 → 65404); served JS/CSS match the primary checkout.
Daily paper PDF/source/notes/layer bytes and model selection were preserved. Actual in-app-browser verification
confirmed no correction banner, and direct clicking produced `eq-caption has-source local-open` with original prose.
The isolated feature server was stopped. Unrelated glossary and design drafts remain untouched; no push/PR.
