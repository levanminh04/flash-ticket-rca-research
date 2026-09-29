from __future__ import annotations

import unittest
from unittest import mock

import numpy as np
import pandas as pd

from rca.comparators import RCD_ADAPTED, rcd_run
from rca.observation import ObservationError, public_c5_observation

from _helpers import pipeline, qualified_adapter, synthetic_c1


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

    def test_04_rcd_boundary_requires_registered_contract_and_preserves_output(self):
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

        result = rcd_run(frame, seed=420, bins=5, upstream_rcd=upstream)
        self.assertEqual(result["method"], RCD_ADAPTED)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["ranks"], ["n1::latency", "n0::cpu"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1], 300)
        self.assertEqual(calls[0][2]["gamma"], 5)
        self.assertTrue(calls[0][2]["localized"])
        self.assertFalse(calls[0][2]["dk_select_useful"])
        self.assertEqual(
            rcd_run(frame, upstream_rcd=None)["reason"],
            "unqualified_upstream_callable",
        )
        self.assertEqual(
            rcd_run(frame, seed=999, upstream_rcd=upstream)["reason"],
            "unregistered_seed_or_bins",
        )

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
