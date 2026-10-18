# Handoff: reference lists and readable visuals at summary levels

Status: design agreed in chat on 2026-10-18. This document authorizes the scope for a subsequent feature implementation; this discussion has changed documentation only.

## Outcome

Reference lists remain available as references, outside the article's generated summaries. Figures and tables remain large enough to read at Key and Takeaway, using the existing Brief presentation as the baseline.

Terminology is in [GLOSSARY.md](../../GLOSSARY.md). A reference list is distinct from a narrative Related Work section. A figure remains a figure even if an extractor labels its block as a table.

## Agreed behavior

### Reference lists

- Preserve the complete bibliography in the existing collapsible References presentation at Full.
- Exclude bibliography entries from narrative reading units, five-level summaries, section summaries, translations of those summaries, and generated argument links. Preserve inline citation markers and actual Related Work prose.
- Make reference separation part of the workflow **before generating takeaways or other model-written levels**. Use existing structured evidence, including MinerU `ref_text`, and the existing bibliography normalization. Model prompts must receive narrative units and sections with the reference list already separated.
- Cover headingless `ref_text` as well as references with a heading. Do not treat ordinary numbered/bulleted narrative lists as bibliographies.
- Fix the shared conversion boundary used by Zotero cache imports and native PDF conversion where practical. No new model classification pass is required for explicitly tagged reference entries.
- Merely hiding the redundant Prior Work items in CSS does not repair the generation input or already generated section content.

### Figures and tables

- At Key (2) and Takeaway (1), keep both figure bodies and table bodies visible at the **same presentation size as Brief (3)**. Brief currently centers figure bodies with an 82% maximum width of the reading column. Reuse that responsive behavior rather than introducing separate arbitrary widths.
- Preserve aspect ratios, image quality, narrow-window usability, and existing handling of wide tables. Small images need not be stretched beyond the existing Brief behavior.
- Keep true tables as tables. Keep existing figure-like-table recognition and the complete panel grouping introduced by the recent chart fixes.
- Keep caption wording on its existing semantic level: Key and Takeaway captions can remain shorter while their visual body stays readable. Full (4), Brief (3), Topic (0), image enlargement, and PDF comparison retain their current intended behavior.
- Check the effective local level when a paragraph/caption is opened in place, as well as whole-document level changes. Reuse the existing figure IDs, layout measurements and morph/keyframe machinery.

## Existing documents

The user requested repair of **all documents already imported into TextFold**, not just future imports or the current paper. This scope concerns TextFold's stored documents, not every attachment in Zotero.

1. Inventory the active TextFold data directory at execution time and identify affected documents from their stored structured content and parsed representation.
2. Back up each affected paper before modifying its source or generated layers. Preserve the selected original PDF, metadata, figures, tables, model cache and notes.
3. Separate mistaken reference-list units from narrative units and remove their generated Prior Work summaries from the narrative reading levels.
4. Regenerate only affected summaries and existing-language translations as necessary. In particular, a conclusion section summary may have consumed reference entries even after the individual items are removed. Audit generated argument-link endpoints and any generated content that consumed the affected units. Keep healthy prose summaries and translations.
5. The user explicitly permits model calls for this limited regeneration. Use the existing configured model/provider workflow. Avoid forcing full-paper regeneration or generating languages the document does not already have.
6. Preserve every existing non-bibliography passage's identity or correctly map its unit/atom references, generated token alignment, note anchors, and cited passages. Keep layer version/base relationships truthful. Validate existing annotations and retained generated content against the repaired source.
7. Give a per-document result: affected/repaired, unaffected, and any unresolved extraction ambiguity. Report what was regenerated. Do not silently drop unresolved content.

Use a bounded repair for the current stored corpus. The task does not call for a generalized migration system, new feature flags or checksums.

## Confirmed diagnosis and source pointers

At discussion time, `personal` is at `38dcc6e9d08ea8ac6b969123af27fcf326244ddd`, clean except for the discussion documentation. It is five local commits ahead of `origin/personal`. Verify actual state before starting; preserve those commits and unrelated work.

The daily source server is `http://localhost:3027`, with `TEXTFOLD_DATA=C:/Users/admin/AppData/Local/Temp/textfold-zotero-trial-final-20261018`. The current imported documents are:

