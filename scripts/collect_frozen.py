"""Serial collector for one frozen model phase; preserves the frozen runtime."""
import argparse
from datetime import datetime,timezone
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from harness.artifacts import digest,read_json,write_json
from harness.budget import exclusive_lock
from harness.freeze import planned_rows,verify_freeze
from harness.run_frozen import enforce_order


def collect(role):
    manifest=verify_freeze()
    rows=planned_rows()
    selected=[row for row in rows if row['role']==role]
    if len(selected)!=(64 if role=='A' else 32): raise ValueError('Incomplete frozen phase')
    output=ROOT/'data/main'
    output.mkdir(parents=True,exist_ok=True)
    progress=output/f'collector-{role}.json'
    with exclusive_lock(output/'.phase-collector.lock'):
        for index,row in enumerate(selected,1):
            # run_frozen independently verifies existing responses/workspaces
            # when resuming a terminal run; it never repeats its inference.
            verify_freeze()
            enforce_order(row,rows,output)
            write_json(progress,dict(role=role,status='running',run_id=row['run_id'],
                phase_position=index,phase_total=len(selected),
                freeze_hash=digest(manifest),timestamp_utc=datetime.now(timezone.utc).isoformat()))
            print(f"[{index}/{len(selected)}] {row['run_id']}: start/resume",flush=True)
            process=subprocess.run([sys.executable,'-m','harness.run_frozen','--run-id',row['run_id'],'--execute'],cwd=ROOT)
            path=output/'scored'/f"{row['run_id']}.json"
            if not path.exists():
                raise RuntimeError('No terminal record; reconcile this exact run before resumption: '+row['run_id'])
            record=read_json(path)
            state=read_json(output/'runs'/row['run_id']/'state.json')
            if state.get('result_hash')!=digest(record): raise ValueError('Terminal record checksum mismatch')
            status=record['trajectory']['status']
            if status not in ('completed','provider_failed'): raise ValueError('Nonterminal run')
            print(f"[{index}/{len(selected)}] {row['run_id']}: {status}; exit={process.returncode}",flush=True)
            # Evaluate the frozen operational pause rules even for the last
            # phase row. Never manufacture an acknowledgement to bypass them.
            execution=read_json(ROOT/'config/execution.json')
            failure=record['trajectory'].get('provider_failure_type')
            if failure in execution['collection']['pause_on_failure']:
                try:
                    enforce_order({'run_id':'phase-review-boundary'},[row],output)
                except ValueError as exc:
                    write_json(progress,dict(role=role,status='operational_review_required',
                        run_id=row['run_id'],failure=failure,phase_position=index,phase_total=len(selected)))
                    raise RuntimeError('Frozen operational review required: '+str(failure)) from exc
        write_json(progress,dict(role=role,status='terminal',phase_total=len(selected),
            freeze_hash=digest(manifest),timestamp_utc=datetime.now(timezone.utc).isoformat()))
        print(f'Phase {role}: all {len(selected)} planned trajectories have terminal records.',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--role',choices=('A','B'),required=True)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    if not args.execute:
        verify_freeze()
        print('Verification only. Collection requires --execute.')
        return
    collect(args.role)


if __name__=='__main__':
    main()
