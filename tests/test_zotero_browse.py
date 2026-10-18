"""Browse latency regressions; attachments keep the serial _all contract."""
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from textfold import zotero


class BrowseTest(unittest.TestCase):
    def test_default_address_avoids_localhost_fallback(self):
        with patch('textfold.models.load_settings', return_value={}):
            self.assertEqual(zotero.settings()['base'], 'http://127.0.0.1:23119')
        with patch('textfold.models.load_settings', return_value={'zotero': {'base': 'http://custom:1234'}}):
            self.assertEqual(zotero.settings()['base'], 'http://custom:1234')

    def test_browse_pages_overlap_but_remain_ordered(self):
        active, peak = 0, 0
        lock = threading.Lock()
        def get(path, params):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(active, peak)
            time.sleep(.05)
            with lock:
                active -= 1
            return list(range(params['start'], min(params['start'] + 100, 450))), {'Total-Results': '450'}
        with patch.object(zotero, '_get', side_effect=get):
            self.assertEqual(zotero._browse_all('users/0/items/top'), list(range(450)))
        self.assertGreater(peak, 1)
        self.assertLessEqual(peak, 3)

    def test_identical_inflight_browse_is_shared_and_failure_retries(self):
        calls = []
        def get(path, params):
            calls.append(path)
            time.sleep(.05)
            return [1], {'Total-Results': '1'}
        with patch.object(zotero, '_get', side_effect=get), ThreadPoolExecutor(2) as pool:
            results = list(pool.map(lambda _: zotero._browse_all('users/0/collections'), range(2)))
        self.assertEqual(results, [[1], [1]])
        self.assertEqual(len(calls), 1)
        with patch.object(zotero, '_get', side_effect=zotero.Off('not-running')):
            with self.assertRaises(zotero.Off):
                zotero._browse_all('users/0/collections')
        with patch.object(zotero, '_get', return_value=([2], {})):
            self.assertEqual(zotero._browse_all('users/0/collections'), [2])

    def test_attachment_enumeration_still_fetches_serially(self):
        starts = []
        def get(path, params):
            starts.append(params['start'])
            return [params['start']], {'Total-Results': '201'}
        with patch.object(zotero, '_get', side_effect=get):
            self.assertEqual(zotero._all('users/0/items/ARXVKEY2/children'), [0, 100, 200])
        self.assertEqual(starts, [0, 100, 200])

    def test_search_uses_zotero_whole_library_even_with_a_collection(self):
        with patch.object(zotero, '_browse_all', return_value=[]) as browse:
            self.assertEqual(zotero.items('users/0', 'TPCLKEY2', 'turbulence'), [])
        browse.assert_called_once_with('users/0/items/top', {'q':'turbulence', 'qmode':'titleCreatorYear'})

    def test_collection_refresh_failure_is_not_an_empty_success(self):
        with patch.object(zotero, '_get', side_effect=zotero.Off('not-running')):
            with self.assertRaises(zotero.Off):
                zotero.collections('users/0')
