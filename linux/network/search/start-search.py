#!/usr/bin/env python3
"""Start the bounded, loopback-only free search service; preserve local config."""
import os
from pathlib import Path
import secrets
import subprocess


def main():
    here = Path(__file__).resolve().parent
    root = here.parents[1]
    data = root / 'dsh/data/search'
    config = data / 'config/settings.yml'
    config.parent.mkdir(parents=True, exist_ok=True)
    if not config.exists():
        template = (here / 'settings.example.yml').read_text()
        with open(config, 'x', opener=lambda name, flags: os.open(name, flags, 0o600)) as out:
            out.write(template.replace('GENERATE_LOCAL_SECRET', secrets.token_hex(32)))
    env = dict(os.environ, LOCAL_LLM_SEARCH_DATA=str(data),
               LOCAL_LLM_SEARCH_UID=str(os.getuid()), LOCAL_LLM_SEARCH_GID=str(os.getgid()))
    subprocess.run(['docker', 'compose', '-f', str(here / 'compose.yaml'), 'up', '-d'], env=env, check=True)
    print('Free local search: http://127.0.0.1:10001 (no API key; no paid fallback)')


if __name__ == '__main__':
    main()
