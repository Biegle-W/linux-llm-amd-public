#!/usr/bin/env python3
"""Repair pi-ai HTTP activity tracking without changing timeout values.

The installed DSH bundle remains third-party source. Keep its exact preimage in
ignored data/patch-backups, and only replace the reviewed bundle shape.
Upstream explanation: deepseek-ai/deepseek-harness discussion 9311.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

MARKER = '// LOCAL_DSH_HTTP_ACTIVITY_V1'
CLASS = 'var PiAiAdapter = class extends LlmAdapter {'
OPTIONS = '...profileOptions(profile, reasoning, apiKey),'
HOOK = '...(model.api === "openai-completions" ? { fetch: activityFetch(() => watchdog.pulse()) } : {}),'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def patched(source, helper):
    embedded = helper.replace('export function activityFetch', 'function activityFetch')
    if MARKER in source:
        if source.count(HOOK) != 1 or embedded not in source:
            raise RuntimeError('Existing activity patch differs; review before replacing it.')
        return source
    if source.count(CLASS) != 1 or source.count(OPTIONS) != 1:
        raise RuntimeError('Unsupported DSH bundle shape; installed source left unchanged.')
    start = source.index(OPTIONS)
    section = source[start:source.index('}), model.contextWindow', start)]
    if 'fetch:' in section or 'function activityFetch' in source:
        raise RuntimeError('DSH already supplies a fetch hook; review its activity handling.')
    return source.replace(CLASS, MARKER + '\n' + embedded + '\n' + CLASS, 1).replace(
        OPTIONS, OPTIONS + '\n                    ' + HOOK, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--undo', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    target = root / 'node_modules/@deepseek-ai/dsh-llm-pi-ai/lib/index.js'
    helper = (root / 'stream-activity-fetch.mjs').read_text()
    backup = root / 'data/patch-backups/stream-activity'
    state = backup / 'state.json'
    original = target.read_bytes()
    if args.undo:
        record = json.loads(state.read_text())
        if digest(original) != record['patched_sha256']:
            raise RuntimeError('Installed bundle changed after patch; refusing rollback overwrite.')
        before = (backup / (record['original_sha256'] + '.js')).read_bytes()
        if digest(before) != record['original_sha256']:
            raise RuntimeError('Rollback preimage checksum differs.')
        output = before
    else:
        output = patched(original.decode(), helper).encode()
        if args.check:
            if output != original:
                raise SystemExit('DSH HTTP stream activity repair is not applied.')
            print('DSH HTTP stream activity repair verified; timeout values unchanged.')
            return
        if output == original:
            print('DSH HTTP stream activity repair already applied.')
            return
        backup.mkdir(parents=True, exist_ok=True)
        preimage = backup / (digest(original) + '.js')
        if not preimage.exists():
            preimage.write_bytes(original)
        state.write_text(json.dumps({'original_sha256': digest(original),
                                     'patched_sha256': digest(output)}, indent=2) + '\n')
    temporary = target.with_name(target.name + '.activity.tmp')
    temporary.write_bytes(output)
    temporary.chmod(target.stat().st_mode & 0o777)
    os.replace(temporary, target)
    print('Restored DSH bundle preimage.' if args.undo else
          'Applied DSH HTTP stream activity repair; restart the idle frontend to activate.')


if __name__ == '__main__':
    main()
