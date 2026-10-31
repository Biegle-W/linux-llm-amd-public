#!/usr/bin/env python3
"""Install only maintained device-loader sources into the selected Comfy runtime."""
from pathlib import Path
import argparse,shutil
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parent/'comfyui-device-loaders';dest=a.runtime/'custom_nodes/local_graphics_devices'
files=[Path('__init__.py'),*(Path('clipproj_vendor')/n for n in ['__init__.py','clipproj_nodes.py','clipproj_projection.py','clipproj_pinning.py','LICENSE','SOURCE.json'])]
for rel in files:
 source=root/rel;target=dest/rel;assert source.is_file() and not source.is_symlink();target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);target.chmod(0o644)
print('Maintained graphics device loaders installed.')
