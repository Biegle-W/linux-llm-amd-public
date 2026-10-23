#!/usr/bin/env python3
"""Validate an already running native UI; never loads or stops a worker."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=['strata', 'maya'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    port = 30021 if args.kind == 'strata' else 30031
    project = ROOT / ('strata' if args.kind == 'strata' else 'maya/upstream')
    base = f'http://127.0.0.1:{port}'
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def get(path):
        with opener.open(base + path, timeout=30) as response:
            return response.read()

    health = json.loads(get('/health'))
    assert health['status'] == 'ok'
    assert health.get('loaded', True) and not health.get('unloaded', False)
    html = get('/')
    expected_html = (project / 'serve/web/index.html').read_bytes()
    if args.kind == 'maya':
        expected_html = expected_html.replace(
            b'</body>', b'<script src="/managed/model-switch.js" defer></script></body>')
        assert get('/managed/model-switch.js') == (ROOT / 'dsh/maya-model-switch.js').read_bytes()
        managed = json.loads(get('/managed/models'))
        assert isinstance(managed, dict)
    assert html == expected_html
    assets = sorted({asset.split('#', 1)[0].split('?', 1)[0] for asset in re.findall(r'(?:src|href)=["\']((?:/)?web/[^"\']+)', html.decode())})
    assert assets
    for asset in assets:
        body = get('/' + asset.lstrip('/'))
        assert body == (project / 'serve' / asset.lstrip('/')).read_bytes()
    for path in ('/metrics', '/status', '/settings'):
        assert isinstance(json.loads(get(path)), dict)
    blocked = ['/api/context', '/api/update', '/api/port', '/config', '/load', '/unload']
    for path in blocked:
        request = urllib.request.Request(base + path, b'{}', {'Content-Type': 'application/json'})
        try:
            opener.open(request, timeout=30)
        except urllib.error.HTTPError as error:
            assert error.code == 409
            detail = json.load(error)['error']
            if args.kind == 'maya':
                assert isinstance(detail, str) and 'Managed profiles' in detail
            else:
                assert detail['type'] == 'managed_profile'
        else:
            raise AssertionError('Runtime mutation was accepted: ' + path)
    if args.kind == 'maya':
        limits = json.loads(get('/api/context'))
        assert limits['min'] == limits['max'] == limits['context'] == health['max_context']
    result = {'status': 'passed', 'kind': args.kind, 'model': health['model'],
              'context': health['max_context'], 'original_html_sha256': hashlib.sha256(html).hexdigest(),
              'original_asset_count': len(assets), 'metrics_status_settings': True,
              'runtime_mutations_blocked': blocked,
              'method': 'Existing native HTTP worker; functional frontend validation only, no benchmark.'}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
