"""Document-context repairs and cross-page evidence preserve source and publication boundaries."""
import threading
import io
import unittest
from unittest.mock import patch

from tests import test_correction as fixtures
from textfold import correction, targeted, llm, llm_openai, pipeline

PID, SPEC = fixtures.PID, fixtures.SPEC


class TargetedTests(unittest.TestCase):
    setUp = fixtures.CorrectionTests.setUp
    tearDown = fixtures.CorrectionTests.tearDown
    def screen(self):
        return {"out": {"candidates": [{"before": "Broken turbuð Þlent flow.",
                "anchor": "The original turbulent flow", "page": 1, "reason": "broken prose"}],
                "issues": []}}, False

    def source_result(self, edits=(), verdict='correct', candidates=(0,)):
        return {'edits': [dict(e, candidate=e.get('candidate', 0), page=e.get('page', 1)) for e in edits],
                'issues': [], 'displays': [], 'decisions': [
                    {'candidate': cid, 'verdict': verdict if cid == 0 else 'correct', 'reason': 'literal original'}
                    for cid in candidates]}

    def test_default_is_text_first_and_not_exhaustive_coverage(self):
        correction.queue(PID)
        edit = {'before': 'Broken turbuð Þlent flow.', 'after': 'The turbulent flow.', 'reason': 'printed'}
        with patch.object(llm, 'call', return_value=self.screen()) as screen, \
             patch.object(targeted, 'crops', side_effect=lambda pdf, page, anchors: ([b'local-image'], anchors)), \
             patch.object(llm_openai, 'vision', return_value=self.source_result([edit], 'corrected')) as vision:
            correction.run(PID, SPEC)
        self.assertEqual(screen.call_count, 1)
        self.assertEqual(vision.call_count, 1)
        self.assertEqual(correction.state(PID)['checked'], [])
        self.assertEqual(correction.state(PID)['status'], 'done')
        self.assertIn('The turbulent flow.', (self.d/'source.md').read_text(encoding='utf-8'))

    def test_source_correct_verdict_keeps_author_source(self):
        correction.queue(PID)
        with patch.object(llm, 'call', return_value=self.screen()), \
             patch.object(targeted, 'crops', side_effect=lambda pdf, page, anchors: ([b'crop'], anchors)), \
             patch.object(llm_openai, 'vision', return_value=self.source_result()):
            correction.run(PID, SPEC)
        self.assertEqual((self.d/'source.md').read_text(encoding='utf-8'), self.md)

    def test_unlocated_candidate_never_triggers_full_image_or_edit(self):
        correction.queue(PID)
        with patch.object(llm, "call", return_value=self.screen()), \
             patch.object(targeted, "crops", return_value=([], [])), patch.object(llm_openai, "vision") as vision:
            correction.run(PID, SPEC)
        vision.assert_not_called()
        self.assertTrue(correction.state(PID)["issues"])
        self.assertEqual((self.d/"source.md").read_text(encoding="utf-8"), self.md)

    def test_stop_resumes_saved_discovery_and_provider_error_blocks_generation(self):
        correction.queue(PID)
        stop = threading.Event()
        def fail(*args, **kwargs):
            stop.set()
            raise llm.Stopped()
        with patch.object(llm, "call", return_value=self.screen()), \
             patch.object(targeted, "crops", side_effect=lambda pdf, page, anchors: ([b"crop"], anchors)), \
             patch.object(llm_openai, "vision", side_effect=fail), patch.object(pipeline.ladder, "build") as build:
            with self.assertRaises(llm.Stopped):
                pipeline.generate(PID, "en", SPEC, stop=stop)
            build.assert_not_called()
        stop.clear()
        with patch.object(llm, "call") as screen, patch.object(targeted, "crops", side_effect=lambda pdf, page, anchors: ([b"crop"], anchors)), \
             patch.object(llm_openai, "vision", return_value=self.source_result()):
            correction.run(PID, SPEC, stop=stop)
        screen.assert_not_called()
        self.assertEqual(correction.state(PID)["status"], "done")


    def test_explicit_full_check_does_not_reuse_targeted_coverage(self):
        correction.queue(PID)
        with patch.object(llm, "call", return_value=({"out": {"candidates": [], "issues": []}}, False)):
            correction.run(PID, SPEC)
        with patch.object(llm_openai, "vision", return_value=self.source_result()) as vision:
            correction.run(PID, SPEC, scope=correction.choose(PID, {"kind": "document"}))
        self.assertEqual(vision.call_count, 2)
        self.assertEqual(correction.state(PID)["checked"], [1, 2])
        self.assertEqual(correction.state(PID)["method"], "full")


    def test_pdf_geometry_crop_uses_literal_anchor(self):
        self.assertEqual(targeted.locate("One two\nthree four five", "two three four five"), (4, 23))
        self.assertIsNone(targeted.locate("one two three four one two three four", "one two three four"))
        from reportlab.pdfgen import canvas
        import pypdfium2 as pdfium
        path = self.d/"anchor.pdf"
        canvas_ = canvas.Canvas(str(path))
        canvas_.drawString(72, 700, "The original turbulent flow is printed here with its complete physical source line and label.")
        canvas_.drawString(500, 670, "(1)")
        canvas_.save()
        with pdfium.PdfDocument(str(path)) as pdf:
            images, anchors = targeted.crops(pdf, 1, ["The original turbulent flow", "turbulent flow is printed"])
        self.assertEqual(len(images), 1)
        self.assertEqual(len(anchors), 2)
        self.assertTrue(images[0].startswith(b"\x89PNG"))
        from PIL import Image
        with Image.open(io.BytesIO(images[0])) as image:
            self.assertGreater(image.width, 900)  # short anchors cannot clip the source line/label

    def test_source_failure_resumes_discovery_and_blocks_generation(self):
        correction.queue(PID)
        edit = {'before': 'Broken turbuð Þlent flow.', 'after': 'A turbulent flow.', 'reason': 'printed'}
        with patch.object(llm, 'call', return_value=self.screen()), \
             patch.object(targeted, 'crops', side_effect=lambda pdf, page, anchors: ([b'crop'], anchors)), \
             patch.object(llm_openai, 'vision', side_effect=RuntimeError('provider')), \
             patch.object(pipeline.ladder, 'build') as generated:
            with self.assertRaisesRegex(RuntimeError, 'provider'):
                pipeline.generate(PID, 'en', SPEC)
            generated.assert_not_called()
        self.assertEqual((self.d/'source.md').read_text(encoding='utf-8'), self.md)
        with patch.object(llm, 'call') as screen, \
             patch.object(targeted, 'crops', side_effect=lambda pdf, page, anchors: ([b'crop'], anchors)), \
             patch.object(llm_openai, 'vision', return_value=self.source_result([edit], 'corrected')) as vision:
            correction.run(PID, SPEC)
        screen.assert_not_called()
        self.assertEqual(vision.call_count, 1)
        self.assertEqual(correction.state(PID)['status'], 'done')

    def test_candidates_on_same_page_share_requests_and_identical_image(self):
        correction.queue(PID)
        response = self.screen()
        response[0]["out"]["candidates"].append({"before": "A healthy paragraph with $x+y$.",
                "anchor": "A healthy paragraph with", "page": 1, "reason": "possible boundary"})
        with patch.object(llm, "call", return_value=response), patch.object(targeted, "crops", side_effect=lambda pdf, page, anchors: ([b"same-crop"], anchors)), \
             patch.object(llm_openai, "vision", return_value=self.source_result(candidates=(0, 1))) as vision:
            correction.run(PID, SPEC)
        self.assertEqual(vision.call_count, 1)
        self.assertEqual(vision.call_args.args[3], [b"same-crop"])
        self.assertEqual(correction.state(PID)["done"], 2)


    def test_overlapping_source_edits_withhold_incomplete_candidate(self):
        correction.queue(PID)
        edits = [{'before': 'Broken turbuð Þlent flow.', 'after': 'A turbulent flow.', 'reason': 'printed'},
                 {'before': 'turbuð Þlent', 'after': 'turbulent', 'reason': 'overlaps'}]
        with patch.object(llm, 'call', return_value=self.screen()), \
             patch.object(targeted, 'crops', side_effect=lambda pdf, page, anchors: ([b'crop'], anchors)), \
             patch.object(llm_openai, 'vision', return_value=self.source_result(edits, 'corrected')):
            correction.run(PID, SPEC)
        self.assertEqual((self.d/'source.md').read_text(encoding='utf-8'), self.md)
        self.assertTrue(correction.state(PID)['issues'])

    def test_rejected_restoration_keeps_missing_label_explicit(self):
        correction.queue(PID)
        result = self.source_result(verdict='unresolved')
        result['decisions'][0]['reason'] = 'Printed display label 1 remains unreadable'
        with patch.object(llm, 'call', return_value=self.screen()), \
             patch.object(targeted, 'crops', side_effect=lambda pdf, page, anchors: ([b'crop'], anchors)), \
             patch.object(llm_openai, 'vision', return_value=result):
            correction.run(PID, SPEC)
        self.assertEqual((self.d/'source.md').read_text(encoding='utf-8'), self.md)
        self.assertTrue(any('label 1' in x['text'] for x in correction.state(PID)['issues']))

    def test_source_publication_cannot_leave_a_dangling_footnote(self):
        work = {'text': self.md, 'issues': []}
        edits = [{'before': 'Broken turbuð Þlent flow.', 'after': 'Corrected flow[^1].', 'reason': 'printed marker'},
                 {'before': '# Method', 'after': '# Method result', 'reason': 'heading'}]
        blocked = targeted.apply_edits(work, edits, self.d, 1)
        self.assertEqual(blocked, [edits[0]])
        self.assertNotIn('[^1]', work['text'])
        self.assertIn('# Method result', work['text'])

    def test_screen_observations_are_not_asserted_as_unresolved_pdf_findings(self):
        correction.queue(PID)
        response = self.screen()
        observation = 'Candidates need image verification; this text batch ends here.'
        response[0]['out']['issues'] = [observation]
        with patch.object(llm, 'call', return_value=response), patch.object(targeted, 'crops', return_value=([], [])):
            correction.run(PID, SPEC)
        state = correction.state(PID)
        self.assertEqual(state['screen_notes'], [observation])
        self.assertFalse(any(observation in issue['text'] for issue in state['issues']))
        self.assertTrue(any('source location' in issue['text'] for issue in state['issues']))


    def test_direct_document_repairs_need_only_one_text_request(self):
        correction.queue(PID)
        edit = {"before": "Broken turbuð Þlent flow.", "after": "Broken turbulent flow.",
                "reason": "The unique repeated phrase establishes the damaged word", "evidence": "document-text"}
        with patch.object(llm, "call", return_value=({"out": {"edits": [edit], "candidates": [], "issues": []}}, False)) as call, \
             patch.object(llm_openai, "vision") as vision:
            correction.run(PID, SPEC)
        self.assertEqual(call.call_count, 1)
        vision.assert_not_called()
        self.assertIn("Broken turbulent flow.", (self.d/"source.md").read_text(encoding="utf-8"))
        self.assertEqual(correction.state(PID)["edits"], 1)
        import json
        history = json.loads((self.d/"targeted-work.json").read_text(encoding="utf-8"))["history"]
        self.assertEqual(history[0]["edits"][0]["evidence"], "document-text")

    def test_direct_symbol_repair_and_numerical_evidence_boundary(self):
        text = self.md + "\nDefined $u$ is velocity. Repeated $u+x$. Damaged $v+x$. Value 12.\n"
        (self.d/"source.md").write_text(text, encoding="utf-8")
        (self.d/"source.html").write_text(correction.render(text, {}), encoding="utf-8")
        correction.queue(PID)
        edits = [{"before": "Damaged $v+x$.", "after": "Damaged $u+x$.",
                  "reason": "Explicit document definition and identical repeated expression establish extraction fault", "evidence": "document-symbol"},
                 {"before": "Value 12.", "after": "Value 13.", "reason": "suspected numeric error", "evidence": "document-text"}]
        with patch.object(llm, "call", return_value=({"out": {"edits": edits, "candidates": [], "issues": []}}, False)), \
             patch.object(llm_openai, "vision") as vision:
            correction.run(PID, SPEC)
        vision.assert_not_called()
        source = (self.d/"source.md").read_text(encoding="utf-8")
        self.assertIn("Damaged $u+x$.", source)
        self.assertIn("Value 12.", source)
        self.assertTrue(any("Numerical" in x["text"] for x in correction.state(PID)["issues"]))

    def test_cross_page_candidates_share_one_source_decision(self):
        correction.queue(PID)
        response = self.screen()
        response[0]["out"]["candidates"].append({"before": "A healthy paragraph with $x+y$.",
             "anchor": "A healthy paragraph with", "page": 2, "reason": "possible boundary"})
        edit = {"before": "Broken turbuð Þlent flow.", "after": "A turbulent flow.", "reason": "printed"}
        with patch.object(llm, "call", return_value=response), \
             patch.object(targeted, "crops", side_effect=lambda pdf, page, anchors: ([str(page).encode()], anchors)), \
             patch.object(llm_openai, "vision", return_value=self.source_result([edit], 'corrected', (0, 1))) as vision:
            correction.run(PID, SPEC)
        self.assertEqual(vision.call_count, 1)
        self.assertEqual(vision.call_args.args[3], [b"1", b"2"])
        self.assertIn('"page": 2', vision.call_args.args[0])
        self.assertEqual(correction.state(PID)["done"], 2)


    def test_mineru_box_works_without_pdf_text_layer(self):
        import json
        (self.d/"layout.json").write_text(json.dumps([
            {"p": 1, "b": [.1, .2, .8, .4], "t": "Broken turbuð Þlent flow."}]), encoding="utf-8")
        correction.queue(PID)
        response = self.screen()
        response[0]["out"]["candidates"][0].update(block=0, anchor="")
        with patch.object(llm, "call", return_value=response), patch.object(targeted, "crops") as fallback, \
             patch.object(llm_openai, "vision", return_value=self.source_result()) as vision:
            correction.run(PID, SPEC)
        fallback.assert_not_called()
        self.assertTrue(vision.call_args.args[3][0].startswith(b"\x89PNG"))
        self.assertIn('"block": 0', vision.call_args.args[0])


    def test_short_documents_are_not_split_at_six_pages(self):
        self.assertEqual(targeted.text_spans("paragraph\n\n" * 2000), [(0, 22000)])
        text = "paragraph\n\n" * 20000
        spans = targeted.text_spans(text)
        self.assertEqual("".join(text[a:b] for a, b in spans), text)
        self.assertTrue(all(b-a <= 90000 for a, b in spans))


    def test_number_guard_detects_values_and_keeps_duplicate_cleanup_possible(self):
        self.assertEqual(targeted.number_values("$1 2 . 0$"), targeted.number_values("$12.0$"))
        self.assertTrue(targeted.number_values("$1.0$") - targeted.number_values("$0.1$"))
        self.assertTrue(targeted.number_values("$+1$") - targeted.number_values("$-1$"))
        self.assertFalse(targeted.number_values("$x_0$ ") - targeted.number_values("$x_0$ x0"))

    def test_clean_screen_uses_no_images_and_preserves_author_notation(self):
        text = self.md + "\nDefined $u$; printed result $v=x$. Defined $alpha$; printed scale $beta$.\n"
        (self.d/"source.md").write_text(text, encoding="utf-8")
        (self.d/"source.html").write_text(correction.render(text, {}), encoding="utf-8")
        correction.queue(PID)
        with patch.object(llm, "call", return_value=({"out": {"edits": [], "candidates": [], "issues": []}}, False)) as call, \
             patch.object(llm_openai, "vision") as vision:
            correction.run(PID, SPEC)
        vision.assert_not_called()
        self.assertIn("physical plausibility", call.call_args.args[0])
        self.assertEqual((self.d/"source.md").read_text(encoding="utf-8"), text)


    def test_narrow_equation_box_retains_neighbor_column_and_printed_label(self):
        import json
        import pypdfium2 as pdfium
        from PIL import Image
        # Extractors can box the formula body separately from its right-margin label.
        layout = [{"p": 1, "b": [.32, .38, .6, .41], "t": "$x=y$"},
                  {"p": 1, "b": [.08, .32, .92, .37], "t": "Full column context"}]
        candidate = {"page": 1, "block": 0, "before": "Broken", "anchor": "", "reason": "missing label"}
        with pdfium.PdfDocument(str(self.d/"source.pdf")) as pdf:
            images, located, _ = targeted.evidence(pdf, [candidate], "Broken", layout, 2)
        self.assertEqual(located, [candidate])
        with Image.open(io.BytesIO(images[0])) as image:
            self.assertGreater(image.width, 1200)


    def test_old_page_group_completion_does_not_skip_remaining_batched_candidates(self):
        import json
        correction.queue(PID)
        first = {"before": "Broken turbuð Þlent flow.", "after": "A turbulent flow.", "reason": "printed"}
        second = {"before": "A healthy paragraph with $x+y$.", "after": "A healthy paragraph with $x-y$.", "reason": "printed"}
        candidates = [self.screen()[0]["out"]["candidates"][0],
                      {"before": second["before"], "anchor": "The second physical page", "page": 2, "reason": "math"}]
        # This is the deployed version's saved record: completed indexes refer to page groups.
        old = {"text": correction.patches(self.md, [first]), "candidates": candidates,
               "history": [{"page": 1, "edits": [first]}], "issues": [], "completed": [0]}
        (self.d/"targeted-work.json").write_text(json.dumps(old), encoding="utf-8")
        with patch.object(llm, "call") as screen, \
             patch.object(targeted, "crops", side_effect=lambda pdf, page, anchors: ([b"page2"], anchors)), \
             patch.object(llm_openai, "vision", return_value={'edits': [dict(second, candidate=1, page=2)], 'issues': [], 'displays': [], 'decisions': [{'candidate': 1, 'verdict': 'corrected', 'reason': 'visible'}]}) as vision:
            correction.run(PID, SPEC)
        screen.assert_not_called()
        self.assertEqual(vision.call_count, 1)
        source = (self.d/"source.md").read_text(encoding="utf-8")
        self.assertIn(first["after"], source)
        self.assertIn(second["after"], source)
        self.assertEqual(correction.state(PID)["done"], 2)



    def test_direct_relocation_cannot_publish_only_the_caption_deletion_half(self):
        text = self.md + "\nFigs. 2(a) and\n\nFIG. 1. Original caption with $x+y$.\n\n2(b), give the result.\n"
        (self.d/"source.md").write_text(text, encoding="utf-8")
        (self.d/"source.html").write_text(correction.render(text, {}), encoding="utf-8")
        correction.queue(PID)
        edit = {"before": "Figs. 2(a) and\n\nFIG. 1. Original caption with $x+y$.\n\n2(b),", "after": "Figs. 2(a) and 2(b),",
                "reason": "Caption will be moved by a companion edit", "evidence": "document-text"}
        with patch.object(llm, "call", return_value=({"out": {"edits": [edit], "candidates": [], "issues": []}}, False)), \
             patch.object(llm_openai, "vision") as vision:
            correction.run(PID, SPEC)
        vision.assert_not_called()
        self.assertIn("FIG. 1. Original caption", (self.d/"source.md").read_text(encoding="utf-8"))
        self.assertTrue(any("caption" in x["text"] for x in correction.state(PID)["issues"]))

    def test_pdf_proposal_can_depend_on_an_earlier_draft_edit(self):
        correction.queue(PID)
        edits = [{'before': 'Broken turbuð Þlent flow.', 'after': 'A turbulent flow.', 'reason': 'word'},
                 {'before': 'A turbulent flow.', 'after': 'A turbulent flow $x=y\\tag{1}$.', 'reason': 'label'}]
        with patch.object(llm, 'call', return_value=self.screen()), \
             patch.object(targeted, 'crops', side_effect=lambda pdf, page, anchors: ([b'crop'], anchors)), \
             patch.object(llm_openai, 'vision', return_value=self.source_result(edits, 'corrected')):
            correction.run(PID, SPEC)
        self.assertIn(edits[1]['after'], (self.d/'source.md').read_text(encoding='utf-8'))
        self.assertEqual(correction.state(PID)['edits'], 2)

    def test_rejected_prerequisite_withholds_dependent_accepted_edit(self):
        correction.queue(PID)
        edits = [{'before': 'An absent prerequisite.', 'after': 'A turbulent flow.', 'reason': 'stale'},
                 {'before': 'A turbulent flow.', 'after': 'New formula $x=y$.', 'reason': 'dependent'}]
        with patch.object(llm, 'call', return_value=self.screen()), \
             patch.object(targeted, 'crops', side_effect=lambda pdf, page, anchors: ([b'crop'], anchors)), \
             patch.object(llm_openai, 'vision', return_value=self.source_result(edits, 'corrected')):
            correction.run(PID, SPEC)
        self.assertEqual((self.d/'source.md').read_text(encoding='utf-8'), self.md)
        self.assertTrue(correction.state(PID)['issues'])

    def test_matching_block_corrects_a_guessed_physical_page(self):
        import json
        (self.d/"layout.json").write_text(json.dumps([
            {"p": 2, "b": [.1, .2, .8, .4], "t": "Broken turbuð Þlent flow."}]), encoding="utf-8")
        correction.queue(PID)
        response = self.screen()
        response[0]["out"]["candidates"][0].update(block=0, page=1, anchor="")
        with patch.object(llm, "call", return_value=response), patch.object(targeted, "crops") as fallback, \
             patch.object(llm_openai, "vision", return_value=self.source_result()) as vision:
            correction.run(PID, SPEC)
        fallback.assert_not_called()
        self.assertIn('"page": 2', vision.call_args.args[0])


    def test_caption_text_layer_refines_an_image_inherited_box(self):
        from reportlab.pdfgen import canvas
        import pypdfium2 as pdfium
        from PIL import Image
        path = self.d/"caption.pdf"
        cv = canvas.Canvas(str(path), pagesize=(600, 800))
        text = "FIG. 1. This complete caption extends beyond both sides of the inherited image box."
        cv.drawString(60, 330, text);cv.save()
        block = {"p": 1, "b": [.3, .2, .7, .5], "fig": [.3, .2, .7, .5], "t": text}
        with pdfium.PdfDocument(str(path)) as pdf:
            image = targeted.block_crop(pdf, block, [block])
        with Image.open(io.BytesIO(image)) as image:
            self.assertLess(image.getextrema()[0][0], 64)
            self.assertLess(image.height, 300)
            self.assertGreater(image.width, 1000)


    def test_numeric_index_to_letter_needs_pdf_and_keeps_printed_author_variant(self):
        import json
        text = self.md + "\nDefined $Ro$. Printed $R_0$ flows.\n"
        (self.d/"source.md").write_text(text, encoding="utf-8")
        (self.d/"source.html").write_text(correction.render(text, {}), encoding="utf-8")
        (self.d/"layout.json").write_text(json.dumps([
            {"p": 1, "b": [.1, .2, .8, .4], "t": "Printed $R_0$ flows."}]), encoding="utf-8")
        correction.queue(PID)
        edit = {"before": "$R_0$", "after": "$Ro$", "evidence": "document-symbol", "reason": "initial definition differs"}
        with patch.object(llm, "call", return_value=({"out": {"edits": [edit], "candidates": [], "issues": []}}, False)), \
             patch.object(llm_openai, "vision", return_value=self.source_result()) as vision:
            correction.run(PID, SPEC)
        self.assertEqual(vision.call_count, 1)
        self.assertEqual((self.d/"source.md").read_text(encoding="utf-8"), text)
        self.assertEqual(correction.state(PID)["issues"], [])



    def test_partial_math_boundary_repair_cannot_publish_a_dangling_dollar(self):
        text = self.md + "\nEven for the $1 6 3 8 4 \\mathrm { run }$, where the spectrum is measured.\n"
        (self.d/"source.md").write_text(text, encoding="utf-8")
        (self.d/"source.html").write_text(correction.render(text, {}), encoding="utf-8")
        correction.queue(PID)
        edit = {"before": "1 6 3 8 4 \\mathrm { run }", "after": "1 6 3 8 4$ run",
                "reason": "A later companion will remove the old closing dollar", "evidence": "document-text"}
        with patch.object(llm, "call", return_value=({"out": {"edits": [edit], "candidates": [], "issues": []}}, False)), \
             patch.object(llm_openai, "vision") as vision:
            correction.run(PID, SPEC)
        vision.assert_not_called()
        self.assertEqual((self.d/"source.md").read_text(encoding="utf-8"), text)
        self.assertTrue(any("math boundary" in x["text"] for x in correction.state(PID)["issues"]))

    def test_markdown_only_fallback_locates_rejected_repair_without_an_extra_model_call(self):
        pages = ["Unrelated source page.", "Even for the 16 384 run, where we measure a spectrum."]
        text = "Even for the $1 6 3 8 4 \\mathrm { run }$, where we measure a spectrum."
        edit = {"before": "1 6 3 8 4 \\mathrm { run }", "reason": "boundary repair"}
        candidate = targeted.source_candidate(edit, text, [], pages)
        self.assertEqual(candidate["page"], 2)
        self.assertIsNotNone(targeted.locate(pages[1], candidate["anchor"]))

    def test_retained_html_math_caption_matches_markdown_math(self):
        edit = {"before": "$C _ { 1 } (\\Gamma) ( N u - 1 )$", "reason": "numeric evidence"}
        layout = [{"p": 10, "b": [.1, .2, .9, .4],
                   "t": 'Caption <span class="math inline">C _ { 1 } (\\Gamma) ( N u - 1 )</span>.'}]
        candidate = targeted.source_candidate(edit, edit["before"], layout, [""] * 10)
        self.assertEqual((candidate["block"], candidate["page"]), (0, 10))
        self.assertEqual(targeted.compact("$x < y > z$"), "x<y>z")


    def test_unique_pdf_anchor_overrides_a_contradicted_guessed_page(self):
        import json
        from reportlab.pdfgen import canvas
        cv = canvas.Canvas(str(self.d/"source.pdf"), pagesize=(600, 800))
        cv.drawString(50, 700, "Unrelated source geometry on the first page.");cv.showPage()
        cv.drawString(50, 700, "The actual scaling exponent agrees excellently here.");cv.save()
        (self.d/"layout.json").write_text(json.dumps([
            {"p": 1, "b": [.1, .2, .9, .4], "t": "Broken turbuð Þlent flow."}]), encoding="utf-8")
        correction.queue(PID)
        response = self.screen()
        response[0]["out"]["candidates"][0].update(block=0, page=1, anchor="The actual scaling exponent")
        with patch.object(llm, 'call', side_effect=[response, ({'out': self.source_result()}, False)]), \
             patch.object(targeted, "crops", side_effect=lambda pdf, page, anchors: ([b"correct source"], anchors)) as crop, \
             patch.object(llm_openai, "vision", return_value=self.source_result()):
            correction.run(PID, SPEC)
        crop.assert_not_called()
        import json
        work = json.loads((self.d/'targeted-work.json').read_text(encoding='utf-8'))
        self.assertEqual(work['pdf_text_evidence'][0]['page'], 2)


    def test_new_reference_review_gets_literal_pdf_text_without_a_separate_call(self):
        pages = ["[1] J. G. Charney, Geostrophic turbulence, J. Atom. Sci. 28, 1087 (1971)."]
        edit = {"before": "Partial following citation", "after": "[1] J. G. Charney, Geostrophic turbulence, J. Atmos. Sci. 28, 1087 (1971).", "page": 1}
        cues = targeted.reference_cues([edit], pages)
        self.assertEqual(len(cues), 1)
        self.assertIn("J. Atom. Sci.", cues[0]["text"])
