#!/usr/bin/env python3
"""Exercise registered DSH HyperQwen choices in isolated synthetic sessions."""
import hashlib
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
DSH = ROOT / 'dsh'
OUTPUT = ROOT / 'hyperqwen/research/dsh-switching-2026-10-07.json'
RAW = ROOT / 'hyperqwen/research/raw/dsh-switching-2026-10-07'
SETTINGS = DSH / 'data/settings.yaml'
original = hashlib.sha256(SETTINGS.read_bytes()).hexdigest()
provider = yaml.safe_load(SETTINGS.read_text())['llm-pi-ai']['providers']['hyperqwen-local']
assert provider['baseURL'] == 'http://127.0.0.1:18020/v1'
assert {m['id'] for m in provider['models']} == {'qwen3.8-27b-hyperqwen-dflash2', 'qwen3.8-27b-hyperqwen-mtp'}
node = DSH / 'node-v24.21.0-linux-x64/bin/node'
result = {'date': '2026-10-07', 'isolated_test_home': True, 'stages': [], 'passed': False}

def save():
    OUTPUT.write_text(json.dumps(result, indent=2) + '\n')

try:
    for index, mode in enumerate(('dflash2', 'mtp', 'dflash2')):
        model = 'qwen3.8-27b-hyperqwen-' + mode
        home = RAW / str(index) / 'home'
        workspace = RAW / str(index) / 'workspace'
        home.mkdir(parents=True, exist_ok=True)
        workspace.mkdir(parents=True, exist_ok=True)
        marker = 'DSH-SWITCH-' + str(index) + '-CEDAR-731'
        (workspace / 'verification.txt').write_text('The verification word is ' + marker + '.\n')
        (home / 'AGENTS.md').write_text('Use the file-reading tool when asked to read a file. Report its actual contents.\n')
        (home / 'settings.yaml').write_text(yaml.safe_dump({
            'llm-pi-ai': {'providers': {'hyperqwen-local': provider}},
            'agent-default-model': {'provider': 'hyperqwen-local', 'model': model}}))
        start = time.monotonic()
        print('DSH integration stage', index, mode, flush=True)
        log = RAW / str(index) / 'output.log'
        with log.open('w') as stream:
            finished = subprocess.run([str(node), str(DSH / 'node_modules/@deepseek-ai/dsh/lib/bin.js'),
                '--profile', 'headless', 'Read verification.txt using your file-reading tool. Reply with only the verification word from that file.'],
                cwd=workspace, env={**os.environ, 'DSH_HOME': str(home), 'LOCAL_LLAMA_API_KEY': 'local-test',
                                  'PATH': str(node.parent) + ':' + os.environ['PATH']},
                stdout=stream, stderr=subprocess.STDOUT, timeout=900)
        text = log.read_text()
        with urllib.request.urlopen('http://127.0.0.1:18020/health', timeout=5) as response:
            health = json.load(response)
        assert finished.returncode == 0 and marker in text, 'DSH did not report the file value; inspect synthetic output.log'
        assert health['active_mode'] == mode and health['active_model'] == model
        trace_code = r'''
const fs=require('node:fs'),zlib=require('node:zlib');
const directory=process.argv[1]+'/sessions',marker=process.argv[2];
const file=fs.readdirSync(directory,{recursive:true}).find(n=>n.endsWith('session.v3.jsonl.zstd'));
const compressed=fs.readFileSync(directory+'/'+file);let offset=0,parts=[];
while(offset<compressed.length){
  const frame=zlib.zstdDecompressSync(compressed.subarray(offset),{info:true});
  if(!frame.engine.bytesWritten)throw new Error('No decompression progress');
  offset+=frame.engine.bytesWritten;parts.push(frame.buffer);
}
const rows=Buffer.concat(parts).toString().trim().split('\n').map(JSON.parse);
console.log(JSON.stringify({
  read_called:rows.some(r=>r.type==='tool/call'&&r.data.name==='read'&&r.data.arguments.includes('verification.txt')),
  tool_result_seen:rows.some(r=>r.type==='tool/result'&&JSON.stringify(r.data.message).includes(marker)),
}));
'''
        trace = json.loads(subprocess.check_output([str(node), '-e', trace_code, str(home), marker], text=True))
        assert trace['read_called'] and trace['tool_result_seen'], 'Missing DSH tool trace'
        result['stages'].append({'mode': mode, 'model': model, 'exit': finished.returncode,
            'elapsed_s': round(time.monotonic() - start, 3), 'file_value_returned': True,
            'router_active_matches': True, **trace, 'passed': True})
        save()
        print('DSH stage passed:', mode, flush=True)
    assert hashlib.sha256(SETTINGS.read_bytes()).hexdigest() == original
    result['user_settings_unchanged'] = True
    result['passed'] = True
    save()
    print('PASS: DSH DFlash2/MTP/DFlash2 file-tool integration; original settings unchanged.', flush=True)
except Exception as error:
    result['error'] = str(error)
    result['user_settings_unchanged'] = hashlib.sha256(SETTINGS.read_bytes()).hexdigest() == original
    save()
    raise
