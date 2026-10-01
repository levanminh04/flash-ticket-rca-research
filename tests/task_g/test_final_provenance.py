"""Synthetic-only G32 seal canaries; no telemetry, host key or truth files.

These deliberately assembled output fixtures test storage/controller boundaries.
They perform zero model computations and cannot qualify actual predictions.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import hmac
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import numpy as np

from scripts.task_g import final_provenance as p
from scripts.task_g import final_evaluation as evaluation
from tests.task_g import test_campaign_provenance as historical_fixtures


def numeric(value):
    array = np.ascontiguousarray(value)
    return {"dtype": array.dtype.str, "shape": list(array.shape),
            "bytes_b64": base64.b64encode(array.tobytes()).decode("ascii")}


KEYS = ["s" + hashlib.sha256(("TD13-G32|literal-service|fixture" + str(j)).encode()).hexdigest()[:24] for j in range(2)]


def synthetic_case(ordinal=0):
    """An assembled storage fixture, not numerical algorithm evidence."""
    case = historical_fixtures.CampaignDurabilityTests.case(None, ordinal)
    case.update(cell_ordinal=ordinal, repeat=0)
    adj = np.array([[False, True], [True, False]])
    z = np.zeros((2, 1))
    mask = np.ones((2, 1), dtype=bool)
    state = {"config": {"lag": 1, "arm": "G"}, "E": numeric(mask), "centers": numeric(z),
        "scales": numeric(np.ones((2, 1))), "adj": numeric(adj),
        "channel_types": numeric(np.array([0], dtype=np.int64)),
        "fit_service_mask": numeric(np.ones(2, dtype=bool)),
        "memberships": {name: numeric(adj[:, :, None]) for name in ("out", "in", "all")},
        "degrees": {name: numeric(np.ones((2, 1), dtype=np.int64)) for name in ("out", "in", "all")},
        "coefficients": numeric(np.zeros((2, 1, 5))), "intercepts": numeric(z),
        "fit_model_mask": numeric(mask), "model_mask": numeric(mask),
        "residual_centers": numeric(z), "residual_scales": numeric(np.ones((2, 1))),
        "history": numeric(z[None]), "bins_seen": 36,
        "calibration_errors": numeric(np.zeros((12, 2, 1))),
        "calibration_predictions": numeric(np.zeros((12, 2, 1))),
        "fit_target_mask": numeric(np.ones((24, 2, 1), dtype=bool)),
        "calibration_target_mask": numeric(np.ones((12, 2, 1), dtype=bool)),
        "warmup_z": numeric(np.zeros((36, 2, 1))), "diagnostics": {
            **{name: numeric(np.ones((2, 1), dtype=np.int64)) for name in ("finite_fit_support", "fit_rows", "calibration_rows")},
            **{name: numeric(np.ones((2, 1), dtype=bool)) for name in ("singleton_scale", "constant_scale", "scale_floor_used", "residual_floor_used", "constant_calibration_errors")},
            "applicability_reasons": [["SCALER_DEFINED"], ["SCALER_DEFINED"]], "model_count": 2,
            "ridge": [[{"centered_design_rank": 1, "design_rank_with_intercept": 2, "effective_ridge_df": 2.,
                "scaled_centered_singular_values": numeric(np.ones(1)), "singular_value_scale": 1.,
                "active_columns": 1, "fit_rows": 24, "nominal_columns": 5, "intercept_unpenalized": True}] for _ in range(2)]}}
    state["diagnostics"]["fit_rows"] = numeric(np.full((2, 1), 24, dtype=np.int64))
    state["diagnostics"]["calibration_rows"] = numeric(np.full((2, 1), 12, dtype=np.int64))
    source = {"warmup": numeric(np.zeros((36, 2, 1))), "stream": numeric(np.zeros((5, 2, 1))),
        "channel_types": state["channel_types"], "fit_mask": state["fit_service_mask"], "adj": state["adj"],
        "endpoints": numeric(np.array([185, 190, 195, 200, 205], dtype=np.int64))}
    rank = {"scores": numeric(np.array([1., .5])), "rounded_scores": numeric(np.array([1., .5])),
        "diagnostics": {"operator": "diffusion", "direction": "undirected", "damping": .85, "raw_local_scale": 1.,
            "isolates": numeric(np.zeros(2, dtype=bool)), "transition": numeric(adj.astype(float)),
            "no_evidence": False, "residual_inf": 0.}}
    for group in case["c1"].values():
        for row in group["R"]:
            row["operator_diagnostics"] = copy.deepcopy(rank)
    bins = []
    for index, endpoint in enumerate([185, 190, 195, 200, 205]):
        bins.append({"score": 11., "residuals": numeric(z + 11), "errors": numeric(z + 11),
            "predictions": numeric(z), "target_mask": numeric(mask), "z": numeric(z + 11),
            "features": numeric(np.zeros((2, 1, 5))),
            "availability": {"available_out": numeric(np.ones((2, 1), dtype=np.int64)),
                "available_in": numeric(np.ones((2, 1), dtype=np.int64))},
            "endpoint": endpoint, "start": endpoint - 5, "scored_channels": 2, "tv_score": 11.,
            "tv_channels": numeric(np.zeros(1)), "tv_edge_counts": numeric(np.ones(1, dtype=np.int64)),
            "tv_failure": None, "local_magnitude": 11., "selected_system_score": 11.,
            "event": {"available": True, "positive": True, "trigger": index == 2,
                "streak": index + 1, "endpoint": endpoint, "last_trigger": None if index < 2 else 195}})
    evidence = {"local": numeric(np.array([1., .5])), "channel_scores": numeric(np.array([[1.], [.5]])),
        "blocks": {name: numeric(np.array([1., .5])) for name in ("metric", "trace", "log")},
        "masks": {"channels": numeric(mask), "local": numeric(np.ones(2, dtype=bool)),
            "blocks": {name: numeric(np.ones(2, dtype=bool)) for name in ("metric", "trace", "log")}},
        "diagnostics": {"reference_valid_bins": numeric(np.full((2, 1), 36, dtype=np.int64)),
            "query_valid_bins": numeric(np.full((2, 1), 36, dtype=np.int64)), "reference_min_bins": 29,
            "query_min_bins": 29, "centers": numeric(z), "scales": numeric(z + 1),
            "channel_reasons": [["available"], ["available"]], "numerical_channel_failures": numeric(~mask), "config": {"fixture": "SYNTHETIC_ONLY"}}}
    case["scientific_diagnostics"] = {"c1": {"input": {"ref": numeric(np.zeros((2, 1, 36))),
        "query": numeric(np.zeros((2, 1, 36))), "adj": numeric(adj), "channel_types": state["channel_types"]},
        "evidence": evidence, "observed_adjacency": numeric(adj), "graph_sha256": case["control_graphs"][0]["graph_sha256"],
        "degrees": {name: numeric(np.ones(2, dtype=np.int64)) for name in ("in", "out", "undirected")},
        "reachability": numeric(np.ones((2, 2), dtype=bool)),
        "uniform_personalization": {name: copy.deepcopy(rank) for name in ("primary", "secondary")},
        "ranking": {name: {arm: copy.deepcopy(rank) for arm in ("L", "O")} for name in ("primary", "secondary")}},
        "c5": {name: {"status": "SUCCESS", "state": copy.deepcopy(state), "input": copy.deepcopy(source),
            "bins": copy.deepcopy(bins)} for name in p.historical._DETECTORS},
        "quality": {"fixture": "SYNTHETIC_ONLY"},
        "controller_bindings": {"candidate_ids": KEYS[:],
            "integrated_candidate_ids": {name: {"195": []} for name in p.historical._DETECTORS}}}
    case["costs"] = {field: None for field in p._COST_FIELDS}
    case["costs"].update({"aggregate_case_walltime_seconds": .125,
        "arm_wall_seconds": {"primary": {"L": .1}}, "exit_code": -1,
        "diagnostics": {"fixture": "SYNTHETIC_ONLY", "stderr_bytes": 23}})
    return case


def with_integrated_trigger(case):
    """A distinct late-trigger storage fixture with no model computation."""
    detector = "G-MT"
    record = case["scientific_diagnostics"]["c5"][detector]
    example = record["bins"][0]
    bins = []
    endpoints = list(range(185, 375, 5))
    for index, endpoint in enumerate(endpoints):
        row = copy.deepcopy(example)
        score = None if index < 35 else 11.
        row.update(endpoint=endpoint, start=endpoint-5, score=score, tv_score=score, selected_system_score=score,
            target_mask=numeric(np.full((2, 1), index >= 35, dtype=bool)), scored_channels=0 if index < 35 else 2,
            event={"available": index >= 35, "positive": index >= 35, "trigger": index == 37,
                "streak": max(0, index-34), "endpoint": endpoint, "last_trigger": 370 if index == 37 else None})
        bins.append(row)
    record["bins"] = bins
    record["input"]["stream"] = numeric(np.zeros((len(endpoints), 2, 1)))
    record["input"]["endpoints"] = numeric(np.array(endpoints, dtype=np.int64))
    trigger = {"endpoint": 370, "status": "SUCCESS", "candidate_count": 2, "scores": [1., .5],
        "input_sha256": "b" * 64, "candidate_ids": KEYS[::-1], "quality": {"fixture": "SYNTHETIC_ONLY"},
        "graph_provenance": {"fixture": "SYNTHETIC_ONLY"},
        "scientific_diagnostics": copy.deepcopy(case["scientific_diagnostics"]["c1"])}
    case["c5"][detector].update(starts=[end-5 for end in endpoints], ends=endpoints,
        scores=[None]*35 + [11.]*3, bin_statuses=["UNAVAILABLE"]*35 + ["SUCCESS"]*3, triggers=[trigger])
    case["scientific_diagnostics"]["controller_bindings"]["integrated_candidate_ids"][detector] = {"370": KEYS[::-1]}
    return case


class FinalDurabilityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="g32-isolated-seal-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        for name, value in (("_WORKSPACE", self.workspace), ("_HOST_TRUST_MODE", "ISOLATED_FIXTURE")):
            self._patch(patch.object(p, name, value))
        self._patch(patch.dict(os.environ, {"LOCALAPPDATA": str(self.root / "local")}))
        self._patch(patch.object(p, "_validate_frozen_files", return_value=None))
        snapshot = {}
        for relative in p._SOURCES:
            path = self.workspace / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(("ISOLATED_SOURCE:" + relative).encode())
            snapshot[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.prepared = {"scientific_objects": {"selections": {"c5": {"detectors": [
            {"id": name, "threshold": 10.} for name in sorted(p.historical._DETECTORS)]}}}}
        self.contract = {"schema": p.CONTRACT_SCHEMA, "run_id": p.RUN_ID, "domain": p.DOMAIN, "phase": p.PHASE,
            "permissions": {**dict.fromkeys(p._FINAL_PERMISSIONS, False),
                "synthetic_development_conversion_readiness": True, "synthetic_evaluation": True,
                "tau_only_input_audit": True, "readiness_host_key_generation": True,
                "telemetry_final60_new_acquisition": False},
            "frozen_inputs": copy.deepcopy(p._FROZEN), "source_test_snapshot_before_qualification": snapshot,
            "prepared_conditions": self.prepared, "environment": {"main_python": platform.python_version(),
                "packages": {name: importlib.metadata.version(name) for name in
                    ("numpy", "pandas", "pyarrow", "huggingface-hub")}, "dependency_installation": False},
            "resource_policy": {"worker_count": 1}, "entry_bindings": {"receipt_sha256": "a" * 64},
            "protected_sha256": {"W/frozen": "b" * 64}, "trust_anchor": None}
        p._contract_path().parent.mkdir(parents=True)
        self.write_contract()
        self.contract["trust_anchor"] = p.initialize_readiness_key()
        self.write_contract()
        self.issued = {}
        module = types.ModuleType("scripts.task_g.final_campaign")
        def require(handle):
            entry = self.issued.get(id(handle))
            if entry is None or entry[0] is not handle:
                raise p.FinalProvenanceError("Not issued by isolated synthetic fixture")
            return copy.deepcopy(entry[1])
        module._readiness_payload_for_provenance = require
        frozen_module = types.ModuleType("scripts.task_g.campaign")
        frozen_module.prepare_conditions = lambda: {"conditions": copy.deepcopy(self.prepared), "sha256": p._digest(self.prepared)}
        self._patch(patch.dict(sys.modules, {"scripts.task_g.final_campaign": module, "scripts.task_g.campaign": frozen_module}))

    def _patch(self, patcher):
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_contract(self):
        p._contract_path().write_bytes(p._canonical(self.contract))

    def payload(self, count=1):
        context, _ = p.registered_context()
        return {"schema": p.EXECUTION_SCHEMA, "run_id": p.RUN_ID, "domain": p.DOMAIN,
            "phase": p.PHASE, "trust_mode": "ISOLATED_FIXTURE", "scope": "SYNTHETIC_BRIDGE_READINESS",
            **{name: context[name] for name in ("source_snapshot_sha256", "permissions_sha256", "config_sha256")},
            "prepared_conditions": copy.deepcopy(self.prepared), "source_summary": {"source_kind": "THREE_DISTINCT_ARTIFICIAL_ARCHIVES"},
            "planned_case_count": count, "cases": [synthetic_case(j) for j in range(count)]}

    def issue(self, payload=None):
        handle = object()
        self.issued[id(handle)] = (handle, self.payload() if payload is None else payload)
        return handle

    def commit(self):
        return p.commit_readiness(self.issue())

    def rewrite_signed(self, mutate):
        _, envelope = p._read_json(p._receipt_path())
        mutate(envelope["commitment"])
        envelope["hmac_sha256"] = hmac.new(p._key_path().read_bytes(), p._canonical(envelope["commitment"]), hashlib.sha256).hexdigest()
        p._receipt_path().write_bytes(p._canonical(envelope))

    def assert_before_truth(self):
        calls = []
        with self.assertRaises((p.FinalProvenanceError, evaluation.EvaluationError)):
            evaluation.evaluate_readiness(lambda: calls.append("truth"))
        self.assertEqual(calls, [])

    def test_roundtrip_full_artifact_and_lazy_callback_after_fresh_verification(self):
        payload = self.payload(3)
        summary = p.commit_readiness(self.issue(payload))
        self.assertEqual((summary["planned_cases"], summary["persisted_case_artifacts"]), (3, 3))
        self.assertEqual(summary, p.verify_readiness_receipt())
        self.assertFalse(summary["final_prediction_qualified"])
        reopened = p.require_verified_readiness_execution()
        reopened.pop("_verified_context")
        self.assertEqual(reopened, payload)
        calls = []
        result = evaluation.evaluate_readiness(lambda: (calls.append("artificial"), {
            j: {"root_key": KEYS[0], "tau_relative": 180.} for j in range(3)})[1])
        self.assertEqual(calls, ["artificial"])
        self.assertTrue(result["durable_verification_before_truth_callback"])
        self.assertEqual(result["planned_cases"], 3)
        self.assertIsNone(result["cost_summary"]["components"]["c5_fit_seconds"]["total"])

    def test_foreign_copied_payload_and_arbitrary_handle_cannot_sign(self):
        issued = self.issue()
        for handle in (self.payload(), object(), copy.copy(issued), None):
            with self.subTest(handle=type(handle).__name__), self.assertRaises(p.FinalProvenanceError):
                p.commit_readiness(handle)
        self.assertFalse(p._receipt_path().exists())
        self.assertFalse(hasattr(p, "_bind_committer"))

    def test_exclusive_key_receipt_and_domain_never_grant_final(self):
        key = p._key_path().read_bytes()
        with self.assertRaises(p.FinalProvenanceError):
            p.initialize_readiness_key()
        self.assertEqual(key, p._key_path().read_bytes())
        self.commit()
        receipt = p._receipt_path().read_bytes()
        with self.assertRaises(p.FinalProvenanceError):
            self.commit()
        self.assertEqual(receipt, p._receipt_path().read_bytes())
        for callback in (p.require_final_campaign_receipt, evaluation.evaluate_final):
            with self.assertRaises((p.FinalProvenanceError, evaluation.EvaluationError)):
                callback()
        self.contract["permissions"]["final_campaign"] = True
        self.write_contract()
        self.assert_before_truth()

    def test_artifact_tamper_and_missing_block_before_callback(self):
        self.commit()
        _, envelope = p._read_json(p._receipt_path())
        path = p._artifact_path(envelope["commitment"]["artifact_manifest"][0]["sha256"])
        original = path.read_bytes()
        path.write_bytes(original + b" ")
        self.assert_before_truth()
        path.write_bytes(original)
        path.rename(path.with_suffix(".missing"))
        self.assert_before_truth()

    def test_signed_duplicate_stale_and_missing_manifest_reject_semantically(self):
        p.commit_readiness(self.issue(self.payload(2)))
        original = p._receipt_path().read_bytes()
        for mutation in (lambda c: c["artifact_manifest"].pop(),
                         lambda c: c["artifact_manifest"].__setitem__(1, copy.deepcopy(c["artifact_manifest"][0])),
                         lambda c: c["execution_header"].update(planned_case_count=1)):
            p._receipt_path().write_bytes(original)
            def mutate(c):
                mutation(c)
                c["artifact_manifest_sha256"] = p._digest(c["artifact_manifest"])
            self.rewrite_signed(mutate)
            self.assert_before_truth()

    def test_source_config_anchor_or_permission_drift_before_truth(self):
        self.commit()
        original_contract = p._contract_path().read_bytes()
        path = self.workspace / p._SOURCES[0]
        original_source = path.read_bytes()
        path.write_bytes(original_source + b"drift")
        self.assert_before_truth()
        path.write_bytes(original_source)
        for update in ({"prepared_conditions": {}}, {"trust_anchor": {"run_id": "foreign"}},
                       {"domain": p.historical.DOMAIN}, {"entry_bindings": {"receipt_sha256": "d" * 64}}):
            self.contract.update(update)
            self.write_contract()
            self.assert_before_truth()
            self.contract = json.loads(original_contract)
        p._contract_path().write_bytes(original_contract)
        p._key_path().write_bytes(b"x" * 32)
        self.assert_before_truth()

    def test_complete_diagnostics_universe_and_missing_timing_before_seal(self):
        mutators = [lambda c: c.pop("scientific_diagnostics"),
            lambda c: c["scientific_diagnostics"]["controller_bindings"].update(candidate_ids=[KEYS[0], KEYS[0]]),
            lambda c: c["scientific_diagnostics"]["controller_bindings"]["integrated_candidate_ids"].pop(next(iter(p.historical._DETECTORS))),
            lambda c: c["scientific_diagnostics"]["c1"].update(graph_sha256="f" * 64),
            lambda c: c["costs"].pop("c5_fit_seconds"),
            lambda c: c["scientific_diagnostics"].update(quality={"case_id": "forbidden"}),
            lambda c: c["scientific_diagnostics"]["c1"].update(evidence={}),
            lambda c: c["scientific_diagnostics"]["c1"]["evidence"].pop("masks"),
            lambda c: c["scientific_diagnostics"]["c1"]["ranking"]["primary"]["O"].update(scores=numeric(np.zeros(2))),
            lambda c: c["scientific_diagnostics"]["c5"]["G-MT"].update(state={}),
            lambda c: c["scientific_diagnostics"]["c5"]["G-MT"]["state"].pop("model_mask"),
            lambda c: c["scientific_diagnostics"]["c5"]["G-MT"]["bins"][0].pop("target_mask"),
            lambda c: c["scientific_diagnostics"]["c5"]["G-MT"]["bins"][0].update(selected_system_score=12.)]
        for mutate in mutators:
            payload = self.payload()
            mutate(payload["cases"][0])
            with self.subTest(mutate=mutate), self.assertRaises(p.FinalProvenanceError):
                p.commit_readiness(self.issue(payload))
        self.assertFalse(p._receipt_path().exists())

    def test_explicit_failure_prefix_and_absent_observation_preserve_every_slot(self):
        one = self.payload()
        case = one["cases"][0]
        detector = "G-MT"
        case["c5"][detector].update(status="FAILURE", scores=[11., 11., None, None, None],
            bin_statuses=["SUCCESS", "SUCCESS", "FAILURE", "FAILURE", "FAILURE"], triggers=[])
        record = case["scientific_diagnostics"]["c5"][detector]
        record.update(status="FAILURE", reason="SYNTHETIC_PARTIAL_FAILURE", bins=record["bins"][:2])
        case["scientific_diagnostics"]["controller_bindings"]["integrated_candidate_ids"][detector] = {}
        detector = "L-MT"
        case["c5"][detector].update(status="FAILURE", starts=[], ends=[], scores=[], bin_statuses=[], triggers=[])
        case["scientific_diagnostics"]["c5"][detector].update(status="FAILURE", input={}, state=None,
            bins=[], reason="C5_OBSERVATION_UNAVAILABLE")
        case["scientific_diagnostics"]["controller_bindings"]["integrated_candidate_ids"][detector] = {}
        summary = p.commit_readiness(self.issue(one))
        self.assertEqual(summary["persisted_case_artifacts"], 1)
        verified = p.require_verified_readiness_execution()["cases"][0]
        self.assertEqual(len(verified["c5"]), 8)
        self.assertEqual(len(verified["c5"]["G-MT"]["ends"]), 5)
        self.assertEqual(len(verified["scientific_diagnostics"]["c5"]["G-MT"]["bins"]), 2)
        self.assertIsNone(verified["scientific_diagnostics"]["c5"]["L-MT"]["state"])

    def test_fresh_process_verification_does_not_require_issuance_registry(self):
        self.commit()
        code = """import copy, json, os, sys, types
