#!/usr/bin/env python3
"""Read-only, standard-library checks of the paper handoff. No training/import of ML code."""
from pathlib import Path
import csv
import hashlib
import json
import math
import statistics

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'paper/evidence'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def rows(name):
    with (EVIDENCE / name).open(newline='') as stream:
        return list(csv.DictReader(stream))


def equal(actual, expected, name):
    if not math.isclose(float(actual), float(expected), rel_tol=1e-9, abs_tol=1e-9):
        raise AssertionError(f'{name}: {actual} != {expected}')


def macro(data, column='pred'):
    labels = sorted({row['label'] for row in data})
    values = []
    for label in labels:
        tp = sum(row['label'] == label and row[column] == label for row in data)
        fp = sum(row['label'] != label and row[column] == label for row in data)
        fn = sum(row['label'] == label and row[column] != label for row in data)
        values.append(2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.)
    return statistics.mean(values)


def select(data, split, typ, pid):
    tests = {
        'isolated': lambda row: row['part'] != 'scripts',
        'stories_oracle_boundaries': lambda row: row['part'] == 'scripts',
        'isolated_seated': lambda row: row['part'] in {'actions_seated', 'signs_seated'},
        'isolated_original_parts': lambda row: row['part'] in {'actions', 'signs_standing'},
    }
    return [row for row in data if row['pid'] == pid and row['type'] == typ and tests[split](row)]


