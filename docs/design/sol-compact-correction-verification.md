# Compact source correction: Sol / medium

2026-10-20. **Retained for review; not integrated into personal.** The three Clercx failures from the completed
pair are now closed by the real local-model replay described below. The historical pair and its original quality
failure remain recorded unchanged; local closure is not a new whole-paper acceptance or speed result.
Keep `codex/sol-compact-correction` and its worktree for review. No push or PR.

## Implementation and boundary

Latest authority: `C:/Users/admin/AppData/Local/Temp/textfold-sol-compact-correction-handoff-2026-10-20.md`.
The primary checkout remains on personal, with its dirty provider/design changes and unrelated chats' work intact.
The old `codex/pdf-text-evidence` experiment is retained separately.

An ordinary short paper receives one text-only coherent MinerU scan with compact location hints. Direct repairs
retain their document-evidence permission. Remaining questions combine candidate-local original PDF characters
and placement with images only where mapping is faulty or evidence is missing. Readable but unresolved questions
may receive a local image follow-up. There is no fixed broad character judgment or blanket image rereview.
Patches retain exact-source, numeric, caption, footnote and math-boundary publication checks. Candidate repairs are
atomic; successful decisions checkpoint before later requests, so resuming does not repeat completed questions.
Saved API effort handling and the supplied provider edits were carried forward. The running Personal service and
its selected provider were not changed or restarted; no connection tests were repeated.

Measured implementation: `c20e344`. Baseline targeted module: frozen `c0fa57d`, with the same current application
adapters. Follow-up `f41278d` and title-region fix `122d871` have the three-case local evidence below; their
full-paper behavior has not been measured. Do not attribute the paired timing to these later fixes.

## Fixed cases and paired protocol

Original PDFs: Boffetta attachment 3506 / MLMPBK65 (eight pages), Clercx 2951 / 4I6IB88E (four pages), as listed in
[the sample manifest](targeted-correction-sample-manifest.md). Both versions import the same preserved
`launch/mineru-cloud-reparse-20261020/after/{3506,2951}` snapshots through the normal cache adapter. PDFs and
producer caches remain read-only. All correction output uses task-owned data directories.

Fixed-question probes restored Boffetta's two plain E spectra, exponent 2/3 and complete eight-value contour list,
while retaining printed (e,r). After fixing a real inherited-page error, a Clercx local probe restored the Rutgers
exponent, both prose tau readings, the mistaken Latin l while retaining the correct lambda relation, and grant
slashes. These were supplied-question checks, not discovery/recall evidence. An earlier fragment probe kept the
full location table, creating artificial omission questions; it is retained as a diagnostic and excluded.

Then run once, serially, in this order:

```powershell
python tools/bench_pdf_evidence.py baseline --label sol-baseline
python tools/bench_pdf_evidence.py new --label sol-new
```

All sixteen actual paired requests used the existing application bridge at `127.0.0.1:10531/v1`, API model
`gpt-6.1-sol`, effort medium. Both text and images use the application's normal adapters. No request failed,
retried, dropped effort or hit a TextFold response cache. Reported provider cached-input tokens were zero.
This is a single same-day pair on known regression papers, not independent generalization or a stable latency estimate.

## Completed measurements

| Paper | Old seconds | Compact seconds | Logical / HTTP calls | Submitted images | HTTP body bytes |
|---|---:|---:|---|---|---|
| Boffetta | 104.41 | 95.37 | 5/5 → 2/2 | 26 → 5 | 3,773,063 → 719,914 |
| Clercx | 129.32 | 103.65 | 5/5 → 4/4 | 28 → 18 | 8,976,925 → 1,613,028 |
| Total | 233.73 | 199.02 | 10/10 → 6/6 | 54 → 23 | 12,749,988 → 2,332,942 |

Actual total completion time fell 14.8%; no failed-attempt subtraction is involved. Raw submitted PNG bytes fell
9,438,140 → 1,606,030 (83.0%); HTTP body bytes fell 81.7%. Logical prompt text **grew** 144,222 → 172,778 characters.
Returned answer text, recovered from actual HTTP responses, fell 31,044 → 25,700 characters. Bridge usage reports
81,370 → 70,750 input tokens and 10,263 → 8,961 output tokens, including 915 → 912 reasoning tokens. Usage was
available for every completed attempt. Shorter payloads did not materially reduce reasoning generation.

| Stage seconds | Boffetta old | Boffetta compact | Clercx old | Clercx compact |
|---|---:|---:|---:|---:|
| Text screen | 56.78 | 49.15 | 53.52 | 38.40 |
| Local evidence proposal(s) | 27.59 | 42.39 | 42.70 | 61.12 |
| Independent image review | 18.85 | — | 30.93 | — |

Clercx compact used two initial payload batches and a follow-up for two unresolved source questions. It did not
resubmit all images. Model/API waiting remains the dominant cost; reducing image/wire volume is much larger than
the observed time reduction. Timing covers correction through source publication, excluding initial import and
derived reading-layer generation.

## Actual source quality in the measured pair

All twelve original PDF pages were rendered and inspected locally. Accepted patches were checked against those
pages and the focused original crops. Replaying each run's complete accepted history from a fresh identical import
reproduces its published source exactly. Original-PDF and retained-layout copies match across runs byte-for-byte.
No caption-label loss, new dangling footnote or odd math-delimiter parity was found; those structural checks do not
certify transcription correctness.

