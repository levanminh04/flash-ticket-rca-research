"""Synthetic-only PRE-G checks; no corpus files, final IDs, or final labels."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from rca.qualified_rcd import QualifiedRcdRunner
from scripts.pre_g import controller_contract as controller
from scripts.pre_g.controller_contract import (
    ControllerContractError,
    evaluate_rcd_seal,
    run_registered_rcd_triplet,
    score_service_vector,
    seal_synthetic_rcd_predictions,
    verify_rcd_seal,
)


def success(seed, ranks, columns=("m0", "m1", "m2")):
    return {
        "method": "RCD-RCAEval-adapted-TD12",
        "seed": seed,
        "bins": 5,
        "status": "SUCCESS",
        "ranks": ranks,
        "reason": None,
        "error": None,
        "unknown_metric_keys": [key for key in ranks if key not in columns],
    }


def failure(seed):
    return {
        "method": "RCD-RCAEval-adapted-TD12",
        "seed": seed,
        "bins": 5,
        "status": "FAILURE",
        "ranks": None,
        "reason": "upstream_exception",
        "error": "ValueError",
    }


class ControllerContractTests(unittest.TestCase):
    def setUp(self):
        self.rows = [success(421, ["m1"]), failure(422), success(420, ["m1", "ghost", "m0"])]
        self.inputs = {
            "candidate_ids": ["svc-a", "svc-b", "svc-c"],
            "metric_columns": ["m0", "m1", "m2"],
            "metric_owners": {"m0": 0, "m1": 1, "m2": 2},
            "input_sha256": "a" * 64,
        }

    def seal(self, rows=None, **changes):
        return seal_synthetic_rcd_predictions(
            copy.deepcopy(self.rows if rows is None else rows),
            **{**copy.deepcopy(self.inputs), **changes},
        )

    def test_three_seed_metric_mean_owner_mapping_unknown_coverage_and_failed_zero(self):
        sealed = self.seal()
        self.assertTrue(verify_rcd_seal(sealed))
        self.assertEqual([row["seed"] for row in sealed["seed_outputs"]], [420, 421, 422])
        self.assertEqual(sealed["qualification_scope"], "SYNTHETIC_UNQUALIFIED")
        result = evaluate_rcd_seal(sealed, root_index=2, allow_synthetic_fixture=True)
        self.assertEqual(result["qualification_scope"], "SYNTHETIC_UNQUALIFIED")
        self.assertEqual(result["evidence_scope"], "PRE_G_SYNTHETIC_TEST_ONLY")
        self.assertEqual(result["planned_seeds"], [420, 421, 422])
        self.assertEqual(result["per_seed"][0]["service_scores"], [1.0, 2.0, 0.0])
        self.assertEqual(result["per_seed"][0]["mapping"]["unknown_metric_keys"], ["ghost"])
        self.assertEqual(result["per_seed"][1]["service_scores"], [0.0, 1.0, 0.0])
        self.assertEqual(result["per_seed"][1]["metrics"]["tie_start"], 2)
        self.assertEqual(result["per_seed"][1]["metrics"]["tie_end"], 3)
        self.assertEqual(result["per_seed"][2]["metrics"]["status"], "METHOD_FAILURE")
        self.assertAlmostEqual(result["mean"]["rr"], 0.25)
        self.assertEqual((result["success_seeds"], result["failure_seeds"]), (2, 1))
        self.assertEqual(result["unknown_key_count"], 1)

    def test_empty_success_is_a_valid_complete_worst_tie(self):
        sealed = self.seal(rows=[success(seed, []) for seed in (420, 421, 422)])
        result = evaluate_rcd_seal(sealed, root_index=2, allow_synthetic_fixture=True)
        self.assertEqual(result["per_seed"][0]["mapping"]["ranked_services"], 0)
        self.assertEqual(result["per_seed"][0]["metrics"]["status"], "VALID_TIE")
        self.assertEqual(result["valid_empty_seeds"], 3)
        self.assertEqual((result["per_seed"][0]["metrics"]["tie_start"],
                          result["per_seed"][0]["metrics"]["tie_end"]), (1, 3))
        self.assertAlmostEqual(result["mean"]["rr"], (1 + 1 / 2 + 1 / 3) / 3)

    def test_root_absence_is_zero_without_dropping_planned_seeds(self):
        result = evaluate_rcd_seal(self.seal(), root_index=None, allow_synthetic_fixture=True)
        self.assertFalse(result["root_in_candidate"])
        self.assertEqual(result["mean"]["rr"], 0.0)
        self.assertEqual(result["per_seed"][0]["metrics"]["status"], "ROOT_ABSENT")
        self.assertEqual(result["per_seed"][2]["metrics"]["status"], "METHOD_FAILURE")

    def test_missing_duplicate_and_unregistered_seeds_or_bins_fail_closed(self):
        for rows in (
            self.rows[:2],
            [success(420, []), success(420, []), success(422, [])],
            [success(420, []), success(421, []), success(999, [])],
        ):
            with self.subTest(rows=rows), self.assertRaises(ControllerContractError):
                self.seal(rows=rows)
        changed = copy.deepcopy(self.rows)
        changed[0]["bins"] = 3
        with self.assertRaises(ControllerContractError):
            self.seal(rows=changed)

    def test_malformed_duplicate_rank_and_owner_map_fail_closed(self):
        for ranks in (["m0", "m0"], [None], [math.nan]):
            changed = copy.deepcopy(self.rows)
            changed[0] = success(421, ranks)
            with self.subTest(ranks=ranks), self.assertRaises(ControllerContractError):
                self.seal(rows=changed)
        with self.assertRaises(ControllerContractError):
            self.seal(metric_owners={"m0": 0, "m1": 1})
        with self.assertRaises(ControllerContractError):
            self.seal(metric_owners={"m0": 0, "m1": 1, "m2": math.nan})

    def test_tampering_is_rejected_before_evaluator(self):
        sealed = self.seal()
        sealed["seed_outputs"][0]["ranks"].append("m2")
        with patch("scripts.pre_g.controller_contract.tie_metrics") as evaluator:
            with self.assertRaises(ControllerContractError):
                evaluate_rcd_seal(sealed, root_index=2, allow_synthetic_fixture=True)
            evaluator.assert_not_called()
        with self.assertRaises(ControllerContractError):
            evaluate_rcd_seal({"seed_outputs": self.rows}, root_index=2)
        with self.assertRaises(ControllerContractError):
            evaluate_rcd_seal(self.seal(), root_index=2)

    def test_rehashed_synthetic_output_cannot_claim_qualified_provenance(self):
        sealed = self.seal()
        sealed["qualification_scope"] = "QUALIFIED_CORE_RUN"
        sealed["qualification_sha256"] = "0" * 64
        plain = {key: value for key, value in sealed.items() if key != "prediction_sha256"}
        sealed["prediction_sha256"] = hashlib.sha256(
            json.dumps(plain, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False).encode("utf-8")
        ).hexdigest()
        with self.assertRaisesRegex(ControllerContractError, "not issued"):
            verify_rcd_seal(sealed)
        for allow_fixture in (False, True):
            with patch("scripts.pre_g.controller_contract.tie_metrics") as evaluator:
                with self.assertRaisesRegex(ControllerContractError, "not issued"):
                    evaluate_rcd_seal(
                        sealed, root_index=2, allow_synthetic_fixture=allow_fixture
                    )
                evaluator.assert_not_called()

    def test_private_sealing_helper_cannot_issue_qualification(self):
        sealed = controller._seal_rcd_predictions(
            copy.deepcopy(self.rows), **self.inputs,
            qualification_scope="QUALIFIED_CORE_RUN", qualification_sha256="a" * 64,
        )
        with self.assertRaisesRegex(ControllerContractError, "not issued"):
            verify_rcd_seal(sealed)
        self.assertFalse(hasattr(controller, "_bind_issued_triplets"))
        self.assertFalse(hasattr(controller, "_run_registered_rcd_triplet"))

    def test_oracle_fields_and_absolute_paths_cannot_enter_prediction_seal(self):
        changed = copy.deepcopy(self.rows)
        changed[0]["root_cause_service"] = "svc-c"
        with self.assertRaises(ControllerContractError):
            self.seal(rows=changed)
        with self.assertRaises(ControllerContractError):
            self.seal(candidate_ids=["C:\\private\\answer", "svc-b", "svc-c"])
        changed = copy.deepcopy(self.rows)
        changed[0] = success(421, ["C:\\private\\answer"])
        with self.assertRaises(ControllerContractError):
            self.seal(rows=changed)
        with self.assertRaises(ControllerContractError):
            self.seal(candidate_ids=["../answer.txt", "svc-b", "svc-c"])
        with self.assertRaises(ControllerContractError):
            self.seal(candidate_ids=["case/labels", "svc-b", "svc-c"])
        changed = copy.deepcopy(self.rows)
        changed[0] = success(421, ["case\\labels"])
        with self.assertRaises(ControllerContractError):
            self.seal(rows=changed)

    def test_nonfinite_numeric_output_rejected_before_root_absent_shortcut(self):
        with patch("scripts.pre_g.controller_contract.tie_metrics") as evaluator:
            with self.assertRaises(ControllerContractError):
                score_service_vector([math.nan], None)
            evaluator.assert_not_called()
        with self.assertRaises(ControllerContractError):
            score_service_vector([1.0], 9)

    def test_registered_triplet_calls_exact_seeds_on_equal_copies_and_seals_failures(self):
        frame = pd.DataFrame({
            "time": np.arange(600, dtype=np.float64),
            "m0": np.arange(600, dtype=np.float64),
            "m1": np.arange(600, dtype=np.float64) + 1,
            "m2": np.arange(600, dtype=np.float64) + 2,
        })
        expected = frame.copy(deep=True)
        input_sha256 = hashlib.sha256(
            np.ascontiguousarray(frame[["m0", "m1", "m2"]].to_numpy(), dtype="<f8").tobytes()
        ).hexdigest()
        calls = []

        def synthetic_rcd(received, *, seed, bins, qualified_rcd):
            self.assertIs(qualified_rcd, handle)
            self.assertEqual(bins, 5)
            pd.testing.assert_frame_equal(received, expected)
            calls.append(seed)
            received.loc[0, "m0"] = -999.0
            if seed == 421:
                raise RuntimeError("synthetic failure must be redacted")
            return success(seed, ["m1", "m0"])

        handle = object.__new__(QualifiedRcdRunner)
        object.__setattr__(handle, "_identity", json.dumps({"fixture": "synthetic"}))
        with patch("rca.qualified_rcd.qualified_callable", return_value=lambda: None), patch(
            "rca.comparators.rcd_run", side_effect=synthetic_rcd
        ), patch("scripts.pre_g.controller_contract.tie_metrics") as evaluator:
            sealed = run_registered_rcd_triplet(
                frame,
                qualified_rcd=handle,
                input_sha256=input_sha256,
                **{key: self.inputs[key] for key in ("candidate_ids", "metric_columns", "metric_owners")},
            )
            evaluator.assert_not_called()
        self.assertEqual(calls, [420, 421, 422])
        pd.testing.assert_frame_equal(frame, expected)
        self.assertTrue(verify_rcd_seal(sealed))
        self.assertTrue(verify_rcd_seal(json.loads(json.dumps(sealed))))
        self.assertEqual(sealed["qualification_scope"], "QUALIFIED_CORE_RUN")
        self.assertEqual(len(sealed["qualification_sha256"]), 64)
        self.assertEqual(sealed["seed_outputs"][1]["status"], "FAILURE")
        self.assertEqual(sealed["seed_outputs"][1]["reason"], "controller_exception")
        self.assertEqual(sealed["seed_outputs"][1]["error"], "RuntimeError")
        evaluated = evaluate_rcd_seal(sealed, root_index=2)
        self.assertEqual(evaluated["per_seed"][1]["metrics"]["rr"], 0)
        self.assertEqual(
            evaluated["evidence_scope"], "QUALIFIED_CONTROLLER_OUTPUT__PERSISTENCE_STILL_REQUIRED"
        )
        # A genuine qualification digest cannot authorize altered predictions
        # or owner mapping, even after the caller recomputes the outer hash.
        for field in ("ranks", "owners"):
            changed = copy.deepcopy(sealed)
            if field == "ranks":
                changed["seed_outputs"][0]["ranks"] = ["m2", "m1", "m0"]
            else:
                changed["metric_owners"]["m0"] = 2
            plain = {key: value for key, value in changed.items() if key != "prediction_sha256"}
            changed["prediction_sha256"] = controller._digest(plain)
            with self.subTest(field=field), patch(
                "scripts.pre_g.controller_contract.tie_metrics"
            ) as evaluator:
                with self.assertRaisesRegex(ControllerContractError, "not issued"):
                    evaluate_rcd_seal(changed, root_index=2)
                evaluator.assert_not_called()

    def test_registered_triplet_rejects_unqualified_handle_and_input_drift_before_calls(self):
        frame = pd.DataFrame({
            "time": np.arange(600, dtype=np.float64),
            "m0": np.zeros(600),
            "m1": np.ones(600),
            "m2": np.full(600, 2.0),
        })
        with patch("rca.comparators.rcd_run") as comparator:
            with self.assertRaises(ControllerContractError):
                run_registered_rcd_triplet(frame, qualified_rcd=object(), **self.inputs)
            forged = object.__new__(QualifiedRcdRunner)
            object.__setattr__(forged, "_identity", json.dumps({"fixture": "forged"}))
            with self.assertRaises(ControllerContractError):
                run_registered_rcd_triplet(frame, qualified_rcd=forged, **self.inputs)
            comparator.assert_not_called()


if __name__ == "__main__":
    unittest.main()
