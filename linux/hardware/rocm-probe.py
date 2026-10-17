"""Validate both ROCm devices before handover."""
import json
import os
from pathlib import Path
import amdsmi
import torch
assert Path(os.environ['SGLANG_NCCL_SO_PATH']).is_file(), 'Install the dual-AMD RCCL library first'
assert torch.version.hip and torch.cuda.is_available(), 'ROCm GPU unavailable'
assert torch.cuda.device_count() == 2, 'Expected exactly two visible AMD GPUs'
devices = []
for i in range(2):
    p = torch.cuda.get_device_properties(i)
    assert p.gcnArchName.split(':')[0] == 'gfx1100' and '7900 XTX' in p.name, p
    assert p.total_memory >= 23 * 1024**3, 'Expected 24 GB AMD GPU'
    devices.append({'index': i, 'device': p.name, 'architecture': p.gcnArchName,
                    'total_bytes': p.total_memory})
print(json.dumps({'torch': torch.__version__, 'hip': torch.version.hip, 'devices': devices,
                  'peer_access': [torch.cuda.can_device_access_peer(0, 1),
                                  torch.cuda.can_device_access_peer(1, 0)]}))
