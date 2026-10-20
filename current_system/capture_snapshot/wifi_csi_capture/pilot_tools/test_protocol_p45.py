"""Offline checks only: no radios, cues, sound, or recorded dataset writes."""
import argparse
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import cue_session as cue
import protocol
import protocol_p45 as p45

HERE = Path(__file__).resolve().parent


def args(mode, posture="standing", **kwargs):
    values = dict(mode=mode, posture=posture, protocol="p45", only=[], reps=0,
                  runs=2, pid="P04", seed=42, ready=0, rest=0, break_every=0)
    values.update(kwargs)
    return argparse.Namespace(**values)


class ProtocolChecks(unittest.TestCase):
    def setUp(self):
        self.previous = cue.P
        cue.P = p45

    def tearDown(self):
        cue.P = self.previous

    def test_original_classes_and_stories_preserved(self):
        self.assertEqual(len(protocol.ACTIONS), 10)
        self.assertEqual(len(protocol.SIGNS), 14)
        self.assertEqual(set(protocol.SCRIPTS), {"M-SEQ", "T-SEQ", "C-SEQ"})
        for name in ("T-SEQ", "C-SEQ"):
            self.assertEqual(p45.SCRIPTS[name], protocol.SCRIPTS[name])
        self.assertEqual({k: p45.ACTIONS[k] for k in protocol.ACTIONS}, protocol.ACTIONS)
        cue.P = protocol
        self.assertEqual(len(cue.build_trials(args("actions", protocol="original"))), 95)
        self.assertEqual(len(cue.build_trials(args("signs", protocol="original"))), 70)

    def test_counts_and_supported_seated_actions(self):
        self.assertEqual(len(cue.build_trials(args("actions"))), 115)
        self.assertEqual(len(cue.build_trials(args("actions", "seated"))), 70)
        for posture in ("standing", "seated"):
            self.assertEqual(len(cue.build_trials(args("signs", posture))), 70)
        labels = {t[0] for t in cue.build_trials(args("actions", "seated"))}
        self.assertEqual(labels, {"drink", "eat", "answerphone", "tvremote", "wipetable", "chop_food", "stir_pot"})
        self.assertFalse(labels & {"walk", "sitstand", "fall", "pickup", "lightswitch"})
        many = cue.build_trials(args("actions", reps=30))
        self.assertEqual(sum(t[0] == "fall" for t in many), 5)

    def test_story_postures_and_intents(self):
        self.assertEqual(set(p45.script_postures("S-SEQ")), {"seated"})
        for name in ("M-SEQ", "T-SEQ"):
            for (label, typ, _), posture in zip(p45.SCRIPTS[name], p45.script_postures(name)):
                if typ == "sign":
                    self.assertEqual(posture, "seated")
        for step, posture in zip(p45.SCRIPTS["C-SEQ"], p45.script_postures("C-SEQ")):
            if step[0] in ("PAIN", "ACCIDENT", "CALL"):
                self.assertEqual(posture, "mattress")
        for name, steps in p45.SCRIPTS.items():
            self.assertEqual(steps[0][1], "sync")
            self.assertEqual(steps[-1][1], "sync")
            for label, typ, ctx in steps:
                if typ == "activity":
                    self.assertIn(label, p45.ACTIONS)
                    self.assertEqual(p45.intent_of(label, typ, ctx), ("I0", "none"))
                elif typ == "sign":
                    self.assertIn(label, p45.SIGNS)
        self.assertEqual(p45.intent_of("HOT", "sign", "meal"), ("I3", "kitchen_hazard_alert"))
        self.assertEqual(p45.intent_of("HOT", "sign", "tv"), ("I2", "cool_room"))

    def test_recorded_seated_labels_and_sync_markers(self):
        tick = iter(range(1_000_000, 1_000_000_000, 10_000))
        with tempfile.TemporaryDirectory() as folder:
            writer = cue.LabelWriter(folder, "P04", "actions_seated", p45.VERSION)
            with patch("builtins.input", return_value=""), patch.object(cue, "now_us", side_effect=lambda: next(tick)), \
                    patch.object(cue.time, "sleep"), patch.object(cue, "beep"), patch.object(cue.D, "show"), \
                    patch.object(cue.D, "plain"), patch("sys.stdout", io.StringIO()):
                cue.run_isolated(args("actions", "seated"), writer,
                                 cue.build_trials(args("actions", "seated")))
            writer.close()
            with open(writer.path) as stream:
                rows = list(csv.DictReader(stream))
            events = [r for r in rows if r["type"] == "activity"]
            self.assertEqual(len(events), 70)
            self.assertEqual({r["posture"] for r in events}, {"seated"})
            self.assertEqual(sum(r["type"] == "sync" for r in rows), 2)
            self.assertTrue(all("protocol=p45-v1" in r["note"] for r in rows))
            self.assertTrue(all(int(r["t_end_us"]) > int(r["t_start_us"]) for r in events))

    def test_story_csv_has_eight_runs_and_posture(self):
        tick = iter(range(1_000_000, 1_000_000_000, 10_000))
        with tempfile.TemporaryDirectory() as folder:
            writer = cue.LabelWriter(folder, "P05", "script", p45.VERSION)
            with patch("builtins.input", return_value=""), patch.object(cue, "now_us", side_effect=lambda: next(tick)), \
                    patch.object(cue.D, "show"), patch.object(cue.D, "plain"), patch("sys.stdout", io.StringIO()):
                cue.run_scripts(args("script", pid="P05"), writer)
            writer.close()
            with open(writer.path) as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len({(r["script_id"], r["run"]) for r in rows}), 8)
            self.assertEqual(sum(r["type"] == "sync" for r in rows), 16)
            events = [r for r in rows if r["type"] != "sync"]
            self.assertEqual(len(events), 100)
            self.assertTrue(all(r["posture"] for r in rows))
            self.assertTrue(all(r["posture"] == "seated" for r in rows if r["script_id"] == "S-SEQ"))
            self.assertTrue(all(int(r["t_end_us"]) > int(r["t_start_us"]) for r in events))

    def test_cli_plan_and_invalid_seated_selection(self):
        with tempfile.TemporaryDirectory() as folder:
            cmd = [sys.executable, str(HERE / "cue_session.py"), "actions", "--pid", "P04",
                   "--protocol", "p45", "--posture", "seated", "--outdir", folder]
            result = subprocess.run(cmd + ["--plan"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["trials"], 70)
            self.assertEqual(list(Path(folder).iterdir()), [])
            result = subprocess.run(cmd + ["--only", "fall"], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsupported", result.stderr)
            self.assertEqual(list(Path(folder).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
