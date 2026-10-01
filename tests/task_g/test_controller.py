"""Safe entry firewall tests: synthetic outputs never become final evidence."""

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from scripts.task_g import controller as c


def context():
    contract = {"permissions": {"final_labels": False},
                "source_test_snapshot_before_qualification": {"fixture": "a" * 64}}
    manifest = {k: {} for k in ("td", "dataset", "split", "exposure_ledger", "selections",
                                "r_control", "comparators", "evaluator", "packet",
                                "selection_policy", "final60_policy", "prohibited_runtime_rules")}
    manifest["selections"] = {"c5": {"detectors": [{"id": "G-MTL", "threshold": 3.14}]}}
    manifest["comparators"] = [{"id": "RCD-RCAEval-adapted-TD12"}]
    return contract, manifest, {"checked_reference_count": 44}


def fixture_seal():
    from scripts.pre_g.controller_contract import seal_synthetic_rcd_predictions
    values = c._numeric_fixture()
    rows = [{"method": "RCD-RCAEval-adapted-TD12", "seed": seed, "bins": 5,
             "status": "SUCCESS", "ranks": ["m1", "m0"], "reason": None, "error": None,
             "unknown_metric_keys": []} for seed in (420, 421, 422)]
    sealed = seal_synthetic_rcd_predictions(rows, candidate_ids=["S0", "S1", "S2"],
              metric_columns=["m0", "m1", "m2"], metric_owners={"m0": 0, "m1": 1, "m2": 2},
              input_sha256=hashlib.sha256(values.tobytes()).hexdigest())
    sealed["qualification_scope"] = "QUALIFIED_CORE_RUN"
    sealed["qualification_sha256"] = c.RCD_IDENTITY_SHA
    sealed["prediction_sha256"] = c._digest({k: v for k, v in sealed.items() if k != "prediction_sha256"})
    return sealed


class EntryControllerTests(unittest.TestCase):
    def test_closed_campaign_and_label_provider_never_called(self):
        callback = unittest.mock.Mock()
        for call in (c.run_campaign, c.evaluate_final):
            with self.assertRaises(c.EntryError):
                call(label_provider=callback)
        callback.assert_not_called()

    def test_public_execution_cannot_accept_predictions_callable_or_root(self):
        for args in ({"predictions": {}}, {"runner": lambda: None}, {"root_index": 0}):
            with self.assertRaises(TypeError):
                c.run_entry_fixture(**args)
        with self.assertRaises(c.EntryError):
            c._entry_payload_for_provenance(c.EntryExecution())
        with self.assertRaises(c.EntryError):
            c._entry_payload_for_provenance({"scope": "ENTRY_RAW_ADMISSION"})
        self.assertFalse(hasattr(c, "_bind_entry_execution"))

    def test_prepared_matrix_uses_exact_frozen_objects_and_thresholds(self):
        expected = context()
        with patch.object(c, "_registered_context", return_value=expected):
            result = c.prepare_conditions()
        self.assertEqual(result["conditions"]["scientific_objects"], expected[1])
        self.assertEqual(result["conditions"]["matrix"][3]["detectors"],
                         expected[1]["selections"]["c5"]["detectors"])
        self.assertFalse(result["conditions"]["execution_enabled"])
        self.assertEqual(result["conditions"]["planned_final_cases"], 60)
        self.assertEqual(result["conditions"]["matrix"][0]["draws_R"], 256)
        result["conditions"]["scientific_objects"]["selections"]["c5"]["detectors"][0]["threshold"] = 0
        self.assertEqual(expected[1]["selections"]["c5"]["detectors"][0]["threshold"], 3.14)

    def test_worker_stdin_is_numeric_only_fixed_command_and_digest_bound(self):
        sealed = fixture_seal()
        completed = subprocess.CompletedProcess([], 0, json.dumps(
            {"schema": "ENTRY-NUMERIC-RCD-WORKER-v1", "sealed": sealed}), "")
        with patch.object(c.subprocess, "run", return_value=completed) as worker:
            actual = c._execute_fixture()
        args, kwargs = worker.call_args
        self.assertEqual(args[0][-1], "--rcd-fixture-worker")
        self.assertIn("rcd39", args[0][0])
        payload = json.loads(kwargs["input"])
        self.assertEqual(set(payload), {"values", "owners"})
        self.assertEqual(payload["owners"], [0, 1, 2])
        self.assertEqual(np.asarray(payload["values"]).shape, (600, 3))
        self.assertEqual(actual, sealed)
        self.assertEqual(kwargs["timeout"], 300)

    def test_worker_failure_or_changed_input_fails_before_issuance(self):
        cases = [subprocess.CompletedProcess([], 1, "private token", "private token")]
        changed = fixture_seal()
        changed["input_sha256"] = "f" * 64
        cases.append(subprocess.CompletedProcess([], 0, json.dumps(
            {"schema": "ENTRY-NUMERIC-RCD-WORKER-v1", "sealed": changed}), ""))
        for completed in cases:
            with patch.object(c.subprocess, "run", return_value=completed), self.assertRaises(c.EntryError) as error:
                c._execute_fixture()
            self.assertNotIn("private token", str(error.exception))

    def test_issued_fixture_handle_payload_copies_and_phase_stays_entry(self):
        # Runtime patches are isolated fixture harnesses, outside the threat
        # model of the ordinary caller. This test is not real RCD qualification.
        with patch.object(c, "_registered_context", return_value=context()), patch.object(
            c, "_execute_fixture", return_value=fixture_seal()):
            token = c.run_entry_fixture()
            payload = c._entry_payload_for_provenance(token)
            payload["outputs"].clear()
            original = c._entry_payload_for_provenance(token)
        self.assertEqual(original["scope"], "ENTRY_SYNTHETIC_DEVELOPMENT")
        self.assertEqual(original["execution_kind"], "ENTRY_ONLY")
        self.assertEqual(len(original["outputs"][0]["items"]), 3)
        self.assertFalse(original["aggregate_report"]["final_predictions_executed"])

    def test_unissued_raw_audit_rejected_before_numeric_worker(self):
        from scripts.task_g.source_admission import SourceAdmissionError
        with patch.object(c, "_registered_context", return_value=context()), patch.object(
            c, "_execute_fixture") as worker:
            with self.assertRaises(SourceAdmissionError):
                c.run_entry_admission({"source_identity_verified": True, "case_audits": [{}] * 60})
            worker.assert_not_called()


if __name__ == "__main__":
    unittest.main()
