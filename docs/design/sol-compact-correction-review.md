# Compact correction review

2026-10-20. Fixed point `c0fa57d`; initial implementation `eb659b6`. Spec authority is the latest Sol compact
handoff; older Flash settings and universal image-review descriptions are superseded. Review is read-only and
separate from the real-paper quality gate in [verification](sol-compact-correction-verification.md).

## Standards

No documented-standard violations or actionable baseline smells found. The changes follow the surrounding plain
Python style and are signed off. Reader rendering is untouched, so the GPU zoom requirement does not apply.
The development documentation now describes coherent text screening and compact combined source decisions.

## Spec

One P2 finding: successful source decisions remained only in memory until all later batches/follow-ups finished.
A later request failure could repeat completed image work on resume, contrary to the instruction to finish when
evidence resolves a question. `c20e344` checkpoints accepted text, finished candidates and outstanding image
questions after every successful decision. The actual failure/resume regression preserves the earlier repair and
does not repeat text screening. The independent spec reviewer confirmed resolution.

The initial review otherwise found the coherent text-only scan, combined local character/image evidence,
faulty-font fallback, removal of blanket review and candidate-level publication consistent with the handoff.
Subsequent real-paper checking found the localization and partial-caption failures documented in verification;
local follow-up `f41278d` was independently reviewed with no further substantiated issue. It has regression coverage but no new whole-paper acceptance measurement.

Standards: 0 findings. Spec: 1 finding, resolved. The historical paired-run quality failure is preserved;
do not merge personal.

## Three-case closeout

User-authorized local follow-up `122d871` adds the missing same-page prefix blocks to title evidence. The actual
production replay now supplies complete title/author, page-2 formula and full Figure 4 caption crops. One live
Sol/medium request returns three complete repairs, all published with no unresolved issue or rejected patch.
The published diff changes only those three question units and preserves the existing correct lambda/time
notation and caption lead. The Figure 4 repair is a single full-caption edit, including every legend entry and
the enclosing parentheses. See the live-closeout section and retained audit in verification.

This closes the three reported local failures. It does not replace the earlier full-paper result or establish a
new speed/generalization claim. The latest instruction explicitly keeps the result on this branch for review.
