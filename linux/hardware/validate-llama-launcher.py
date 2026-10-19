#!/usr/bin/env python3
"""Validate an already-started llama launcher through the authenticated gateway."""
import json
import argparse
import sys
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/generated/llama-migration/integration.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=OUT)
    options = parser.parse_args()
    sys.path.insert(0,str(ROOT/'dsh'))
    from backend_switch import processes
    from amd_device import amd_devices
    from moe_memory import worker_memory
    key = (ROOT / 'dsh/data/network-api.key').read_text().strip()
    models = json.loads((ROOT / 'dsh/models.json').read_text())

    def request(path, body=None, native=False, stream=False):
        headers = {'Content-Type': 'application/json'}
        if not native:
            headers['Authorization'] = 'Bearer ' + key
        req = urllib.request.Request('http://127.0.0.1:' + ('8080' if native else '10000') + path,
                                     None if body is None else json.dumps(body).encode(), headers)
        with urllib.request.urlopen(req, timeout=1200) as response:
            if not stream:
                return json.load(response)
            text = ''
            for line in response:
                line = line.decode().strip()
                if line.startswith('data: ') and line != 'data: [DONE]':
                    for choice in json.loads(line[6:]).get('choices', []):
                        text += choice.get('delta', {}).get('content') or ''
            return text

    rows = {m['id']: m for m in request('/v1/models')['data']}
    assert not any('hyperqwen' in ident for ident in rows)
    results = []
    for model in models:
        ident = model['id']
        print('CHECK', ident, flush=True)
        assert rows[ident]['context_length'] == model['context']
        assert rows[ident]['backend_available']
        base = {'model': ident, 'temperature': 0, 'max_tokens': 128,
                'chat_template_kwargs': {'enable_thinking': False}}
        answer = request('/v1/chat/completions', dict(base, stream=True, messages=[{
            'role': 'user', 'content': 'What is 17 times 19? Reply with only the number.'}]), stream=True)
        assert '323' in answer, (ident, answer)
        messages = [{'role': 'user', 'content': 'Use lookup_inventory for SKU BOLT-42. Do not guess stock.'}]
        tools = [{'type': 'function', 'function': {'name': 'lookup_inventory',
                  'description': 'Look up stock by SKU.', 'parameters': {'type': 'object',
                  'properties': {'sku': {'type': 'string'}}, 'required': ['sku']}}}]
        reply = request('/v1/chat/completions', dict(base, messages=messages, tools=tools))
        message = reply['choices'][0]['message']
        calls = message.get('tool_calls', [])
        assert len(calls) == 1 and calls[0]['function']['name'] == 'lookup_inventory', (ident, message)
        assert json.loads(calls[0]['function']['arguments'])['sku'] == 'BOLT-42'
        messages += [message, {'role': 'tool', 'tool_call_id': calls[0]['id'],
                              'content': '{"sku":"BOLT-42","stock":137}'}]
        reply = request('/v1/chat/completions', dict(base, messages=messages, tools=tools, tool_choice='none'))
        assert '137' in (reply['choices'][0]['message'].get('content') or ''), (ident, reply)
        loaded = [m['id'] for m in request('/v1/models', native=True)['data']
                  if m.get('status', {}).get('value') == 'loaded']
        assert loaded == [ident], loaded
        props = request('/props?model=' + ident, native=True)
        assert props['default_generation_settings']['n_ctx'] == model['context']
        tree = processes()
        workers = {p.pid for p in tree.values() if p.args and p.args[0] in {
            str(ROOT/'llama.cpp/build-hip/bin/llama-server'),
            str(ROOT/'llama.cpp/build-vulkan/bin/llama-server')}}
        assert workers, 'Expected an owned llama.cpp worker'
        for pid in workers:
            group = next(line.split(':',2)[2] for line in Path(f'/proc/{pid}/cgroup').read_text().splitlines() if line.startswith('0::'))
            assert (Path('/sys/fs/cgroup')/group.lstrip('/')/'memory.swap.max').read_text().strip() == '0'
        telemetry = [worker_memory(pid) for pid in workers]
        swap = sum(row[0] for row in telemetry)
        spill = sum(row[1] for row in telemetry)
        assert spill == 0, (ident, spill)
        assert swap == 0, (ident, swap)
        vram = [int((d/'mem_info_vram_used').read_text()) for d in amd_devices()]
        assert len(vram) == 2 and min(vram) > 2*1024**3
        results.append({'model': ident, 'context': model['context'], 'gateway_streaming': True,
                        'tool_roundtrip': True, 'one_loaded_model': True,
                        'nonresident_vram_bytes':spill,'worker_swap_bytes':swap,
                        'worker_scope_swap_max_bytes':0,'gpu_vram_bytes':vram})
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(json.dumps(results, indent=2) + '\n')
        print('PASS', ident, flush=True)


if __name__ == '__main__':
    main()
