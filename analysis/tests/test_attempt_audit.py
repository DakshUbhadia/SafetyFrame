from pathlib import Path
import tempfile
import unittest

from analysis.model_a import audit_attempts
from harness.artifacts import write_json


class AttemptAuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        self.model={'model_id':'model','generation':{'temperature':0,'max_output_tokens':8192}}
        self.policy={'maximum_retries_per_turn':2,'retryable':['timeout','transport','5xx']}
        self.context={'run_id':'test'}

    def pair(self,turn,attempt,result=False,failure='timeout',retryable=True):
        prefix=f'turn{turn}-attempt{attempt}'
        common=dict(turn=turn,attempt=attempt,context=self.context)
        write_json(self.root/(prefix+'-request.json'),dict(**common,**self.model))
        outcome=dict(common)
        if result: outcome['result']={'text':'even malformed output is a nonretryable response'}
        else: outcome.update(failure=failure,retryable=retryable)
        write_json(self.root/(prefix+'-outcome.json'),outcome)

    def test_permitted_retries_are_paired_contiguous_and_hash_logged(self):
        self.pair(1,0); self.pair(1,1,result=True); self.pair(2,0,result=True)
        entries=audit_attempts(self.root,self.model,self.policy,self.context)
        self.assertEqual(len(entries),3)
        self.assertTrue(all(len(request_hash)==64 for path,outcome,request_hash in entries))

    def test_responses_or_nonretryable_failures_cannot_be_rerun(self):
        for first in ('response','filter'):
            with self.subTest(first=first):
                self.pair(1,0,result=first=='response',failure='provider_filter',retryable=False)
                self.pair(1,1,result=True)
                with self.assertRaisesRegex(ValueError,'Nonretryable'):
                    audit_attempts(self.root,self.model,self.policy,self.context)

    def test_unreconciled_request_or_changed_generation_is_rejected(self):
        self.pair(1,0,result=True)
        write_json(self.root/'turn2-attempt0-request.json',{})
        with self.assertRaisesRegex(ValueError,'Unreconciled'):
            audit_attempts(self.root,self.model,self.policy,self.context)


if __name__=='__main__':
    unittest.main()
