#!/usr/bin/env python3
"""Check API auth/catalogs; --generate also checks Q3 SDK streaming and tools."""
import argparse
import json
from datetime import datetime
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--generate', action='store_true')
parser.add_argument('--output', type=Path, help='Optional JSON report; no file is written by default')
args = parser.parse_args()
from gateway import catalog
expected_catalog = catalog()
config = json.loads((ROOT / 'dsh/data/network-access.json').read_text())
key = Path(config['key_file']).read_text().strip()
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
model = 'qwen3.8-flash-next-iq3_xxs'
expected_context = json.loads((ROOT / 'dsh/strata-profiles.json').read_text())[model]['context']
labels = dict(zip(config['listen'], ('loopback', 'lan', 'tailscale')))
result = {'date': datetime.now().astimezone().isoformat(), 'auth_and_catalog': {}, 'generation': {},
          'remote_peer_tested': False, 'no_performance_benchmark': True}


def request(address, path, body=None, auth=key):
    req = urllib.request.Request(f'http://{address}:{config["port"]}' + path,
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json',
                                          **({'Authorization': 'Bearer ' + auth} if auth else {})})
    with opener.open(req, timeout=20) as response:
        return json.load(response)


for address in config['listen']:
    for auth in (None, 'wrong-key'):
        try:
            request(address, '/v1/models', auth=auth)
            raise AssertionError('Unauthenticated or wrong-key request accepted')
        except urllib.error.HTTPError as error:
            assert error.code == 401
    data = request(address, '/v1/models')
    ids = [m['id'] for m in data['data']]
    assert len(ids) == len(set(ids)) and set(ids) == set(expected_catalog), 'API catalog differs from enabled local profiles'
    assert all(m['context_length'] == expected_catalog[m['id']]['context_length'] for m in data['data']), 'Context metadata mismatch'
    assert model in ids and not any('iq2_xs' in m for m in ids)
    try:
        request(address, '/v1/models/qwen3.8-flash-next-iq2_xs')
        raise AssertionError('Retired Q2 accepted')
    except urllib.error.HTTPError as error:
        assert error.code == 404
    health = request(address, '/health')
    assert health['status'] == 'ok'
    result['auth_and_catalog'][labels[address]] = {'unauthenticated_401': True, 'wrong_key_401': True,
                                         'catalog_count': len(ids), 'q2_rejected': True,
                                         'health_ok': True, 'available_models': sorted(m['id'] for m in data['data'] if m.get('backend_available'))}

if args.generate:
    from openai import OpenAI
    deadline = time.monotonic() + 600
    while True:
        data = request('127.0.0.1', '/v1/models')
        if any(m['id'] == model and m['backend_available'] for m in data['data']):
            break
        if time.monotonic() > deadline:
            raise TimeoutError('Strata Q3 did not become ready')
        time.sleep(3)
    for address in config['listen']:
        # The HTTP client bypasses unrelated proxy environment settings.
        import httpx
        client = OpenAI(base_url=f'http://{address}:{config["port"]}/v1', api_key=key, timeout=600,
                        http_client=httpx.Client(trust_env=False))
        assert model in [m.id for m in client.models.list().data]
        stream = client.chat.completions.create(
            model=model, messages=[{'role': 'user', 'content': 'Reply with only NETWORK_API_OK.'}],
            max_tokens=64, temperature=0, stream=True,
            extra_body={'chat_template_kwargs': {'enable_thinking': False}})
        text = ''.join(c.choices[0].delta.content or '' for c in stream if c.choices)
        assert 'NETWORK_API_OK' in text, 'Streaming response check failed'
        result['generation'][labels[address]] = {'openai_sdk_models': True, 'streaming_passed': True}
        client.close()
    client = OpenAI(base_url=f'http://{config["listen"][1]}:{config["port"]}/v1', api_key=key, timeout=600,
                    http_client=httpx.Client(trust_env=False))
    tools = [{'type': 'function', 'function': {'name': 'get_test_value',
             'description': 'Get a test value', 'parameters': {'type': 'object',
             'properties': {'key': {'type': 'string'}}, 'required': ['key']}}}]
    prompt = {'role': 'user', 'content': 'Call get_test_value with key alpha.'}
    answer = client.chat.completions.create(model=model, messages=[prompt], tools=tools,
                                            tool_choice='required', max_tokens=128, temperature=0,
                                            extra_body={'chat_template_kwargs': {'enable_thinking': False}})
    message = answer.choices[0].message
    call = message.tool_calls[0]
    assert call.function.name == 'get_test_value'
    assert json.loads(call.function.arguments) == {'key': 'alpha'}
    followup = client.chat.completions.create(model=model, messages=[prompt,
        message.model_dump(exclude_none=True), {'role': 'tool', 'tool_call_id': call.id,
        'content': '{"value":"NETWORK_TOOL_OK_731"}'}], max_tokens=64, temperature=0,
        extra_body={'chat_template_kwargs': {'enable_thinking': False}})
    assert 'NETWORK_TOOL_OK_731' in followup.choices[0].message.content
    result['tool_call_and_result'] = True
    client.close()
    with urllib.request.urlopen('http://127.0.0.1:30021/health', timeout=10) as response:
        health = json.load(response)
    assert health['loaded'] and health['model'] == model and health['max_context'] == expected_context
    result['strata_health'] = {k: health[k] for k in ('loaded', 'model', 'max_context')}

if args.output:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
