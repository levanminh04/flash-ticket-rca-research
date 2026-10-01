"""Isolated G31 durability, completeness, forgery and recovery canaries.

No host key, telemetry, labels or campaign is accessed.  The isolated fixture
controller seam explicitly carries ISOLATED_FIXTURE authority only.
"""

from __future__ import annotations

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

from scripts.task_g import campaign_provenance as p


class CampaignDurabilityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="g31-provenance-isolated-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        for target, value in (("_WORKSPACE", self.workspace),
                              ("_HOST_TRUST_MODE", "ISOLATED_FIXTURE")):
            fixture_patch = patch.object(p, target, value)
            fixture_patch.start()
            self.addCleanup(fixture_patch.stop)
        fixture_patch = patch.dict(os.environ, {"LOCALAPPDATA": str(self.root / "local")})
        fixture_patch.start()
        self.addCleanup(fixture_patch.stop)
        fixture_patch = patch.object(p, "_validate_frozen_files", return_value=None)
        fixture_patch.start()
        self.addCleanup(fixture_patch.stop)
        snapshot = {}
        for relative in p._SOURCES:
            file = self.workspace / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            data = ("ISOLATED_SOURCE:" + relative).encode("utf-8")
            file.write_bytes(data)
            snapshot[relative] = hashlib.sha256(data).hexdigest()
        self.prepared = {"scientific_objects": {"selections": {"c5": {
            "detectors": [{"id": detector, "threshold": 10.0} for detector in sorted(p._DETECTORS)]}}}}
        self.contract = {
            "schema": "TD13-G31-READINESS-CONTRACT-v1", "run_id": p.RUN_ID,
            "domain": p.DOMAIN, "phase": p.PHASE,
            "permissions": {**{key: False for key in p._FINAL_PERMISSIONS},
                "synthetic_development_readiness": True, "development30_timing_only": True,
                "synthetic_evaluation": True, "readiness_host_key_generation": True,
                "telemetry_final60_new_acquisition": False},
            "frozen_inputs": copy.deepcopy(p._FROZEN),
            "source_test_snapshot_before_qualification": snapshot,
            "prepared_conditions": self.prepared,
            "environment": {"main_python": platform.python_version(),
                "packages": {name: importlib.metadata.version(name) for name in (
                    "numpy", "pandas", "pyarrow", "huggingface-hub")},
                "dependency_installation": False},
            "resource_policy": {"worker_count": 1, "numeric_threads": 1,
                "thread_environment": {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
                    "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"},
                "development_timing_infrastructure_deadline_seconds": 900,
                "common_L_O_R_timeout_seconds": None, "R_generation_included": True,
                "secondary_reuses_same_realized_undirected_graphs": True,
                "failures_and_attempts_preserved": True,
                "timing_measurement_repetition": "ONE_PREDECLARED_PASS_ALL_DEVELOPMENT30_NO_OUTCOME_SELECTION"},
            "entry_bindings": {"receipt_sha256": "a" * 64},
            "development_inputs": {"numeric_inventory_sha256": "b" * 64},
            "registration_history": [], "trust_anchor": None,
        }
        p._contract_path().parent.mkdir(parents=True, exist_ok=True)
        self.write_contract()
        self.contract["trust_anchor"] = p.initialize_readiness_key()
        self.write_contract()
        self.issued, self.case_issued = {}, {}

        def require(handle):
            if id(handle) not in self.issued or self.issued[id(handle)][0] is not handle:
                raise p.CampaignProvenanceError("Not issued by isolated fixture controller")
            return copy.deepcopy(self.issued[id(handle)][1])

        def case_require(handle):
            if id(handle) not in self.case_issued or self.case_issued[id(handle)][0] is not handle:
                raise p.CampaignProvenanceError("Not issued by isolated fixture case controller")
            return copy.deepcopy(self.case_issued[id(handle)][1])

        module = types.ModuleType("scripts.task_g.campaign")
        module._campaign_payload_for_provenance = require
        module._case_payload_for_checkpoint = case_require
        module.prepare_conditions = lambda: {"conditions": copy.deepcopy(self.prepared),
                                              "sha256": p._digest(self.prepared)}
        fixture_patch = patch.dict(sys.modules, {"scripts.task_g.campaign": module})
        fixture_patch.start()
        self.addCleanup(fixture_patch.stop)

    def write_contract(self):
        p._contract_path().write_bytes(p._canonical(self.contract))

    def case(self, ordinal=0, *, timing=False):
        adjacency = np.array([[False, True], [True, False]], dtype=np.bool_)
        graph_digest = hashlib.sha256(str(adjacency.shape).encode("ascii") + np.packbits(adjacency).tobytes()).hexdigest()
        graphs = [{"draw": draw, "seed": draw, "status": "SUCCESS", "adjacency": adjacency.astype(int).tolist(),
                   "graph_sha256": graph_digest, "acceptance": 0, "retained_edge_fraction": 1.0}
                  for draw in range(256)]
        arms = {"L": {"status": "SUCCESS", "scores": [1.0, 0.5]},
                "O": {"status": "SUCCESS", "scores": [1.0, 0.5]},
                "R": [{"draw": draw, "seed": draw, "status": "SUCCESS", "scores": [1.0, 0.5],
                       "graph_sha256": graph_digest, "retained_edge_fraction": 1.0} for draw in range(256)]}
        return {
            "ordinal": ordinal, "cell_ordinal": ordinal // 3, "repeat": ordinal % 3,
            "candidate_count": 2, "numeric_input_sha256": hashlib.sha256(str(ordinal).encode()).hexdigest(),
            "shared_preprocessing_failed": False, "local_evidence": [1.0, 0.5],
            "control_graphs": graphs, "c1": {"primary": copy.deepcopy(arms), "secondary": copy.deepcopy(arms)},
            "contextual": {} if timing else {
                "Local-MAX-MT": {"status": "SUCCESS", "scores": [1.0, 0.5]},
                "BARO-RANK-adapted-TD12": {"status": "SUCCESS", "scores": [1.0, 0.5]},
                "RCD": {"metric_owners": {"m000": 0, "m001": 1}, "n_services": 2, "input_sha256": "c" * 64,
                    "qualification_identity_sha256": "38253ebbfaa53bdad20b66e655ade3fade363fdd9ef71ee2ab6df722ab4fac04",
                    "seed_outputs": [{"seed": seed, "bins": 5, "status": "SUCCESS", "ranks": ["m000", "m001"]}
                                     for seed in (420, 421, 422)]}},
            "c5": {} if timing else {name: {"status": "SUCCESS", "threshold": 10.0,
                "starts": [180, 185, 190, 195, 200], "ends": [185, 190, 195, 200, 205],
                "scores": [11.0] * 5, "bin_statuses": ["SUCCESS"] * 5,
                "triggers": [{"endpoint": 195, "status": "INSUFFICIENT_HISTORY", "scores": None,
                              "candidate_count": 0, "input_sha256": None}]} for name in p._DETECTORS},
            "costs": {"aggregate_case_walltime_seconds": 0.125},
        }

    def payload(self, *, timing=False, with_report=False):
        context, _ = p._registered_context()
        payload = {
            "schema": p.EXECUTION_SCHEMA, "run_id": p.RUN_ID, "domain": p.DOMAIN,
            "phase": p.PHASE, "trust_mode": "ISOLATED_FIXTURE",
            "scope": "DEVELOPMENT_TIMING_ONLY" if timing else "SYNTHETIC_CAMPAIGN_READINESS",
            **{key: context[key] for key in ("source_snapshot_sha256", "permissions_sha256", "config_sha256")},
            "prepared_conditions": copy.deepcopy(self.prepared),
            "source_summary": {"source_kind": "DEVELOPMENT_NUMERIC_CACHE" if timing else "SYNTHETIC_NUMERIC"},
            "planned_case_count": 30 if timing else 60,
            "cases": [self.case(ordinal, timing=timing) for ordinal in range(30 if timing else 60)],
        }
        if with_report:
            payload["development_timing_report"] = {
                "cases": [self.case(ordinal, timing=True) for ordinal in range(30)],
                "maximum_successful_development_case_walltime_seconds": 0.125,
                "common_L_O_R_timeout_seconds": 300.0,
            }
        return payload

    def issue(self, payload=None):
        handle = object()
        self.issued[id(handle)] = (handle, payload if payload is not None else self.payload())
        return handle

    def case_issue(self, *, timing=False, ordinal=0):
        case = self.case(ordinal, timing=timing)
        payload = {"kind": "development" if timing else "synthetic", "ordinal": ordinal,
                   "numeric_input_sha256": case["numeric_input_sha256"], "case": case,
                   "source_summary": {"source_kind": "DEVELOPMENT_NUMERIC_CACHE" if timing else "SYNTHETIC_NUMERIC"}}
        handle = object()
        self.case_issued[id(handle)] = (handle, payload)
        return handle, payload

    def assert_rejected_before_provider(self, call):
        counter = []
        with self.assertRaises((p.CampaignProvenanceError, ValueError, RuntimeError)):
            call(lambda: counter.append("opened"))
        self.assertEqual(counter, [])

    def test_full60_and_development30_roundtrip_preserves_all_numerical_artifacts(self):
        payload = self.payload(with_report=True)
        result = p.commit_readiness(self.issue(payload))
        self.assertEqual(result["planned_cases"], 60)
        self.assertEqual(result["persisted_case_artifacts"], 90)
        self.assertFalse(result["final_prediction_qualified"])
        self.assertEqual(result, p.verify_readiness_receipt())
        verified = p.require_verified_readiness_execution()
        context = verified.pop("_verified_context")
        self.assertEqual(verified, payload)
        self.assertTrue(context["permissions"]["synthetic_evaluation"])
        self.assertFalse(context["final_prediction_qualified"])

    def test_arbitrary_dictionary_copied_unknown_or_foreign_handle_cannot_sign(self):
        handle = self.issue()
        for forged in (self.payload(), object(), copy.copy(handle), None):
            with self.assertRaises(p.CampaignProvenanceError):
                p.commit_readiness(forged)
        self.assertFalse(p._receipt_path().exists())
        case_handle, _ = self.case_issue()
        with self.assertRaises(p.CampaignProvenanceError):
            p.commit_readiness(case_handle)
        with self.assertRaises(p.CampaignProvenanceError):
            p.commit_case_checkpoint(handle)

    def test_no_exported_signer_factory_or_caller_key_anchor_path(self):
        for name in ("_bind_committer", "_bind_checkpoint_committer", "sign", "sign_payload", "reset_issuer"):
            self.assertFalse(hasattr(p, name))
        with self.assertRaises(TypeError):
            p.initialize_readiness_key(self.root / "caller.key")
        with self.assertRaises(TypeError):
            p.verify_readiness_receipt(path=self.root / "caller.json")
        with self.assertRaises(TypeError):
            p.commit_readiness(self.issue(), key=b"x" * 32)

    def test_exclusive_key_and_partial_key_never_repaired(self):
        original = p._key_path().read_bytes()
        with self.assertRaises(p.CampaignProvenanceError):
            p.initialize_readiness_key()
        self.assertEqual(p._key_path().read_bytes(), original)
        p._key_path().write_bytes(b"partial")
        with self.assertRaises(p.CampaignProvenanceError):
            p.initialize_readiness_key()
        self.assertEqual(p._key_path().read_bytes(), b"partial")

    def test_missing_changed_anchor_and_source_snapshot_fail_closed(self):
        handle = self.issue()
        self.contract["trust_anchor"]["key_sha256"] = "0" * 64
        self.write_contract()
        with self.assertRaises(p.CampaignProvenanceError):
            p.commit_readiness(handle)
        self.contract["trust_anchor"] = p.readiness_anchor_descriptor()
        self.write_contract()
        (self.workspace / p._SOURCES[0]).write_bytes(b"source drift")
        with self.assertRaises(p.CampaignProvenanceError):
            p.commit_readiness(handle)

    def test_package_version_and_final_permission_drift_rejected(self):
        self.contract["environment"]["packages"]["numpy"] = "wrong"
        self.write_contract()
        with self.assertRaises(p.CampaignProvenanceError):
            p._registered_context()
        self.contract["environment"]["packages"]["numpy"] = importlib.metadata.version("numpy")
        self.contract["permissions"]["final_tau_metadata"] = True
        self.write_contract()
        with self.assertRaises(p.CampaignProvenanceError):
            p._registered_context()

    def test_wrong_run_domain_scope_source_or_config_cannot_promote(self):
        payload = self.payload()
        for field, value in (("scope", "FINAL_CAMPAIGN"), ("domain", "foreign"),
                             ("run_id", "foreign"), ("phase", "FINAL"),
                             ("trust_mode", "HOST_TRUSTED"), ("config_sha256", "0" * 64)):
            forged = copy.deepcopy(payload)
            forged[field] = value
            with self.assertRaises(p.CampaignProvenanceError):
                p.commit_readiness(self.issue(forged))
        payload["source_summary"]["source_kind"] = "FINAL_TELEMETRY"
        with self.assertRaises(p.CampaignProvenanceError):
            p.commit_readiness(self.issue(payload))

    def test_missing_duplicate_case_and_wrong_cell_repeat_rejected(self):
        context, contract = p._registered_context()
        payload = self.payload()
        for change in (lambda v: v["cases"].pop(),
                       lambda v: v["cases"].__setitem__(1, v["cases"][0]),
                       lambda v: v["cases"][0].__setitem__("repeat", 1)):
            forged = copy.deepcopy(payload)
            change(forged)
            with self.assertRaises(p.CampaignProvenanceError):
                p._validate_execution(forged, context, contract)

    def test_missing_R_draw_seed_or_realized_graph_and_secondary_binding_rejected(self):
        context, contract = p._registered_context()
        payload = self.payload()
        changes = (
            lambda c: c["c1"]["primary"]["R"].pop(),
            lambda c: c["control_graphs"].pop(),
            lambda c: c["c1"]["secondary"]["R"][0].__setitem__("seed", 999),
            lambda c: c["control_graphs"][0]["adjacency"][0].__setitem__(1, 0),
            lambda c: c["c1"]["secondary"]["R"][0].__setitem__("graph_sha256", "0" * 64),
        )
        for change in changes:
            forged = copy.deepcopy(payload)
            change(forged["cases"][0])
            with self.assertRaises(p.CampaignProvenanceError):
                p._validate_execution(forged, context, contract)

    def test_failed_RCD_seed_retained_and_missing_or_forged_identity_rejected(self):
        case = self.case()
        case["contextual"]["RCD"]["seed_outputs"][1].update(status="FAILURE", ranks=None)
        p._validate_case(case, 0, timing=False, prepared=self.prepared)
        for field, value in (("qualification_identity_sha256", "0" * 64), ("n_services", 3)):
            forged = copy.deepcopy(case)
            forged["contextual"]["RCD"][field] = value
            with self.assertRaises(p.CampaignProvenanceError):
                p._validate_case(forged, 0, timing=False, prepared=self.prepared)
        case["contextual"]["RCD"]["seed_outputs"].pop()
        with self.assertRaises(p.CampaignProvenanceError):
            p._validate_case(case, 0, timing=False, prepared=self.prepared)

    def test_all_C5_bins_thresholds_and_every_trigger_are_semantically_verified(self):
        changes = (
            lambda c: c["c5"].pop("G-MTL"),
            lambda c: c["c5"]["G-MTL"]["ends"].pop(),
            lambda c: c["c5"]["G-MTL"].__setitem__("threshold", 99),
            lambda c: c["c5"]["G-MTL"]["triggers"].clear(),
            lambda c: c["c5"]["G-MTL"]["triggers"][0].update(status="SUCCESS", scores=[]),
        )
        for change in changes:
            case = self.case()
            change(case)
            with self.assertRaises(p.CampaignProvenanceError):
                p._validate_case(case, 0, timing=False, prepared=self.prepared)

    def test_nonfinite_scores_or_oracle_location_fields_are_not_issued(self):
        for field, value in (("tau", 720), ("root_index", 0), ("case_path", "synthetic/path")):
            case = self.case()
            case[field] = value
            with self.assertRaises(p.CampaignProvenanceError):
                p._validate_case(case, 0, timing=False, prepared=self.prepared)
        case = self.case()
        case["c1"]["primary"]["L"]["scores"][0] = float("nan")
        with self.assertRaises(p.CampaignProvenanceError):
            p._validate_case(case, 0, timing=False, prepared=self.prepared)

    def test_shared_failure_cannot_be_success_or_successful_zero_vector(self):
        case = self.case()
        case["shared_preprocessing_failed"] = True
        for arms in case["c1"].values():
            arms["L"]["scores"] = [0.0, 0.0]
        with self.assertRaises(p.CampaignProvenanceError):
            p._validate_case(case, 0, timing=False, prepared=self.prepared)

    def test_artifact_fsync_failure_preserved_without_readiness_publication(self):
        with patch.object(p.os, "fsync", side_effect=OSError("isolated failure")):
            with self.assertRaises(p.CampaignProvenanceError):
                p.commit_readiness(self.issue())
        self.assertFalse(p._receipt_path().exists())
        attempts = list((p._run_root() / "cache/artifacts").glob("attempt-*.json"))
        self.assertEqual(len(attempts), 1)
        self.assertTrue(attempts[0].read_bytes())
        from scripts.task_g.evaluation import evaluate_readiness
        self.assert_rejected_before_provider(evaluate_readiness)

    def test_second_receipt_fsync_failure_leaves_only_unaccepted_staging(self):
        count = 0
        def fail_second_receipt(_):
            nonlocal count
            count += 1
            if count == 62:  #60 artifact fsyncs, then receipt prefix and envelope
                raise OSError("second receipt fsync")
        with patch.object(p.os, "fsync", side_effect=fail_second_receipt):
            with self.assertRaises(p.CampaignProvenanceError):
                p.commit_readiness(self.issue())
        self.assertEqual(count, 62)
        self.assertFalse(p._receipt_path().exists())
        attempts = list((p._run_root() / "cache").glob("readiness-attempt-*.json"))
        self.assertEqual(len(attempts), 1)
        self.assertIn("hmac_sha256", json.loads(attempts[0].read_bytes()))
        from scripts.task_g.evaluation import evaluate_readiness
        self.assert_rejected_before_provider(evaluate_readiness)

    def test_readback_failure_preserves_stage_and_cannot_open_provider(self):
        original = Path.read_bytes
        def changed(path):
            raw = original(path)
            return raw + b"isolated change" if path.name.startswith("attempt-") else raw
        with patch.object(Path, "read_bytes", changed):
            with self.assertRaises(p.CampaignProvenanceError):
                p.commit_readiness(self.issue())
        self.assertFalse(p._receipt_path().exists())
        from scripts.task_g.evaluation import evaluate_readiness
        self.assert_rejected_before_provider(evaluate_readiness)

    def test_exclusive_receipt_and_content_addressed_reuse_never_overwrite(self):
        p.commit_readiness(self.issue())
        original = p._receipt_path().read_bytes()
        with self.assertRaises(p.CampaignProvenanceError):
            p.commit_readiness(self.issue())
        self.assertEqual(original, p._receipt_path().read_bytes())
        case = self.case()
        record = p._persist_artifact(case, "EXECUTION_CASE")
        cache = p._artifact_path(record["sha256"])
        previous = cache.read_bytes()
        self.assertEqual(record, p._persist_artifact(case, "EXECUTION_CASE"))
        self.assertEqual(previous, cache.read_bytes())
        cache.write_bytes(b"tamper")
        with self.assertRaises(p.CampaignProvenanceError):
            p._persist_artifact(case, "EXECUTION_CASE")
        self.assertEqual(cache.read_bytes(), b"tamper")

    def test_missing_or_tampered_artifact_rejected_before_lazy_provider(self):
        p.commit_readiness(self.issue())
        envelope = json.loads(p._receipt_path().read_bytes())
        row = envelope["commitment"]["artifact_manifest"][0]
        path = p._artifact_path(row["sha256"])
        path.write_bytes(path.read_bytes() + b" ")
        from scripts.task_g.evaluation import evaluate_readiness
        self.assert_rejected_before_provider(evaluate_readiness)
        path.unlink()
        self.assert_rejected_before_provider(evaluate_readiness)

    def test_correct_HMAC_cannot_make_incomplete_or_promoted_semantics_valid(self):
        p.commit_readiness(self.issue())
        envelope = json.loads(p._receipt_path().read_bytes())
        envelope["commitment"]["artifact_manifest"].pop()
        envelope["commitment"]["artifact_manifest_sha256"] = p._digest(envelope["commitment"]["artifact_manifest"])
        envelope["hmac_sha256"] = hmac.new(p._key_path().read_bytes(), p._canonical(envelope["commitment"]), hashlib.sha256).hexdigest()
        p._receipt_path().write_bytes(p._canonical(envelope))
        with self.assertRaises(p.CampaignProvenanceError):
            p.verify_readiness_receipt()

    def test_fresh_process_needs_no_live_issuance_registry(self):
        result = p.commit_readiness(self.issue())
        real_workspace = Path(__file__).resolve().parents[2]
        script = (
            "import json,sys,types;from pathlib import Path;"
            "from scripts.task_g import campaign_provenance as p;"
            "p._WORKSPACE=Path(sys.argv[1]);p._HOST_TRUST_MODE='ISOLATED_FIXTURE';"
            "p._validate_frozen_files=lambda _:None;"
            "m=types.ModuleType('scripts.task_g.campaign');conditions=json.loads(sys.argv[2]);"
            "m.prepare_conditions=lambda:{'conditions':conditions,'sha256':p._digest(conditions)};"
            "sys.modules['scripts.task_g.campaign']=m;"
            "print(json.dumps(p.verify_readiness_receipt(),sort_keys=True))"
        )
        run = subprocess.run([sys.executable, "-B", "-c", script, str(self.workspace), json.dumps(self.prepared)],
                             cwd=real_workspace, env=dict(os.environ), capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(run.stdout), result)

    def test_readiness_or_entry_never_authenticate_actual_final_scope(self):
        counter = []
        with self.assertRaises(p.CampaignProvenanceError):
            p.require_final_campaign_receipt()
        from scripts.task_g.evaluation import evaluate_final
        with self.assertRaises(ValueError):
            evaluate_final(lambda: counter.append("opened"))
        self.assertEqual(counter, [])

    def test_checkpoint_missing_roundtrip_and_foreign_handle_rejected(self):
        handle, payload = self.case_issue()
        self.assertIsNone(p.verify_case_checkpoint("synthetic", 0, payload["numeric_input_sha256"]))
        result = p.commit_case_checkpoint(handle)
        self.assertEqual(result, payload)
        self.assertEqual(result, p.verify_case_checkpoint("synthetic", 0, payload["numeric_input_sha256"]))
        with self.assertRaises(p.CampaignProvenanceError):
            p.commit_case_checkpoint(payload)
        with self.assertRaises(p.CampaignProvenanceError):
            p.verify_case_checkpoint("synthetic", 0, "0" * 64)
        with self.assertRaises(p.CampaignProvenanceError):
            p.verify_case_checkpoint("final", 0, payload["numeric_input_sha256"])

    def test_checkpoint_exclusive_and_two_fsync_crash_preserves_attempt(self):
        handle, payload = self.case_issue()
        with patch.object(p.os, "fsync", side_effect=[None, OSError("second checkpoint fsync")]):
            with self.assertRaises(p.CampaignProvenanceError):
                p.commit_case_checkpoint(handle)
        path = p._checkpoint_path("synthetic", 0)
        self.assertFalse(path.exists())
        attempts = list(path.parent.glob("case-attempt-*.json"))
        self.assertEqual(len(attempts), 1)
        partial = attempts[0].read_bytes()
        self.assertIsNone(p.verify_case_checkpoint("synthetic", 0, payload["numeric_input_sha256"]))
        p.commit_case_checkpoint(handle)
        original = path.read_bytes()
        with self.assertRaises(p.CampaignProvenanceError):
            p.commit_case_checkpoint(handle)
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(attempts[0].read_bytes(), partial)

    def test_development_checkpoint_survives_derived_timeout_with_exact_history(self):
        handle, payload = self.case_issue(timing=True)
        p.commit_case_checkpoint(handle)
        original = p._contract_path().read_bytes()
        self.contract["registration_history"].append({"raw_utf8": original.decode("utf-8"),
                                                      "sha256": hashlib.sha256(original).hexdigest()})
        self.contract["resource_policy"]["common_L_O_R_timeout_seconds"] = 300.0
        self.write_contract()
        self.assertEqual(p.verify_case_checkpoint("development", 0, payload["numeric_input_sha256"]), payload)
        self.contract["resource_policy"]["worker_count"] = 2
        self.write_contract()
        with self.assertRaises(p.CampaignProvenanceError):
            p.verify_case_checkpoint("development", 0, payload["numeric_input_sha256"])

    def test_development_checkpoint_does_not_trust_claimed_or_missing_history(self):
        handle, payload = self.case_issue(timing=True)
        p.commit_case_checkpoint(handle)
        self.contract["resource_policy"]["common_L_O_R_timeout_seconds"] = 300.0
        self.write_contract()
        with self.assertRaises(p.CampaignProvenanceError):
            p.verify_case_checkpoint("development", 0, payload["numeric_input_sha256"])

    def test_synthetic_checkpoint_binds_full_timeout_and_bad_HMAC_is_retained(self):
        handle, payload = self.case_issue()
        p.commit_case_checkpoint(handle)
        path = p._checkpoint_path("synthetic", 0)
        previous = path.read_bytes()
        self.contract["resource_policy"]["common_L_O_R_timeout_seconds"] = 301.0
        self.write_contract()
        with self.assertRaises(p.CampaignProvenanceError):
            p.verify_case_checkpoint("synthetic", 0, payload["numeric_input_sha256"])
        self.assertEqual(path.read_bytes(), previous)

    def test_duplicate_JSON_or_reparse_cache_path_is_rejected(self):
        handle, payload = self.case_issue()
        p.commit_case_checkpoint(handle)
        path = p._checkpoint_path("synthetic", 0)
        original = path.read_bytes()
        path.write_bytes(original.replace(b'{"commitment":', b'{"hmac_sha256":"x","commitment":', 1))
        with self.assertRaises(p.CampaignProvenanceError):
            p.verify_case_checkpoint("synthetic", 0, payload["numeric_input_sha256"])
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        # Test a separate missing cache branch so preserved evidence is intact.
        target = p._run_root() / "cache/artifacts"
        try:
            target.symlink_to(elsewhere, target_is_directory=True)
        except OSError:
            import _winapi
            _winapi.CreateJunction(str(elsewhere), str(target))
        with self.assertRaises(p.CampaignProvenanceError):
            p._persist_artifact(self.case(), "EXECUTION_CASE")


if __name__ == "__main__":
    unittest.main()
