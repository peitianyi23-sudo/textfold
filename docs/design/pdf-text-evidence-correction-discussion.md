# Correction using local PDF text evidence

Status: evidence and validation decisions accepted, 2026-10-20. TextFold's DeepSeek provider changes are implemented locally and active. The PDF-text evidence prototype failed speed/quality acceptance in its separate worktree. The user has now selected low effort and requested a quick worker comparison. The earlier native Codex worker probe failed before inference; application API calls succeed. See the latest decision below.

## Existing authority and evidence

- [Agreed document-batched design](document-batched-correction-discussion.md).
- [Delivered batched implementation and incomplete final validation](document-batched-correction-verification.md).
- [Two actual LLM for Zotero cloud reparses](../../launch/mineru-cloud-reparse-20261020/comparison.md).

The new proposal retains direct agent repairs based on unambiguous document context, immediate readable Full,
generation after the current correction workflow, exact source identity, producer-cache protection, existing
scope/menu behavior and author-notation preservation. Do not reopen those decisions.

Prior requests fell from 142 to 34 in an intermediate trial, but images rose from 171 to 186 and wire payload
remained about 52 MB. That trial later failed quality; final aggregate speed/quality was not completed. It shows
why batching alone is insufficient, not a valid final-release speedup. The current candidate-context construction
includes everything between the earliest and latest candidate and repeats all batch images for review.

## New local, read-only observations

The two exact PDFs already selected were inspected with PDFium and PyMuPDF, without model calls:

- Boffetta 2007, attachment 3506, physical page 1: native text includes `E(k)` and `epsilon 2/3 k -5/3`.
  PyMuPDF identifies the main epsilon/E/k baseline at y=450.6 and 10.5 pt; the 2, slash, 3 and -5/3 glyphs sit
  at y=446.8 and 7.0 pt. These original-source characters and positions establish the exponent and plain E,
  unlike MinerU's `epsilon^{273}` and false dot/bar. Actual PDF images inspected earlier confirm the reading.
- Clercx 2000, attachment 2951, physical page 1: both libraries extract the suspect passage as `k25` followed by
  U+0001 and `3`, not reliable mathematical text. The superscript 2 is in MathematicalPi-One-A; the control
  character is in MathematicalPi-Three. Font size/position establishes superscript structure but does not by
  itself establish the intended character identities. Do not silently equate these codes with minus/slash.

Thus original PDF evidence need not always be an image; PDF text can also be corrupt. Do not build a universal
font-decoding framework for this experiment. Existing extraction APIs can provide a useful small source snippet
with only the local glyph/position information required to resolve a candidate.

## Proposed implementation judgment

Within the existing authorized scope, one coherent text pass directly repairs clear document-context errors and
collects the remaining source questions. Resolve source questions locally in a batch, using cached MinerU block/page
geometry and PDF character/line information. Return candidate-specific nearby lines with limited mathematical
position annotations, rather than the full PDF rawdict, all block text, or the continuous span across distant
candidates. Agent decisions use this compact evidence together. Only unresolved character/source ambiguities
receive readable local images. Avoid per-candidate tool/model round trips.

Return minimal exact source edits and short reasons, rather than complete rewritten paragraphs or long explanations.
Where a necessary paragraph move spans multiple places, maintain atomic content preservation with existing checks;
minimality must not reintroduce the lost-caption or half-applied delimiter failures. The proposed improvement is
to reduce actual input/output and evidence work, not only request count. No arbitrary confidence score or hard
one/two-call cap. Source text with demonstrably faulty mappings is not confirmation by itself.

## Accepted decisions

1. Evidence boundary: readable original PDF characters plus sufficient placement may establish a numeric/formula
   repair without image input or an extra independent model review when that source evidence
   unambiguously establishes the edit; retain the initial direct-context permission, and local image evidence/review
   for unresolved symbols. Restoring omitted formulas requires sufficiently complete source evidence, not physics
   inference. This changes the image-only implementation interpretation of the earlier PDF-evidence requirement.
2. Validation scope: first implement and compare only these two papers (Boffetta for text-evidence repair, Clercx
   for faulty-encoding fallback), plus meaningful existing regression checks. Inspect the
   changed passages for mis-edits/content loss and record wall time, calls, evidence payload and output size.
   If the small comparison does not improve, diagnose it before expanding; do not launch another ten-paper full
   run as routine validation. Two known papers are prototype/regression evidence, not generalization proof.

## Proposed fast worker for remaining image evidence

The user proposed DeepSeek-V4.1-Flash-1017 for heavy image work and explicitly requested updating the local
`v4_flash_worker` configuration. Official model discovery confirms that `deepseek-flash` accepts text/images
and supports low/high/max effort; the October 17 release is the current Flash release. This is a moving API
alias, not a pinned model snapshot. The local agent file now selects that alias with `model_reasoning_effort = "low"`.
This was the initial low-effort proposal, superseded by the application-provider decision and xhigh choice below.

