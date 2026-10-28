# Long-document scrolling trial, 2026-10-28

Branch: `codex/textfold-long-document-scroll`, based on the personal checkout's committed HEAD.
This is a trial for the user to experience before any merge. No merge or upstream publication is authorized.
The primary checkout's unrelated PDF attachment edits remain there, untouched.

## Change

Ordinary page scrolling previously scheduled a complete alternate-level keyframe after just 200 ms of rest.
On the supplied Galtier paper, these tasks repeatedly blocked the browser for 50–105 ms in the paired baseline run.
The renderer now waits through short reading pauses, prepares an alternate level across cancellable frame-separated
steps, and abandons incomplete preparation when scrolling or zoom input resumes. Completed keyframes and the
existing word/formula animations remain in use; an incomplete keyframe is never published.

Equation bodies retain exact measured heights and use `content-visibility` outside the viewport. Sandbox copies
use those measured dimensions while their formula trees remain unrendered. The animated stage and printing
explicitly render the formulas. Width/type changes invalidate saved dimensions; hidden equations keep known
dimensions only at the matching width/type. The document, text selection, notes, and equation HTML stay in the DOM.

## Environment and paired scrolling result

Windows, headed Edge, GPU compositing/rasterization enabled, 1512 × 982 CSS pixels at device scale factor 2.
The test server on port 3018 uses a copied paper under the worktree's ignored `launch/scroll/data` directory.
The daily service on port 3017 and its library are not replaced. The user trial runs on port 3019 with its own
settings file as well as the copied paper; port 3018 was used for measurement.

Paper: `md-a-multiple-time-scale-approach-for-a8604d3f`, *A multiple time scale approach for anisotropic inertial
wave turbulence*. No model requests or paper regeneration were needed. The contributor guide's specific
2512.23916 fixture was unavailable locally; measurements here use the user's supplied equation-heavy document.

Three down/up/down sequences at each reading level, with 380 ms reading pauses:

| Measurement | Baseline | Candidate |
| --- | ---: | ---: |
| Longest measured keyframe preparation task/step | 105.1 ms | 22.3 ms |
| Preparation tasks/steps at least 50 ms | 16 | 0 |
| Full: dropped frames | 9.1% | 1.2% |
| Brief: dropped frames | 7.0% | 1.2% |
| Key: dropped frames | 0.6% | 0.0% |
| Full document height | 27245 px | 27245 px |
| Brief document height | 22954 px | 22954 px |
| Key document height | 16263 px | 16263 px |

Raw paired results are in ignored `launch/scroll/baseline.json` and `launch/scroll/final.json`, with GPU traces
beside them. An earlier candidate that merely shortened the preparation band was discarded. These are local
measurements, not a guarantee for every browser extension or machine. Frame gaps across deliberately idle
intervals are not treated as animation stalls.

The full paired run also exercised pinch out/in, slider drag, and clicking Full. Dropped-frame percentages
were respectively 2.3/1.2/4.0/12.7 before and 1.6/0.8/2.2/4.9 after; both reached levels 1/4/0/4.
A separate gesture-bounded run gave 1.9/6.2/2.9/3.9 before and 2.3/2.9/2.9/5.9 after. That baseline also
stopped pinch-in at level 3; the candidate reached the expected level 4. The one- or two-frame differences
on the other gestures show measurement variation; these samples do not establish an across-the-board zoom
speedup. Both bounded traces had a 50 ms worst gap for clicking Full. The earlier unbounded trace's long
idle gaps should not be read as continuous-animation stalls. Bounded results/traces are retained in
`launch/scroll/zoom-baseline` and `launch/scroll/zoom-candidate`.

## Functional regression checks

`tools/readercheck.cjs` exercises all five levels at widths 1512 and 1000, interrupts preparation with scrolling
and another level change, and checks that level transitions still animate. Comparing formula geometry with
off-screen skipping enabled and disabled gave zero position/height differences for all displayed equations
(80 at Full/Brief, 34 at Key, 12 at Takeaway). Reading-anchor and document-height drift after preparation were
both zero at both widths. No reader JavaScript errors occurred.

