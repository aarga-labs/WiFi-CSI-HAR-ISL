from pathlib import Path
import json,sys,os,shutil
os.environ['MPLBACKEND']='Agg'
import fyp_fast as fyp
spec=json.loads(Path(sys.argv[2]).read_text())
out=Path(spec['out']);out.mkdir(parents=True,exist_ok=True)
fyp.summarize(out)
import matplotlib.pyplot as plt
plt.close('all')
completed=[p for p in fyp.PIDS if (out/p/'complete.json').exists()]
fyp.atomic_json(dict(completed_test_participants=completed,evaluation_complete=len(completed)==5,
    all_five_model_ready=(out/'deployment_all5/model_card.json').exists(),report_generated=True),out/'run_completion.json')
archive=fyp.archive_outputs(out)
print('[RESULTS ZIP]',archive,flush=True)
