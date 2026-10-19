#!/usr/bin/env python3
"""Validate an already running Strata router; never load or stop another backend."""
import argparse
import json
from pathlib import Path
import sys
import subprocess
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'dsh'))
from amd_device import amd_devices
from backend_switch import processes
from moe_memory import host_memory, worker_memory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=30020)
    parser.add_argument('--long', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT/'hardware/generated/strata-live-validation.json')
    a = parser.parse_args()
    cfg = json.loads((ROOT/'dsh/strata-iq3-profile.json').read_text())
    model = cfg['model_name']
    base = f'http://127.0.0.1:{a.port}'
    def api(path, body=None):
        request = urllib.request.Request(base+path, None if body is None else json.dumps(body).encode(),
                                         {'Content-Type':'application/json'})
        return urllib.request.urlopen(request, timeout=600)
    with api('/v1/models') as response:
        models = json.load(response)['data']
    assert any(m['id'] == model and m['context_length'] >= 32768 for m in models)
    engine = [p.pid for p in processes().values() if p.args and p.args[0] == cfg['exe']]
    assert len(engine) == 1, 'Expected exactly one owned Strata HIP engine'
    devices = amd_devices()
    readings = []
    stop = threading.Event()
    def monitor():
        while not stop.is_set():
            swap, nonresident = worker_memory(engine[0])
            readings.append({'available':host_memory()[1], 'swap':swap,'nonresident':nonresident,
                             'vram':[int((d/'mem_info_vram_used').read_text()) for d in devices]})
            stop.wait(1)
    watcher = threading.Thread(target=monitor, daemon=True);watcher.start()
    runtime_env = dict(__import__('os').environ)
    runtime_env['LD_LIBRARY_PATH'] = ':'.join(cfg.get('lib_dirs', []))
    version = subprocess.run([cfg['exe'], '--version'], env=runtime_env,
                             capture_output=True, text=True, check=True, timeout=15).stdout.strip()
    configured_context = int(cfg['args'][cfg['args'].index('--max-context') + 1])
    result = {'model':model,'runtime':version,'context':configured_context,'tests':[]}
    def save():
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(result,indent=2)+'\n')
    def run(name, prompt=None, **extra):
        body = {'model':model,'messages':[{'role':'user','content':prompt}],
                'max_tokens':512,'temperature':0,'chat_template_kwargs':{'enable_thinking':False},**extra}
        start=time.monotonic()
        with api('/v1/chat/completions',body) as response:
            data=json.load(response)
        trial={'name':name,'wall_seconds':round(time.monotonic()-start,3),
               'usage':data.get('usage'),'timings':data.get('timings'),
               'message':data['choices'][0]['message']}
        result['tests'].append(trial);save();print(json.dumps(trial),flush=True)
        return trial
    try:
        assert run('math','What is 37 multiplied by 19? Reply with only the integer.',max_tokens=32)['message']['content'].strip() == '703'
        run('code','Write a Python function that merges two sorted lists. Explain its time and space complexity.')
        run('prose','Write a short story about a lighthouse keeper finding a letter.')
        tools=[{'type':'function','function':{'name':'get_weather','description':'Get weather for a city',
                'parameters':{'type':'object','properties':{'city':{'type':'string'}},'required':['city']}}}]
        first=run('tool','Call the get_weather tool for Toronto.',max_tokens=128,tools=tools,
                  tool_choice={'type':'function','function':{'name':'get_weather'}})
        call=first['message']['tool_calls'][0]
        assert call['function']['name']=='get_weather'
        assert json.loads(call['function']['arguments'])['city']=='Toronto'
        follow=[{'role':'user','content':'Call the get_weather tool for Toronto.'},first['message'],
                {'role':'tool','tool_call_id':call['id'],'content':'{"city":"Toronto","temperature_c":18}'}]
        answer=run('tool_result',messages=follow,tools=tools,tool_choice='none',max_tokens=96)
        assert '18' in answer['message']['content']
        body={'model':model,'messages':[{'role':'user','content':'Reply with exactly STREAM_OK.'}],
              'max_tokens':32,'temperature':0,'stream':True,'chat_template_kwargs':{'enable_thinking':False}}
        chunks=[];done=False
        with api('/v1/chat/completions',body) as response:
            for line in response:
                line=line.decode().strip()
                if line=='data: [DONE]':done=True
                elif line.startswith('data: '):
                    data=json.loads(line[6:])
                    chunks.extend(c.get('delta',{}).get('content') or '' for c in data.get('choices',[]))
        assert done and 'STREAM_OK' in ''.join(chunks)
        result['stream_passed']=True
        if a.long:
            line='The ledger entry lists a routine inventory check.\n'
            blocks=[line*1000,line*1000,line*1000]
            prompt=('Read the following ledger and retrieve its three access codes.\n'
                    'alpha access code: CEDAR-57\n'+blocks[0]+'\nbeta access code: MAPLE-83\n'+blocks[1]+
                    '\ngamma access code: BIRCH-29\n'+blocks[2]+
                    '\nReturn only the alpha, beta and gamma access codes, in that order.')
            trial=run('long_retrieval',prompt,max_tokens=96)
            assert trial['usage']['prompt_tokens'] < 32768
            assert trial['usage']['prompt_tokens'] > 28000
            assert all(code in trial['message']['content'] for code in ('CEDAR-57','MAPLE-83','BIRCH-29'))
            result['long_retrieval_passed']=True
        result['functional_status']='passed'
    finally:
        stop.set();watcher.join(timeout=3)
        if readings:
            result['memory']={'minimum_available_gib':round(min(r['available'] for r in readings)/1024**3,2),
                              'maximum_worker_swap_bytes':max(r['swap'] for r in readings),
                              'maximum_nonresident_vram_bytes':max(r['nonresident'] for r in readings),
                              'peak_vram_gib':[round(max(r['vram'][i] for r in readings)/1024**3,2) for i in range(2)]}
        save()
    assert result['memory']['maximum_worker_swap_bytes']==0
    assert result['memory']['maximum_nonresident_vram_bytes']==0
    result['status']='passed';save()
    print('Strata validation passed:',a.output,flush=True)

if __name__=='__main__':
    main()
