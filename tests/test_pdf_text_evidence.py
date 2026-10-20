import unittest
from tests import test_correction as fixtures
from unittest.mock import patch
from textfold import targeted, correction, llm, llm_openai


class EvidenceTests(unittest.TestCase):
    def test_source_question_retains_the_complete_formula_and_contour_caption(self):
        text = 'Intro.\n\nSpectrum $\\bar{E}(k)=\\epsilon^{273} k^{-5/3}$ follows.\n\nCaption ' + 'levels ' * 100 + '$4.4, 0.32, 0.32$.\n\nEnd.'
        candidate = targeted.candidate_unit(text, {'before': '\\epsilon^{273}'})
        self.assertEqual(candidate['before'], '$\\bar{E}(k)=\\epsilon^{273} k^{-5/3}$')
        context = targeted.candidate_context(text, [{'before': 'Caption'}])
        self.assertIn('$4.4, 0.32, 0.32$', context)

    def test_cross_page_mineru_paragraph_does_not_pin_tail_question_to_first_page(self):
        before = 'dimensionless lattice parameter l, with $\\lambda \\cong 0.17$'
        text = 'The initial condition begins on page one, approximately 6% of the ' + before
        layout = [{'p': 1, 'b': [.5, .8, .9, .9], 't': text}]
        pages = ['The initial condition begins on page one.',
                 'approximately 6% of the dimensionless lattice parameter lambda, with lambda = 0.17']
        candidate = targeted.source_candidate({'before': before, 'reason': 'Greek/Latin variant'}, text, layout, pages)
        self.assertEqual(candidate['page'], 2)
        self.assertEqual(candidate['block'], -1)

    def test_repeated_anchor_on_one_page_is_not_unique_on_another(self):
        before = '$\\bar{k}^{-3}$'
        text = 'with periodic boundary conditions ' + before
        layout = [{'p': 2, 'b': [.5, .4, .9, .5], 't': text}]
        pages = ['', 'with periodic boundary conditions and with periodic boundary conditions',
                 '', 'with periodic boundary conditions']
        candidate = targeted.source_candidate({'before': before, 'reason': 'spurious bar'}, text, layout, pages)
        self.assertEqual(candidate['page'], 2)
        self.assertEqual(candidate['block'], 0)

    def test_caption_question_retains_all_legend_entries_and_parentheses(self):
        caption = '<figcaption>FIG. 4. Legend (<span class="math inline">-- + --</span> for 5000, ' + \
                  '<span class="math inline">broken</span> for 10000, -- * -- for 20000).</figcaption>'
        candidate = targeted.candidate_unit('Intro.\n\n' + caption, {'before': 'broken'})
        self.assertEqual(candidate['before'], caption)

    def test_distant_candidates_do_not_include_intervening_document(self):
        text = 'First $x$ passage.\n\n' + 'Unrelated paragraph.\n\n' * 200 + 'Last $y$ passage.'
        context = targeted.candidate_context(text, [{'before': 'First $x$ passage.'},
                                                   {'before': 'Last $y$ passage.'}])
        self.assertLess(len(context), 2000)
        self.assertIn('First $x$', context)
        self.assertIn('Last $y$', context)

    def test_native_character_placement_is_retained_without_image_render(self):
        import tempfile
        from pathlib import Path
        from reportlab.pdfgen import canvas
        import pypdfium2 as pdfium
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'source.pdf'
            cv = canvas.Canvas(str(path), pagesize=(600, 800))
            cv.drawString(72, 700, 'The energy spectrum is E(k) = k')
            cv.setFont('Helvetica', 8)
            cv.drawString(245, 705, '-5/3')
            cv.save()
            candidate = {'id': 0, 'page': 1, 'block': -1, 'before': 'energy spectrum',
                         'anchor': 'The energy spectrum is'}
            with pdfium.PdfDocument(str(path)) as pdf:
                evidence = targeted.text_evidence(pdf, [candidate], [])
        self.assertEqual(len(evidence), 1)
        self.assertIn('-5/3', str(evidence))
        self.assertTrue(evidence[0]['readable'])
        runs = evidence[0]['runs']
        self.assertTrue(any(r['size'] == 8 and r['y'] == 705 for r in runs))


