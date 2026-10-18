#!/usr/bin/env python3
"""Read raw AMD SMU limits; AMD SMI's high-level API reduces these masks to bools."""
import argparse
import ctypes
import json
import time
import amdsmi
from amdsmi import amdsmi_wrapper as w

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--seconds',type=int,default=120)
args=parser.parse_args()
amdsmi.amdsmi_init()
handles=amdsmi.amdsmi_get_processor_handles()
rows=[dict(gpu=i,samples=0,hotspot_flag_samples=0,power_flag_samples=0,
           peak_hotspot_celsius=0,peak_memory_celsius=0,raw_independent_masks=[]) for i in range(len(handles))]
try:
 for _ in range(args.seconds):
  for row,handle in zip(rows,handles):
   metrics=w.amdsmi_gpu_metrics_t()
   status=w.amdsmi_get_gpu_metrics_info(handle,ctypes.byref(metrics))
   if status!=0:
    continue
   bits=int(metrics.indep_throttle_status)
   if bits==2**64-1:
    continue
   row['samples']+=1
   # Linux amdgpu_smu.h: independent bit 36 = hotspot; bits 0..7 = power.
   row['hotspot_flag_samples']+=bool(bits & (1<<36))
   row['power_flag_samples']+=bool(bits & 255)
   row['peak_hotspot_celsius']=max(row['peak_hotspot_celsius'],int(metrics.temperature_hotspot))
   row['peak_memory_celsius']=max(row['peak_memory_celsius'],int(metrics.temperature_mem))
   mask=hex(bits)
   if mask not in row['raw_independent_masks']:row['raw_independent_masks'].append(mask)
  time.sleep(1)
finally:
 amdsmi.amdsmi_shut_down()
print(json.dumps(dict(seconds=args.seconds,cards=rows)),flush=True)
