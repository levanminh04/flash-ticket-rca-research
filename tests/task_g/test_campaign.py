"""Numeric orchestration tests never confer production source qualification."""
from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKSPACE))
sys.path.insert(0, str(WORKSPACE / "src"))
from scripts.task_g import campaign as c
from rca.observation import C1Observation


class ByteStdout:
    def __init__(self):
        self.buffer = io.BytesIO()


def observation():
    x = np.arange(30, dtype=float)
    ref = np.array([[10 + np.sin(x)], [10 + np.sin(x + 1)], [10 + np.sin(x + 2)]])
    query = ref + np.array([[[1.]], [[2.]], [[4.]]])
    return C1Observation("0000000000000000", ref, query, (0,),
        np.array([[0, 1, 0], [0, 0, 1], [0, 0, 0]], dtype=bool), ("v0", "v1", "v2"), {"numeric": "a" * 64}, {}, {}, {})


class CampaignTests(unittest.TestCase):
    def test_conditions_are_frozen_not_caller_selected(self):
        result = c.prepare_conditions()
        contract = json.loads(c.CONTRACT.read_bytes())
        self.assertEqual(result["conditions"], contract["prepared_conditions"])
        self.assertEqual(result["sha256"], c._digest(contract["prepared_conditions"]))
        self.assertEqual(result["conditions"]["RCD_seeds"], [420, 421, 422])

    def test_arbitrary_handles_and_dictionaries_cannot_issue(self):
        for obj in ({}, c.CampaignExecution(), object.__new__(c.CampaignExecution)):
            with self.assertRaisesRegex(c.CampaignError, "UNISSUED"):
                c._campaign_payload_for_provenance(obj)
        for obj in ({}, c.CaseExecution()):
            with self.assertRaisesRegex(c.CampaignError, "UNISSUED"):
                c._case_payload_for_checkpoint(obj)
        self.assertFalse(hasattr(c, "_bind_execution"))

    def test_numeric_wire_roundtrip_keeps_nan_missingness(self):
        array = np.array([[1., np.nan], [0., 2.]])
        actual = c._unpack(c._pack(array))
        np.testing.assert_equal(actual, array)
        array[0, 0] = 90
        self.assertEqual(actual[0, 0], 1)

    def test_numeric_wire_rejects_object_oracle_extra_and_infinity(self):
        with self.assertRaises(c.CampaignError):
            c._pack(np.array([object()]))
        with self.assertRaises(c.CampaignError):
            c._pack(np.array([np.inf]))
        wire = c._pack(np.zeros(2))
        wire["root_index"] = 0
        with self.assertRaises(c.CampaignError):
            c._unpack(wire)

    def test_c1_wire_has_only_numeric_and_opaque_fields(self):
        wire = c._c1_wire(observation())
        self.assertEqual(set(wire), {"mode", "ref", "query", "adj", "channel_types", "routing_handle"})
        self.assertNotIn("v0", json.dumps(wire))
        self.assertNotIn("tau", json.dumps(wire))

    def test_timeout_keeps_256_explicit_failed_draws(self):
        case = {"c1": observation(), "ordinal": 0, "cell_ordinal": 0, "repeat": 0,
                "numeric_input_sha256": "a" * 64}
        worker = {"rows": [], "timed_out": True, "exit_code": -1, "wall_seconds": 1.,
                  "stderr_sha256": "b" * 64, "stderr_bytes": 0}
        result = c._assemble_c1(case, worker)
        self.assertTrue(result["shared_preprocessing_failed"])
        self.assertEqual(len(result["control_graphs"]), 256)
        for arms in result["c1"].values():
            self.assertEqual(len(arms["R"]), 256)
            self.assertTrue(all(row["status"] == "TIMEOUT" and row["scores"] is None for row in arms["R"]))

    def test_real_numeric_worker_shares_graphs_secondary_and_matches_identity(self):
        # Only registration is isolated; all mathematical operators and all256
        # perturbations are the actual frozen core, without issued production handles.
        out = ByteStdout()
        with patch.object(c, "_worker_guard"), patch.object(sys, "stdout", out):
            c._numeric_c1_worker(c._c1_wire(observation()))
        rows = [json.loads(line) for line in out.buffer.getvalue().splitlines()]
        self.assertEqual(len(rows), 258)
        header = rows[0]
        local = np.asarray(header["local_evidence"])
        np.testing.assert_allclose(header["c1"]["primary"]["L"]["scores"], local / local.sum())
        np.testing.assert_allclose(header["c1"]["secondary"]["L"]["scores"], local / local.max())
        for row in rows[1:-1]:
            self.assertEqual(row["rankers"]["primary"]["graph_sha256"], row["rankers"]["secondary"]["graph_sha256"])
            self.assertEqual(row["graph"]["seed"], c._seed("0000000000000000", row["draw"]))
        case = {"c1": observation(), "ordinal": 0, "cell_ordinal": 0, "repeat": 0, "numeric_input_sha256": "a" * 64}
        worker = {"rows": rows, "timed_out": False, "exit_code": 0, "wall_seconds": 4., "stderr_sha256": "b" * 64, "stderr_bytes": 0}
        result = c._assemble_c1(case, worker)
        self.assertFalse(result["shared_preprocessing_failed"])
        self.assertTrue(result["costs"]["timing_completed"])
        for name in ("primary", "secondary"):
            self.assertGreaterEqual(result["costs"]["arm_wall_seconds"][name]["R"], result["costs"]["control_generation_seconds"])
        self.assertEqual(set(result["contextual"]), {"Local-MAX-MT", "BARO-RANK-adapted-TD12"})
        self.assertTrue(all(row["status"] == "SUCCESS" for row in result["contextual"].values()))

    def test_completed_prefix_retained_after_timeout(self):
        out = ByteStdout()
        with patch.object(c, "_worker_guard"), patch.object(sys, "stdout", out):
            c._numeric_c1_worker(c._c1_wire(observation()))
        rows = [json.loads(line) for line in out.buffer.getvalue().splitlines()][:8]
        case = {"c1": observation(), "ordinal": 0, "cell_ordinal": 0, "repeat": 0, "numeric_input_sha256": "a" * 64}
        worker = {"rows": rows, "timed_out": True, "exit_code": -1, "wall_seconds": 4., "stderr_sha256": "b" * 64, "stderr_bytes": 0}
        result = c._assemble_c1(case, worker)
        self.assertEqual(sum(row["status"] == "SUCCESS" for row in result["control_graphs"]), 7)
        self.assertEqual(sum(row["status"] == "TIMEOUT" for row in result["control_graphs"]), 249)
        self.assertFalse(result["costs"]["timing_completed"])

    def test_overflow_is_failure_not_silent_zero_success(self):
        out = ByteStdout()
        wire = c._c1_wire(observation())
        wire["ref"] = c._pack(np.full((3, 1, 30), 10.))
        wire["query"] = c._pack(np.full((3, 1, 30), 1e308))
        with patch.object(c, "_worker_guard"), patch.object(sys, "stdout", out):
            with self.assertRaises(c.CampaignError):
                c._numeric_c1_worker(wire)
        self.assertEqual(out.buffer.getvalue(), b"")

    def test_no_matched_timing_fails_closed(self):
        cases = [{"costs": {"timing_completed": False}}] * 30
        with self.assertRaisesRegex(c.CampaignError, "NO_MATCHED"):
            c._timing_report(cases, {})
        with self.assertRaisesRegex(c.CampaignError, "INCOMPLETE"):
            c._timing_report([], {})

    def test_timeout_uses_measured_full_case_wall_not_numeric_components(self):
        rows = []
        for ordinal in range(30):
            row = {"ordinal": ordinal, "c1": {name: {"L": {"status": "SUCCESS"}, "O": {"status": "SUCCESS"},
                "R": [{"status": "SUCCESS"}] * 256} for name in ("primary", "secondary")},
                "costs": {"timing_completed": True, "arm_wall_seconds": {name: {"L": .01, "O": .02, "R": .03} for name in ("primary", "secondary")}}}
            rows.append(c._apply_walltime_measurement(row, .5, 31.0 + ordinal))
        report = c._timing_report(rows, {})
        self.assertEqual(report["maximum_successful_development_aggregate_case_walltime_across_arms"], 60.5)
        self.assertEqual(report["derived_common_timeout_seconds"], 605.)
        self.assertEqual(rows[-1]["costs"]["arm_numeric_components_seconds"]["primary"]["R"], .03)
        for name in ("primary", "secondary"):
            self.assertEqual(rows[-1]["costs"]["arm_wall_seconds"][name], {"L": 60.5, "O": 60.5, "R": 60.5})

    def test_final_runtime_remains_closed(self):
        with patch.object(c, "_context"):
            with self.assertRaisesRegex(c.CampaignError, "PERMISSION_CLOSED"):
                c.run_final_campaign()

    def test_actual_frozen_c5_preserves_all_planned_numeric_bins(self):
        from scripts.task_g import campaign_source as source
        context = {"contract_sha256": "a" * 64, "permissions": {}, "entry_bindings": {}}
        with patch.object(source, "_registered_context", return_value=context):
            handle = source.make_synthetic_source()
            one = source.get_case(handle, 0)["c5"]
        wire = {"warmup": c._pack(one.warmup_values), "stream": c._pack(one.stream_values),
            "adj": c._pack(one.adjacency), "channel_types": c._pack(one.channel_types),
            "fit_mask": c._pack(one.fit_service_mask), "endpoints": c._pack(one.relative_endpoints)}
        out = ByteStdout()
        with patch.object(c, "_worker_guard"), patch.object(sys, "stdout", out):
            c._numeric_c5_worker(wire)
        rows = [json.loads(line) for line in out.buffer.getvalue().splitlines()]
        self.assertEqual([row["detector"] for row in rows], list(c.DETECTORS))
        for row in rows:
            self.assertEqual(row["status"], "SUCCESS")
            self.assertEqual([item["endpoint"] for item in row["bins"]], list(range(185, 1081, 5)))
            self.assertTrue(all(item["score"] is None or np.isfinite(item["score"]) for item in row["bins"]))
            self.assertTrue(all(type(item["trigger"]) is bool for item in row["bins"]))

    def test_driver_lock_cannot_run_second_controller(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(c, "CONTRACT", Path(directory) / "run-contract.json"):
                with c._driver_lock():
                    with self.assertRaisesRegex(c.CampaignError, "ALREADY_RUNNING"):
                        with c._driver_lock():
                            self.fail("Second controller unexpectedly acquired fixed lock")
                with c._driver_lock():
                    pass

    def test_script_entry_uses_canonical_issuance_registry(self):
        import subprocess
        program = "import runpy,sys;sys.argv=['campaign.py'];\ntry: runpy.run_path('scripts/task_g/campaign.py',run_name='__main__')\nexcept ValueError: pass\nassert 'scripts.task_g.campaign' in sys.modules\nprint('canonical-registry-alias-PASS')"
        result = subprocess.run([sys.executable, "-B", "-c", program], cwd=WORKSPACE,
            capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("canonical-registry-alias-PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
