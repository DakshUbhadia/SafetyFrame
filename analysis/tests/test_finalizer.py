from pathlib import Path
import tempfile
import unittest

from harness.artifacts import write_json
from scripts.finish_model_a import NUMERICAL_FILES,compare_outputs,ready


class FinalizerTests(unittest.TestCase):
    def test_analysis_waits_for_terminal_collector_and_refuses_operational_pause(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); progress=root/'data/main/collector-A.json'
            with self.assertRaises(ValueError): ready(root)
            write_json(progress,{'status':'running'})
            with self.assertRaises(ValueError): ready(root)
            lock=root/'data/main/.phase-collector.lock'; lock.touch()
            self.assertFalse(ready(root))
            write_json(progress,{'status':'operational_review_required'})
            with self.assertRaises(ValueError): ready(root)
            write_json(progress,{'status':'terminal','phase_total':64})
            self.assertTrue(ready(root))

    def test_reproduction_compares_every_numeric_table_and_rejects_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            a=Path(temporary)/'a'; b=Path(temporary)/'b'; a.mkdir(); b.mkdir()
            for name in NUMERICAL_FILES:
                (a/name).write_text('same\n'); (b/name).write_text('same\n')
            self.assertEqual(len(compare_outputs(a,b)),len(NUMERICAL_FILES))
            (b/'model_a_contrasts.csv').write_text('different\n')
            with self.assertRaisesRegex(ValueError,'contrasts'):
                compare_outputs(a,b)


if __name__=='__main__':
    unittest.main()
