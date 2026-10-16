"""Fail before handover if the isolated ROCm runtime cannot see the expected card."""
import json
import amdsmi  # Load AMD SMI before torch on this wheel combination.
import torch
assert torch.version.hip and torch.cuda.is_available(), 'ROCm GPU unavailable'
assert torch.cuda.device_count() == 1, 'Expected exactly one visible AMD GPU'
p = torch.cuda.get_device_properties(0)
assert p.gcnArchName.split(':')[0] == 'gfx1100' and '7900 XTX' in p.name, p
assert p.total_memory >= 23 * 1024**3, 'Expected 24 GB AMD GPU'
print(json.dumps({'torch': torch.__version__, 'hip': torch.version.hip,
                  'device': p.name, 'architecture': p.gcnArchName,
                  'total_bytes': p.total_memory}))
