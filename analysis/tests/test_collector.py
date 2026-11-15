from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch

from harness.artifacts import digest,read_json,write_json
from scripts.collect_frozen import collect


class CollectorTests(unittest.TestCase):
    def test_collects_exact_frozen_phase_in_order_without_model_calls_in_test(self):
        rows=[dict(role='A',run_id=f'run-{i}') for i in range(64)]+[dict(role='B',run_id='never')]
        with tempfile.TemporaryDirectory() as temporary,redirect_stdout(io.StringIO()):
            root=Path(temporary)
            write_json(root/'config/execution.json',{'collection':{'pause_on_failure':['rate_limit']}})
            calls=[]
            def execute(command,cwd):
                run=command[-2]; calls.append(run)
                record={'trajectory':{'status':'completed','provider_failure_type':'none'}}
                write_json(root/'data/main/scored'/f'{run}.json',record)
                write_json(root/'data/main/runs'/run/'state.json',{'result_hash':digest(record)})
                return Mock(returncode=0)
            with patch('scripts.collect_frozen.ROOT',root),patch('scripts.collect_frozen.verify_freeze',return_value={}),patch(
                    'scripts.collect_frozen.planned_rows',return_value=rows),patch(
                    'scripts.collect_frozen.enforce_order'),patch('scripts.collect_frozen.subprocess.run',side_effect=execute):
                collect('A')
            self.assertEqual(calls,[r['run_id'] for r in rows if r['role']=='A'])
            self.assertEqual(read_json(root/'data/main/collector-A.json')['status'],'terminal')

    def test_missing_outcome_stops_without_skipping_or_resending(self):
        rows=[dict(role='A',run_id=f'run-{i}') for i in range(64)]
        with tempfile.TemporaryDirectory() as temporary,redirect_stdout(io.StringIO()):
            with patch('scripts.collect_frozen.ROOT',Path(temporary)),patch('scripts.collect_frozen.verify_freeze',return_value={}),patch(
                    'scripts.collect_frozen.planned_rows',return_value=rows),patch('scripts.collect_frozen.enforce_order'),patch(
                    'scripts.collect_frozen.subprocess.run',return_value=Mock(returncode=2)) as execute:
                with self.assertRaisesRegex(RuntimeError,'reconcile'):
                    collect('A')
                self.assertEqual(execute.call_count,1)

    def test_operational_failure_requires_the_frozen_review_before_next_run(self):
        rows=[dict(role='A',run_id=f'run-{i}') for i in range(64)]
        with tempfile.TemporaryDirectory() as temporary,redirect_stdout(io.StringIO()):
            root=Path(temporary)
            write_json(root/'config/execution.json',{'collection':{'pause_on_failure':['rate_limit']}})
            def execute(command,cwd):
                run=command[-2]
                record={'trajectory':{'status':'provider_failed','provider_failure_type':'rate_limit'}}
                write_json(root/'data/main/scored'/f'{run}.json',record)
                write_json(root/'data/main/runs'/run/'state.json',{'result_hash':digest(record)})
                return Mock(returncode=1)
            with patch('scripts.collect_frozen.ROOT',root),patch('scripts.collect_frozen.verify_freeze',return_value={}),patch(
                    'scripts.collect_frozen.planned_rows',return_value=rows),patch(
                    'scripts.collect_frozen.enforce_order',side_effect=[None,ValueError('review required')]),patch(
                    'scripts.collect_frozen.subprocess.run',side_effect=execute) as process:
                with self.assertRaisesRegex(RuntimeError,'operational review'):
                    collect('A')
                self.assertEqual(process.call_count,1)
            self.assertEqual(read_json(root/'data/main/collector-A.json')['status'],'operational_review_required')


if __name__=='__main__':
    unittest.main()
