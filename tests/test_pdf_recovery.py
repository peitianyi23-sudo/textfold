"""Reachable visual-provider failures and page-localization regressions."""
import unittest
import urllib.error
import threading
from unittest.mock import patch

from textfold import correction, llm, llm_openai, store
from tests.test_correction import SPEC
from tests import test_correction as fixtures


class RecoveryTests(unittest.TestCase):
    def test_transient_image_500_retries_the_same_image_request(self):
        failed = urllib.error.HTTPError("http://127.0.0.1:10531/v1/responses",500,"temporary bridge failure",{},None)
        done = {"status":"completed","output":[{"content":[{"type":"output_text", "text":
                '{"edits": [], "issues": [], "displays": []}'}]}]}
        with patch.object(llm_openai,"_post",side_effect=[failed,done]) as post, patch.object(llm_openai.time,"sleep"):
            result = llm_openai.vision("Check original page",correction.SCHEMA,SPEC,[b"original PDF image"])
        self.assertEqual(result["edits"],[])
        self.assertEqual(post.call_count,2)
        self.assertEqual(post.call_args_list[0],post.call_args_list[1])

    def test_distant_repeated_four_word_phrase_does_not_expand_page_to_whole_document(self):
        opening = "The measured velocity field decays through nonlinear strain and transport across length scales."
        main = "The rotating experiment records a distinct vertical correlation and an anisotropic transfer spectrum."
        repeated = "spectral energy transfer measured experimentally"
        middle = "\n\n".join("Unrelated extraction about boundary conditions and spectral resolution " + str(i) for i in range(90))
        ending = repeated + " the acoustic measurement gives a separate result."
        text = opening+"\n\n"+main+"\n\n"+middle+"\n\n"+ending
        page = main + " " + repeated
        a,b = correction.page_ranges(text,[page])[0]
        self.assertIn(main,text[a:b])
        self.assertNotIn(ending,text[a:b])

    def test_stop_during_retry_wait_does_not_send_another_image_request(self):
        stop = threading.Event()
        failed = urllib.error.HTTPError("http://127.0.0.1:10531/v1/responses",500,"temporary",{},None)
        with patch.object(llm_openai,"_post",side_effect=failed) as post:
            with self.assertRaises(llm.Stopped):
                llm_openai.vision("Check page",correction.SCHEMA,SPEC,[b"PDF image"],stop=stop,
                                  on_retry=lambda *a:stop.set())
        self.assertEqual(post.call_count,1)


class ProposalReuseTests(unittest.TestCase):
    setUp = fixtures.CorrectionTests.setUp
    tearDown = fixtures.CorrectionTests.tearDown

    def test_smaller_unchanged_context_reuses_proposal_but_still_verifies_every_edit(self):
        pid = fixtures.PID
        correction.queue(pid)
        proposals = self.d/"correction-proposals"
        proposals.mkdir()
        edit = {"before":"Broken turbuð Þlent flow.","after":"A turbulent flow.","reason":"PDF"}
        correction._write(proposals,"1.json",{"local":"Extra outside context\n\n"+self.md,
                                             "result":{"edits":[edit],"issues":[],"displays":[]}})
        def reply(prompt,schema,*a,**kw):
            self.assertIs(schema,correction.REVIEW)
            return {"decisions":[{"index":0,"verdict":"accept","reason":"Printed text"}]}
        with patch.object(llm_openai,"vision",side_effect=reply) as call:
            correction.run(pid,SPEC,scope=correction.choose(pid,{"kind":"range","ranges":[[1,1]]}))
        self.assertEqual(call.call_count,1)
        self.assertEqual(correction.state(pid)["timing"]["reused_comparisons"],[1])
        self.assertIn("A turbulent flow.",(store.pdir(pid)/"source.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