from pathlib import Path
from scripts.task_g import final_provenance as p
p._WORKSPACE=Path(sys.argv[1]); p._HOST_TRUST_MODE='ISOLATED_FIXTURE'
p._validate_frozen_files=lambda c: None
contract=json.loads(p._contract_path().read_bytes())
m=types.ModuleType('scripts.task_g.campaign')
m.prepare_conditions=lambda: {'conditions':copy.deepcopy(contract['prepared_conditions']), 'sha256':p._digest(contract['prepared_conditions'])}
sys.modules['scripts.task_g.campaign']=m
result=p.verify_readiness_receipt()
assert result['planned_cases']==1 and result['final_prediction_qualified'] is False
print('PASS_FRESH_ISOLATED_DURABLE_VERIFICATION')
"""
        result = subprocess.run([sys.executable, "-B", "-c", code, str(self.workspace)],
            cwd=Path(__file__).resolve().parents[2], env=dict(os.environ), capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "PASS_FRESH_ISOLATED_DURABLE_VERIFICATION")

    def test_integrated_full_provenance_before_seal_and_trigger_literal_mapping(self):
        one = self.payload()
        one["cases"][0] = with_integrated_trigger(one["cases"][0])
        for mutate in (lambda t: t.update(scientific_diagnostics=None), lambda t: t.update(quality=None),
                       lambda t: t.update(graph_provenance=None), lambda t: t.update(candidate_ids=KEYS[:]),
                       lambda t: t["scientific_diagnostics"]["evidence"].pop("masks"),
                       lambda t: t.update(scores=[.5, 1.])):
            bad = copy.deepcopy(one)
            mutate(bad["cases"][0]["c5"]["G-MT"]["triggers"][0])
            with self.subTest(mutate=mutate), self.assertRaises(p.FinalProvenanceError):
                p.commit_readiness(self.issue(bad))
        p.commit_readiness(self.issue(one))
        result = evaluation.evaluate_readiness(lambda: {0: {"root_key": KEYS[0], "tau_relative": 350.}})
        self.assertEqual(result["case_metrics"][0]["c5"]["G-MT"]["composition"]["metrics"]["rr"], .5)

    def test_numeric_envelope_shapes_masks_and_nan_retention(self):
        array = np.array([[np.nan, 2.]])
        self.assertTrue(np.isnan(p._numeric(numeric(array), "missing", shape=(1, 2))[0, 0]))
        for value in ({"dtype": "O", "shape": [1], "bytes_b64": "AAAA"},
                      {"dtype": "<f8", "shape": [2], "bytes_b64": "AAAA"}, numeric(np.array([np.inf]))):
            with self.subTest(value=value), self.assertRaises(p.FinalProvenanceError):
                p._numeric(value, "tampered")
        payload = self.payload()
        detector = next(iter(p.historical._DETECTORS))
        payload["cases"][0]["scientific_diagnostics"]["c5"][detector]["state"]["model_mask"] = numeric(np.ones((3, 1), dtype=bool))
        with self.assertRaises(p.FinalProvenanceError):
            p.commit_readiness(self.issue(payload))

    def test_second_fsync_failure_retains_attempt_and_prevents_truth(self):
        real_fsync = os.fsync
        calls = []
        def fsync(fd):
            calls.append(fd)
            if len(calls) == 3:  # case artifact; commitment; authenticated suffix
                raise OSError("synthetic second seal fsync failure")
            return real_fsync(fd)
        with patch.object(p.os, "fsync", side_effect=fsync), self.assertRaises(p.FinalProvenanceError):
            self.commit()
        self.assertFalse(p._receipt_path().exists())
        self.assertEqual(len(list((p._run_root() / "cache").glob("seal-attempt-*.json"))), 1)
        self.assert_before_truth()

    def test_fresh_context_race_prevents_publication_and_retains_attempt(self):
        real_context = p.registered_context
        calls = []
        def changed():
            calls.append(True)
            if len(calls) == 2:
                self.contract["resource_policy"]["worker_count"] = 2
                self.write_contract()
            return real_context()
        handle = self.issue()
        with patch.object(p, "registered_context", side_effect=changed), self.assertRaises(p.FinalProvenanceError):
            p.commit_readiness(handle)
        self.assertFalse(p._receipt_path().exists())
        self.assertEqual(len(list((p._run_root() / "cache").glob("seal-attempt-*.json"))), 1)


if __name__ == "__main__":
    unittest.main()
