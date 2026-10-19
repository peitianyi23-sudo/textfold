# MinerU extraction correction discussion

Status: implemented and verified on codex/extraction-correction from personal, 2026-10-19. User authorized merging back after validation. Daily library application uses only the two explicitly selected papers.

## User problem and evidence

The user reports infrequent but disruptive formula-recognition and paragraph-recognition errors while reading two papers shown in the screenshot:

- Weak inertial-wave turbulence theory, personal paper pdf-8d292a5354b434a1, Zotero parent HJNBGR3L.
- Energy transfer from large to small scales in turbulence by multiscale nonlinear strain and vorticity interactions, personal paper pdf-309ab6cbec778a16, Zotero parent A3ISBVMD.

The attached screenshot identifies the papers in the sidebar; it does not identify an erroneous passage. Current personal data is under C:/Users/admin/AppData/Local/TextFold/personal/papers. Both papers have English generated layers. The Weak inertial-wave paper was imported from finalized cached Markdown without content-list blocks, so repair cannot assume block coordinates exist for every document. Original PDFs are retained.

Current pipeline parses stored source first, then creates English levels/argument links and translations. An agent making summaries from corrupt extracted text does not by itself fix the Full/source view. Changes to paragraph/atom identity can also affect generated layers and annotations; inspect these dependencies before designing updates.

## Agreed direction

Treat source extraction correction separately from generated summaries. Use the original selected attachment PDF as the evidence for corrections; keep Zotero's producer cache intact. Detect suspicious formulas and structure, inspect the relevant PDF region/page, then apply an evidence-backed correction to the TextFold reading source before downstream summaries use it. Model fluency or a plausible physics identity alone is not evidence of what the author wrote.

This is a design direction, not a guarantee that detectors can identify every OCR mistake. Formula syntax validity does not prove semantic correctness. Paragraph line-break normalization differs from changing reading order or assigning equations to paragraphs.

## Accepted decisions

- Q1 accepted: correct TextFold's own imported reading source so Full and generated layers share corrected content; keep original selected PDF and Zotero producer cache unchanged.
- Q2 user steering: iterate checking and correction against the PDF until content agrees, rather than accept a single model edit. Verification must inspect the corrected result against the PDF, not merely its fluency or valid LaTeX. Unresolved ambiguity remains explicit; repeated model agreement is not proof, and no unconditional zero-error guarantee has been established.
- Q3 accepted: initial comparison covers the entire PDF page by page, rather than only detector-selected suspicious locations. Follow-up correction and verification can focus on identified regions plus context, including paragraph/page transitions.
- Q4 accepted: allow immediate reading of the extracted draft with an explicit checking state; perform full PDF comparison in the background. Generate summaries and other derived content only after correction/verification completes, so they consume a consistent corrected reading source.
- Q5 accepted: use the user's existing ChatGPT subscription channel for visual PDF-page comparison. The configured local bridge is the intended route; image-input capability and actual end-to-end page visibility must be verified before implementation relies on it. No additional account/service purchase or silent fallback is authorized.
- Q6 user correction: no mandatory human confirmation for unresolved regions. Continue autonomous checking/correction, preserve uncertainty rather than invent content, and let the user request agent help when encountered during reading. This supersedes the proposed manual-resolution gate. Distinguish completion of the checking process from a claim that every passage is verified consistent. Model/provider failure is not completion of checking.

Q6 implication, made explicit in the discussion: unresolved regions may remain in the reading copy with visible indicators; derived content should use the same corrected source and retain pertinent uncertainty. The earlier Q4 completion gate therefore means completion of the checking workflow, not waiting indefinitely for human resolution of every ambiguous symbol. Exact rollout scope still awaits agreement.

## Source/code findings

Read-only examination found Johnson source structured blocks already contain `turbuð Þlent`, `¼A turbulent flow`, and mixed formula fragments inside prose. The same damage persists into source.md, so at least these are upstream extraction-content issues, not just reader rendering. Galtier Markdown has broken math/text boundaries and suspicious accents; exact corrections still require viewing the PDF. Neither paper has been edited.

Existing layer IDs and sequential atom IDs are coupled to source segmentation; notes use unit/section/quoted-text anchors. Existing-paper correction needs affected-layer updates and annotation preservation. Simply replacing source text and leaving old layers attached can display inconsistent content. Full and summary consistency includes questions as well as translations and argument links.

## Current frontier

7. Q7 accepted: validate first on the two named existing papers, then enable background correction for future imports. Leave other existing papers unchanged until requested. No whole-library batch rewrite. Work starts from personal on codex/extraction-correction in an isolated checkout; merge to personal after passing verification.

The accepted uncertainty policy is not a reason for unlimited repeat requests: correction iterations must seek specific remaining PDF differences, and cease making changes when evidence no longer supports a better correction. Routine retry/cache/concurrency implementation choices belong to the implementer; no arbitrary confidence score or repeated agreement can certify correctness.

## Original first frontier (answered above)

1. Authority/scope: may TextFold correct its own imported reading copy, using the original PDF as authority, while preserving the original Zotero cache and PDF? Accepted.
2. Automation boundary: user requires iterative verification against PDF, superseding single-pass automatic correction as the starting proposal. Stopping and uncertainty behavior are recorded in Q3-Q6 above.

Implementation follows the accepted background workflow, current ChatGPT subscription, explicit uncertainty and note-preservation decisions above. Independent edit review must reject scientifically plausible changes that do not match the printed PDF; an actual initial trial incorrectly changed a printed velocity v to u, and a separate image-backed review rejected it. This is a regression example, not a claim of error-free model review.

No ADR yet: architecture and irreversible choices have not been settled. Glossary additions should capture agreed domain terms only, not speculative mechanics.

## Implementation validation

Both selected PDF copies completed full comparison (4 and 6 physical pages), followed by fresh English generation.
The reading copies contain 35 and 101 units, 12 and 13 display equations, and the second paper retains all 3 images.
Existing recognition artifacts in the Johnson kinetic-energy definition and prose were removed against PDF evidence;
the missing Galtier equation (10) was restored. A live ChatGPT question read its correct prefactor and the corrected
vorticity definition with paragraph citations. All saved English unit/atom references were checked against the current
source. The final workflow reported no unresolved regions for these two trials; this is not an error-free guarantee.

132 automated tests passed, including actual reachable correction failures, resume, note/layer remapping, source-image
preservation, independent rejection of an author-symbol rewrite, and long restored equations retaining the existing
scrollable equation rendering. The page was inspected in the dark theme, including the repaired formulas and paragraphs.
GPU frame traces at 2x pixels use the same 104-unit local paper with and without the status notice (the documented dense
paper 2512.23916 is unavailable locally); traces and original/corrected reading evidence remain under the ignored
launch/extraction-correction directory in the feature checkout. No reader animation logic changed.
