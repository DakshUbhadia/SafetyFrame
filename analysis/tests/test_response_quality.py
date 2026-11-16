import copy
import json
from pathlib import Path
import tempfile
import unittest

from analysis.response_quality import enrich,metadata,summarize
from harness.artifacts import digest,write_json


def response():
    return dict(text='',summary={'usage':{'output_tokens':8192,'output_tokens_details':{'reasoning_tokens':8192}}},
        raw={'status':'incomplete','incomplete_details':{'reason':'max_output_tokens'},
             'output':[{'type':'reasoning','content':'PRIVATE_REASONING_NOT_FOR_RELEASE'}]})


class ResponseQualityTests(unittest.TestCase):
    def test_reasoning_only_cap_is_metadata_without_reasoning_content(self):
        info=metadata(response(),8192)
        self.assertTrue(info['reasoning_only_budget_exhaustion'])
        self.assertEqual(info['emitted_text_characters'],0)
        self.assertFalse(info['extraction_mismatch'])
        self.assertNotIn('PRIVATE_REASONING',json.dumps(info))

    def test_completed_text_is_not_mislabeled_as_budget_exhaustion(self):
        r=response(); r['text']='final code'; r['raw']={'status':'completed','output':[
            {'type':'message','content':[{'type':'output_text','text':'final code'}]}]}
        info=metadata(r,8192)
        self.assertFalse(info['reasoning_only_budget_exhaustion'])
        self.assertFalse(info['extraction_mismatch'])
        self.assertEqual(info['raw_message_characters'],10)

    def test_unextracted_final_message_is_detected(self):
        r=response(); r['raw']['output'].append({'type':'message','content':[{'type':'output_text','text':'actual code'}]})
        self.assertTrue(metadata(r,8192)['extraction_mismatch'])

    def test_enrichment_checks_hashes_and_leaves_frozen_scores_unchanged(self):
        r=response(); outcome={'turn':1,'result':r}
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); write_json(root/'response.json',outcome)
            data={'records':[dict(trajectory={'condition':'C'},attempts=[
                {'file':'response.json','outcome_hash':digest(outcome)}],
                turns=[{'response_hash':digest(r),'tcs':0,'format_success':False}])]}
            enrich(data,root,8192)
            self.assertEqual(data['records'][0]['turns'][0]['tcs'],0)
            info=summarize(data['records'],('C','S'))
            self.assertEqual(info['reasoning_only_budget_exhaustions'],1)
            self.assertFalse(info['scoring_changed'])
            self.assertFalse(info['additional_inference'])
            data['records'][0]['attempts'][0]['outcome_hash']='wrong'
            with self.assertRaises(ValueError): enrich(data,root,8192)

    def test_integration_mismatch_stops_annotation_instead_of_blaming_model(self):
        r=response(); r['raw']['output']=[{'type':'message','content':[{'type':'output_text','text':'actual code'}]}]
        outcome={'turn':1,'result':r}
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); write_json(root/'response.json',outcome)
            data={'records':[dict(attempts=[{'file':'response.json','outcome_hash':digest(outcome)}],
                                 turns=[{'response_hash':digest(r)}])]}
            with self.assertRaisesRegex(ValueError,'Raw final text'):
                enrich(data,root,8192)


if __name__=='__main__':
    unittest.main()
