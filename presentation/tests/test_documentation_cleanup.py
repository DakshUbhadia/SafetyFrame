"""Check that relocation does not weaken scientific or source integrity checks."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
import verify_presentation as verifier


class CleanupIntegrityTests(unittest.TestCase):
    def test_original_records_and_current_navigation_verify(self):
        result = verifier.verify()
        self.assertEqual(result['original_frozen_files_verified'], 570)
        self.assertEqual(result['study2_protocol_files_verified'], 121)
        self.assertEqual(result['relocated_files'], 32)
        self.assertEqual(result['new_model_calls'], 0)

    def test_preserved_source_tampering_is_rejected(self):
        original = verifier.sha
        target = ROOT/'docs/archive/source_snapshots/02_EXPERIMENT_PROTOCOL.md.txt'
        with patch.object(verifier, 'sha', side_effect=lambda p: '0'*64 if p == target else original(p)):
            with self.assertRaisesRegex(ValueError, 'Archived original source changed'):
                verifier.verify()

    def test_unrecorded_presentation_edit_is_rejected(self):
        original = verifier.documentation_sha
        with patch.object(verifier, 'documentation_sha', side_effect=lambda p: '0'*64 if p == ROOT/'README.md' else original(p)):
            with self.assertRaisesRegex(ValueError, 'Reviewed cleanup document changed'):
                verifier.verify()


if __name__ == '__main__':
    unittest.main()
