"""Check recovery provenance/partition and refusal of the old phone app."""
import contextlib,io,json,sys,tempfile,unittest
from pathlib import Path
from collections import Counter
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import controller,run_paired
from capture_paths import saved_capture_path

class RecoveryChecks(unittest.TestCase):
    def test_retained_and_makeup_cover_original_once(self):
        root=Path(__file__).resolve().parents[1]
        m=json.loads((root/'recovery/P04_activities_standing_20261113_124340/recovery_manifest.json').read_text())
        source=json.loads((saved_capture_path(m['source_phone_run'])/'plan.json').read_text())
        original=[e for e in source['phases'] if e['kind']=='perform']
        patch=controller.make_plan(dict(pid='P04',block='activities_standing_makeup'),0)
        events=[e for e in patch['phases'] if e['kind']=='perform']
        retained=set(m['retained_trials']);replaced=[e['source_trial'] for e in events]
        self.assertEqual(len(retained),70);self.assertEqual(len(replaced),45)
        self.assertEqual(len(replaced),len(set(replaced)))
        self.assertFalse(retained.intersection(replaced))
        self.assertEqual(retained.union(replaced),{e['trial'] for e in original})
        lookup={e['trial']:e for e in original}
        for e in events:self.assertEqual(e['label'],lookup[e['source_trial']]['label'])
        self.assertEqual(Counter(e['label'] for e in events)+Counter(m['retained_class_counts']),Counter(e['label'] for e in original))
    def test_old_app_is_refused_before_radio_start(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'data').mkdir();(root/'data/pairing.json').write_text('{"token":"synthetic"}')
            s=dict(paired_commands_version=2,sessions=[],devices=[dict(seen_s_ago=0,app_version='1.0')])
            with mock.patch.object(run_paired,'ROOT',root),mock.patch.object(run_paired,'api',return_value=s),mock.patch.object(run_paired.subprocess,'Popen') as spawn,mock.patch.object(sys,'argv',['runner','--pid','P04','--block','stand_still']),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(run_paired.main(),1);spawn.assert_not_called()
