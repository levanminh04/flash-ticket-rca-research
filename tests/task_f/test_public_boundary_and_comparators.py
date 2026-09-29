from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd
import rca.qualified_rcd as rcd_boundary

from rca.comparators import RCD_ADAPTED, rcd_run
from rca.observation import ObservationError, public_c5_observation
from rca.qualified_rcd import (
    QualifiedRcdRunner,
    RcdQualificationError,
    _verify_evidence_identity,
)

from _helpers import W, pipeline, qualified_adapter, synthetic_c1


class PublicBoundaryAndComparatorTests(unittest.TestCase):
    def test_01_direct_observation_detaches_and_deep_freezes_inputs(self):
        observation = synthetic_c1()
        self.assertFalse(observation.ref.flags.writeable)
        self.assertFalse(observation.adjacency.flags.writeable)
        with self.assertRaises(ValueError):
            observation.ref[0, 0, 0] = 99.0
        with self.assertRaises(TypeError):
            observation.quality["new"] = True

    def test_02_public_boundary_rejects_unbound_callable(self):
        admitted = synthetic_c1()
        with self.assertRaises(ObservationError):
            from rca.observation import public_c1_observation

            public_c1_observation(
                {"public": "telemetry"},
                qualified_adapter=lambda raw: raw,
                loader_kwargs={},
                handle=admitted.handle,
            )

    def test_03_adapter_binds_exact_sources_and_receipts(self):
        adapter = qualified_adapter()
        self.assertEqual(adapter.identity["adapter_id"], "TASK-F-TD13-EXACT-TASK-E-BUNDLE-ADAPTER-v1")
        self.assertEqual(len(adapter.identity["source_sha256"]), 3)
        self.assertEqual(len(adapter.identity["receipt_sha256"]), 3)

    def test_04_rcd_forwards_registered_parameters_after_admission(self):
        frame = pd.DataFrame(
            {
                "time": np.arange(600, dtype=np.float64),
                "n0::cpu": np.linspace(0.0, 1.0, 600),
                "n1::latency": np.linspace(1.0, 0.0, 600),
            }
        )
        calls = []

        def upstream(data, inject_time, **kwargs):
            calls.append((data.copy(), inject_time, kwargs))
            return {"ranks": ["n1::latency", "n0::cpu"]}

        # This isolates forwarding only. The real pinned factory is exercised
        # by the Python 3.9 bounded smoke, not by this patched unit test.
        with mock.patch("rca.comparators.qualified_callable", return_value=upstream):
            result = rcd_run(frame, seed=420, bins=5, qualified_rcd=object())
            wrong_seed = rcd_run(frame, seed=999, bins=5, qualified_rcd=object())
            wrong_bins = rcd_run(frame, seed=420, bins=9, qualified_rcd=object())
        self.assertEqual(result["method"], RCD_ADAPTED)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["ranks"], ["n1::latency", "n0::cpu"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1], 300)
        self.assertEqual(calls[0][2]["gamma"], 5)
        self.assertTrue(calls[0][2]["localized"])
        self.assertFalse(calls[0][2]["dk_select_useful"])
        self.assertEqual(calls[0][2]["bins"], 5)
        self.assertIsNone(calls[0][2]["dataset"])
        self.assertEqual(wrong_seed["reason"], "unregistered_seed_or_bins")
        self.assertEqual(wrong_bins["reason"], "unregistered_seed_or_bins")

    def test_04a_rcd_rejects_plain_lambda_and_fake_callable(self):
        frame = pd.DataFrame({"time": np.arange(600), "n0::cpu": np.ones(600)})

        def plain(*args, **kwargs):
            return {"ranks": ["n0::cpu"]}

        class Fake:
            def __call__(self, *args, **kwargs):
                return {"ranks": ["n0::cpu"]}

        for candidate in (plain, lambda *args, **kwargs: {"ranks": []}, Fake(), None):
            with self.subTest(candidate=type(candidate).__name__):
                result = rcd_run(frame, qualified_rcd=candidate)
                self.assertEqual(result["status"], "FAILURE")
                self.assertEqual(result["reason"], "unqualified_rcd_runner")
        fake_handle = object.__new__(QualifiedRcdRunner)
        self.assertEqual(
            rcd_run(frame, qualified_rcd=fake_handle)["reason"],
            "unqualified_rcd_runner",
        )

    def test_04b_rcd_rejects_intact_forged_handle_without_factory(self):
        frame = pd.DataFrame({"time": np.arange(600), "n0::cpu": np.ones(600)})
        handle = object.__new__(QualifiedRcdRunner)
        function = lambda *args, **kwargs: {"ranks": []}
        identity = json.dumps({"executable": str(Path(sys.executable).resolve())})
        object.__setattr__(handle, "_function", function)
        object.__setattr__(handle, "_identity", identity)
        self.assertFalse(hasattr(rcd_boundary, "_ISSUED"))
        self.assertEqual(rcd_run(frame, qualified_rcd=handle)["reason"], "unqualified_rcd_runner")
        object.__setattr__(handle, "_identity", identity + " ")
        self.assertEqual(rcd_run(frame, qualified_rcd=handle)["reason"], "unqualified_rcd_runner")

    def test_04c_rcd_rejects_wrong_source_patch_and_receipt_identity(self):
        manifest = json.loads((W / "configs/task-f-td13-frozen-release-v2.json").read_text(encoding="utf-8"))
        row = next(row for row in manifest["comparators"] if row["id"] == RCD_ADAPTED)
        report = json.loads(
            (W / "results/task-e/e27-018-rcd-real-qualification/rcd-fixture-report.json").read_text(encoding="utf-8")
        )
        _verify_evidence_identity(row, report["provenance"])
        for field in ("upstream_revision", "original_lineage_revision", "source_manifest_sha256", "patch_sha256", "original_rcd_sha256", "patched_rcd_sha256"):
            changed = copy.deepcopy(row)
            changed[field] = "0" * 64
            with self.subTest(field=field), self.assertRaises(RcdQualificationError):
                _verify_evidence_identity(changed, report["provenance"])
        changed = copy.deepcopy(row)
        changed["qualification_report"]["sha256"] = "0" * 64
        with self.assertRaises(RcdQualificationError):
            _verify_evidence_identity(changed, report["provenance"])
        changed = copy.deepcopy(report["provenance"])
        changed["patch_sha256"] = "0" * 64
        with self.assertRaises(RcdQualificationError):
            _verify_evidence_identity(row, changed)

    def test_04d_rcd_input_output_and_failure_contract(self):
        frame = pd.DataFrame({"time": np.arange(600), "n0::cpu": np.ones(600)})
        with mock.patch("rca.comparators.qualified_callable", return_value=lambda *a, **k: {"ranks": []}):
            self.assertEqual(rcd_run(frame, qualified_rcd=object())["status"], "SUCCESS")
            self.assertEqual(rcd_run(frame, qualified_rcd=object())["ranks"], [])
            bad = frame.copy()
            bad.loc[2, "n0::cpu"] = np.inf
            self.assertEqual(rcd_run(bad, qualified_rcd=object())["reason"], "nonfinite_after_imputation")
            self.assertEqual(rcd_run({"time": []}, qualified_rcd=object())["reason"], "malformed_input")
        for output, reason in (({"ranks": ["n0::cpu", "n0::cpu"]}, "duplicate_metric_rank"), ({"ranks": [None]}, "unparseable_metric_rank")):
            with mock.patch("rca.comparators.qualified_callable", return_value=lambda *a, **k: output):
                self.assertEqual(rcd_run(frame, qualified_rcd=object())["reason"], reason)
        with mock.patch("rca.comparators.qualified_callable", return_value=mock.Mock(side_effect=RuntimeError("sensitive"))):
            failed = rcd_run(frame, qualified_rcd=object())
        self.assertEqual(failed["reason"], "upstream_exception")
        self.assertEqual(failed["error"], "RuntimeError")

    def test_05_early_trigger_is_retained_as_insufficient_history(self):
        adapter = qualified_adapter()
        total = 76
        values = np.zeros((total, 1, 12), dtype=np.float64)
        values[:, 0, :] = (np.arange(total, dtype=np.float64) % 7)[:, None]
        values[36:39, 0, :] = 1e12
        bundle = {
            "values": values,
            "adj": np.zeros((1, 1), dtype=bool),
            "service_names": ["a"],
            "channel_types": np.array([0] * 10 + [1, 2], dtype=np.int64),
            "fit_service_mask": np.ones(1, dtype=bool),
            "endpoints": np.arange(1, total + 1, dtype=np.int64) * 5,
            "s0": 1_700_000_000,
            "audit": {
                "profile": "TD13-C5-EVENT-TIME",
                "qualification": {
                    "status": "QUALIFIED",
                    "profile": "TD13-C5-EVENT-TIME",
                    "adapter_id": adapter.adapter_id,
                },
                "graph": {},
            },
        }
        raw = {
            "audit": {
                "modalities": {
                    name: {
                        "status": "LOADED",
                        "source_identity_verified": True,
                        "sha256": character * 64,
                    }
                    for name, character in (("metrics", "a"), ("traces", "b"), ("logs", "c"))
                }
            }
        }
        with mock.patch.object(type(adapter), "c5", return_value=bundle), mock.patch.object(
            type(adapter), "integrated", side_effect=AssertionError("early trigger must not load a window")
        ):
            result = pipeline().run_public_c5(
                raw,
                "G-MTL",
                qualified_adapter=adapter,
                loader_kwargs={},
                handle="early",
            )
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(len(result["integrated_diagnoses"]), 1)
        self.assertEqual(result["integrated_diagnoses"][0]["relative_endpoint"], 195)
        self.assertEqual(result["integrated_diagnoses"][0]["status"], "INSUFFICIENT_HISTORY")
        self.assertNotIn("1700000000", repr(result["trigger_packets"][0]))


if __name__ == "__main__":
    unittest.main()
