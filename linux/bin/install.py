#!/usr/bin/env python3
"""Install actual launcher scripts in the user's PATH, including SSH command shells."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
COMMANDS = ('llm-llama', 'llm-sglang', 'llm-vllm', 'llm-strata', 'llm-maya', 'dsh', 'turnstone', 'llm-upgrade-check')
BEGIN = '# BEGIN local-llm SSH PATH'
END = '# END local-llm SSH PATH'
BLOCK = '''# BEGIN local-llm SSH PATH
# Must precede the noninteractive return: ssh host command reads this file.
case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) export PATH="$HOME/.local/bin:$PATH" ;;
esac
# END local-llm SSH PATH
'''


def install():
    destination = Path.home() / '.local/bin'
    destination.mkdir(parents=True, exist_ok=True)
    for name in COMMANDS:
        target = destination / name
        if target.is_symlink() or (target.exists() and target.read_bytes() != (ROOT / name).read_bytes()):
            raise RuntimeError(f'Refusing to replace an unrelated command: {target}')
    for name in COMMANDS:
        shutil.copyfile(ROOT / name, destination / name)
        (destination / name).chmod(0o755)
    bashrc = Path.home() / '.bashrc'
    original = bashrc.read_text() if bashrc.exists() else ''
    if BEGIN in original:
        before, block = original.split(BEGIN, 1)
        if END not in block:
            raise RuntimeError('Existing PATH marker is incomplete; refusing to alter .bashrc')
        original = before + block.split(END, 1)[1].lstrip('\n')
    updated = BLOCK + '\n' + original
    if bashrc.exists() and bashrc.read_text() != updated:
        backup = bashrc.with_name('.bashrc.before-local-llm-path')
        if not backup.exists():
            shutil.copy2(bashrc, backup)
    bashrc.write_text(updated)
    print('Installed actual command files in', destination)
    print('Available:', ', '.join(COMMANDS))
    print('PATH is enabled for new local terminals and SSH command shells.')


if __name__ == '__main__':
    install()
