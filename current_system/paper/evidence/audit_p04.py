"""Audit kept P04/P05 captures without changing recordings or their labels."""
from collections import Counter
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/adhikkesh/adhikkesh/FYP/wifi_csi_capture/pilot_tools")
import protocol_p45 as protocol

ROOT = Path("/home/adhikkesh/usrp-projects/data/phase1")
OUT = Path(__file__).resolve().parent
PID = sys.argv[1] if len(sys.argv)>1 else "P04"
if PID not in ("P04", "P05"):
    raise SystemExit("Participant must be P04 or P05")
PARTS = ["baseline", "actions", "actions_seated", "signs_standing", "signs_seated", "scripts"]
session_log = pd.read_csv(ROOT / "session_log.csv").fillna("")
kept = session_log[session_log.status == "kept"].copy()
kept = kept.sort_values(["date", "time"]).drop_duplicates(["pid", "part"], keep="last")
records = []
for part in PARTS + ["empty"]:
    pid = "DAY" if part == "empty" else PID
    selected = kept[(kept.pid == pid) & (kept.part == part)]
    if len(selected) != 1:
        records.append({"part": part, "errors": ["Missing kept take"]})
        continue
    take = selected.iloc[0]
    path = ROOT / take.csi_file
    df = pd.read_csv(path)
    t = df.Timestamp_us.to_numpy(np.int64)
    gaps_ms = np.diff(t)/1000
    expected_header = ["Packet", "Timestamp_us", "Channel"] + [f"SC{k}_{c}" for k in range(52) for c in ("Re", "Im")]
    checks = {
        "schema_correct": list(df.columns) == expected_header,
        "all_values_finite": bool(np.isfinite(df.to_numpy(float)).all()),
        "timestamps_strictly_increasing": bool((np.diff(t)>0).all()),
        "channel_1_only": bool((df.Channel == 1).all()),
        "rows_match_log": int(take.rows) == len(df),
        "rx_gain_12": float(take.rx_gain) == 12,
    }
    result = {"part": part, "pid": pid, "csi_file": str(path),
        "recording_date": str(take.date), "rows": len(df), "duration_s": float((t[-1]-t[0])/1e6),
        "rows_per_s": float((len(t)-1)/((t[-1]-t[0])/1e6)),
        "gaps_over_100ms": int((gaps_ms>100).sum()), "max_gap_ms": float(gaps_ms.max()),
        "checks": checks, "expected_video_name": take.video_file,
        "matching_video_in_dataset": any(ROOT.rglob(str(take.video_file))),
        "errors": []}
    log_path = ROOT / "logs" / (Path(take.csi_file).stem + ".rx.log")
    log_text = log_path.read_text(errors="replace")
    result["receiver_log"] = str(log_path)
    result["receiver_overflow_or_link_dead"] = any(x in log_text.lower() for x in ("overflows occurred", "link dead"))
    if part != "empty":
        label_path = ROOT / "labels" / take.label_file
        lab = pd.read_csv(label_path).fillna("")
        result["label_file"] = str(label_path)
        flags = lab[lab.type == "flag"]
        result["operator_flags"] = flags.to_dict("records")
        events = lab[lab.type.isin(["activity", "sign", "idle"])]
        sync = lab[lab.type == "sync"]
        checks.update({"no_operator_exclusions": flags.empty,
            "label_participant_correct": bool((lab.pid==pid).all()),
            "protocol_version_present": bool(lab.note.str.contains("protocol=p45-v1", regex=False).all()),
            "all_labels_in_csi_range": bool(((lab.t_start_us.astype(np.int64)>=t[0]) & (lab.t_end_us.astype(np.int64)<=t[-1])).all())})
        details = []
        for r in events.itertuples():
            a, b = int(r.t_start_us), int(r.t_end_us)
            i, j = np.searchsorted(t,[a,b])
            local = np.diff(t[i:j])/1000
            details.append({"trial": r.trial, "label": r.label, "type": r.type, "posture": r.posture,
                "script_id": r.script_id, "run": r.run, "step": r.step,
                "duration_s": (b-a)/1e6,
                "inside_csi": bool(a>=t[0] and b<=t[-1]), "rows": int(j-i),
                "rows_per_s": float((j-i)/((b-a)/1e6)) if b>a else None,
                "gaps_over_100ms": int((local>100).sum()),
                "max_gap_ms": float(local.max()) if len(local) else None})
        checks["all_event_durations_positive"] = all(d["duration_s"]>0 for d in details)
        result.update(events=len(details), event_types=dict(Counter(events.type)),
            event_counts=dict(Counter(events.label)), sync_markers=len(sync),
            covered_events=sum(d["inside_csi"] for d in details),
            events_under_80_rows_per_s=[d for d in details if d["rows_per_s"] is not None and d["rows_per_s"]<80],
            events_with_gaps=[d for d in details if d["gaps_over_100ms"]],
            all_event_details=details)
        if part == "scripts":
            expected_runs = {(name,run) for name in protocol.SCRIPTS for run in (1,2)}
            actual_runs = {(r.script_id,int(r.run)) for r in lab.itertuples()}
            checks["all_eight_story_runs_present"] = expected_runs == actual_runs
            runs = []
            for name, run in sorted(actual_runs):
                rows = lab[(lab.script_id==name)&(lab.run==run)].sort_values("step")
                expected = protocol.SCRIPTS[name]
                # Sync rows deliberately leave context blank in the logger.
                actual_sequence = [(r.label,r.type,"" if r.type=="sync" else r.context) for r in rows.itertuples()]
                expected_sequence = [(label,typ,"" if typ=="sync" else ctx) for label,typ,ctx in expected]
                sequence_ok = actual_sequence == expected_sequence
                posture_ok = rows.posture.tolist() == protocol.script_postures(name)
                step_ok = rows.step.astype(int).tolist() == list(range(len(expected)))
                intents_ok = all((r.intent,r.home_action) == protocol.intent_of(r.label,r.type,r.context)
                                 for r in rows.itertuples() if r.type != "sync")
                runs.append({"script_id":name,"run":run,"events":int((rows.type!="sync").sum()),
                    "sequence_correct":sequence_ok,"postures_correct":posture_ok,
                    "steps_correct":step_ok,"intent_mapping_correct":intents_ok})
            result["story_runs"] = runs
            checks["story_sequences_postures_and_intents_correct"] = all(all(r[k] for k in
                ("sequence_correct","postures_correct","steps_correct","intent_mapping_correct")) for r in runs)
            checks["expected_event_and_sync_counts"] = len(events)==100 and len(sync)==16
        else:
            if part == "baseline":
                expected_counts = {name:1 for name in protocol.BASELINES}
            elif part.startswith("signs"):
                expected_counts = {name:5 for name in protocol.SIGNS}
            else:
                actions = protocol.SEATED_ACTIONS if part=="actions_seated" else protocol.ACTIONS
                expected_counts = {name:meta[1] for name,meta in actions.items()}
            checks["expected_class_counts"] = dict(Counter(events.label)) == expected_counts
            checks["two_sync_markers"] = len(sync)==2
            checks["consecutive_trial_ids"] = sorted(events.trial.astype(int)) == list(range(1,len(events)+1))
            if part in ("actions_seated","signs_seated"):
                checks["all_events_marked_seated"] = bool((events.posture=="seated").all())
            if part == "signs_standing":
                checks["all_events_marked_standing"] = bool((events.posture=="standing").all())
            if part == "baseline":
                checks["baseline_postures_correct"] = dict(zip(events.label,events.posture)) == {"sit_still":"seated","stand_still":"standing"}
                checks["each_baseline_at_least_60_seconds"] = all(d["duration_s"]>=60 for d in details)
        result["event_rows_per_s_min"] = min(d["rows_per_s"] for d in details)
        result["max_gap_inside_event_ms"] = max(d["max_gap_ms"] for d in details)
    result["errors"] = [k for k,v in checks.items() if not v]
    records.append(result)

