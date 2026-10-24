#!/usr/bin/env python3
"""Link selected-format/actual-shape tests against the exact DeepSeek engine objects.

The upstream CMake target exposes the uniform IQ test. Also exercise its shipped
core test (dense matrices, Engram, KV and the retained mixed IQ expert pairs).
Mixed pairs are restricted to the IQ2/3 types in the reused packs. Unselected
Q4_K/IQ4_XS and Q2_K/Q3_K expert pairs remain blocked; no numerical tolerance or
engine source is changed. Uniform IQ tests also cover the XS and drafter types.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('build',type=Path)
a=ap.parse_args();source=a.source.resolve();build=a.build.resolve()
commands=subprocess.check_output(['ninja','-C',str(build),'-t','commands','ds4_iq_test','strata-dsv41'],text=True).splitlines()
compile_line=next(s for s in commands if ' -c ' in s and 'tests/dsv41/iq_expert_test.cpp' in s)
link_line=next(s for s in reversed(commands) if ' -o strata-dsv41 ' in s)
assert link_line.startswith(': && ') and link_line.endswith(' && :')
iq=(source/'tests/dsv41/iq_expert_test.cpp').read_text()
assert 'const int E = 512, FF = 256,' in iq
iq=iq.replace('const int E = 512, FF = 256,','const int E = 5120, FF = 2304,')
core=(source/'tests/dsv41/ds4_gguf_test.cu').read_text()
old='for (const auto& pr : kQPairs) test_experts_q(512, 256, pr.first, pr.second, s);'
assert old in core
core=core.replace(old,'for (const auto& pr : kQPairs) if (pr.first != gg::iq::kIQ4_XS && pr.first != gg::iq::kQ4_K && pr.first != gg::iq::kQ2_K && pr.first != gg::iq::kQ3_K) test_experts_q(512, 256, pr.first, pr.second, s);')
assert 'for (int i : {0, 4}) test_experts_q' in core
core=core.replace('for (int i : {0, 4}) test_experts_q','for (int i : {0, 1}) test_experts_q')
# Relative includes in these source copies still resolve against the pinned tree.
for name,text in [('ds4_core_selected_test.cu',core),('ds4_iq_shape_test.cpp',iq)]:
    text=text.replace('"../../src/dsv41/','"'+str(source/'src/dsv41')+'/')
    test=build/name;test.write_text(text)
    obj=build/(name+'.o')
    cmd=shlex.split(compile_line)
    cmd[cmd.index('-o')+1]=str(obj)
    cmd[cmd.index('-c')+1]=str(test)
    if '-MF' in cmd:cmd[cmd.index('-MF')+1]=str(obj)+'.d'
    if '-MT' in cmd:cmd[cmd.index('-MT')+1]=str(obj)
    subprocess.run(cmd,cwd=build,check=True)
    link=shlex.split(link_line[len(': && '):-len(' && :')])
    main=next(i for i,v in enumerate(link) if v.endswith('/ds4_main.cpp.o'))
    link[main]=str(obj)
    link[link.index('-o')+1]=name.rsplit('.',1)[0]
    subprocess.run(link,cwd=build,check=True)
record={'source_commit':subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip(),
        'scope':'Test-source-only variants; engine objects and tolerances unchanged. Mixed experts limited to selected IQ2/3 pairs (all five small-shape pairs and IQ2_XXS/IQ3_XXS plus IQ2_S/IQ3_S at5120/2304). Unselected Q4_K/IQ4_XS and Q2_K/Q3_K pairs excluded. Uniform actual-shape IQ test uses5120/2304.',
        'tests':{n:hashlib.sha256((build/n).read_bytes()).hexdigest() for n in ('ds4_core_selected_test','ds4_iq_shape_test')}}
(build/'selected-test-build.json').write_text(json.dumps(record,indent=2)+'\n')
