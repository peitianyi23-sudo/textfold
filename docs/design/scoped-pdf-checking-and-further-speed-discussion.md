# Scoped PDF checking and further speed improvements

Status: design agreed, 2026-10-19. User invoked grill-with-docs, changed the default to 30 pages, and accepted all
four frontier recommendations ("都按你的推荐吧"). Shared understanding is confirmed; the product frontier is empty.
The design session updated documentation only. Implementation, measurements and rollout are recorded in
[the verification report](scoped-pdf-checking-and-speed-verification.md).

## Existing authority

- [Delivered correction/equation design](pdf-check-speed-and-essential-equations-discussion.md).
- [Measured implementation and daily rollout](pdf-check-speed-and-essential-equations-verification.md).
- [Original correction boundary and selected validation papers](extraction-repair-discussion.md).

The existing full-page comparison and independent PDF-backed verification requirements apply within the selected
correction scope. The next design changes when and how much work starts, not what constitutes evidence for a correction.
The prior cache-opening incident remains separate and unresolved. Preserve original PDF, producer cache, notes,
translations, source identity and the current daily-service ownership. Do not revisit already agreed equation selection.

## Agreed in this discussion

- The automatic whole-document threshold is **30 physical PDF pages**, including front matter, bibliography and
  appendices, replacing the assistant's proposed 20. The number is an agreed initial default, not a measured optimum.
- At or below the threshold, newly imported PDFs automatically receive full checking.
- Above the threshold, open the extraction for immediate reading; do not automatically check the whole document.
  The reader explicitly chooses a chapter or page range. Whole-document checking requires an explicit action.
- Scrolling, changing pages or opening a chapter does not itself enqueue agent work.
- A selected chapter longer than the limit initially processes up to 30 pages beginning at the chosen reading
  position. Explicit whole-document checking proceeds in resumable batches of up to 30 pages. Do not silently
  claim whole-chapter completion when only part of that chapter has been checked.
- Complete and generate within the chosen scope rather than making a long document wait for whole-book checking.
  Preserve completed work. Unstarted scope selections can be replaced.
- Reduce redundant omission-restoration requests when the initial comparison already proposes the same correction.
  Merge adjacent/overlapping review crops while retaining independent decisions for every edit.
- Experiment with three concurrent requests against the current two; adopt only with measured quality/latency and
  provider-error evidence. Retain full comparison and independent verification; no promised speed multiplier.

## Domain term

**Correction scope** means the document content selected for PDF-backed extraction correction: the entire document,
a chapter, or a page range. Selecting a scope does not mean it has been checked. A processing batch is not itself
proof that a chapter or document is complete.

## Resolved frontier (all recommendations accepted)

1. **Threshold counting:** use the physical total with an inclusive boundary: 30 automatic; 31 explicit scope.
2. **Partial chapter / document summaries:** generate levels for checked content, label any aggregate as a
   selected-range summary; generate
   a whole-chapter/document summary only after its required content completes checking. Preserve visible uncertainties.
3. **Switching the requested scope:** stop scheduling new requests for the old scope, retain completed results and
   checkpoints, and
   prioritize the new explicit request; do not silently finish the old chapter or start a whole-book backlog.
4. **Dependencies outside the scope:** use available extracted context with an explicit unchecked provenance;
   do not recursively add
   PDF checking outside the selected scope. Mark dependencies that materially limit interpretation.

Requests already in flight can finish, but an unreviewed proposal is not completed PDF checking. Preserve useful
results without allowing an old scope's late response to overwrite a newer source or another scope's work.

## Implementation facts at design approval (read-only inspection)

- `textfold/correction.py:301-303,390-393,493-502` persists one contiguous page-prefix cursor and publishes the
  corrected source only after all physical pages. `textfold/pipeline.py:44-51` waits for that before generating.
  Scoped correction therefore needs real coverage/publication changes, not just a 30-page early return.
- `textfold/ladder.py:255-264` and `textfold/translate.py:157-164` already accept a set of chunk ids. Pipeline uses
  that for incomplete-layer recovery, not explicit user ranges. Parser chunks are heading-based sections and
  cannot automatically be equated with book chapters.
- Extractor page blocks are retained, but the dynamic reading-navigation match in `textfold/pdfdoc.py:574-600`
  does not establish complete page-to-section coverage, especially for multi-page paragraphs/equations or finalized
  Markdown without coordinates. Coverage must not be inferred from that navigation approximation alone.
- `textfold/server.py:175-180,204-213` has cooperative stop/resubmission and deduplicates active jobs by paper and
  language; it does not yet replace active scopes. Completed correction checkpoints/model replies survive a process
  restart, but the in-memory job queue does not automatically resume jobs.

## Implementation judgment and validation

Coverage tracking, source publication, scope-aware queue identity, chapter/page mapping, crop grouping and safe
reuse of already reviewed edits belong to implementation. Preserve healthy layers, notes, translations and stable
equation provenance when another scope changes the reading source. A paragraph spanning pages is not fully checked
merely because one navigation anchor points inside the checked range. Missing chapter structure must not be invented;
page ranges remain an explicit supported scope.

Test the 30/31 physical-page boundary, a 100-page import with no automatic vision work, a chapter spanning more than
30 pages, noncontiguous range selection, scope replacement during in-flight requests, stop/resume, partial summaries,
cross-scope dependencies and preservation of existing notes/layers. Use isolated fixtures and mocked providers for
large-document task-count checks; do not automatically run a 100-page live model benchmark to test the cutoff.
No real book has been selected for this rollout. Use the two named real papers and original-extraction copies in the
referenced verification artifacts for model quality/performance comparisons; report any long-document quality limit.
Measure the three speed improvements against the delivered implementation, including calls, durations and provider
errors. Validate actual reader behavior and the repository's GPU/2x zoom requirement when changing reader UI.

The final handoff references this document and is saved in the OS temporary directory. Preserve the private
personal -> isolated codex/ feature -> validated personal merge workflow; no push or upstream PR is requested.
