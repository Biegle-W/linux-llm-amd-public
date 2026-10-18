#!/usr/bin/env python3
"""Check gated rocWMMA against CPU references, including Qwen GQA and decode."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'hardware/generated/level1-tests-2026-10-17'


def audit(path, mode, device, returncode):
    text = path.read_text(errors='replace')
    lines = [line for line in text.splitlines() if 'FLASH_ATTN_EXT(hsk=256,hsv=256,nh=4,nr23=[6,1]' in line]
    expected = {(kv,nb,cache) for kv in (512,4096) for nb in (1,4,33,128) for cache in ('f16','q8_0')}
    observed = set()
    for line in lines:
        values = re.search(r',kv=(\d+),nb=(\d+),.*type_K=(\w+),type_V=(\w+),',line)
        if values and 'OK' in line:
            observed.add((int(values[1]),int(values[2]),values[3]))
    result = dict(mode=mode,device=device,returncode=returncode,ok_cases=sum('OK' in line for line in lines),
                  rocwmma_selected='LOCAL_ROCWMMA' in text,
                  required_shapes_passed=expected.issubset(observed))
    result['passed'] = (returncode==0 and result['required_shapes_passed'] and result['rocwmma_selected']==bool(mode))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-existing', action='store_true')
    options = parser.parse_args()
    if not options.audit_existing:
        sys.path.insert(0,str(ROOT/'dsh'))
        import backend_switch
        if any(backend_switch.is_inference(p) for p in backend_switch.processes().values()):
            raise RuntimeError('Another configured inference worker is active; run numerical checks separately')
    results = []
    for mode in (0,1):
        for device in (0,1):
            log = OUT/f'rocwmma-numerical-v2-mode{mode}-gpu{device}.log'
            if options.audit_existing:
                old = json.loads((OUT/'rocwmma-numerical-v2.json').read_text())
                returncode = next(x['returncode'] for x in old if x['mode']==mode and x['device']==device)
            else:
                cmd = [str(OUT/'llama-rocwmma/build-test/bin/test-backend-ops'),'test','-b',f'ROCm{device}',
                       '-o','FLASH_ATTN_EXT','-p',r'hsk=256,hsv=256,nh=4,nr23=\[6,1\]']
                with log.open('w') as output:
                    returncode = subprocess.run(cmd,env={**os.environ,'GGML_HIP_LOCAL_ROCWMMA':str(mode)},
                                                stdout=output,stderr=subprocess.STDOUT,timeout=150).returncode
            result = audit(log,mode,device,returncode)
            results.append(result)
            print(json.dumps(result),flush=True)
            if not result['passed']:
                break
        if not results[-1]['passed']:
            break
    (OUT/'rocwmma-numerical-summary.json').write_text(json.dumps(results,indent=2)+'\n')
    assert len(results)==4 and all(x['passed'] for x in results), 'Numerical validation failed'


if __name__ == '__main__':
    main()
