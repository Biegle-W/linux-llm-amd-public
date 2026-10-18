#!/usr/bin/env python3
"""Check the runtime prerequisites of experimental peer-read collectives."""
import ctypes
import json
import os
from pathlib import Path

hip = ctypes.CDLL(str(Path(os.environ['ROCM_PATH'])/'lib/libamdhip64.so'))
hip.hipInit.argtypes = [ctypes.c_uint]
hip.hipGetDeviceCount.argtypes = [ctypes.POINTER(ctypes.c_int)]
hip.hipDeviceCanAccessPeer.argtypes = [ctypes.POINTER(ctypes.c_int),ctypes.c_int,ctypes.c_int]
assert hip.hipInit(0) == 0
count = ctypes.c_int()
assert hip.hipGetDeviceCount(ctypes.byref(count)) == 0
assert count.value == 2
pairs = []
for source,destination in [(0,1),(1,0)]:
    can = ctypes.c_int()
    error = hip.hipDeviceCanAccessPeer(ctypes.byref(can),source,destination)
    pairs.append(dict(source=source,destination=destination,error=error,can_access_peer=bool(can.value)))
print(json.dumps(dict(visible_devices=count.value,force_fine_grain_pcie=os.environ.get('HSA_FORCE_FINE_GRAIN_PCIE','unset'),pairs=pairs,
                     peer_collective_prerequisite=all(p['error']==0 and p['can_access_peer'] for p in pairs)),indent=2))
