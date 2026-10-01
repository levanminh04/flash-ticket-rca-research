"""Purposeful synthetic-only worker/assembly probes; no final qualification.

The registration guard is isolated only for mathematical equivalence tests.
One real C1 fixture and one real eight-detector C5 fixture are reused for
orchestration assertions, so sixty fixture slots do not recompute sixty models.
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[2]
for root in (WORKSPACE, WORKSPACE / "src"):
    sys.path.insert(0, str(root))
from scripts.task_g import final_campaign as c, final_source as s
from rca.observation import C1Observation


class ByteStdout:
    def __init__(self):
        self.buffer = io.BytesIO()


def capture(call, *args):
    out = ByteStdout()
    with patch.object(c, "_worker_guard"), patch.object(sys, "stdout", out):
        call(*args)
    return [json.loads(line) for line in out.buffer.getvalue().splitlines()]


def worker(rows, *, timeout=False):
    return {"rows": rows, "timed_out": timeout, "exit_code": -1 if timeout else 0,
            "wall_seconds": 1., "stderr_sha256": "b" * 64, "stderr_bytes": 0}


class FinalCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(s, "_context", return_value=({}, {})):
            cls.source = s.make_synthetic_source()
            cls.case = s.get_case(cls.source, 0)
        cls.c1rows = capture(c._numeric_c1_worker, c.previous._c1_wire(cls.case["c1"]))
        cls.c5rows = capture(c._numeric_c5_worker, c._c5_wire(cls.case["c5"]))

    def test_real_c1_identity_and_shared_256_controls(self):
        header = self.c1rows[0]
        local = np.array(header["local_evidence"])
        np.testing.assert_allclose(header["c1"]["primary"]["L"]["scores"], local / local.sum())
        np.testing.assert_allclose(header["c1"]["secondary"]["L"]["scores"], local / local.max())
        self.assertEqual(len(self.c1rows), 258)
        for draw, row in enumerate(self.c1rows[1:-1]):
            self.assertEqual(row["graph"]["seed"], c.previous._seed(self.case["c1"].handle, draw))
            self.assertEqual(row["rankers"]["primary"]["graph_sha256"], row["rankers"]["secondary"]["graph_sha256"])
            self.assertIn("operator_diagnostics", row["rankers"]["primary"])

    def test_numeric_workers_do_not_receive_controller_identities_or_tau(self):
        for wire in (c.previous._c1_wire(self.case["c1"]), c._c5_wire(self.case["c5"])):
            encoded = json.dumps(wire)
            for key in self.case["c1"].node_ids:
                self.assertNotIn(key, encoded)
            for word in ("case_id", "tau", "fault", "source_metadata", "root"):
                self.assertNotIn(word, encoded)
        bad = c._c5_wire(self.case["c5"]); bad["tau"] = 720
        with self.assertRaises(c.FinalCampaignError):
            capture(c._numeric_c5_worker, bad)

    def test_full_c1_diagnostics_keep_missing_and_graph_nuisance(self):
        scientific = self.c1rows[0]["scientific_diagnostics"]
        self.assertIn("masks", scientific["evidence"])
        self.assertIn("diagnostics", scientific["evidence"])
        adj = c._unpack(scientific["observed_adjacency"])
        np.testing.assert_equal(adj, self.case["c1"].adjacency)
        self.assertTrue(c._unpack(scientific["reachability"]).diagonal().all())
        self.assertEqual(set(scientific["uniform_personalization"]), {"primary", "secondary"})

    def test_timeout_and_prefix_preserve_all_planned_controls(self):
        row = c._assemble_c1(self.case, worker(self.c1rows[:8], timeout=True))
        self.assertEqual(sum(x["status"] == "SUCCESS" for x in row["control_graphs"]), 7)
        self.assertEqual(sum(x["status"] == "TIMEOUT" for x in row["control_graphs"]), 249)
        self.assertFalse(row["costs"]["timing_completed"])
        self.assertIsNone(row["costs"]["c5_fit_seconds"])
        row = c._assemble_c1(self.case, worker([], timeout=True))
        self.assertEqual(row["scientific_diagnostics"]["c1"]["status"], "UNAVAILABLE_WORKER_FAILURE")
        self.assertTrue(all(x["scores"] is None for x in row["c1"]["primary"]["R"]))

    def test_overflow_preserves_numeric_failure_diagnostics(self):
        wire = c.previous._c1_wire(self.case["c1"])
        shape = self.case["c1"].ref.shape
        wire["ref"] = c._pack(np.full(shape, 10.)); wire["query"] = c._pack(np.full(shape, 1e308))
        rows = capture(c._numeric_c1_worker, wire)
        self.assertEqual(rows[0]["kind"], "scientific_failure")
        self.assertIn("numerical_channel_failures", rows[0]["scientific_diagnostics"]["evidence"]["diagnostics"])

    def test_real_c5_equivalence_to_frozen_pipeline_all_eight(self):
        from rca.pipeline import FrozenRcaPipeline
        manifest = json.loads(c.MANIFEST.read_bytes())
        pipeline = FrozenRcaPipeline.from_manifest(c.MANIFEST,
            code_identity={row["path"]: row["sha256"] for row in manifest["implementation"]["source_files"]},
            release_id=manifest["implementation"]["release_id"])
        self.assertEqual([x["detector"] for x in self.c5rows], list(c.DETECTORS))
        for row in self.c5rows:
            expected = pipeline.run_c5(self.case["c5"], row["detector"])
            self.assertEqual(row["status"], expected["status"])
            self.assertEqual(row["state"]["bins_seen"], 36)
            self.assertIsNotNone(row["fit_seconds"]); self.assertIsNotNone(row["prediction_seconds"])
            for actual, frozen in zip(row["bins"], expected["bins"], strict=True):
                for key in ("score", "selected_system_score", "tv_score"):
                    number = frozen[key]
                    self.assertEqual(actual[key], None if not np.isfinite(number) else number)
                self.assertEqual(actual["event"], frozen["event"])
                np.testing.assert_equal(c._unpack(actual["target_mask"]), frozen["target_mask"])

    def test_c5_future_change_does_not_change_prefix(self):
        wire = c._c5_wire(self.case["c5"])
        changed = c._unpack(wire["stream"]); changed[20:] += 300
        wire["stream"] = c._pack(changed)
        with patch.object(c, "DETECTORS", (c.DETECTORS[0],)):
            row = capture(c._numeric_c5_worker, wire)[0]
        original = self.c5rows[0]
        self.assertEqual(row["bins"][:20], original["bins"][:20])
        self.assertNotEqual(row["bins"][20:], original["bins"][20:])

    def test_c5_grid_drift_is_rejected(self):
        wire = c._c5_wire(self.case["c5"])
        ends = c._unpack(wire["endpoints"]); ends[3] += 5; wire["endpoints"] = c._pack(ends)
        with self.assertRaisesRegex(c.FinalCampaignError, "GRID_DRIFT"):
            capture(c._numeric_c5_worker, wire)

    def test_partial_c5_worker_failure_retains_prefix_and_missing_suffix(self):
        partial = dict(self.c5rows[0]); partial.update(status="FAILURE", reason="synthetic injected failure", bins=partial["bins"][:4])
        with patch.object(c, "_run_worker", return_value=worker([partial], timeout=True)):
            rows, diagnostics, bindings, costs = c._run_c5(self.source, self.case, 1.)
        one = rows[partial["detector"]]
        self.assertEqual(len(one["ends"]), len(self.case["c5"].relative_endpoints))
        self.assertEqual(len(diagnostics[partial["detector"]]["bins"]), 4)
        self.assertTrue(all(x is None for x in one["scores"][4:]))
        self.assertTrue(all(x == "TIMEOUT" for x in one["bin_statuses"][4:]))
        self.assertEqual(set(bindings), set(c.DETECTORS))
        self.assertIsNone(costs["c5_fit_seconds"])
        self.assertIsNotNone(costs["c5_fit_partial_measured_seconds"])

    def test_integrated_conversion_failure_retained_and_endpoint_computation_reused(self):
        artificial = []
        ends = self.case["c5"].relative_endpoints.tolist()
        for row in self.c5rows:
            bins = [{"endpoint": end, "selected_system_score": 0., "event": {"trigger": end == 400}} for end in ends]
            artificial.append({**row, "bins": bins})
        # Explicit synthetic-only orchestration outputs, never issuer qualification.
        with patch.object(c, "_run_worker", return_value=worker(artificial)), patch.object(s, "integrated_observation", side_effect=s.FinalSourceError("synthetic conversion error")) as convert:
            outputs, diagnostics, bindings, costs = c._run_c5(self.source, self.case, 1.)
        self.assertEqual(convert.call_count, 1)
        for detector in c.DETECTORS:
            result = outputs[detector]["triggers"][0]
            self.assertEqual(result["status"], "FAILURE")
            self.assertEqual(bindings[detector]["400"], [])
        self.assertEqual(costs["integrated_measured_calls"], 1)

    def test_missing_c5_and_rcd_are_explicit_failures(self):
        case = {**self.case, "c5": None, "rcd": None}
        with patch.object(c, "_run_worker") as run:
            outputs, diagnostics, bindings, costs = c._run_c5(self.source, case, 1.)
            rcd = c._run_rcd(case, 1.)
        run.assert_not_called()
        self.assertTrue(all(row["status"] == "FAILURE" for row in outputs.values()))
        self.assertTrue(all(row["state"] is None for row in diagnostics.values()))
        self.assertEqual([row["seed"] for row in rcd["seed_outputs"]], [420, 421, 422])
        self.assertTrue(all(row["ranks"] is None for row in rcd["seed_outputs"]))
        self.assertIsNone(costs["c5_fit_seconds"])

    def test_actual_conversion_scope_cannot_reach_numeric_models(self):
        for scope in (s.ACTUAL_SCOPE, s.DEVELOPMENT_SCOPE, None):
            case = {**self.case, "source_metadata": {"scope": scope}}
            with patch.object(c, "_run_worker") as run, self.assertRaisesRegex(c.FinalCampaignError, "ONLY_SYNTHETIC"):
                c._compute_case(self.source, case, 1., 1.)
            run.assert_not_called()

    def test_missing_all_observations_preserves_case_without_invented_candidates(self):
        case = {**self.case, "c1": None, "c5": None, "rcd": None}
        with patch.object(c, "_run_worker") as run:
            row = c._compute_case(self.source, case, 1., 1.)
        run.assert_not_called()
        self.assertEqual(row["candidate_count"], 0)
        self.assertEqual(row["ordinal"], case["ordinal"])
        self.assertEqual(len(row["control_graphs"]), 256)
        self.assertTrue(all(x["scores"] is None for x in row["c1"]["primary"]["R"]))
        self.assertEqual(row["scientific_diagnostics"]["controller_bindings"]["candidate_ids"], [])
        self.assertEqual(row["scientific_diagnostics"]["c1"]["status"], "UNAVAILABLE_SOURCE_OBSERVATION")

    def test_failure_inside_real_c5_replay_retains_fit_and_completed_prefix(self):
        from rca.detection import score_bin
        calls = []
        def fail_after_prefix(state, values):
            calls.append(True)
            if len(calls) == 4:
                raise RuntimeError("synthetic-only numerical failure after three bins")
            return score_bin(state, values)
        with patch.object(c, "DETECTORS", (c.DETECTORS[0],)), patch("rca.detection.score_bin", side_effect=fail_after_prefix):
            result = capture(c._numeric_c5_worker, c._c5_wire(self.case["c5"]))[0]
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(len(result["bins"]), 3)
        self.assertEqual(result["state"]["bins_seen"], 36)
        self.assertIsNotNone(result["fit_seconds"])
        self.assertIsNotNone(result["prediction_seconds"])

    def test_readiness_cannot_grant_campaign_or_accept_forged_execution(self):
        with self.assertRaises(c.FinalCampaignError):
            c.run_final_campaign()
        for handle in ({}, c.ReadinessExecution()):
            with self.assertRaisesRegex(c.FinalCampaignError, "UNISSUED"):
                c._readiness_payload_for_provenance(handle)

    def test_lock_excludes_parallel_controller_and_releases(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(c, "CONTRACT", Path(directory) / "run-contract.json"):
            with c._readiness_lock():
                with self.assertRaisesRegex(c.FinalCampaignError, "ALREADY_RUNNING"):
                    with c._readiness_lock():
                        pass
            with c._readiness_lock():
                pass


if __name__ == "__main__":
    unittest.main()
