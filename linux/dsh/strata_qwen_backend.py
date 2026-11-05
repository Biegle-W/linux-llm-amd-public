"""Start an independently qualified Strata Qwen package in its owned worker scope."""
from pathlib import Path
import argparse
import importlib
import importlib.util
import json
import sys

from llama_runtime import require_worker_scope
from strata_runtime import require_strata
from strata_qwen_qualification import require_package


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--config', required=True)
    selected, _ = parser.parse_known_args()
    cfg = json.loads(Path(selected.config).read_text())
    require_worker_scope()
    admitted = require_strata(model=cfg['model_name'])
    if admitted != cfg:
        raise RuntimeError('Worker config differs from its admitted Strata profile.')
    record = require_package(cfg)
    sys.path.insert(0, record['control'])
    server = importlib.import_module('serve.server')
    spec = importlib.util.spec_from_file_location(
        'managed_strata_qwen_ui', Path(__file__).with_name('native-ui-server.py'))
    managed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(managed)
    managed.install_guard(server)
    sys.argv[0] = str(Path(record['control']) / 'serve/server.py')
    sys.argv.extend(['--engine', 'strata'])
    return server.main()


if __name__ == '__main__':
    raise SystemExit(main())
