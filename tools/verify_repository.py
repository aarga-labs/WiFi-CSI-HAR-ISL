#!/usr/bin/env python3
"""Verify imported content and current scientific evidence without executing ML code."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-originals', action='store_true',
                        help='Also rehash original source folders on Adhikkesh\'s machine')
    args = parser.parse_args()
    with (ROOT / 'provenance/file_manifest.csv').open(newline='') as stream:
        entries = list(csv.DictReader(stream))
    copies = [e for e in entries if e['disposition'] == 'copy']
    assert len({e['destination'] for e in copies}) == len(copies), 'Destination collision'
    changes_path = ROOT / 'provenance/maintenance_changes.json'
    changes = json.loads(changes_path.read_text())['files'] if changes_path.exists() else {}
    imported = {e['destination'] for e in copies}
    assert set(changes) <= imported, 'Maintenance entry is not an imported file'
    notebooks = 0
    updated = removed = 0
    for item in copies:
        rel = Path(item['destination'])
        assert not rel.is_absolute() and '..' not in rel.parts
        path = ROOT / rel
        change = changes.get(item['destination'])
        expected = item['destination_sha256']
        if change:
            assert change['imported_sha256'] == expected, f'Original hash mismatch: {rel}'
            assert change['reason'].strip(), f'Missing maintenance reason: {rel}'
            assert change['action'] in {'update', 'remove'}, f'Invalid maintenance action: {rel}'
            if change['action'] == 'remove':
                assert not path.exists(), f'Removed file returned: {rel}'
                removed += 1
                continue
            expected = change['sha256']
            updated += 1
        assert path.is_file(), f'Missing imported file: {rel}'
        assert digest(path) == expected, f'Changed imported file: {rel}'
        if path.suffix == '.ipynb':
            data = json.loads(path.read_text())
            assert data.get('nbformat') == 4 and isinstance(data.get('cells'), list), rel
            notebooks += 1
    print(f'PASS: {len(copies) - updated - removed} unchanged imported hashes; '
          f'{updated} documented updates; {removed} documented removals; '
          f'{notebooks} notebook JSON structures read')
    if args.check_originals:
        roots = json.loads((ROOT / 'provenance/source_roots.json').read_text())
        checked = 0
        for item in entries:
            if not item['sha256']:
                continue
            path = Path(roots[item['source_root']]) / item['source_relative']
            assert digest(path) == item['sha256'], f'Original changed: {item["source_root"]}:{item["source_relative"]}'
            checked += 1
        print(f'PASS: {checked} original source/data hashes remain unchanged')
    histories = json.loads((ROOT / 'provenance/git_history/index.json').read_text())['histories']
    assert len(histories) == 9
    assert all(h['bundle']['verified'] for h in histories)
    print('PASS: provenance records nine verified original Git-history backups')
    subprocess.run([sys.executable, str(ROOT / 'current_system/paper/tools/verify_evidence.py')],
                   cwd=ROOT / 'current_system', check=True)
    print('Repository checks passed. No training, inference or hardware recording was run.')


if __name__ == '__main__':
    main()