class PipelineEvidenceTests(unittest.TestCase):
    setUp = fixtures.CorrectionTests.setUp
    tearDown = fixtures.CorrectionTests.tearDown

    def test_numeric_repair_from_source_text_needs_no_images_or_second_review(self):
        from reportlab.pdfgen import canvas
        cv = canvas.Canvas(str(self.d/'source.pdf'), pagesize=(600, 800))
        cv.drawString(72, 700, 'The original turbulent flow has value 12.')
        cv.save()
        screen = {'candidates': [{'before': 'Broken turbuð Þlent flow.', 'page': 1,
                  'anchor': 'The original turbulent flow', 'reason': 'damaged value'}], 'edits': [], 'issues': []}
        edit = {'before': 'Broken turbuð Þlent flow.', 'after': 'The turbulent flow has value 12.',
                'candidate': 0, 'page': 1, 'reason': 'Literal source says value 12'}
        result = {'edits': [edit], 'decisions': [{'candidate': 0, 'verdict': 'corrected', 'reason': 'literal 12'}],
                  'issues': [], 'displays': []}
        correction.queue(fixtures.PID)
        with patch.object(llm, 'call', side_effect=[({'out': screen}, False), ({'out': result}, False)]) as call, \
                patch.object(llm_openai, 'vision') as vision:
            correction.run(fixtures.PID, fixtures.SPEC)
        vision.assert_not_called()
        self.assertEqual(call.call_count, 2)
        self.assertEqual(correction.state(fixtures.PID)['done'], 1)
        self.assertIn('value 12', (self.d/'source.md').read_text(encoding='utf-8'))

    def test_unmapped_source_question_uses_image_in_the_existing_decision(self):
        screen = {'candidates': [{'before': 'Broken turbuð Þlent flow.', 'page': 1,
                  'anchor': 'The original turbulent flow', 'reason': 'ambiguous glyph'}], 'edits': [], 'issues': []}
        result = {'edits': [], 'decisions': [{'candidate': 0, 'verdict': 'unresolved',
                  'reason': 'unmapped glyph'}], 'issues': [], 'displays': []}
        native = [{'candidate': 0, 'page': 1, 'readable': False, 'box': [10, 10, 200, 50],
                   'runs': [{'text': '\x01', 'x': 10, 'y': 20, 'size': 10,
                             'unmapped': True, 'font': 'MathematicalPi-One'}]}]
        edit = {'before': 'Broken turbuð Þlent flow.', 'after': 'The turbulent flow.',
                'candidate': 0, 'page': 1, 'reason': 'literal image'}
        correction.queue(fixtures.PID)
        result = {'edits': [edit], 'decisions': [{'candidate': 0, 'verdict': 'corrected',
                  'reason': 'literal image'}], 'issues': [], 'displays': []}
        with patch.object(targeted, 'text_evidence', return_value=native), \
                patch.object(llm, 'call', return_value=({'out': screen}, False)) as call, \
                patch.object(llm_openai, 'vision', return_value=result) as vision:
            correction.run(fixtures.PID, fixtures.SPEC)
        self.assertEqual(call.call_count, 1)  # full text screening only
        self.assertIn('NOT evidence', vision.call_args.args[0])
        self.assertEqual(vision.call_count, 1)
        self.assertTrue(vision.call_args.args[3][0].startswith(b'\x89PNG'))
        self.assertIn('The turbulent flow.', (self.d/'source.md').read_text(encoding='utf-8'))

    def test_readable_unresolved_gets_only_its_local_image_followup(self):
        from reportlab.pdfgen import canvas
        cv = canvas.Canvas(str(self.d/'source.pdf'), pagesize=(600, 800))
        cv.drawString(72, 700, 'The original turbulent flow has value 12.')
        cv.save()
        screen = {'candidates': [{'before': 'Broken turbuð Þlent flow.', 'page': 1,
                  'anchor': 'The original turbulent flow', 'reason': 'unclear exponent'}], 'edits': [], 'issues': []}
        uncertain = {'edits': [], 'decisions': [{'candidate': 0, 'verdict': 'unresolved',
                     'reason': 'placement does not establish identity'}], 'issues': [], 'displays': []}
        done = {'edits': [], 'decisions': [{'candidate': 0, 'verdict': 'correct',
                'reason': 'printed variant'}], 'issues': [], 'displays': []}
        correction.queue(fixtures.PID)
        with patch.object(llm, 'call', side_effect=[({'out': screen}, False), ({'out': uncertain}, False)]) as call, \
                patch.object(llm_openai, 'vision', return_value=done) as vision:
            correction.run(fixtures.PID, fixtures.SPEC)
        self.assertEqual(call.call_count, 2)
        self.assertEqual(vision.call_count, 1)
        self.assertEqual((self.d/'source.md').read_text(encoding='utf-8'), self.md)

    def test_mixed_evidence_uses_one_decision_and_images_only_for_faulty_mapping(self):
        screen = {'candidates': [
            {'before': 'Broken turbuð Þlent flow.', 'page': 1, 'anchor': '', 'reason': 'value'},
            {'before': 'A healthy paragraph with $x+y$.', 'page': 2, 'anchor': '', 'reason': 'symbol'}],
            'edits': [], 'issues': []}
        native = [dict(candidate=i, page=i+1, readable=i == 0, box=[10, 10, 200, 50], runs=[
            dict(text='12' if i == 0 else '\x01', x=10, y=20, size=10, unmapped=i == 1)]) for i in range(2)]
        done = {'edits': [], 'issues': [], 'displays': [], 'decisions': [
            dict(candidate=i, verdict='correct', reason='literal source') for i in range(2)]}
        correction.queue(fixtures.PID)
        with patch.object(targeted, 'text_evidence', return_value=native), \
                patch.object(llm, 'call', return_value=({'out': screen}, False)) as call, \
                patch.object(llm_openai, 'vision', return_value=done) as vision:
            correction.run(fixtures.PID, fixtures.SPEC)
        self.assertEqual(call.call_count, 1)
        self.assertEqual(vision.call_count, 1)
        self.assertEqual(len(vision.call_args.args[3]), 1)
        prompt = vision.call_args.args[0]
        self.assertIn('"candidate": 0', prompt)
        self.assertIn('"candidate": 1', prompt)
        self.assertIn('"candidates": [1]', prompt)

    def test_later_image_failure_resumes_only_unresolved_question(self):
        screen = {'candidates': [
            {'before': 'Broken turbuð Þlent flow.', 'page': 1, 'anchor': '', 'reason': 'word'},
            {'before': 'A healthy paragraph with $x+y$.', 'page': 2, 'anchor': '', 'reason': 'symbol'}],
            'edits': [], 'issues': []}
        native = [dict(candidate=i, page=i+1, readable=True, box=[10, 10, 200, 50], runs=[
            dict(text='printed', x=10, y=20, size=10, unmapped=False)]) for i in range(2)]
        result = {'edits': [{'before': 'Broken turbuð Þlent flow.', 'after': 'The turbulent flow.',
                  'reason': 'literal', 'candidate': 0, 'page': 1}], 'issues': [], 'displays': [],
                  'decisions': [dict(candidate=0, verdict='corrected', reason='word'),
                                dict(candidate=1, verdict='unresolved', reason='needs image')]}
        correction.queue(fixtures.PID)
        with patch.object(targeted, 'text_evidence', return_value=native), \
                patch.object(llm, 'call', side_effect=[({'out': screen}, False), ({'out': result}, False)]), \
                patch.object(llm_openai, 'vision', side_effect=RuntimeError('provider')):
            with self.assertRaisesRegex(RuntimeError, 'provider'):
                correction.run(fixtures.PID, fixtures.SPEC)
        done = {'edits': [], 'issues': [], 'displays': [], 'decisions': [
            dict(candidate=1, verdict='correct', reason='printed original')]}
        with patch.object(llm, 'call') as call, \
                patch.object(llm_openai, 'vision', return_value=done) as vision:
            correction.run(fixtures.PID, fixtures.SPEC)
        call.assert_not_called()
        self.assertEqual(vision.call_count, 1)
        self.assertIn('"candidates": [1]', vision.call_args.args[0])
        self.assertIn('The turbulent flow.', (self.d/'source.md').read_text(encoding='utf-8'))
        self.assertEqual(correction.state(fixtures.PID)['edits'], 1)

    def test_pdf_text_stage_keeps_caption_relocation_atomic(self):
        text = self.md + '\nFIG. 1. Complete caption.\n'
        work = {'text': text, 'issues': []}
        edits = [{'before': 'FIG. 1. Complete caption.', 'after': '', 'reason': 'move later'}]
        blocked = targeted.apply_edits(work, edits, self.d, 1)
        self.assertEqual(blocked, edits)
        self.assertEqual(work['text'], text)

    def test_observed_partial_contour_tail_cannot_splice_two_decimal_values(self):
        text = self.md + '\nLevels $4.4, 0 . 3 2 , 0 . 3 2 , 0 . 3 2 , 0 . 5 2$.\n'
        work = {'text': text, 'issues': []}
        edit = {'before': ', 0 . 3 2 , 0 . 3 2 , 0', 'after': ', 0 . 3 2',
                'reason': 'remove repeated tail'}
        blocked = targeted.apply_edits(work, [edit], self.d, 7)
        self.assertEqual(blocked, [edit])
        self.assertEqual(work['text'], text)


if __name__ == '__main__':
    unittest.main()
