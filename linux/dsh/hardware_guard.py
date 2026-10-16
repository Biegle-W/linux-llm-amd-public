"""Reject stale two-NVIDIA profiles before any backend handover or model load."""
import csv
import io
import subprocess


def nvidia_inventory():
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=pci.bus_id,name,memory.total',
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=10, check=True)
        cards = []
        for row in csv.reader(io.StringIO(result.stdout)):
            if len(row) != 3:
                raise ValueError('Unexpected NVIDIA inventory row')
            cards.append({'pci': row[0].strip(), 'name': row[1].strip(),
                          'memory_mib': int(row[2].strip())})
        return sorted(cards, key=lambda card: card['pci'])
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise RuntimeError('Cannot verify NVIDIA hardware. Check nvidia-smi before '
                           'starting inference; no backend has been stopped.') from error


def require_current_cuda_pair(cards=None):
    cards = nvidia_inventory() if cards is None else cards
    names = [card['name'] for card in cards]
    expected = ['NVIDIA GeForce RTX 4070', 'NVIDIA GeForce RTX 3060']
    if names != expected or any(card['memory_mib'] < 12000 for card in cards):
        raise RuntimeError(
            'These active profiles require RTX 4070 + RTX 3060 in PCI order. '
            'Detected: ' + (', '.join(names) or 'no NVIDIA GPUs') + '. '
            'After the AMD upgrade, run llm-upgrade-check and follow '
            'hardware/UPGRADE-7900XTX-4070.md to validate and activate the new '
            'profiles. AMD VRAM cannot be added to a CUDA TP/PP profile. '
            'No backend has been stopped.')


def require_strata():
    """Do not activate CPU expert residency or the old GPU split before migration."""
    import json
    from pathlib import Path
    profiles = json.loads((Path(__file__).resolve().parent / 'strata-profiles.json').read_text())
    if not any(p.get('enabled', True) for p in profiles.values()):
        raise RuntimeError(next(iter(profiles.values()))['unavailable_reason'] + ' No backend has been stopped.')
    require_current_cuda_pair()


def require_hyperqwen():
    """Fail before handover; retained CUDA profiles are explicitly disabled on AMD."""
    import json
    from pathlib import Path
    profiles = json.loads((Path(__file__).resolve().parent / 'hyperqwen-profiles.json').read_text())
    enabled = [p for p in profiles.values() if p.get('enabled', True)]
    if not enabled:
        reason = next(iter(profiles.values()))['unavailable_reason']
        raise RuntimeError(reason + ' No backend has been stopped.')
    require_current_cuda_pair()


if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['hyperqwen']:
        try:
            require_hyperqwen()
        except RuntimeError as error:
            raise SystemExit(str(error))