Proposed role: send only remaining ambiguous source crops, a small relevant text context, and exact questions.
Return a short literal transcription, minimal proposed edits, and explicit unresolved readings. Parent owns
integration and checks that edits match supplied evidence; do not automatically resend all images for a second
model review. Keep full-paper text triage and local PDF-text evidence ahead of image dispatch.

This Codex worker setting does not configure TextFold's application runtime provider. First prove native worker
image delivery and correctness on the two-paper prototype before deciding application routing. This session's
role metadata refreshed to `deepseek-flash` / `low` after the configuration edit. A single read-only probe was
staged through the required plaintext Hook and spawned as `/root/flash_image_probe`. It failed before image
inspection with HTTP 400: `The 'deepseek-flash' model is not supported when using Codex with a ChatGPT account.`
Thus model/effort selection is recognized but the external-provider execution route is blocked. No direct API
inference fallback was attempted. No image inference, quality result, or measured speedup is claimed here.

Compare actual end-to-end latency, model/evidence calls, payload, generated output and correctness. Higher TPS
alone does not establish lower total latency: image prefill, queueing, reasoning and delegation overhead matter.

Sources: [release](https://api-docs.deepseek.com/news/news261017/),
[model metadata](https://api-docs.deepseek.com/api/list-models/),
[effort mapping](https://api-docs.deepseek.com/guides/thinking_mode/).

## Application provider decision and small live probe

The user chose TextFold's own DeepSeek API provider, with Flash as the application model rather than a Codex
subagent. This includes text screening and image evidence, and the application's default model also serves
reading-layer generation and questions without an explicit question model. Original producer caches are untouched.

The existing application provider was already present. Its default Flash model ID is now `deepseek-flash`.
The adapter now sends explicit thinking plus reasoning effort for DeepSeek text requests and image requests;
the initial adapter default was low, subsequently raised to xhigh below, while an explicit off remains off. Previously image requests omitted effort entirely,
and text requests could accept a toggle alone and leave DeepSeek's default high effort active.

A real call through `textfold.llm_openai.vision` with `deepseek-flash`, low effort, and the existing Boffetta page-1
PNG (322973 bytes) took 2.84 seconds and returned `E(k) \\simeq \\varepsilon^{2/3} k^{-5/3}` plus the matching
adjacent phrase. This matches the previously inspected original, including the unaccented E. This is one image
call, not a full-paper speed/quality evaluation. Nineteen focused correction/provider recovery tests pass.

An initial scoped restart of the idle Personal server was rejected by automatic approval policy before execution
(`blocked by policy`, no detailed reason). After the user requested continuation, the scoped restart succeeded.
The running Personal service now loads the updated modules, and its saved default was selected through
`/api/models/select` as `deepseek-flash`. Resolution confirms the DeepSeek API provider at
`https://api.deepseek.com/v1`. A real `/api/settings/test` against the running service returned
`{"ok": true, "model": "deepseek-flash", "seconds": 0.6}`. The application switch is effective; the two-paper
end-to-end comparison remains pending. These edits are local and have not been committed or pushed.

Subsequent user decision: raise Flash effort from low to xhigh for quality. The resolved Flash model spec now
sets xhigh, retained by reading-layer and question task defaults as well as correction. The DeepSeek adapter
maps xhigh to its documented native high level for text and image requests. Nineteen focused tests pass after
this change. The earlier 2.84-second image and 0.6-second connection observations used low, not this new effort.

Latest decision after reviewing the worker's actual reasoning-token receipts: switch Flash back to low and
resume the same implementation chat (`01a15893-a341-7632-9a77-fae015d78234`) for a small fixed-input comparison.
Personal's resolved model/default adapter effort is now low, 19 focused tests pass, and its idle service was
restarted. The worker was explicitly asked to synchronize low in its separate branch and first test the costly
character-evidence stage against existing high receipts, recording reasoning/cache usage and actual quality.
Only promising results justify the remaining two-paper acceptance run; integration remains conditional.

## Superseding compact Sol decision, 2026-10-20

Latest authority: `C:/Users/admin/AppData/Local/Temp/textfold-sol-compact-correction-handoff-2026-10-20.md`.
Use the existing local ChatGPT bridge with `gpt-6.1-sol` / medium for text and images. Earlier Flash/effort
observations remain historical evidence. One text-only coherent MinerU scan precedes candidate-local source
decisions. Combine readable original characters/placement and necessary ambiguous-region images in the same
decision; remove the mandatory broad character pass and blanket independent image rereview. Only an unresolved
reading warrants a further local image question. Direct context repairs retain their existing evidence boundary.
Preserve complete patches, printed unusual values and notation. Fix real discovery/localization failures without
hardcoding sample answers. Validate fixed real failures before a single serial same-model two-paper comparison.
Integrate locally into personal only if both speed and actual source fidelity pass; otherwise retain the isolated
branch and evidence for review. No upstream push or PR.
