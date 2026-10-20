"""Default discovery uses text; edits require local image evidence and a second decision."""
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

    def test_default_is_text_first_and_not_exhaustive_coverage(self):
        correction.queue(PID)
        edit = {"before": "Broken turbuð Þlent flow.", "after": "The turbulent flow.", "reason": "printed"}
        replies = [{"edits": [edit], "issues": []}, {"decisions": [
            {"index": 0, "verdict": "accept", "reason": "printed turbulent"}]}]
        with patch.object(llm, "call", return_value=self.screen()) as screen, \
             patch.object(targeted, "crops", side_effect=lambda pdf, page, anchors: ([b"local-image"], anchors)) as crop, \
             patch.object(llm_openai, "vision", side_effect=replies) as vision:
            correction.run(PID, SPEC)
        self.assertEqual(screen.call_count, 1)
        self.assertEqual(vision.call_count, 2)
        self.assertEqual(crop.call_args.args[1:], (1, ["The original turbulent flow"]))
        self.assertEqual(correction.state(PID)["checked"], [])
        self.assertEqual(correction.state(PID)["status"], "done")
        self.assertIn("The turbulent flow.", (self.d/"source.md").read_text(encoding="utf-8"))

    def test_independent_rejection_keeps_author_source(self):
        correction.queue(PID)
        with patch.object(llm, "call", return_value=self.screen()), \
             patch.object(targeted, "crops", side_effect=lambda pdf, page, anchors: ([b"crop"], anchors)), \
             patch.object(llm_openai, "vision", side_effect=[{"edits": [{
                 "before": "Broken turbuð Þlent flow.", "after": "Plausible rewrite.", "reason": "physics"}],
                 "issues": []}, {"decisions": [{"index": 0, "verdict": "reject", "reason": "printed v, not u"}]}]):
            correction.run(PID, SPEC)
        self.assertEqual((self.d/"source.md").read_text(encoding="utf-8"), self.md)

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
             patch.object(llm_openai, "vision", return_value={"edits": [], "issues": []}):
            correction.run(PID, SPEC, stop=stop)
        screen.assert_not_called()
        self.assertEqual(correction.state(PID)["status"], "done")

    def test_explicit_full_check_does_not_reuse_targeted_coverage(self):
        correction.queue(PID)
        with patch.object(llm, "call", return_value=({"out": {"candidates": [], "issues": []}}, False)):
            correction.run(PID, SPEC)
        with patch.object(llm_openai, "vision", return_value={"edits": [], "issues": []}) as vision:
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

    def test_review_failure_reuses_proposal_and_generation_waits_for_acceptance(self):
        correction.queue(PID)
        edit = {"before": "Broken turbuð Þlent flow.", "after": "A turbulent flow.", "reason": "printed"}
        with patch.object(llm, "call", return_value=self.screen()), \
             patch.object(targeted, "crops", side_effect=lambda pdf, page, anchors: ([b"crop"], anchors)), \
             patch.object(llm_openai, "vision", side_effect=[{"edits": [edit], "issues": []}, RuntimeError("provider")]):
            with self.assertRaisesRegex(RuntimeError, "provider"):
                correction.run(PID, SPEC)
        self.assertEqual((self.d/"source.md").read_text(encoding="utf-8"), self.md)
        def build(doc, *args, **kwargs):
            self.assertEqual(correction.state(PID)["status"], "done")
            self.assertIn("A turbulent flow.", (self.d/"source.md").read_text(encoding="utf-8"))
            for u in doc["units"].values():
                u["lad"] = pipeline.ladder.local(u, doc["atoms"])
        with patch.object(llm, "call") as screen, patch.object(targeted, "crops", side_effect=lambda pdf, page, anchors: ([b"crop"], anchors)), \
             patch.object(llm_openai, "vision", return_value={"decisions": [
                 {"index": 0, "verdict": "accept", "reason": "printed"}]}) as vision, \
             patch.object(pipeline.ladder, "build", side_effect=build) as generated, \
             patch.object(pipeline.links, "build"):
            pipeline.generate(PID, "en", SPEC)
        screen.assert_not_called()
        self.assertEqual(vision.call_count, 1)
        self.assertIs(vision.call_args.args[1], correction.REVIEW)
        generated.assert_called_once()

    def test_candidates_on_same_page_share_requests_and_identical_image(self):
        correction.queue(PID)
        response = self.screen()
        response[0]["out"]["candidates"].append({"before": "A healthy paragraph with $x+y$.",
                "anchor": "A healthy paragraph with", "page": 1, "reason": "possible boundary"})
        with patch.object(llm, "call", return_value=response), patch.object(targeted, "crops", side_effect=lambda pdf, page, anchors: ([b"same-crop"], anchors)), \
             patch.object(llm_openai, "vision", return_value={"edits": [], "issues": []}) as vision:
            correction.run(PID, SPEC)
        self.assertEqual(vision.call_count, 1)
        self.assertEqual(vision.call_args.args[3], [b"same-crop"])
        self.assertEqual(correction.state(PID)["done"], 2)