- `pdf-46dbaefa0485d9b4`: Liberzon et al., *On turbulent entrainment and dissipation in dilute polymer solutions*; existing English and Chinese layers.
- `pdf-05589319112e54d0`: Jamin et al., *Experimental study of three-dimensional turbulence under a free surface*; existing English layers, figures and tables.

Recheck this inventory when implementing. Runtime PID receipts from earlier tasks are historical, not authority to stop a current process.

For the Liberzon paper, the Zotero cache `D:/Paper/Zotero lib/llm-for-zotero-mineru/17350/content_list.json` contains 34 explicit `ref_text` entries but no References heading. The adapter preserves their type. `pdfdoc.to_markdown` emits them as a Markdown list; `semantic` depends on a heading to create the bibliography section. The saved paper consequently has 72 units, including 34 bibliography items (`u38` through `u71`) assigned to its Summary and Conclusions section, and an empty `bib`. Stored English layers contain redundant Prior Work summaries for those entries.

The native PDF conversion route calls the same converter. The same headingless input would encounter the same boundary failure. A fresh native MinerU run on this paper has **not** been performed; do not claim its exact output is known.

Relevant modules:

- `textfold/zotero_cache.py`: cached structured blocks into TextFold's PDF document shape; preserve existing chart/panel fixes.
- `textfold/pdfdoc.py`: reference blocks, Markdown assembly and native PDF conversion.
- `textfold/semantic.py`: `_sections` and `_bibliography`.
- `textfold/parse.py`: recognized bibliography is stored outside narrative `units`.
- `textfold/pipeline.py`: parse precedes `ladder.build`, links, persisted English layers and translation. Existing layers can be reused, so source repair alone is insufficient for old generated output.
- `textfold/store.py`, `ladder.py`, `translate.py`, `links.py`, `notes.py`: persisted layers, generation and passage references.
- `textfold/web/reader.css`: current Brief image size, Key image grid (168px/96px), Takeaway thumbnail (64px), table hiding at Key/Takeaway and bibliography visibility.
- `textfold/web/reader.js`: caption effective level, figure rendering, measured figure boxes and morph/keyframe layout.

## Validation

- Regression input: headingless MinerU `ref_text`, with real narrative conclusion content. Check the parsed model input has a bibliography and no reference-entry narrative units, while retaining conclusion prose.
- Preserve existing headed bibliographies, genuine Related Work prose, ordinary narrative lists, inline citations and figures/tables appearing near the reference list.
- Exercise the shared PDF conversion and Zotero cache path without installing or running MinerU. Keep reference-list extraction tests tied to the actual boundary rather than only prompt wording.
- Verify repaired stored source and generated layers: redundant Prior Work items disappear, affected section summaries use corrected input, healthy prose and translations remain, note/citation targets still resolve.
- In a real browser, compare Brief, Key and Takeaway visual-body dimensions for both figures and tables at wide and narrow viewports, including PDF side-by-side mode. Confirm captions still shorten, images enlarge, Topic stays an overview and no visual body is lost.
- Include Liberzon Figure 3's complete two-panel image and a Jamin table. Confirm prior chart and narrow-window PDF fixes remain usable.
- Follow CONTRIBUTING: `python -m unittest discover tests`, signed-off commits, and before/after zoom smoothness measurement for reader changes. Use GPU, 2x pixels and actual Chrome frame traces. The documented dense sample is `2512.23916`; it was previously absent locally. Recheck availability and clearly report any justified sample/platform substitution or measurement limitation.
- Protect the live generation queues. Validate against an isolated data copy and port first; restart only the identified source service once no generation is active. Retain the original data and repair backups. Do not install MinerU or alter llm-for-zotero, Zotero's database or its caches.

## Git and delivery

- Create a feature branch from the actual current `personal` HEAD; suggested name: `codex/reference-lists-and-visuals`.
- Keep the current local PDF-button, chart import and panel-grouping commits. Leave `main` and `upstream` unchanged.
- Implement, validate and save clear signed-off commits; ordinary merge back into `personal` preserves feature history. Leave the local checkout and daily source service on `personal`.
- Keep literature, credentials, generated layers, data and local screenshots out of public commits. Existing `launch/` is ignored and can hold local evidence/repair scripts.
- This discussion requests no PR and grants no new push authorization. Report local commits and unpushed status explicitly.
- Return a working local page, concise per-document repair/regeneration results, validation evidence, backup locations, branch/commit status and actual limitations.
