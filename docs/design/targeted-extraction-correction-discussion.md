# Targeted extraction correction discussion

Status: design agreed, 2026-10-20. The user accepted the last frontier with "可以 尽可能提速这样".
The product frontier is empty. This session records decisions and prepares a handoff; implementation and rollout
have not started. Sample selection and the five/five discovery/evaluation plan are approved.

## User direction

The user questions the cost of page-by-page PDF comparison because it duplicates work already done by MinerU.
Explore reading the existing extraction quickly, using recurring observed failure patterns to identify candidates,
then locating the relevant original PDF regions and correcting against that evidence. The user suggests semantic
search for localization. Treat the prior papers as test material, not evidence of general detection completeness.

## Existing records

- [Original correction decisions and actual error examples](extraction-repair-discussion.md).
- [Measured correction and equation results, including rejected faster trial](pdf-check-speed-and-essential-equations-verification.md).
- [Previous scoped checking design](scoped-pdf-checking-and-further-speed-discussion.md).
- [Scoped implementation verification](scoped-pdf-checking-and-speed-verification.md).
- Referenced chats: `01a1521a-d9e8-7be1-93cd-16a753988c59` and `01a15352-9107-73a3-9591-e7fee3260240`, local host; read in this session.

The previous design explicitly required full-page comparison within each selected scope. The user now accepts
targeted correction as the default, retaining explicit whole-document checking. Existing source protection and
equation selection decisions are not implicitly revoked.

## Evidence relevant to the proposal

The existing reports document corrupt prose/math boundaries, malformed inline symbols, omitted numbered equations,
and fragmented paragraph structure. They also document a model proposing an incorrect v-to-u replacement and a
faster trial missing equation (10). A syntactically valid formula can still be wrong. These motivate candidate
discovery and local PDF-backed verification as separate responsibilities.

One selected paper arrived as finalized Markdown without block coordinates. Localization cannot universally
assume page/bounding-box metadata. Semantic relevance alone does not establish that a PDF region is the exact source.

## Resolved first frontier

1. Accepted: default targeted correction replaces automatic full-page comparison, with explicit full checking
   retained. The user requires a better, unobtrusive interface for that optional action. Do not label targeted
   completion as exhaustive PDF checking.
2. Clarified: "Only words I say is fine" was a voice-transcription error. The intended point is that text-only
   input should be much faster. Agents identify suspicious content automatically; the user need not point it out.
   Initial candidate discovery reads extraction text; PDF evidence is consulted locally for actual corrections.
3. Accepted: correct TextFold's imported reading copy; preserve the Zotero producer cache and original PDF.

## Authorized sample discovery

Agents selected ten short papers from the existing Zotero library across PRL, JFM, PRF, PoF,
and optionally other journals. Prefer existing MinerU caches and physical PDFs of at most about twelve pages;
this is a practical selection preference, not a new product limit. Proposed allocation: three PRL, three JFM,
two PRF, two PoF, adjusted to actual availability. Verify attachment identity and physical page counts.
Selection does not itself authorize conversion, library-wide rewriting, production correction jobs, or a claim
of measured error frequencies. The sample manifest is recorded separately. The user approved the discovery/evaluation
split and independent PDF reference review described below; that review has not yet run.

Selection is complete: [ten-paper manifest and preliminary text candidates](targeted-correction-sample-manifest.md).
It contains three PRL, two PRF, three JFM, two PoF, 84 pages total. One thirteen-page JFM publisher PDF is an
explicit length exception; the arXiv-layout attachment is retained as a backup rather than a publisher-layout sample.

## Second frontier

1. Accepted: wait for text screening plus identified local PDF checks before generating derived layers. Full
   remains readable immediately. Existing unresolved-content policy still applies; this does not create a human gate.
2. Accepted after mockup review: use the document-menu variant for explicit whole-document checking. The action
   stays in the document menu; progress appears only while running and disappears on completion. Do not add a
   permanent checking icon/panel. UI sketches remain discussion material; no production UI has changed.
   The conversation preview is at
   `C:/Users/admin/.codex/visualizations/2026/10/20/01a1574f-f358-7851-a785-25d7852140ce/textfold-checking-entry.html`.
3. Accepted test split: the five already skimmed papers (2951, 3354, 3506, 3145, 3836) are discovery material;
   the other five (2982, 2793, 2878, 3206, 148) remain reserved for evaluation. Independent PDF reference review
   of the evaluation set is approved to measure missed errors. Candidate-only review cannot establish recall.
   That reference work is confined to evaluation and does not reinstate per-page production checking.

## Resolved final frontier

Accepted: initial text screening also uses the selected PDF's existing text layer, alongside MinerU text, to flag
missing passages/equation labels where available. No new whole-document OCR or whole-page vision pass by default.
PDF text and MinerU output can both be wrong, so differences are candidates rather than correction authority.
PDF images remain the evidence for accepted edits. Scans lacking a text layer retain targeted discovery with an
explicit limitation, without silently starting full checking. User priority: accelerate as much as practical.

## Implementation judgment within the agreed direction

These are implementation choices, not additional product decisions requiring another interview:

- Reuse exact attachment identity, existing page/block coordinates, PDF text and nearby literal anchors before
  adding semantic localization where it actually helps. Semantic relevance retrieves candidates; it does not
  establish that a crop contains the exact printed symbol. Do not require a new embedding service or account.
- Group text analysis and nearby candidate crops to reduce model calls and payloads, retaining enough surrounding
  context for paragraph/column transitions and correct source attribution. Reuse successful intermediate work.
- Verify proposed source changes independently against the original PDF locally; do not rerun whole-page visual
  comparison just to claim completeness. Retain the regression where an incorrect v-to-u rewrite was rejected.
- Existing uncertainty policy applies when a region cannot be located or read reliably: preserve the source,
  retain the unresolved issue, and avoid unsupported edits. No mandatory human gate, unbounded retry, or silent
  escalation to full checking. Completion still allows explicit unresolved content and pertinent derived uncertainty.
- Preserve the existing explicit-scope requirement above thirty physical pages. The old automatic full-page
  comparison at or below thirty pages is replaced by targeted correction; choosing full checking remains explicit.
  Do not interpret this change as permission to start whole-book jobs on scroll/import.
- Full remains readable immediately. Generate derived layers after the current targeted workflow finishes,
  using its corrected source and relevant uncertainties. Preserve existing notes, translations, identities,
  equation selection and healthy reading-layer behavior when publishing changes.

## Required evidence for implementation delivery

Use the approved five/five split in the sample manifest. Derive initial failure patterns only from discovery
material before evaluating the held-out set. Independent PDF reference review is test work, not the default
production path. Record concrete missed errors, incorrect changes, confirmed fixes and unresolved candidates;
an intact passage must be reported as correct rather than made into a finding. No arbitrary quality score.

Measure wall time, request counts, text/image payloads and provider failures against the existing workflow on
isolated copies of the same original extraction and selected PDFs. Distinguish local preparation from model wait;
report the quality/time trade-off without promising a multiplier. Current examples alone establish neither
frequency nor recall. Any change to the agreed patterns after inspecting held-out failures must be disclosed.

Validate the actual document-menu action, running/stopped/completed states, scope behavior, immediate Full access,
and downstream generation order. Follow repository requirements for reader GPU/2x evidence when changing UI.
Do not use production correction jobs to test orchestration. Preserve the original PDFs and producer caches.

Targeted correction is now a settled domain term, captured in the root glossary. No ADR is warranted yet.
