"""Verify or execute one scheduled main trajectory; never generates by default."""
import argparse
import time

from .artifacts import digest,read_json,write_json
from .budget import BudgetLedger,exclusive_lock
from .freeze import planned_rows,verify_freeze
from .preflight import ROOT,load_env
from .providers.adaption import AdaptionProvider
from .run_tests import TestRunner
from .task_bundle import TaskBundle


class FrozenProvider:
    name='adaption'

    def __init__(self,config,execution,manifest,role,clock=time.time,sleep=time.sleep):
        self.config=config['providers'][config['models'][role]['provider']]
        self.model=config['models'][role]
        self.execution=execution
        self.manifest_hash=digest(manifest)
        self.inner=AdaptionProvider(self.config)
        self.clock,self.sleep=clock,sleep
        self.state=ROOT/'data/main/request_pacing.json'

    def generate(self,messages,model):
        current=verify_freeze()
        if digest(current)!=self.manifest_hash or model!=self.model:
            raise ValueError('Freeze or model changed between requests')
        interval=self.execution['provider_pacing']['minimum_request_start_interval_seconds']
        with exclusive_lock(self.state.with_suffix('.lock')):
            previous=read_json(self.state)['last_request_start'] if self.state.exists() else None
            if previous is not None:
                # Wall clock persists across processes. Clock rollback causes a
                # conservative wait, never an immediate extra request.
                remaining=previous+interval-self.clock()
                while remaining>0:
                    self.sleep(min(remaining,30))
                    remaining=previous+interval-self.clock()
            write_json(self.state,{'last_request_start':self.clock()})
            # Recheck after waiting, before crossing the network boundary.
            if digest(verify_freeze())!=self.manifest_hash:
                raise ValueError('Freeze changed during pacing wait')
            return self.inner.generate(messages,model)


def enforce_order(row,rows,output):
    for preceding in rows:
        if preceding['run_id']==row['run_id']: break
        result=output/'scored'/f"{preceding['run_id']}.json"
        if not result.exists():
            raise ValueError('Earlier frozen trajectory is unresolved: '+preceding['run_id'])
        record=read_json(result)
        state=read_json(output/'runs'/preceding['run_id']/'state.json')
        if (state.get('result_hash')!=digest(record) or record['trajectory']['run_id']!=preceding['run_id']
                or record['trajectory']['status'] not in ('completed','provider_failed')):
            raise ValueError('Earlier trajectory needs reconciliation')
        execution=read_json(ROOT/'config/execution.json')
        if record['trajectory'].get('provider_failure_type') in execution['collection']['pause_on_failure']:
            # A documented operational decision must precede continuation.
            acknowledgement=output/'operational_reviews'/f"{preceding['run_id']}.json"
            if not acknowledgement.exists():
                raise ValueError('Provider failure requires documented operational review: '+preceding['run_id'])
            review=read_json(acknowledgement)
            if (review.get('result_hash')!=digest(record) or review.get('decision')!='continue_remaining_schedule'
                    or not review.get('reason') or not review.get('reviewer') or not review.get('timestamp_utc')):
                raise ValueError('Operational review is incomplete or stale')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id',required=True)
    parser.add_argument('--execute',action='store_true',help='Sends paid API requests for this scheduled trajectory')
    args=parser.parse_args()
    manifest=verify_freeze()
    rows=planned_rows()
    matches=[r for r in rows if r['run_id']==args.run_id]
    if len(matches)!=1: raise ValueError('Unknown frozen run ID')
    row=matches[0]
    if not args.execute:
        print(f"Verified frozen run {row['run_id']}: role {row['role']}, condition {row['condition']}, execution order {row['execution_order']}. No inference sent.")
        return
    config=read_json(ROOT/'config/study.json'); execution=read_json(ROOT/'config/execution.json')
    output=ROOT/execution['collection']['output']
    with exclusive_lock(output/'.collection.lock'):
        enforce_order(row,rows,output)
        load_env(ROOT/'.env')
        provider=FrozenProvider(config,execution,manifest,row['role'])
        runner=TestRunner('docker',execution['executor']['image'],execution['executor']['timeout_seconds'])
        ledger=BudgetLedger(ROOT/'data/usage_ledger.json',config,
                            spend_ceiling=execution['collection']['budget_spend_ceiling_credits'])
        from .run_experiment import run_trajectory
        result=run_trajectory(TaskBundle.load(ROOT/row['task_path']),row['condition'],config,row['role'],
                              provider,runner,output,row['run_id'],row['block_id'],int(row['within_block_order']),ledger)
        print(f"Run {row['run_id']}: {result['trajectory']['status']}")
        return 0 if result['trajectory']['status']=='completed' else 1


if __name__=='__main__':
    # Use the canonical module's class identity even when invoked with -m;
    # authorize_final imports that same FrozenProvider class.
    from .run_frozen import main as entry_main
    raise SystemExit(entry_main())