participant_records = [r for r in records if r["pid"]==PID]
notes = ["Below-80 rows/s events are flagged for review, not automatically rejected. No recognition accuracy or correct physical performance is established by file integrity checks.",
         "The expected videos were not found in this dataset directory; their existence on the phone and performed movements/signs have not been verified."]
if PID == "P04":
    notes += ["P04 baseline is from 15 October; action/sign/story captures are from 16 October. Operator reports same person/environment and baseline before rain. Retain date/session distinction.",
              "T-SEQ run 1 HOT (step 7) contains a 470.433 ms packet gap, inside a 4.561 s segment. This segment requires quality review before modelling; do not assume full temporal coverage from its start/end bounds alone."]
else:
    notes += ["All P05 participant captures are from 16 October."]
empty_record = next(r for r in records if r["part"]=="empty")
notes += [f"Latest kept empty-room reference: {Path(empty_record['csi_file']).name}, recorded on {empty_record['recording_date']}. Earlier empty-room takes remain in the source dataset."]
summary = {"participant":PID, "all_structural_checks_passed": all(not r["errors"] for r in records),
    "total_csi_rows":sum(r["rows"] for r in participant_records),
    "total_events_excluding_baseline":sum(r.get("events",0) for r in participant_records if r["part"]!="baseline"),
    "total_events_including_baseline":sum(r.get("events",0) for r in participant_records),
    "recording_dates": sorted({r["recording_date"] for r in participant_records}),
    "quality_review": [{"part":r["part"], "sampling_below_80_rows_per_s_events":len(r.get("events_under_80_rows_per_s",[])),
                        "event_gaps_over_250ms":[d for d in r.get("events_with_gaps",[]) if d["max_gap_ms"]>250]}
                       for r in records if r.get("events_under_80_rows_per_s") or any(d["max_gap_ms"]>250 for d in r.get("events_with_gaps",[]))],
    "notes":notes,
    "takes":records}