def main():
    manifest = json.loads((ROOT / 'paper/evidence_manifest.json').read_text())
    for name, expected in manifest['files'].items():
        path = ROOT / name
        assert path.is_file(), f'Missing handoff file: {name}'
        assert path.stat().st_size == expected['bytes'], f'Changed size: {name}'
        assert digest(path) == expected['sha256'], f'Changed contents: {name}'
    print(f"PASS: {len(manifest['files'])} evidence/model files match SHA256 manifest")

    data = rows('all_out_of_fold_predictions.csv')
    assert len(data) == 1534
    assert len({row['id'] for row in data}) == len(data)
    assert {row['pid'] for row in data} == {'P01', 'P02', 'P03', 'P04', 'P05'}
    fold = rows('fold_metrics.csv')
    for metric in fold:
        group = select(data, metric['split'], metric['type'], metric['pid'])
        equal(len(group), metric['n'], f"{metric['pid']} support")
        equal(macro(group), metric['macro_f1'], 'macro F1')
        equal(macro(group, 'cnn_pred'), metric['cnn_macro_f1'], 'CNN macro F1')
        equal(sum(row['pred'] == row['label'] for row in group) / len(group), metric['accuracy'], 'accuracy')
        equal(len({row['label'] for row in group}), metric['supported_classes'], 'supported classes')
        equal(sum(float(row['scored_windows']) == 0 for row in group), metric['unavailable'], 'unavailable')
    assert len(fold) == 34
    for summary in rows('summary.csv'):
        group = [row for row in fold if row['split'] == summary['split'] and row['type'] == summary['type']]
        values = [float(row['macro_f1']) for row in group]
        equal(statistics.mean(values), summary['mean_f1'], 'participant mean F1')
        equal(statistics.stdev(values), summary['sd_f1'], 'participant sample SD')
        equal(sum(float(row['n']) for row in group), summary['events'], 'summary events')
        equal(len(group), summary['participants'], 'summary participants')
    print('PASS: all 34 fold metric rows and all 8 summary slices recomputed from saved event predictions')

    for typ, n, correct in [('activity', 628, 311), ('sign', 490, 171)]:
        group = [row for row in data if row['part'] != 'scripts' and row['type'] == typ]
        assert len(group) == n and sum(row['label'] == row['pred'] for row in group) == correct
        print(f'PASS: pooled isolated {typ}: {correct}/{n} correct ({100 * correct/n:.2f}%)')

    story = rows('story_metrics.csv')
    totals = {key: sum(float(row[key]) for row in story) for key in ['n_true', 'n_pred', 'detected', 'identified', 'intent_correct', 'false_on_routine', 'routine_seconds']}
    for key, value in [('n_true', 208), ('n_pred', 239), ('detected', 121), ('identified', 39), ('intent_correct', 32), ('false_on_routine', 50)]:
        equal(totals[key], value, key)
    equal(totals['routine_seconds'], 1218.06, 'story routine seconds')
    assert float(next(row for row in story if row['pid'] == 'P01')['identified']) == 0
    print('PASS: automatic stories: 208 true / 121 detected / 39 named / 32 full responses; 50 routine false commands')

    counts = json.loads((EVIDENCE / 'verified_dataset_counts.json').read_text())
    equal(sum(float(row['rows']) for row in rows('raw_rows_by_recording.csv')), counts['participant_raw_rows'], 'participant rows')
    assert counts['participant_raw_rows'] == 2010899 and counts['all_kept_capture_rows_including_QC'] == 2050030
    selected = rows('selected_session_log.csv')
    assert len(selected) == 25
    equal(sum(float(row['rows']) for row in selected), 2050030, 'selected take rows')
    raw_counts = rows('isolated_raw_rows_by_class.csv')
    for typ, expected_rows, expected_trials in [('activity', 416836, 628), ('sign', 222570, 490)]:
        group = [row for row in raw_counts if row['type'] == typ]
        equal(sum(float(row['raw_rows']) for row in group), expected_rows, 'label interval raw rows')
        equal(sum(float(row['trials']) for row in group), expected_trials, 'isolated trials')
    archived = json.loads((ROOT / 'handoff/manifest.json').read_text())
    assert digest(ROOT / 'handoff/manifest.json') == 'f01651df3c4b758f3cbec5dd742669b4f0605a9f11c24162aecd662949dede62'
    labels = sorted((EVIDENCE / 'labels').glob('*.csv'))
    assert len(labels) == 22
    story_ids = set()
    for label in labels:
        info = archived['files']['labels/' + label.name]
        assert digest(label) == info['sha256']
        with label.open(newline='') as stream:
            for row in csv.DictReader(stream):
                if row.get('mode') == 'scripts' and row.get('script_id') and row.get('run'):
                    story_ids.add((row['pid'], row['script_id'], row['run']))
    # Some label files encode mode as script; identify by script_id instead.
    if len(story_ids) != 34:
        story_ids = set()
        for label in labels:
            with label.open(newline='') as stream:
                for row in csv.DictReader(stream):
                    if row.get('script_id') in {'M-SEQ', 'T-SEQ', 'C-SEQ', 'S-SEQ'} and row.get('run'):
                        story_ids.add((row['pid'], row['script_id'], row['run']))
    assert len(story_ids) == 34, story_ids
    print('PASS: selected dataset rows, 22 annotation hashes, 34 story runs and dataset fingerprint')

    run = ROOT / manifest['retained_results']
    for pid in ['P01', 'P02', 'P03', 'P04', 'P05']:
        choice = json.loads((run / pid / 'selection.json').read_text())
        assert choice['test_pid'] == pid
        assert set(choice['training_pids']) == {'P01', 'P02', 'P03', 'P04', 'P05'} - {pid}
        assert choice['validation_pid'] != pid
        assert (run / pid / 'frame_predictions.npz').is_file()
    card = json.loads((run / 'deployment_all5/model_card.json').read_text())
    assert set(card['training_participants']) == {'P01', 'P02', 'P03', 'P04', 'P05'}
    assert card['roles'] == {'detector': 'normalized4', 'action': 'normalized4', 'sign': 'normalized4'}
    assert card['action_tree_weight'] == 0 and card['seeds'] == [17, 29]
    for paths in card['models'].values():
        for name in paths:
            assert (run / 'deployment_all5' / name).is_file(), name
    print('PASS: recorded split metadata and both retained inference checkpoint references')
    print('Handoff checks passed. No training, classifier fitting, recording edits or model loading occurred.')


if __name__ == '__main__':
    main()
