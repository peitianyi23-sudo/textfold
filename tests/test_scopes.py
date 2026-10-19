"""Scope scheduling uses physical pages and never mistakes navigation for coverage."""
import json
import queue
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from types import SimpleNamespace
from unittest.mock import patch

import pypdfium2 as pdfium
from PIL import Image

from textfold import correction, ladder, llm, llm_openai, pipeline, scopes, server, store
from tests import test_correction as fixtures

PID, SPEC = fixtures.PID, fixtures.SPEC


class ScopeTests(unittest.TestCase):
    setUp = fixtures.CorrectionTests.setUp
    tearDown = fixtures.CorrectionTests.tearDown
    def pdf(self, count):
        with pdfium.PdfDocument.new() as pdf:
            for _ in range(count):
                pdf.new_page(10, 10).close()
            pdf.save(self.d / "source.pdf")

    def test_30_31_and_100_import_boundary_has_no_automatic_model_work(self):
        for count in (30, 31, 100):
            self.pdf(count)
            correction.queue(PID, reset=True)
            s = correction.state(PID)
            self.assertEqual(s["total"], count)
            self.assertEqual(s["status"], "queued" if count == 30 else "awaiting-scope")
            if count > 30:
                with patch.object(llm_openai, "vision") as vision, patch.object(ladder, "build") as build:
                    pipeline.generate(PID, "en", SPEC)
                vision.assert_not_called()
                build.assert_not_called()

    def test_chapter_from_reading_position_is_capped_and_not_marked_complete(self):
        selection = scopes.select({"kind":"chapter", "chapter":"methods", "position":12},100,
                                  {"methods":list(range(5,75))})
        self.assertEqual(selection["pages"],list(range(12,42)))
        self.assertEqual(selection["chapter_pages"],list(range(5,75)))
        with self.assertRaisesRegex(ValueError,"boundaries"):
            scopes.select({"kind":"chapter","chapter":"invented"},100,{})

    def test_noncontiguous_ranges_preserve_prior_coverage_and_resume_without_rechecking(self):
        self.pdf(100)
        correction.queue(PID)
        scope = correction.choose(PID,{"kind":"range","ranges":[[2,3],[80,80]]})
        with patch.object(llm_openai,"vision",return_value={"edits":[],"issues":[]}) as call:
            correction.run(PID,SPEC,scope=scope)
        self.assertEqual(call.call_count,3)
        s = correction.state(PID)
        self.assertEqual(s["checked"],[2,3,80])
        self.assertEqual(s["status"],"scope-done")
        with patch.object(llm_openai,"vision",return_value={"edits":[],"issues":[]}) as call:
            correction.run(PID,SPEC,scope=scope)
            call.assert_not_called()
            correction.run(PID,SPEC,scope=correction.choose(PID,{"kind":"range","ranges":[[3,4]]}))
        self.assertEqual(call.call_count,1)
        self.assertEqual(correction.state(PID)["checked"],[2,3,4,80])

    def test_document_batches_are_at_most_30_and_pipeline_generates_between_batches(self):
        self.pdf(65)
        correction.queue(PID)
        checked = []
        def generated(*a,**kw):
            checked.append(len(correction.state(PID)["checked"]))
        with patch.object(llm_openai,"vision",return_value={"edits":[],"issues":[]}) as call, \
             patch.object(pipeline,"generate_scope",side_effect=generated), \
             patch.object(ladder,"build"), patch.object(pipeline.links,"build"):
            pipeline.generate(PID,"en",SPEC,scope=correction.choose(PID,{"kind":"document"}))
        self.assertEqual(call.call_count,65)
        self.assertEqual(checked,[30,60])
        self.assertEqual(correction.state(PID)["status"],"done")

    def test_stop_discards_unreviewed_reply_keeps_reviewed_work_and_new_scope(self):
        self.pdf(31)
        correction.queue(PID)
        stop = threading.Event()
        edit = {"before":"Broken turbuð Þlent flow.","after":"A turbulent flow.","reason":"PDF"}
        def response(prompt,schema,*a):
            if schema is correction.REVIEW:
                return {"decisions":[{"index":0,"verdict":"accept","reason":"Printed text"}]}
            if "physical PDF page 1 " in prompt:
                return {"edits":[edit],"issues":[]}
            stop.set()
            return {"edits":[{"before":"A healthy paragraph","after":"UNREVIEWED","reason":"late"}],"issues":[]}
        with patch.object(llm_openai,"vision",side_effect=response):
            with self.assertRaises(llm.Stopped):
                correction.run(PID,SPEC,stop=stop,scope=scopes.select({"kind":"range","ranges":[[1,2]]},31))
        self.assertEqual(correction.state(PID)["checked"],[1])
        self.assertIn("A turbulent flow.",(self.d/"source.md").read_text(encoding="utf-8"))
        self.assertNotIn("UNREVIEWED",(self.d/"source.md").read_text(encoding="utf-8"))
        with patch.object(llm_openai,"vision",return_value={"edits":[],"issues":[]}) as call:
            correction.run(PID,SPEC,scope=scopes.select({"kind":"range","ranges":[[20,20]]},31))
        self.assertEqual(call.call_count,1)
        self.assertEqual(correction.state(PID)["checked"],[1,20])

    def test_queued_scope_replacement_stops_old_job_across_languages(self):
        jobs = server.Jobs.__new__(server.Jobs)
        jobs.items, jobs.stops, jobs.q = {}, {}, queue.Queue()
        old = jobs.submit(PID,"en",False,scope={"pages":[1]})
        old["status"] = "running"
        waiting = jobs.submit(PID,"zh",False)
        new = jobs.submit(PID,"en",False,scope={"pages":[20]})
        self.assertTrue(jobs.stops[old["id"]].is_set())
        self.assertEqual(waiting["status"],"stopped")
        self.assertEqual(new["scope"],{"pages":[20]})
        self.assertEqual(json.loads((self.d/"correction-request.json").read_text(encoding="utf-8")),{"pages":[20]})

    def test_cross_page_passage_requires_both_pages_and_unknown_passage_waits(self):
        md = "# Methods\n\nAlpha bravo charlie delta continues across the boundary. Echo foxtrot golf hotel ends here.\n\nUnlocatable text.\n"
        doc = correction.parse(correction.render(md,{}),self.meta)
        pages = ["Alpha bravo charlie delta continues across", "the boundary. Echo foxtrot golf hotel ends here."]
        mapping = scopes.content_pages(doc,pages)
        uid, unknown = list(doc["units"])
        self.assertEqual(mapping[uid],[1,2])
        self.assertEqual(mapping[unknown],[])
        doc["meta"]["correction"] = {"status":"scope-done","checked":[1],"content_pages":mapping}
        self.assertEqual(scopes.generation(doc)["units"],{})
        doc["meta"]["correction"]["checked"] = [1,2]
        view = scopes.generation(doc)
        self.assertEqual(list(view["units"]),[uid])
        self.assertTrue(view["chunks"][0]["scope_partial"])
        self.assertIn("UNCHECKED",view["meta"]["scope_context"])
        self.assertIn("Unlocatable text",view["meta"]["scope_context"])
        self.assertIn("selected-range summary",ladder.prompt_for(view,view["chunks"][0]))

    def test_merged_crops_keep_all_edit_decisions(self):
        edits = [{"box":[.1,.1,.5,.3]},{"box":[.2,.29,.6,.4]},{"box":[.7,.7,.9,.9]}]
        with Image.new("RGB",(100,100)) as image:
            self.assertEqual(len(correction.review_crops(edits,image)),2)

    def test_restoration_request_is_skipped_only_for_already_proposed_number(self):
        result = {"edits":[{"after":r"$$x=y \tag{10}$$"}],"displays":[
            {"number":"10","present":False},{"number":"11","present":False}]}
        self.assertEqual([r["number"] for r in correction.missing_displays(result)],["11"])

    def test_partial_generation_retains_other_layers_and_does_not_regenerate_on_reopen(self):
        doc = store.parsed(PID)
        u1,u2 = list(doc["units"])
        correction._write(self.d,"correction.json",{"status":"scope-done","total":31,"checked":[1],
                         "content_pages":{u1:[1],u2:[2]},"chapters":{}})
        old = {"version":"old","units":{u2:{"keep":"healthy"}},"chunks":{},"edges":[],"incomplete":True}
        store.write(PID,"en",old)
        def build(view,*a,**kw):
            self.assertEqual(set(view["units"]),{u1})
            for u in view["units"].values():
                u["lad"] = ladder.local(u,view["atoms"])
            for c in view["chunks"]:
                c["lad"] = {"take":[],"topic":[]}
        with patch.object(ladder,"build",side_effect=build) as call, patch.object(pipeline.links,"build") as links:
            pipeline.generate(PID,"en",SPEC)
            pipeline.generate(PID,"en",SPEC)
        self.assertEqual(call.call_count,1)
        links.assert_not_called()
        en = store.read(PID,"en")
        self.assertEqual(en["units"][u2],old["units"][u2])
        self.assertTrue(en["incomplete"])
        self.assertTrue(next(iter(en["chunks"].values()))["scope_partial"])

    def test_native_conversion_waits_for_original_pdf_before_queueing(self):
        (self.d/"source.pdf").unlink()
        correction.queue(PID)
        self.assertIsNone(correction.state(PID))

    def test_inflight_comparison_is_a_reusable_proposal_until_its_scope_is_reviewed(self):
        self.pdf(31)
        correction.queue(PID)
        selected = correction.choose(PID,{"kind":"range","ranges":[[1,1]]})
        stop = threading.Event()
        def reply(*a):
            stop.set()
            return {"edits":[],"issues":[]}
        with patch.object(llm_openai,"vision",side_effect=reply):
            with self.assertRaises(llm.Stopped):
                correction.run(PID,SPEC,scope=selected,stop=stop)
        self.assertEqual(correction.state(PID)["checked"],[])
        self.assertTrue((self.d/"correction-proposals/1.json").exists())
        with patch.object(llm_openai,"vision") as call:
            correction.run(PID,SPEC,scope=selected)
            call.assert_not_called()
        self.assertEqual(correction.state(PID)["checked"],[1])
        self.assertEqual(correction.state(PID)["timing"]["reused_comparisons"],[1])

    def test_rejected_restoration_does_not_silently_lose_the_missing_display_number(self):
        correction.queue(PID)
        proposal = {"before":"Broken turbuð Þlent flow.","after":r"$$T=x \tag{4}$$","reason":"Missing label"}
        def reply(prompt,schema,*a):
            if schema is correction.REVIEW:
                if r"\\mathcal" in prompt:
                    return {"decisions":[{"index":0,"verdict":"accept","reason":"Printed calligraphic T and number"}]}
                return {"decisions":[{"index":0,"verdict":"reject","reason":"PDF prints calligraphic T"}]}
            if "Restore ONLY" in prompt:
                return {"edits":[{**proposal,"after":r"$$\mathcal{T}=x \tag{4}$$"}],"issues":[]}
            if "physical PDF page 1" in prompt:
                return {"edits":[proposal],"issues":[],"displays":[{"number":"4","present":False,"box":[0,0,1,1]}]}
            return {"edits":[],"issues":[]}
        with patch.object(llm_openai,"vision",side_effect=reply):
            correction.run(PID,SPEC)
        self.assertIn(r"\mathcal{T}=x \tag{4}",(self.d/"source.md").read_text(encoding="utf-8"))
        self.assertIn("missing-display-recovery",[r["stage"] for r in correction.state(PID)["timing"]["requests"]])

    def test_long_document_repair_endpoint_requests_scope_instead_of_claiming_a_done_job(self):
        self.pdf(100)
        jobs = SimpleNamespace(submit=lambda *a,**kw:self.fail("Unselected long document must not be submitted"))
        httpd = ThreadingHTTPServer(("127.0.0.1",0),server.make_handler(jobs))
        thread = threading.Thread(target=httpd.serve_forever,daemon=True)
        thread.start()
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{httpd.server_port}/api/correction",
                                         data=json.dumps({"paper":PID,"lang":"en"}).encode(),
                                         headers={"Content-Type":"application/json"})
            with urllib.request.urlopen(req) as response:
                got = json.load(response)
            self.assertEqual(got["needs"],"correction-scope")
            self.assertEqual(got["correction"]["total"],100)
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join()

    def test_unrestorable_number_remains_an_explicit_issue_when_no_edit_is_returned(self):
        correction.queue(PID)
        def reply(prompt,*a):
            if "physical PDF page 1" in prompt:
                return {"edits":[],"issues":[],"displays":[{"number":"4","present":False,"box":[0,0,1,1]}]}
            return {"edits":[],"issues":[]}
        with patch.object(llm_openai,"vision",side_effect=reply):
            correction.run(PID,SPEC)
        self.assertTrue(any("Numbered displays still need restoration: 4" in r["text"] for r in correction.state(PID)["issues"]))

    def test_next_page_comparison_waits_for_current_page_independent_review(self):
        correction.queue(PID)
        next_page = threading.Event()
        reviewed = threading.Event()
        def reply(prompt,schema,*a):
            if schema is correction.REVIEW:
                self.assertFalse(next_page.wait(.03),"Next page started during independent review")
                reviewed.set()
                return {"decisions":[{"index":0,"verdict":"accept","reason":"Printed text"}]}
            if "physical PDF page 1" in prompt:
                return {"edits":[{"before":"Broken turbuð Þlent flow.","after":"A turbulent flow.","reason":"PDF"}],"issues":[]}
            next_page.set()
            self.assertTrue(reviewed.is_set(),"Comparison prefetch must remain disabled")
            return {"edits":[],"issues":[]}
        with patch.object(llm_openai,"vision",side_effect=reply):
            correction.run(PID,SPEC)
        self.assertEqual(correction.state(PID)["status"],"done")


if __name__ == "__main__":
    unittest.main()
