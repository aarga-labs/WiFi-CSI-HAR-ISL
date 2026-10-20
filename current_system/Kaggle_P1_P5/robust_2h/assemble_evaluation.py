"""Combine saved members and choose thresholds using inner validation only."""
from pathlib import Path
import json
import sys
import time
import joblib
import fyp_robust as R

def main(spec):
    streams=joblib.load(spec['streams']);done=[];missing=[]
    for test in R.PIDS:
        R.C.atomic_json(dict(time=time.time(),phase='assembling held-out '+test),spec['progress'])
        try:R.score_outer(dict(spec,test=test),streams);done.append(test)
        except AssertionError as exc:missing.append(str(exc));print('[INCOMPLETE]',exc,flush=True)
    R.C.atomic_json(dict(completed=done,missing=missing),Path(spec['out'])/'evaluation_assembly.json')

if __name__=='__main__':main(json.loads(Path(sys.argv[2]).read_text()))
