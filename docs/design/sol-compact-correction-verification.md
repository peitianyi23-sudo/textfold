# Compact source correction: Sol / medium

2026-10-20. **Not accepted for personal integration.** The completed same-model pair is faster and materially
smaller, but Clercx still has an incorrectly localized question, an incomplete caption repair, and withheld
front matter. Keep `codex/sol-compact-correction` and its worktree for review. No push or PR.

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
adapters. Final branch also contains **local-only** follow-up `f41278d`, described below; its full-paper behavior
has not been measured. Do not attribute the measured result to that later fix.

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

## Actual source quality

All twelve original PDF pages were rendered and inspected locally. Accepted patches were checked against those
pages and the focused original crops. Replaying each run's complete accepted history from a fresh identical import
reproduces its published source exactly. Original-PDF and retained-layout copies match across runs byte-for-byte.
No caption-label loss, new dangling footnote or odd math-delimiter parity was found; those structural checks do not
certify transcription correctness.

Boffetta compact fixes both false E bars, the 273 exponent, full contour list, missing convolution star, caption
resolution/subscript faults and the printed negative skewness. It retains printed 16386, computing, dumping,
3.2 and (e,r). One nonunique coefficient spelling proposal remains withheld. Clercx compact correctly restores
the known exponent, omega-zero, nu, tau, lambda and grant separators without changing the correct lambda to l.
No new mathematical mis-edit was identified in these inspected accepted patches. Nevertheless, quality fails:

- Clercx's page-2 barred-k question was moved to page 4. A phrase occurring twice on page 2 was discarded by the
  per-page unique-anchor helper, making its single page-4 occurrence appear globally unique. The model correctly
  reported insufficient evidence; the false bar remains. The old paired output repairs it.
- The Clercx title/author restoration was withheld: the supplied region showed the affiliation/author area but
  not the title. The old output restores both. This source-region selection limitation remains.
- Figure 4's question covered only one inline math span. Its middle legend entry was repaired, but the initial
  parenthesis/plus-marker segment remained damaged while the narrow candidate was declared corrected. The old
  output repairs the complete legend. Full surrounding context alone did not ensure a complete investigation unit.

## Local-only follow-up and review

Both observed anchor/caption problems first failed small regression tests. `f41278d` counts **all** anchor hits
across pages and expands a caption-contained question to its complete figcaption before investigation. Replaying
the actual saved localization question locally now selects page 2 / block 24, rather than page 4. This verifies
localization, not a fresh model answer. The caption test verifies complete question packaging, not model fidelity.
No further whole-paper run was made; these fixes do not retroactively pass acceptance.

Final local suite: `python -m unittest discover -s tests -q`: 237 tests, 234 passed, three existing platform skips.
Existing subprocess/socket ResourceWarnings remain non-failing. [Two-axis review](sol-compact-correction-review.md)
found no standards violation and one resume defect, fixed and checked separately. Real-run quality findings above
take precedence over unit tests and review approval. No ten-paper expansion, personal merge, push or PR occurred.

Raw receipts, per-paper decisions, source renders, imported inputs and source diffs are retained in this worktree's
ignored `launch/sol-compact-correction/`. `summary.json` records aggregate/stage/usage data; `sol-baseline/http.json`
and `sol-new/http.json` contain request measurements and responses, without authorization headers or keys.
`localization-followup.json` preserves the actual local correction of the page error. Keep this worktree to retain
these ignored artifacts. The reviewable Git diff is `git diff c0fa57d...codex/sol-compact-correction`.