Boffetta compact fixes both false E bars, the 273 exponent, full contour list, missing convolution star, caption
resolution/subscript faults and the printed negative skewness. It retains printed 16386, computing, dumping,
3.2 and (e,r). One nonunique coefficient spelling proposal remains withheld. Clercx compact correctly restores
the known exponent, omega-zero, nu, tau, lambda and grant separators without changing the correct lambda to l.
No new mathematical mis-edit was identified in these inspected accepted patches. Nevertheless, that measured
version failed quality:

- Clercx's page-2 barred-k question was moved to page 4. A phrase occurring twice on page 2 was discarded by the
  per-page unique-anchor helper, making its single page-4 occurrence appear globally unique. The model correctly
  reported insufficient evidence; the false bar remains. The old paired output repairs it.
- The Clercx title/author restoration was withheld: the supplied region showed the affiliation/author area but
  not the title. The old output restores both. This source-region selection limitation was still present in that run.
- Figure 4's question covered only one inline math span. Its middle legend entry was repaired, but the initial
  parenthesis/plus-marker segment remained damaged while the narrow candidate was declared corrected. The old
  output repairs the complete legend. Full surrounding context alone did not ensure a complete investigation unit.

## Initial local-only follow-up and review

Both observed anchor/caption problems first failed small regression tests. `f41278d` counts **all** anchor hits
across pages and expands a caption-contained question to its complete figcaption before investigation. Replaying
the actual saved localization question locally now selects page 2 / block 24, rather than page 4. This verifies
localization, not a fresh model answer. The caption test verifies complete question packaging, not model fidelity.
No further whole-paper run was made; these fixes do not retroactively pass acceptance.

Pre-closeout local suite: `python -m unittest discover -s tests -q`: 237 tests, 234 passed, three existing platform skips.
Existing subprocess/socket ResourceWarnings remain non-failing. [Two-axis review](sol-compact-correction-review.md)
found no standards violation and one resume defect, fixed and checked separately. Real-run quality findings above
take precedence over unit tests and review approval. No ten-paper expansion, personal merge, push or PR occurred.

Raw receipts, per-paper decisions, source renders, imported inputs and source diffs are retained in this worktree's
ignored `launch/sol-compact-correction/`. `summary.json` records aggregate/stage/usage data; `sol-baseline/http.json`
and `sol-new/http.json` contain request measurements and responses, without authorization headers or keys.
`localization-followup.json` preserves the actual local correction of the page error. Keep this worktree to retain
these ignored artifacts. The reviewable Git diff is `git diff c0fa57d...codex/sol-compact-correction`.

## Three-case live closeout

The subsequent user instruction authorized only these three real failures, retaining this branch without merging
personal or running another full-paper benchmark. Existing anchor/caption fixes remain. `122d871` also includes
consecutive same-page source blocks missing immediately before the retained insertion anchor. For Clercx this
selects source blocks 0–2: title, author line and affiliation. Both native character evidence and the rendered crop
include the missing content, instead of cropping only around the affiliation. This selects evidence; it does not
deterministically invent or correct source text. The new title-evidence regression failed before this change and passed after it.

`tools/probe_compact_closeout.py` reuses the original stored screening candidates at blocks 2, 24 and 38, the same
saved original import, retained layout and PDF. It runs the current production normalization, evidence selection,
decision and publication code with only those three candidates. Screening is replayed from the saved response;
no new whole-document inference occurs. Images are requested explicitly for these local validation questions.

```powershell
python tools/probe_compact_closeout.py prepare
python tools/probe_compact_closeout.py run
```

Preparation stops before inference so the actual production crops can be inspected. The three images visibly
contain the complete title/author area on page 1, the questioned unbarred spectrum on page 2, and the complete
Figure 4 caption on page 4. The continuation resumes only these questions. One actual application bridge request
used `gpt-6.1-sol` / medium with three images (268,723 PNG bytes; 373,508 HTTP body bytes), no failed/retried
attempt, and no reported cached input. Returned usage: 5,963 input tokens, 965 output tokens including 70 reasoning
tokens. These are local-request receipts, not another throughput or end-to-end speed comparison.

All three decisions returned corrected, and exactly three patches were accepted and published:

- The complete printed title and `H. J. H. Clercx and G. J. F. van Heijst` were inserted before the affiliation.
- The page-2 question stayed on page 2 / block 24; its false bar was removed, retaining the printed exponent −3.
- One atomic replacement of the entire Figure 4 figcaption restores the two dashes on each side of plus, times
  and star, associates them with Re = 5000, 10000 and 20000, and places one pair of parentheses around the full
  three-entry legend. The leading prose, $2\delta(\tau)$, $\lambda_i(\tau)$, panel labels and image path are retained.

The actual published source was compared with the original crops and exact patch history, not just the model's
completion labels. There are no unresolved issues or publication rejections for these three cases. Every changed
byte is inside one of the three supplied question units; replaying the accepted edits exactly reproduces the
published source. The original correct lambda relation and time formula elsewhere remain byte-for-byte present.
Figure 4's previously correct leading prose and symbols are unchanged. Other existing extraction faults are outside
this replay's scope; this result does not assert that the whole paper is corrected.

Related regression command: `python -m unittest tests.test_pdf_text_evidence tests.test_targeted tests.test_correction -q`:
60 tests passed. The original 14.8% single-pair observation and its limitations above are unchanged. No two-paper
rerun, sample expansion, personal integration, daily-service restart, push or PR occurred.

All live evidence is retained under ignored `launch/sol-compact-correction/local-closeout-20261020/`:
`prepare-request-1-image-{1,2,3}.png`, the corresponding actual request images/prompts, `run-http.json`,
`result.json`, `audit.json`, `source.diff`, and the task-owned published source plus full decision history.
