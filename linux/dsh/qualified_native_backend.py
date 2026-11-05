"""Launch only a registry-qualified native source with the retained managed UI."""
from pathlib import Path
import argparse,importlib,importlib.util,json,sys
from qualified_native_runtime import record_for,require_profile

def main():
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--config',required=True)
    selected,_=parser.parse_known_args();cfg=json.loads(Path(selected.config).read_text())
    record=record_for(cfg)
    if record is None:raise RuntimeError('This launcher requires an explicitly qualified native registry entry')
    require_profile(cfg,record)
    source=Path(record['source']);sys.path.insert(0,str(source))
    server=importlib.import_module('serve.server')
    spec=importlib.util.spec_from_file_location('managed_native_ui',Path(__file__).with_name('native-ui-server.py'))
    managed=importlib.util.module_from_spec(spec);spec.loader.exec_module(managed);managed.install_guard(server)
    sys.argv[0]=str(source/'serve/server.py')
    return server.main()

if __name__=='__main__':raise SystemExit(main())
