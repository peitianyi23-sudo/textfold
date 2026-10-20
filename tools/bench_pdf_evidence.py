"""Isolated two-paper paired correction measurement; never writes producer caches."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from textfold import correction, llm_openai, models, store, targeted, zotero_cache


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('version', choices=['baseline', 'new'])
    parser.add_argument('--label', help='Fresh output directory, e.g. final; never overwrites a run')
    parser.add_argument('--effort', choices=['medium'])
    parser.add_argument('--small', action='store_true')
    parser.add_argument('--paper', choices=['3506', '2951'])
    args = parser.parse_args()
    output = ROOT / 'launch/sol-compact-correction' / (args.label or args.version)
    output.mkdir(parents=True, exist_ok=False)
    store.DATA = output
    module = targeted
    if args.version == 'baseline':
        spec = importlib.util.spec_from_file_location('textfold.baseline_targeted', output.parent / 'baseline_targeted.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    spec = models.resolve('gpt-6.1-sol')
    spec['effort'] = 'medium'
    if args.effort:
        spec['effort'] = args.effort
    assert spec['kind'] == 'api' and spec['base'] == 'http://127.0.0.1:10531/v1'
    (output/'config.json').write_text(json.dumps({k: spec[k] for k in ['id','kind','base','model','effort']}, indent=2))
    source = Path('C:/Users/admin/agent-native/textfold/launch/mineru-cloud-reparse-20261020/after')
    storage = Path('D:/Paper/Zotero lib/storage')
    samples = [('3506', 'MLMPBK65', 'Energy and enstrophy fluxes in the double cascade of two-dimensional turbulence'),
               ('2951', '4I6IB88E', 'Energy Spectra for Decaying 2D Turbulence in a Bounded Domain')]
    post = llm_openai._post
    attempts = []
    def measured(url, body, headers, timeout):
        rec = {'wire_bytes': len(json.dumps(body).encode()), 'model': body['model'],
               'effort': body.get('reasoning', {}).get('effort') or body.get('reasoning_effort'), 'thinking': body.get('thinking')}
        now = time.perf_counter()
        try:
            result = post(url, body, headers, timeout)
            rec['usage'] = result.get('usage')
            rec['response'] = result
            rec['request_text'] = body.get('messages') or [{**x, 'content': [c for c in x['content'] if c.get('type') != 'input_image']} for x in body.get('input', [])]
            rec['route'] = url.rsplit('/', 1)[-1]
            message = result.get('choices', [{}])[0].get('message', {})
            answer = message.get('content') or ''.join(c.get('text', '') for o in result.get('output', [])
                for c in o.get('content', []) if c.get('type') == 'output_text')
            rec['output_chars'] = len(answer)
            if 'reasoning_content' in message:
                rec['reasoning_chars'] = len(message['reasoning_content'] or '')
            return result
        except Exception as exc:
            rec['error'] = type(exc).__name__ + ': ' + str(getattr(exc, 'code', ''))
            raise
        finally:
            rec['seconds'] = time.perf_counter() - now
            attempts.append(rec)
            (output / 'http.json').write_text(json.dumps(attempts, indent=2), encoding='utf-8')
    llm_openai._post = measured
    for n, (attachment, key, title) in enumerate(samples):
        if args.paper and args.paper != attachment:
            continue
        pid = 'pdf-' + attachment.zfill(16)
        pdf = next((storage / key).glob('*.pdf'))
        folder = source / attachment
        blocks = zotero_cache.read_json(folder / 'content_list.json')
        zotero_cache.save(pid, (folder, blocks), pdf, title)
        if args.small:
            import re
            path = store.pdir(pid)/'source.md'
            text = path.read_text(encoding='utf-8')
            layout = json.loads((store.pdir(pid)/'layout.json').read_text(encoding='utf-8'))
            patterns = [r'273|2 7 3|bar.*?E|4.*?4.*?0.*?3.*?2|e.*?,.*?r.*?tag',
                        r'Rutgers|rescaled|lambda|0.*?17|ESF']
            candidates = []
            for block, item in enumerate(layout):
                if re.search(patterns[n], item['t'], re.I) and item['t'] in text:
                    candidates.append({'before': item['t'], 'page': item['p'], 'block': block,
                        'anchor': '', 'reason': 'Check all printed symbols, exponent, or complete list literally.'})
            if attachment == '2951':
                import fitz
                with fitz.open(pdf) as original:
                    pages = [p.get_text() for p in original]
                candidates = []
                for start, end in [('Recently, Rutgers', '\n\n'), ('The time t is defined', '\n\n'),
                                   ('dimensionless lattice parameter', '. A smoothing'), ('ESF-TAO', '13')]:
                    a = text.index(start)
                    b = text.index(end, a) + (len(end) if end != '\n\n' else 0)
                    before = text[a:b]
                    candidate = targeted.source_candidate({'before': before, 'reason':
                        'Verify every symbol in this original passage; preserve printed author notation.'}, text, layout, pages)
                    assert candidate, start
                    candidates.append(candidate)
            assert candidates, 'Fixed real-source questions not located'
            (store.pdir(pid)/'targeted-work.json').write_text(json.dumps({'text': text, 'candidates': candidates,
                'history': [], 'issues': [], 'completed': []}, ensure_ascii=False), encoding='utf-8')
        first = len(attempts)
        now = time.perf_counter()
        print(args.version, attachment, 'start', flush=True)
        try:
            module.run(pid, spec, progress=lambda *v: print(attachment, *v, flush=True))
        finally:
            record = {'attachment': attachment, 'snapshot': str(folder), 'pdf': str(pdf),
                      'wall_seconds': time.perf_counter()-now, 'attempts': attempts[first:],
                      'state': correction.state(pid)}
            (output / (attachment + '.json')).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
        print(args.version, attachment, record['wall_seconds'], flush=True)


if __name__ == '__main__':
    main()
