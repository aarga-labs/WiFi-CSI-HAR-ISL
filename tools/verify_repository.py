#!/usr/bin/env python3
"""Verify imported content and current scientific evidence without executing ML code."""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import statistics
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
    parser.add_argument('--private-evidence', action='store_true',
                        help='Recompute event-level scores using separately retained private local files')
    args = parser.parse_args()
    tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0'))
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
                assert rel.as_posix() not in tracked, f'Private/removed file returned to Git: {rel}'
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
    evidence = ROOT / 'current_system/paper/evidence'
    def rows(name):
        with (evidence / name).open(newline='') as stream:
            return list(csv.DictReader(stream))
    groups = defaultdict(list)
    for row in rows('fold_metrics.csv'):
        groups[row['split'], row['type']].append(row)
    for row in rows('summary.csv'):
        folds = groups[row['split'], row['type']]
        values = [float(f['macro_f1']) for f in folds]
        assert math.isclose(statistics.mean(values), float(row['mean_f1']), abs_tol=1e-9)
        assert math.isclose(statistics.stdev(values), float(row['sd_f1']), abs_tol=1e-9)
        assert sum(int(f['n']) for f in folds) == int(row['events'])
        assert len(folds) == int(row['participants'])
    for name, classes, total, correct in [('action_class_performance.csv', 12, 628, 311),
                                           ('sign_class_performance.csv', 14, 490, 171)]:
        table = rows(name)
        assert len(table) == classes
        assert sum(int(r['n']) for r in table) == total
        assert sum(int(r['correct']) for r in table) == correct
        assert all(math.isclose(int(r['correct']) / int(r['n']), float(r['recall']), abs_tol=1e-9)
                   for r in table)
    story = rows('story_metrics.csv')
    for key, expected in [('n_true', 208), ('detected', 121), ('identified', 39),
                          ('intent_correct', 32), ('false_on_routine', 50)]:
        assert sum(int(r[key]) for r in story) == expected
    print('PASS: aggregate fold summaries, class counts/recall and story totals are internally consistent')
    if args.private_evidence:
        subprocess.run([sys.executable, str(ROOT / 'current_system/paper/tools/verify_evidence.py')],
                       cwd=ROOT / 'current_system', check=True)
    else:
        print('Event-level score recomputation requires --private-evidence and the private local inputs.')
    print('Repository checks passed. No training, inference or hardware recording was run.')


if __name__ == '__main__':
    main()
