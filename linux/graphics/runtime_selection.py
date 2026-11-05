"""Select a locally qualified ComfyUI source without moving existing assets."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[1]

def selection(root=ROOT):
 root=Path(root);path=root/'graphics/runtime-versions.json';versions=json.loads(path.read_text());record=versions.get('runtime_selection')
 if record is None:return {'runtime':str(root/'runtime/comfyui'),'overlay':'','devices':'0,1'}
 if record.get('status')!='passed-six-normal-workflows':raise RuntimeError('ComfyUI source requires independent qualification on this host')
 revision=record['source_commit'];runtime=Path(record['source_path']);overlay=Path(record['dependency_overlay'])
 if not runtime.is_absolute() or not re.fullmatch('[0-9a-f]{40}',revision) or not overlay.is_relative_to(runtime):raise RuntimeError('Invalid selected ComfyUI source/overlay')
 if subprocess.check_output(['git','-C',str(runtime),'rev-parse','HEAD'],text=True,timeout=10).strip()!=revision:raise RuntimeError('Selected ComfyUI revision changed')
 subprocess.run(['git','-C',str(runtime),'diff','--quiet','HEAD','--'],check=True,timeout=10)
 if not (runtime/'main.py').is_file() or not (runtime/'.venv/bin/python').is_file() or not overlay.is_dir():raise RuntimeError('Selected ComfyUI files/environment missing')
 if record.get('qualified_device_order')!='1,0':raise RuntimeError('Qualified graphics device order changed')
 for name,expected in record['files'].items():
  path=runtime/name
  if not path.resolve().is_relative_to(runtime.resolve()):raise RuntimeError('Unexpected ComfyUI qualification file')
  if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise RuntimeError('Qualified ComfyUI integration changed: '+name)
 return {'runtime':str(runtime),'overlay':str(overlay),'devices':'1,0'}

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('field',choices=['runtime','overlay','devices']);args=parser.parse_args();print(selection()[args.field])

if __name__=='__main__':main()
