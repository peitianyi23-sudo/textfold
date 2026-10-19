import unittest
from textfold import build, correction, ladder
from textfold.parse import parse

class CompletedBannerTests(unittest.TestCase):
 def test_complete_check_has_no_overlay_even_with_retained_observations(self):
  for status in ['done','stopped','error','awaiting-scope','scope-done']:
   doc=parse(correction.render('# Result\n\nA result.',{}),{'id':'pdf-0123456789abcdef','title':'Result','html_url':'https://example.org/paper','correction':{'status':status,'issues':[{'text':'Retained observation'}]}})
   for u in doc['units'].values():u['lad']=ladder.local(u,doc['atoms'])
   html=build.page(doc,app=True)
   self.assertEqual('aria-label="PDF 校对"' in html,status!='done')

if __name__=='__main__':unittest.main()