`python -m unittest discover tests`: 370 tests completed in 22.824 s, OK, 18 skipped. The suite emitted resource
cleanup warnings for subprocesses/files/sockets; it had no failing tests. JavaScript syntax and Git whitespace
checks also passed.

## Reproduction

Install Playwright and Edge, serve a copied test library, and set `NODE_PATH` if using a bundled Playwright runtime.
Save the original reader assets as `baseline-reader.js` and `baseline-reader.css` before editing.

```powershell
node tools/readerbench.cjs URL launch/scroll/before launch/scroll
node tools/readerbench.cjs URL launch/scroll/after
node tools/readercheck.cjs URL launch/scroll/checks
python -m unittest discover tests
```

The benchmark checks actual scrolling and zoom inputs, records GPU-presented/dropped frames and preparation
durations, and exits unsuccessfully for a preparation step of at least 50 ms, an unexpected zoom destination,
or a reader JavaScript error. Zoom traces are bounded by user-timing marks around the gesture and its settling
animation, excluding later background preparation. `--zoom-only` runs the gesture comparison by itself.

User acceptance of the running trial is still pending.

## Follow-up: reading-level wheel still stalled

The user confirmed ordinary page scrolling was much better but rejected reading-level wheel performance.
The earlier gentle pinch measurements did not cover rapid normal wheel detents and reversals over the level bar.
That stronger test reproduced live preparation work of 59–77 ms and browser long tasks up to 155 ms.

The owning bug was `anchorAt`: an equation or a gap inside a long section selected the section heading even
when the heading was several screens above the viewport. The prepared keyframe covered the actual passage,
so the distant heading was missing and `stageBegin` rejected it. The reader repeatedly fell back to live-page
layout and hundreds of live animations. When the heading is off screen the anchor now uses the nearest
paragraph. Equation explanation captions, which disappear at Full/Brief, resolve to their source passage.

A separate visual bug became visible once the stage actually ran: equation copies inherited `max-width:100%`
inside zero-width animation groups. Their native MathML retained its width but the outer copy was clipped to
zero width. Measured animation boxes now override that maximum width, retaining their actual pixel width.
Visual inspection confirmed the equations remain drawn during a held Full-to-Brief transition. Browser
regression checks verify the animated formula copies have nonzero width and visible content.

An experiment preparing cold zooms asynchronously on demand was discarded: it introduced interruption and
direction-change problems. The final change retains the existing zoom timing and animation pipeline.

The focused rapid-wheel comparison before the final width repair is retained in `launch/scroll/before-levels.json`
and `launch/scroll/anchor-only-levels.json`. In the rested passage the repaired anchor used the stage for all
level crossings and reversals, with no long tasks. Immediately after a page jump it still used the live fallback,
but the longest measured preparation fell to 38.4 ms; browser tasks up to 92 ms remained. This is an improvement,
not a claim that every cold transition is stutter-free. The final GPU benchmark and two-width geometry checks
are retained under `launch/scroll/anchor-final` and `launch/scroll/anchor-checks`.

All five levels and interruptions passed at 1512 and 1000 px; formula geometry and reading-position drift remained
zero. The test suite rerun completed 370 tests in 21.087 s, OK with 18 skipped and the same resource cleanup warnings.
The branch remains unmerged pending another user trial.

Final follow-up benchmark (`launch/scroll/anchor-final/candidate.json`) passed its level destinations,
rapid-wheel preparation threshold, and JavaScript-error checks. GPU frame drops for pinch out/in, slider drag,
and clicking Full were 0.2/0.4/1.8/7.3%; the previous paired trial recorded 2.3/1.2/4.0/12.7%.
These are individual local runs. The rested rapid-reversal test used the stage throughout and committed in
47.8 ms; the cold test still used live preparation, up to 49.7 ms, and recorded browser tasks up to 120 ms.
The latter remains a known performance limitation for the user to assess, not a resolved stutter-free case.
Page scrolling recorded no long tasks at Full/Brief/Key in this run; dropped-frame percentages were 0/0/2.3%.