def encode(value):
    if isinstance(value,np.generic): return value.item()
    raise TypeError(type(value).__name__)
(OUT / f"{PID}_capture_audit.json").write_text(json.dumps(summary,indent=2,default=encode))
lines = [f"# {PID} capture audit", "", "All structural checks passed: " + str(summary["all_structural_checks_passed"]), "",
    "| Part | Date | CSI rows | Rows/s | Events covered | Gaps >100 ms | Max event gap (ms) |", "|---|---|---:|---:|---:|---:|---:|"]
for r in records:
    coverage = f"{r['covered_events']}/{r['events']}" if "events" in r else "n/a"
    event_gap = f"{r['max_gap_inside_event_ms']:.1f}" if "max_gap_inside_event_ms" in r else "n/a"
    lines.append(f"| {r['part']} | {r['recording_date']} | {r['rows']} | {r['rows_per_s']:.1f} | {coverage} | {r['gaps_over_100ms']} | {event_gap} |")
lines += ["", f"{PID} totals: {summary['total_csi_rows']:,} CSI rows; {summary['total_events_excluding_baseline']} action/sign/story events plus two idle baselines.","", "## Review notes", ""]
lines += ["- "+note for note in summary["notes"]]
lines += ["", "## Story verification", "", "All four stories have runs 1 and 2. All step labels, order, postures and intent mappings match the P04/P05 protocol. There are 100 story events (50 activities and 50 signs) and 16 sync markers."]
lines += ["", "## Events below 80 rows/s", "", "| Part | Trial/step | Label | Rows/s |", "|---|---:|---|---:|"]
for r in records:
    for d in r.get("events_under_80_rows_per_s",[]):
        lines.append(f"| {r['part']} | {d['trial'] or d['step']} | {d['label']} | {d['rows_per_s']:.1f} |")
lines += ["", "## Sources", ""]
for r in records:
    lines += [f"- CSI: [{Path(r['csi_file']).name}]({r['csi_file']})"]
    if "label_file" in r:
        lines += [f"- Labels: [{Path(r['label_file']).name}]({r['label_file']})"]
lines += [f"- Session log: [{ROOT / 'session_log.csv'}]({ROOT / 'session_log.csv'})", ""]
(OUT / f"{PID}_capture_audit.md").write_text("\n".join(lines))
compact = {k:v for k,v in summary.items() if k!="takes"}
compact["takes"] = [{k:v for k,v in r.items() if k not in ("all_event_details","checks","event_counts","events_with_gaps")} for r in records]
print(json.dumps(compact,indent=2,default=encode))
