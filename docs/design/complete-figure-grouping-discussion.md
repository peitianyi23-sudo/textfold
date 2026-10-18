# Complete figure grouping before summary generation

Status: design discussion on 2026-10-18; fallback behavior accepted by the user.
This document records the discussion and does not authorize implementation.
The earlier reference-list and readable-visuals change has already been delivered; this is a separate change.

## Established scope

Figure reconstruction belongs in import conversion, before narrative/caption units reach summary generation.
TextFold should receive the extractor's blocks, assemble complete figures and captions, then parse the document and generate reading levels.
The reader displays and scales the resulting figures.
Vocabulary is defined in the root GLOSSARY.md: a figure, its panels, its caption and extracted blocks are distinct objects.

Use a separate feature branch from the actual current personal HEAD.
The proposed branch name is codex/complete-figure-grouping.
Validate on an isolated data copy and port before applying a backed-up repair to the daily corpus.

## Observed failure

The newly imported paper, A generative diffusion framework for physically consistent 3D turbulence, has Figures 1–9 in its PDF but 13 imported visual blocks.
Figure 1 has six panels on PDF page 2 and is split into three overlapping crops, with its caption between fragments.
The structured extraction retains page coordinates, but image and chart blocks are interleaved with two-column prose.
Panel labels and caption continuations also appear in caption fields.
The existing chart-specific same-row grouping and the shared converter's proximity/reading-order rules do not reconstruct this layout.
The local reproduction is launch/figure-layout-diagnosis/repro.py; it currently fails with 13 blocks instead of the nine known figures in this paper.
That count is an assertion for this inspected paper, not a universal rule that all documents must have numbered captions or no uncaptioned images.

## Recommended implementation scope

Unify figure grouping at the conversion boundary shared by Zotero cache imports and native conversion.
Use page geometry together with complete figure captions, panel labels and caption continuations to establish panel ownership.
Treat image, chart and figure-like table extraction consistently while preserving true tables.
Crop each complete figure once from the original PDF, retaining the panels' source arrangement and associated labels.
Separate and preserve the complete author caption before building its generated reading levels.
Geometry and grouping details are implementation choices to resolve against the real examples, not additional questions for the user.

Repair the newly affected import while preserving healthy source passages, summaries, translations, notes and citation targets.
Only regenerate caption-derived or aggregate content whose input actually changed.
Keep the previous two papers as regressions for the two-panel and table behaviors; healthy imports need no data rewrite.
Add a small regression set for this six-panel figure, the earlier two-panel figure, two distinct figures sharing a page, split caption continuations, and figure-like tables.
Check complete coverage, correct caption association and absence of duplicate panel ownership.
Retain the delivered Brief/Key/Takeaway sizes and Takeaway caption inset.
Apply repository tests and GPU/2x frame measurements if the reader changes.

## Accepted fallback behavior

When existing evidence does not establish a unique complete figure grouping, continue importing the narrative, retain the author caption and original PDF access, and show the relevant original PDF page as an explicitly unconfirmed figure fallback.
Avoid presenting a speculative panel combination as a confirmed figure or generating a new caption summary from uncertain figure/caption association.
The user selected continued narrative import with the original PDF page fallback, rather than pausing the import for manual figure resolution.
The selected fallback should use existing PDF rendering/access; a new manual region editor or new vision-model classification pass is outside this proposed scope.

## Program and model responsibilities

Figure grouping, caption-fragment association, PDF cropping and uncertain-group page fallback are program operations over existing extraction and PDF data.
The proposed reconstruction stage requires no Agent or model call.
Models generate reading levels after this stage has established the input structure; bounded repairs may regenerate only affected generated content.
Exporting already stored reading results is also a program operation and does not itself call a model.

## Discussion completion

The fallback decision is settled; implementation has not started or been authorized by this discussion record.
Obtain the user's confirmation that the shared scope is understood before implementation.
Create an ADR only if the eventual choice meets the repository skill's durability and trade-off criteria.

## Implementation authorization

The implementation request following this discussion explicitly authorized the established scope, superseding the
historical authorization statements above. The implementation lives at the shared conversion boundary in pdfdoc.py;
the cache adapter retains extracted order and delegates geometry grouping to that boundary.

Validation includes fresh POST /api/zotero/read imports into independent empty data directories before and after the
signed-off merge, plus bounded repair of the affected stored paper and live reader/PDF comparison. Local sample
receipts, screenshots, model outputs and backups remain outside public commits.
