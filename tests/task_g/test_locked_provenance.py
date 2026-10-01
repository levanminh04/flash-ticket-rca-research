"""Synthetic-only integrity fixtures; none issue production execution handles."""
import copy
import json
from pathlib import Path
import secrets
import unittest
from unittest.mock import patch

from scripts.task_g import locked_provenance as p
from scripts.task_g import locked_campaign as c


class ShardTests(unittest.TestCase):
    def setUp(self):
        self.directory = p.ROOT / 'cache' / ('unit-shards-' + secrets.token_hex(8))
        self.store = p.ShardStore(self.directory)

    def test_roundtrip_numeric_masks_and_missing(self):
        value = {'shape': [2, 3], 'mask': [True, False], 'missing': None, 'finite': 1.25}
        ref = self.store.put(value); self.store.verify(ref)
        self.assertEqual(self.store.get(ref), value)

    def test_large_text_is_losslessly_sharded(self):
        value = {'scope': 'SYNTHETIC_ONLY_CAPACITY', 'message': 'ký tự "\n' * 650000}
        ref = self.store.put(value); seen = set(); self.store.verify(ref, seen)
        self.assertGreater(len(seen), 2)
        self.assertEqual(self.store.get(ref), value)
        self.assertLessEqual(self.store.maximum_frame_bytes, p.MAX_FRAME)

    def test_content_addressed_dedup_does_not_overwrite(self):
        left = self.store.put({'sample': 'same'}); right = self.store.put({'sample': 'same'})
        self.assertEqual(left, right); self.assertEqual(self.store.new_files, 1)

    def test_tamper_is_rejected_on_read_and_reuse(self):
        ref = self.store.put({'sample': 1}); path = p.W / ref['path']
        original = path.read_bytes()
        # A distinct fixture file preserves original bytes in the test evidence.
        (self.directory / 'original-before-tamper.bin').write_bytes(original)
        path.write_bytes(original.replace(b'1', b'2'))
        with self.assertRaises(p.Error): self.store.get(ref)
        with self.assertRaises(p.Error): self.store.put({'sample': 1})

    def test_missing_stale_length_and_path_escape(self):
        ref = self.store.put([1, 2])
        for key, value in (('bytes', ref['bytes'] + 1), ('path', '../elsewhere.json'),
                           ('sha256', '0' * 64)):
            wrong = {**ref, key: value}
            with self.subTest(key=key), self.assertRaises((p.Error, OSError)):
                self.store.get(wrong)

    def test_seen_digest_does_not_hide_wrong_reference(self):
        ref = self.store.put({'synthetic_only': 1}); seen = set(); self.store.verify(ref, seen)
        for wrong in ({**ref, 'path': '../escape.json'}, {**ref, 'bytes': ref['bytes'] + 1}, {**ref, 'extra': True}):
            with self.subTest(wrong=wrong), self.assertRaises(p.Error): self.store.verify(wrong, seen)

    def test_duplicate_json_fields_and_nonfinite_rejected(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{ "x":1}'):
            with self.subTest(raw=raw), self.assertRaises(p.Error): p.decode(raw)

    def test_array_nan_mask_envelope_is_preserved(self):
        import numpy as np
        from scripts.task_g.final_campaign import _scientific_plain, _unpack
        array = np.array([np.nan, 1.])
        ref = self.store.put(_scientific_plain(array))
        np.testing.assert_array_equal(_unpack(self.store.get(ref)), array)

    def test_hydration_budget_is_explicit(self):
        ref = self.store.put('synthetic' * 200)
        with self.assertRaises(p.Error): self.store.get(ref, budget=[100])

    def test_unissued_or_helper_execution_cannot_seal(self):
        for handle in ({'scope': 'ACTUAL_FINAL60'}, c.Execution(), object()):
            with self.subTest(handle=type(handle)), self.assertRaises(p.Error): p.commit_execution(handle)

    def test_preparation_flags_cannot_be_used_as_final_authorization(self):
        for phase in (p.PREP_PHASE, p.FINAL_PHASE):
            with patch.object(p, 'registered_context', return_value=({'phase': phase}, {'permissions': {
                    'final_predictions': False, 'final_campaign': False, 'final_root_fault': False, 'final_labels': False}})):
                with self.assertRaises(p.Error): p.require_final_authorization()

    def test_failed_stage_fsync_verification_or_context_cannot_publish(self):
        # Synthetic-only isolated publisher seam; no production execution handle.
        for failure in ('fsync', 'verify', 'context'):
            root = self.directory / failure
            root.mkdir(parents=True)
            with (patch.object(p, 'ROOT', root),
                  patch.object(p, 'registered_context', return_value=({'x': 2 if failure == 'context' else 1}, {})),
                  patch.object(p, '_verify_envelope', side_effect=p.Error('INTEGRITY') if failure == 'verify' else None),
                  patch.object(p.os, 'fsync', side_effect=OSError('FSYNC') if failure == 'fsync' else None)):
                with self.assertRaises((p.Error, OSError)):
                    p._publish_verified_envelope({'synthetic_only_unqualified': True}, {'x': 1}, False)
            self.assertFalse((root / 'cache/preparation-seal.json').exists())
            self.assertEqual(len(list((root / 'cache').glob('seal-stage-*.json'))), 1)

    def test_descriptor_bytes_detect_same_length_source_drift_and_duplicate(self):
        path = self.directory / 'artificial/metrics.parquet'
        path.parent.mkdir(parents=True); path.write_bytes(b'SYNTHETIC')
        descriptors = [{'path': 'artificial/metrics.parquet', 'bytes': path.stat().st_size, 'sha256': p.sha_file(path)}]
        p._verify_descriptor_bytes(self.directory, descriptors)
        with self.assertRaises(p.Error): p._verify_descriptor_bytes(self.directory, descriptors * 2)
        path.write_bytes(b'SYNTHETIX')
        with self.assertRaises(p.Error): p._verify_descriptor_bytes(self.directory, descriptors)

    def test_proposal_marker_is_not_an_atomic_user_final_authorization(self):
        root = self.directory / 'proposal'
        snapshot = root / 'cache/final-authorization-decision-snapshot.md'
        snapshot.parent.mkdir(parents=True)
        marker = 'G33_FINAL60_PREDICTIONS_AND_POST_SEAL_ROOT_FAULT_TAU'
        snapshot.write_text(f'| RCA-999 | {marker} | CANDIDATE | Proposal only |', encoding='utf-8')
        contract = {'permissions': dict.fromkeys(('final_predictions', 'final_campaign', 'final_root_fault', 'final_labels'), True),
                    'human_final_authorization': {'decision_id': 'RCA-999', 'sha256': p.sha_file(snapshot)}}
        with (patch.object(p, 'ROOT', root), patch.object(p, 'registered_context', return_value=({'phase': p.FINAL_PHASE}, contract)),
              patch.object(p, 'verify_seal') as seal):
            with self.assertRaises(p.Error): p.require_final_authorization()
            seal.assert_not_called()


if __name__ == '__main__': unittest.main()
