"""Correction preserves source identity, healthy generated text and the reader's notes.

All papers, PDFs, model replies and settings here are temporary. No live provider is called.
"""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pypdfium2 as pdfium

from textfold import correction, ladder, llm_openai, markdown, notes, pipeline, store
from textfold.parse import parse


PID = "pdf-0123456789abcdef"
SPEC = {"kind": "api", "protocol": "openai", "id": "test", "model": "test", "base": "http://127.0.0.1:10531/v1"}


class CorrectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patch = patch.object(store, "DATA", Path(self.tmp.name))
        self.patch.start()
        self.d = store.pdir(PID)
        self.d.mkdir(parents=True)
        self.md = "# Method\n\nBroken turbuð Þlent flow.\n\nA healthy paragraph with $x+y$.\n"
        self.html = correction.render(self.md, {})
        self.meta = {"id": PID, "title": "Test", "source": {"kind": "pdf"}}
        for name, text in (("source.md", self.md), ("source.html", self.html), ("meta.json", json.dumps(self.meta))):
            (self.d / name).write_text(text, encoding="utf-8")
        pdf = pdfium.PdfDocument.new()
        for _ in range(2):
            page = pdf.new_page(600, 800)
            page.close()
        pdf.save(self.d / "source.pdf")
        pdf.close()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_ambiguous_and_stale_patches_do_not_change_source(self):
        for text, before in (("a a", "a"), ("abc", "missing")):
            with self.assertRaises(ValueError):
                correction.patches(text, [{"before": before, "after": "z"}])
        self.assertEqual((self.d / "source.md").read_text(encoding="utf-8"), self.md)

    def test_publish_remaps_atoms_preserves_healthy_layers_and_notes(self):
        old = store.parsed(PID)
        old_ids = list(old["units"])
        for u in old["units"].values():
            u["lad"] = ladder.local(u, old["atoms"])
        store.save_en(old, "test")
        notes.put(PID, {"id": "n-healthy", "anchor": {"unit": old_ids[1], "section": "sec-method",
                  "quote": {"exact": "healthy paragraph"}, "tokens": [1, 2], "sents": [0]}, "text": "Keep me"})
        notes.put(PID, {"id": "n-changed", "anchor": {"unit": old_ids[0], "section": "sec-method",
                  "quote": {"exact": "turbuð Þlent"}, "tokens": [1, 2], "sents": [0]}, "text": "Keep this too"})
        changed = self.md.replace("Broken turbuð Þlent flow.", "Corrected turbulent flow with $a=b$.\n\nNew paragraph.")
        s = {}
        correction.publish(PID, changed, s)
        new = store.parsed(PID)
        en = store.read(PID, "en")
        self.assertEqual(len(en["units"]), 1)
        healthy = next(iter(en["units"]))
        self.assertEqual(new["units"][healthy]["toks"][-2].get("a"), "a1")
        self.assertTrue(en["incomplete"])
        self.assertEqual(en["chunks"], {})
        self.assertEqual(en["edges"], [])
        ns = notes.read(PID)["notes"]
        self.assertEqual(ns[0]["text"], "Keep me")
        self.assertEqual(ns[0]["anchor"]["unit"], healthy)
        self.assertIsNone(ns[1]["anchor"]["tokens"])
        self.assertEqual(ns[1]["anchor"]["quote"]["exact"], "turbuð Þlent")
        self.assertEqual((self.d / "correction-original/source.md").read_text(encoding="utf-8"), self.md)

    def test_all_pages_checked_and_edited_page_verified_before_publication(self):
        correction.queue(PID, method="full")
        def reply(prompt, schema, spec, images, **kwargs):
            if schema is correction.REVIEW:
                return {"decisions": [{"index": 0, "verdict": "accept", "reason": "PDF shows turbulent"}]}
            if "physical PDF page 1" in prompt:
                return {"edits": [{"before": "Broken turbuð Þlent flow.", "after": "A turbulent flow.", "reason": "PDF"}], "issues": []}
            return {"edits": [], "issues": ["Page 2: symbol cannot be distinguished"]}
        with patch.object(llm_openai, "vision", side_effect=reply) as call:
            correction.run(PID, SPEC)
        self.assertEqual(call.call_count, 3)
        review_call = next(c for c in call.call_args_list if c.args[1] is correction.REVIEW)
        self.assertIn("corrected result", review_call.args[0])
        self.assertIn("A turbulent flow.", review_call.args[0])
        s = correction.state(PID)
        self.assertEqual((s["done"], s["total"], s["status"]), (2, 2, "done"))
        self.assertEqual(s["issues"][0]["page"], 2)
        self.assertIn("A turbulent flow.", (self.d / "source.md").read_text(encoding="utf-8"))
        with patch.object(llm_openai, "vision") as call:
            correction.run(PID, SPEC)
            call.assert_not_called()

    def test_provider_failure_is_not_success_and_does_not_publish_draft(self):
        correction.queue(PID, method="full")
        with patch.object(llm_openai, "vision", side_effect=RuntimeError("provider unavailable")):
            with self.assertRaisesRegex(RuntimeError, "unavailable"):
                correction.run(PID, SPEC)
        self.assertEqual(correction.state(PID)["status"], "error")
        self.assertEqual((self.d / "source.md").read_text(encoding="utf-8"), self.md)

    def test_parallel_overlap_is_relocated_in_current_context_without_overwriting_reviewed_edit(self):
        correction.queue(PID, method="full")
        edit = {"before": "Broken turbuð Þlent flow.", "after": "A turbulent flow.", "reason": "PDF"}
        def reply(prompt, schema, spec, images, **kwargs):
            if schema is correction.REVIEW:
                return {"decisions": [{"index": 0, "verdict": "accept", "reason": "Printed turbulent"}]}
            if "Region verification pass" in prompt:
                current = prompt.split("CURRENT extraction:\n", 1)[1]
                self.assertIn("A turbulent flow.", current)
                self.assertNotIn("Broken turbuð Þlent flow.", current)
                return {"edits": [], "issues": []}
            return {"edits": [edit], "issues": []}
        with patch.object(llm_openai, "vision", side_effect=reply):
            correction.run(PID, SPEC)
        self.assertEqual(correction.state(PID)["edits"], 1)
        self.assertIn("A turbulent flow.", (self.d / "source.md").read_text(encoding="utf-8"))

    def test_missing_numbered_display_gets_region_restoration_and_independent_review(self):
        correction.queue(PID, method="full")
        def reply(prompt, schema, spec, images, **kwargs):
            if schema is correction.REVIEW:
                return {"decisions": [{"index": 0, "verdict": "accept", "reason": "All terms and number match"}]}
            if "Restore the following numbered" in prompt:
                return {"edits": [{"before": "Broken turbuð Þlent flow.",
                    "after": "Broken turbuð Þlent flow.\n\n$$x=y \\tag{10}$$", "reason": "Missing printed result"}], "issues": []}
            if "physical PDF page 1" in prompt:
                return {"edits": [], "issues": [], "displays": [{"number": "10", "present": False, "box": [.1,.3,.9,.6]}]}
            return {"edits": [], "issues": []}
        with patch.object(llm_openai, "vision", side_effect=reply):
            correction.run(PID, SPEC)
        self.assertIn(r"\tag{10}", (self.d / "source.md").read_text(encoding="utf-8"))
        stages = {r["stage"] for r in correction.state(PID)["timing"]["requests"]}
        self.assertIn("missing-display-regions", stages)
        self.assertIn("independent-region-review", stages)

    def test_resume_skips_completed_pages_and_publishes_only_after_all_pages(self):
        correction.queue(PID, method="full")
        def reply(prompt, *args, **kwargs):
            if "physical PDF page 1" in prompt:
                return {"edits": [], "issues": []}
            raise RuntimeError("offline")
        with patch.object(llm_openai, "vision", side_effect=reply):
            with self.assertRaises(RuntimeError):
                correction.run(PID, SPEC)
        self.assertEqual(correction.state(PID)["done"], 1)
        with patch.object(llm_openai, "vision", return_value={"edits": [], "issues": []}) as call:
            correction.run(PID, SPEC)
        self.assertEqual(call.call_count, 1)
        self.assertIn("physical PDF page 2", call.call_args.args[0])
        self.assertEqual(correction.state(PID)["status"], "done")

    def test_independent_pdf_review_can_reject_plausible_author_rewrite(self):
        edit = {"before": "velocity $v$", "after": "velocity $u$", "reason": "More consistent notation"}
        with patch.object(llm_openai, "vision", return_value={"decisions": [
                {"index": 0, "verdict": "reject", "reason": "The PDF actually prints v"}]}):
            accepted, issues = correction.review([edit], [b"page pixels"], SPEC, [1])
        self.assertEqual(accepted, [])
        self.assertEqual(issues[0]["verdict"], "reject")

    def test_failed_pdf_check_blocks_summary_generation_and_questions(self):
        correction.queue(PID, method="full")
        with patch.object(correction, "run", side_effect=RuntimeError("image check failed")), patch.object(ladder, "build") as build:
            with self.assertRaisesRegex(RuntimeError, "image check failed"):
                pipeline.generate(PID, "en", SPEC)
            build.assert_not_called()
        with self.assertRaisesRegex(RuntimeError, "PDF 校对尚未完成"):
            notes.ask(PID, "n-any", "What does the paper show?", SPEC)

    def test_image_paths_survive_correction(self):
        md = self.md + '<figure><img src="images/fig.png"><figcaption>A caption.</figcaption></figure>'
        html = correction.render(md, {"images/fig.png": "img/01-fig.png"})
        mapping = correction._images(md, html)
        self.assertIn('src="img/01-fig.png"', correction.render(md.replace("A caption", "Correct caption"), mapping))
        with self.assertRaises(ValueError):
            correction.render(md.replace('src="images/fig.png"', 'src="another.png"'), mapping)

    def test_display_equation_changes_invalidate_dependent_section_levels(self):
        before_md = "# Theory\n\nThe transfer follows this equation.\n\n$$x=y$$\n"
        after_md = before_md.replace("x=y", "x=-y")
        old = parse(correction.render(before_md, {}), self.meta)
        new = parse(correction.render(after_md, {}), self.meta)
        for u in old["units"].values():
            u["lad"] = ladder.local(u, old["atoms"])
        store.save_en(old, "test")
        updated, _, affected = correction.reconcile(old, new, {"en": store.read(PID, "en")}, None)
        self.assertEqual(updated["en"]["units"], {})
        self.assertIn(new["chunks"][0]["id"], affected)
        new["meta"]["correction"] = {"status": "done"}
        self.assertIn("x=-y", correction.equations(new))

    def test_restored_long_formula_remains_a_scrollable_equation_block(self):
        md = "# Theory\n\nThe equation is:\n\n$$" + " + ".join(f"x_{i}" for i in range(45)) + "$$\n"
        html = correction.render(md, {})
        doc = parse(html, self.meta)
        self.assertEqual(len([b for b in doc["blocks"] if b["k"] == "eq"]), 1)

    def test_bridge_uses_real_image_responses_and_rejects_incomplete_results(self):
        result = {"status": "completed", "output": [{"content": [{"type": "output_text", "text": '{"edits": [], "issues": [], "displays": []}'}]}]}
        with patch.object(llm_openai, "_post", return_value=result) as post:
            llm_openai.vision("check", correction.SCHEMA, SPEC, [b"page pixels"])
        url, body, _, _ = post.call_args.args
        self.assertTrue(url.endswith("/responses"))
        self.assertEqual(body["input"][0]["content"][1]["type"], "input_image")
        self.assertTrue(body["input"][0]["content"][1]["image_url"].startswith("data:image/png;base64,"))
        with patch.object(llm_openai, "_post", return_value={"status": "incomplete"}):
            with self.assertRaisesRegex(RuntimeError, "did not complete"):
                llm_openai.vision("check", correction.SCHEMA, SPEC, [b"page pixels"])


if __name__ == "__main__":
    unittest.main()
