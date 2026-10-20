# Xu paper figure grouping and stored-item repair

## Report and cause

The `xu2009` entry showed a full PDF page with a duplicate Figure 3 caption. Its original import had
failed to associate the captions beside Figures 4 and 6 with their two-panel figures. The resulting
unconfirmed page-6 fallback was subsequently labelled Figure 3 during extraction correction, although
the proper four-panel Figure 3 crop already existed. Figure 6 remained a page-8 fallback.

The `xu2010` entry had a different grouping failure: the vertically stacked panels of Figure 2 and the
shorter neighboring Figure 3 were connected across the column gutter. Their two caption owners caused
the importer to emit one unconfirmed page instead of two figures.

## Change

The shared conversion boundary now associates a complete caption to the right of panels on its rows
when no caption-below candidate exists. For a connected component reaching multiple captions, it first
partitions panels by aligned rows/columns. A partition with one caption owner can be reconstructed;
genuinely ambiguous ownership retains the existing unconfirmed-page fallback.

Two regressions reproduce the actual layouts and fail before the change. The existing ambiguity,
six-panel, caption-continuation, separate-figure and real-table regressions still pass.

## Bounded repair

Both stored items were backed up in full and repaired on isolated copies before publication:

- `pdf-cab09c60d336f652` (`xu2009`): replace the page-6/page-8 fallbacks with original-PDF crops of
  Figures 4 and 6, attach their existing corrected author captions, and realign their existing generated
  wording. Remove the duplicate Figure 3 caption and the two detached caption paragraphs. The resulting
  six figures have labels 1–6 exactly once.
- `pdf-d5db6d263ede3f8c` (`xu2010`): split the page-3 fallback into the three-panel Figure 2 and two-panel
  Figure 3. Their author captions were checked against the original PDF; only these two new caption
  reading ladders were authored from that source. The resulting seven figures have labels 1–7 exactly once.

The repair retains 63 unchanged source units plus the two realigned caption summaries in `xu2009`,
and all 35 existing units in `xu2010` plus its two new captions. It remaps positional unit, atom and
equation ids in stored reading levels and links. All 31/20 argument links remain, respectively.
The 21/8 original display equations retain their exact HTML. Original PDFs, extraction geometry,
Zotero records, model caches and healthy image files remain untouched. Neither item had saved notes.
Unreferenced old fallback image files remain available for recovery.

The existing source-correction draft is updated to the repaired source so a later continuation cannot
restore the obsolete figure structure. Repair provenance is recorded in each item's `correction.json`.
Backups, crop plans, reports, replay scripts and screenshots remain local under the ignored
`launch/xu-figure-repair/` directory.

## Validation

- All 14 figure-grouping tests pass, including the two previously failing regressions.
- The full Python suite runs 241 tests: OK, three skipped. Existing subprocess/socket cleanup warnings appear.
- An isolated service reads the repaired copies with models disabled. Browser checks find six/seven
  correctly numbered figures, all images loaded, no PDF-page fallback images and no JavaScript errors.
- Takeaway caption clicks expand to original text and collapse back normally for both entries.
- The four new crops were visually compared with their original PDF pages, including all panels,
  formula headings, axis labels and color scales. Both repaired Takeaway views were inspected.
- Reader JavaScript and CSS are unchanged by this repair.
