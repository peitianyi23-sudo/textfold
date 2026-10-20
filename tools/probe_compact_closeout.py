"""Replay only the three saved Clercx failures; never screen or benchmark a paper."""
import argparse
import copy
import difflib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from textfold import correction, llm, llm_openai, models, store, targeted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'run'])
    parser.add_argument('--label', default='local-closeout-20261020')
    args = parser.parse_args()
    evidence_root = ROOT/'launch/sol-compact-correction'
    output = evidence_root/args.label
    pid = 'pdf-0000000000002951'
    source = next((evidence_root/'inputs').rglob(pid))
    if args.action == 'prepare':
        output.mkdir(exist_ok=False)
    store.DATA = output
    folder = store.pdir(pid)
    if args.action == 'prepare':
        shutil.copytree(source, folder)
        correction.queue(pid)
    spec = models.resolve('gpt-6.1-sol')
    spec['effort'] = 'medium'
    assert spec['kind'] == 'api' and spec['base'] == 'http://127.0.0.1:10531/v1'
    (output/'config.json').write_text(json.dumps({k: spec[k] for k in
        ['id', 'kind', 'base', 'model', 'effort']}, indent=2), encoding='utf-8')

    saved = next((evidence_root/'sol-new').rglob(pid))
    screen = next(json.loads(p.read_text(encoding='utf-8'))['out']
        for p in (saved/'llm-cache').glob('*.json')
        if 'candidates' in json.loads(p.read_text(encoding='utf-8'))['out'])
    selected = [copy.deepcopy(next(x for x in screen['candidates'] if x['block'] == block))
                for block in [2, 24, 38]]
    # Exercise images for these supplied failures, without changing the application default.
    for candidate in selected:
        candidate['image_required'] = True
    original_call, original_vision, original_post = llm.call, llm_openai.vision, llm_openai._post

    def replay_screen(prompt, schema, *a, **kw):
        if schema is targeted.SCREEN:
            return {'out': {'edits': [], 'candidates': selected, 'issues': []}}, True
        return original_call(prompt, schema, *a, **kw)

    calls = []

    def captured_vision(prompt, schema, model, images, **kw):
        call = len(calls)+1
        (output/f'{args.action}-request-{call}.txt').write_text(prompt, encoding='utf-8')
        for i, png in enumerate(images, 1):
            (output/f'{args.action}-request-{call}-image-{i}.png').write_bytes(png)
        calls.append({'images': len(images), 'image_bytes': sum(map(len, images))})
        if args.action == 'prepare':
            raise llm.Stopped()
        return original_vision(prompt, schema, model, images, **kw)

    attempts = []

    def captured_post(url, body, headers, timeout):
        rec = {'model': body['model'], 'route': url.rsplit('/', 1)[-1],
               'effort': (body.get('reasoning') or {}).get('effort') or body.get('reasoning_effort'),
               'wire_bytes': len(json.dumps(body).encode())}
        try:
            result = original_post(url, body, headers, timeout)
            rec.update(usage=result.get('usage'), response=result)
            return result
        except Exception as exc:
            rec['error'] = type(exc).__name__
            raise
        finally:
            attempts.append(rec)
            (output/f'{args.action}-http.json').write_text(json.dumps(attempts, indent=2), encoding='utf-8')

    llm.call, llm_openai.vision, llm_openai._post = replay_screen, captured_vision, captured_post
    try:
        targeted.run(pid, spec, progress=lambda *v: print(*v, flush=True))
    except llm.Stopped:
        if args.action != 'prepare':
            raise
    finally:
        llm.call, llm_openai.vision, llm_openai._post = original_call, original_vision, original_post
    work = json.loads((folder/'targeted-work.json').read_text(encoding='utf-8'))
    candidates = work['candidates']
    assert len(candidates) == 3
    assert candidates[0]['source_blocks'] == [0, 1, 2]
    assert candidates[1]['page'] == 2 and candidates[1]['block'] == 24
    assert candidates[2]['before'].startswith('<figcaption>')
    if args.action == 'prepare':
        assert not attempts
        print('Prepared the three production evidence regions; no model call.', flush=True)
        return

    original = (source/'source.md').read_text(encoding='utf-8')
    final = (folder/'source.md').read_text(encoding='utf-8')
    history = [h for h in work['history'] if h.get('stage') == 'pdf-source']
    edits = [e for h in history for e in h['edits']]
    # Every changed byte must belong to one of the three actual supplied questions.
    for edit in edits:
        assert edit['before'] in candidates[edit['candidate']]['before']
    replay = original
    for edit in edits:
        replay = correction.patches(replay, [edit])
    assert final == replay
    assert all(a['model'] == 'gpt-6.1-sol' and a['effort'] == 'medium' for a in attempts)
    (output/'source.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True), final.splitlines(True),
        fromfile='saved-original/source.md', tofile='three-case/source.md')), encoding='utf-8')
    (output/'result.json').write_text(json.dumps({'state': correction.state(pid), 'calls': calls,
        'edits': edits, 'issues': work['issues'], 'unchanged_outside_questions': True},
        ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'edits': edits, 'issues': work['issues']}, ensure_ascii=False, indent=1), flush=True)


if __name__ == '__main__':
    main()
