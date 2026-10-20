# Document-batched targeted correction discussion

Status: design agreed, 2026-10-20. The user accepted the remaining boundary and explicitly expanded agent
discretion to unambiguous mathematical-symbol repairs. Product frontier is empty. Documentation and handoff only;
no implementation or new worker chat started in this discussion.

## User direction

The user wants a substantial reduction in model request count beyond the delivered targeted implementation.
Read the MinerU extraction quickly as text, identify actual garbling/math/paragraph failures, and avoid PDF vision
entirely for clean documents. Where PDF evidence is needed, investigate the document's candidates together rather
than repeat proposal/review per candidate page. "One or two PDF consultations" needs distinguishing request rounds
from image/crop count; multiple attributed crops may travel in one request.

## Evidence and current delivery

- [Delivered implementation and paired measurements](targeted-correction-verification.md).
- [Previous agreed design](targeted-extraction-correction-discussion.md).
- [Corpus and approved split](targeted-correction-sample-manifest.md).
- Current code: `textfold/targeted.py`; benchmark preparation and receipts under
  `C:/Users/admin/.codex/worktrees/targeted-correction/textfold/launch/targeted/`.

Delivered: automatic text discovery; local PDF crops; independent edit review; resumable work; document-menu full
checking; delayed derived generation with immediately readable Full. Ten-paper correction time fell from 2042.63
to 1106.33 seconds. Requests fell only from 168 to 141. The current final run contains 18 text-screening calls,
61 local image proposal calls and 60 independent image reviews, plus two HTTP retries. Response/model wait is
1076.51 seconds; local work is 19.82 seconds; retry backoff is 10 seconds. These are correction times, not
end-to-end import plus all reading-layer generation times.

The five-paper reference inventory has 38 errors: 34 fixed, three detected but unresolved, one missed table exponent.
No whole-document recall claim follows. The test corpus is now known and cannot be called fresh held-out material
in a subsequent optimization. Reuse it for paired regression; any new generalization claim needs uninspected data.

The implemented targeted path ignores existing MinerU block/bbox data. It requires unique literal PDF-text anchors
and derives crop geometry from PDFium text rectangles. Benchmark inputs omit layout/structured cache files.
Thus existing measurements do not test full reuse of available MinerU geometry. Using geometry should help
localization failures and remove redundant anchor work, but local work is too small to explain most latency;
reducing model round trips is the primary opportunity.

## Agreed flow

Within the already authorized document/range, screen the extraction coherently in one text request when practical,
including existing PDF text only where useful rather than duplicating all inputs mechanically. Split only for
actual input/output capacity or observed quality limits, not a fixed six-page unit. Use available extractor
block/page identity and geometry to prepare source-attributed crops; text/semantic localization remains fallback.
An apparently clean document uses no PDF image request. Completion still means targeted screening, not exhaustive
PDF verification. Text-only screening cannot establish that every plausible formula or absent passage is correct.

For remaining PDF-dependent candidates, batch across pages for image-backed proposals and independent review
when image/context capacity permits. Do not require exactly two image requests. Keep every crop associated with attachment,
physical page and candidate identity; individual edits retain separate decisions. Do not create one tiny unreadable
montage or enforce a hard two-request cap that discards needed evidence. Additional calls must address a concrete
remaining issue or actual capacity boundary, not mechanically repeat the whole investigation.

## Resolved decisions

1. Accepted: ordinary short papers are screened coherently in one text request when practical, with no fixed
   six-page splitting. No suspicious candidates means no PDF image request. Preserve explicit long-document scope
   and honest coverage labels.
2. Accepted direction: minimize model calls through batching. The user's "one or two" is an expectation, not a
   hard cap or mandatory two-call recipe. Independent PDF review remains available for image-backed edits; avoid
   mechanically adding image work to text-only repairs. Batch when evidence remains readable and attributable.
3. User steering: delegate more obvious extraction repairs directly to the agent, including spurious heading-like
   residue and citation faults. The earlier display-only proposal is too restrictive and is not accepted.
   The evidence boundary below is now accepted, with the user's mathematical-symbol exception.

Accepted boundary: a text-only repair is allowed when local document evidence identifies
both the extraction fault and an unambiguous repair, without inventing author content. Examples include joining
an obviously split citation with an existing unique reference target, repairing a malformed link whose destination
already exists, and deleting a demonstrably duplicated extraction fragment. A stray-looking '# A' alone does not
prove corruption: it can be a real appendix/heading, and a citation number cannot be guessed from topic similarity.
Keep unresolved ambiguity for local PDF evidence. The user explicitly permits some mathematical-symbol corrections
using the agent's document-level judgment: direct repair is allowed when the extraction fault and intended symbol
are unambiguous from the document's definitions, repeated expressions or notation context. Do not reduce this
permission to display-only cleanup or force a PDF call for every mathematical token. Mathematical plausibility or
preferred notation alone is insufficient; preserve possible printed author inconsistencies and inspect PDF locally
when uncertain. Changes to numerical values and restoration of missing formulas require original PDF evidence.
This supersedes the prior blanket rule that every symbol edit needs PDF-backed independent review.

Use the initial document-text pass to propose/apply supported text-only repairs and identify remaining PDF candidates;
do not add a separate model call for every straightforward text repair. Keep exact before/after changes and a brief
reason in the existing correction record. Evaluate text-only mis-edits as well as PDF-backed ones. Completing such
repairs does not mean that their passages were visually compared with the PDF.

## What still needs evidence

Many papers requiring zero or only two image calls is a target to test, not a measured property of this corpus.
The current papers contain actual damaged extractions on many pages. Batch size and latency must be measured;
one enormous model response may be slow or omit candidates. Report request-stage counts, fixed per-request waiting,
payloads, correction time, missed errors, incorrect edits and unresolved issues with identical baseline inputs.
Evaluate the newly authorized direct symbol edits against PDF reference evidence in testing, without inserting
that evaluation review into the default production workflow. Include correct author-notation counterexamples
(including printed v/u and inconsistent beta/alpha cases), actual numerical errors and omitted formulas. Keep the
old 38-location corpus as regression evidence, not a fresh holdout; disclose any tuning and any added independent
sample's provenance. Report incorrect direct repairs separately from failed PDF localization. No speed multiplier promised.

The old cache-opening incident is separate. A current read-only inspection found cache 17262 with matching source
identity and an existing TextFold reading copy with eleven pages marked complete. Reopening was not tested.
Do not copy the stale "missing directory" statement or call the entire open path fixed without reproducing it.

No new glossary term is settled yet; existing Targeted correction remains accurate. No ADR warranted yet.
