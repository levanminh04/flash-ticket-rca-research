"""Isolated provenance fixtures: never read raw data or create the host key.

The fixture issuer substitutes an isolated controller seam, explicitly signs
ISOLATED_FIXTURE scope, and cannot certify production/core execution.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from scripts.task_g import provenance as p


class DurableEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="task-g-provenance-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.stack = []
        for target, value in (("_WORKSPACE", self.workspace),
                              ("_HOST_TRUST_MODE", "ISOLATED_FIXTURE")):
            item = patch.object(p, target, value)
            item.start()
            self.addCleanup(item.stop)
        item = patch.dict(os.environ, {"LOCALAPPDATA": str(self.root / "local")})
        item.start()
        self.addCleanup(item.stop)
        snapshot = {}
        for relative in p._SOURCES:
            file = self.workspace / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            data = ("ISOLATED_FIXTURE_SOURCE:" + relative).encode("utf-8")
            file.write_bytes(data)
            snapshot[relative] = hashlib.sha256(data).hexdigest()
        anchor = p.initialize_entry_key()
        self.contract = {
            "schema": "TD13-G-ENTRY-CONTRACT-v1", "run_id": p.RUN_ID,
            "permissions": {
                **{key: False for key in p._FINAL_PERMISSIONS},
                "synthetic_development_fixture_execution": True,
                "telemetry_final60_acquisition_and_admission": True,
            },
            "frozen_inputs": copy.deepcopy(p._FROZEN),
            "source_test_snapshot_before_qualification": snapshot,
            "trust_anchor": anchor,
        }
        p._contract_path().parent.mkdir(parents=True, exist_ok=True)
        self.write_contract()
        issued = {}

        def require(handle):
            if id(handle) not in issued or issued[id(handle)][0] is not handle:
                raise p.ProvenanceError("Fixture handle not issued")
            return copy.deepcopy(issued[id(handle)][1])

        self.issued = issued
        module = types.ModuleType("scripts.task_g.controller")
        module._entry_payload_for_provenance = require
        self.prepared = {"schema": "ISOLATED-FIXTURE-CONDITIONS-v1", "execution_enabled": False}
        module.prepare_conditions = lambda: {
            "conditions": copy.deepcopy(self.prepared), "sha256": p._digest(self.prepared)}
        item = patch.dict(sys.modules, {"scripts.task_g.controller": module})
        item.start()
        self.addCleanup(item.stop)

    def write_contract(self):
        p._contract_path().write_bytes(p._canonical(self.contract))

    def payload(self, *, raw=False, draws=False):
        matrix = [{"condition_id": "RCD_SYNTHETIC", "kind": "RCD", "expected_items": 3}]
        outputs = [{"condition_id": "RCD_SYNTHETIC", "items": [
            {"seed": seed, "status": "SUCCESS", "ranks": ["m000", "m001"]}
            for seed in (420, 421, 422)
        ]}]
        if draws:
            matrix.append({"condition_id": "R_FIXTURE", "kind": "R", "expected_items": 256})
            outputs.append({"condition_id": "R_FIXTURE", "items": [
                {"draw": draw, "status": "FAILURE" if draw == 17 else "SUCCESS",
                 "scores": None if draw == 17 else [1.0, 0.5],
                 "reason": "fixture_failure" if draw == 17 else None}
                for draw in range(256)
            ]})
        if raw:
            matrix.append({"condition_id": "RAW_ADMISSION", "kind": "ADMISSION", "expected_items": 60})
            outputs.append({"condition_id": "RAW_ADMISSION", "items": [
                {"ordinal": i, "case_status": "ADMISSION_COMPATIBLE",
                 "opaque_digest": hashlib.sha256(str(i).encode()).hexdigest()}
                for i in range(60)
            ]})
        return {
            "scope": "ENTRY_RAW_ADMISSION" if raw else "ENTRY_SYNTHETIC_DEVELOPMENT",
            "domain": p.DOMAIN, "run_id": p.RUN_ID, "execution_kind": "ENTRY_ONLY",
            "trust_mode": "ISOLATED_FIXTURE", "planned_matrix": matrix, "outputs": outputs,
            "source_snapshot_sha256": p._digest(self.contract["source_test_snapshot_before_qualification"]),
            "permissions_sha256": p._digest(self.contract["permissions"]),
            "prepared_conditions": copy.deepcopy(self.prepared),
            "config_sha256": p._digest(self.prepared),
            "final_condition_matrix_sha256": p._digest(self.prepared),
            "aggregate_report": {"fixture_only": True, "final_predictions": False},
        }

    def issue(self, payload=None):
        handle = object()
        self.issued[id(handle)] = (handle, copy.deepcopy(payload or self.payload()))
        return handle

    def rewrite_envelope(self, transform):
        envelope = json.loads(p._receipt_path().read_bytes())
        transform(envelope)
        p._receipt_path().write_bytes(p._canonical(envelope))

    def test_durable_roundtrip_retains_every_output_failure(self):
        payload = self.payload(draws=True)
        receipt = p.commit_entry(self.issue(payload))
        self.assertEqual(receipt["planned_items"], 259)
        self.assertFalse(receipt["final_prediction_qualified"])
        stored = json.loads(p._receipt_path().read_bytes())["commitment"]["execution"]
        self.assertEqual(stored, payload)
        self.assertEqual(stored["outputs"][1]["items"][17]["status"], "FAILURE")
        self.assertEqual(p.verify_entry_receipt(), receipt)

    def test_arbitrary_dict_copied_or_unknown_handle_cannot_sign(self):
        handle = self.issue()
        for forged in (self.payload(), object(), copy.copy(handle), None):
            with self.assertRaises(p.ProvenanceError):
                p.commit_entry(forged)
        self.assertFalse(p._receipt_path().exists())
        p.commit_entry(handle)

    def test_no_exported_signer_or_reset_factory(self):
        for name in ("_bind_committer", "sign", "sign_payload", "_sign", "reset_issuer"):
            self.assertFalse(hasattr(p, name))
        with self.assertRaises(TypeError):
            p.commit_entry(self.issue(), key=b"x" * 32)
        with self.assertRaises(TypeError):
            p.verify_entry_receipt(path=self.root / "caller.json")
        with self.assertRaises(TypeError):
            p.initialize_entry_key(self.root / "caller.key")

    def test_exclusive_key_no_overwrite_or_rotation(self):
        original = p._key_path().read_bytes()
        with self.assertRaises(p.ProvenanceError):
            p.initialize_entry_key()
        self.assertEqual(original, p._key_path().read_bytes())

    def test_existing_partial_key_is_not_repaired(self):
        p._key_path().write_bytes(b"partial")
        with self.assertRaises(p.ProvenanceError):
            p.initialize_entry_key()
        self.assertEqual(p._key_path().read_bytes(), b"partial")
        with self.assertRaises(p.ProvenanceError):
            p.commit_entry(self.issue())

    def test_exclusive_receipt_no_overwrite(self):
        p.commit_entry(self.issue())
        original = p._receipt_path().read_bytes()
        with self.assertRaises(p.ProvenanceError):
            p.commit_entry(self.issue())
        self.assertEqual(p._receipt_path().read_bytes(), original)

    def test_fsync_failure_retains_partial_bytes_without_callback(self):
        counter = []
        with patch.object(p.os, "fsync", side_effect=OSError("fixture crash")):
            with self.assertRaises(p.ProvenanceError):
                p.commit_entry(self.issue())
        self.assertFalse(p._receipt_path().exists())
        attempts = list((p._receipt_path().parent / "cache").glob("entry-attempt-*.json"))
        self.assertEqual(len(attempts), 1)
        original = attempts[0].read_bytes()
        with self.assertRaises(p.ProvenanceError):
            p.evaluate_entry_fixture(lambda: counter.append("opened"), allow_synthetic_fixture=True)
        self.assertEqual(counter, [])
        p.commit_entry(self.issue())
        self.assertEqual(attempts[0].read_bytes(), original)

    def test_second_fsync_failure_never_publishes_authenticated_cache(self):
        counter = []
        with patch.object(p.os, "fsync", side_effect=[None, OSError("second fixture crash")]):
            with self.assertRaises(p.ProvenanceError):
                p.commit_entry(self.issue())
        self.assertFalse(p._receipt_path().exists())
        attempts = list((p._receipt_path().parent / "cache").glob("entry-attempt-*.json"))
        self.assertEqual(len(attempts), 1)
        # The complete cache artifact is retained as evidence, but cannot be
        # accepted through any caller-supplied alternate receipt path.
        self.assertIn("hmac_sha256", json.loads(attempts[0].read_bytes()))
        with self.assertRaises(p.ProvenanceError):
            p.evaluate_entry_fixture(lambda: counter.append("opened"), allow_synthetic_fixture=True)
        self.assertEqual(counter, [])

    def test_truncated_write_is_preserved_and_rejected_before_callback(self):
        p._receipt_path().write_bytes(b'{"commitment":')
        counter = []
        with self.assertRaises(p.ProvenanceError):
            p.evaluate_entry_fixture(lambda: counter.append("opened"), allow_synthetic_fixture=True)
        self.assertEqual(counter, [])
        with self.assertRaises(p.ProvenanceError):
            p.commit_entry(self.issue())
        self.assertEqual(p._receipt_path().read_bytes(), b'{"commitment":')

    def test_tamper_rehash_does_not_authenticate(self):
        p.commit_entry(self.issue())
        def attack(envelope):
            value = envelope["commitment"]
            value["execution"]["outputs"][0]["items"][0]["ranks"] = ["forged"]
            value["outputs_sha256"] = p._digest(value["execution"]["outputs"])
            value["payload_sha256"] = p._digest(value["execution"])
            envelope["hmac_sha256"] = p._digest(value)
        self.rewrite_envelope(attack)
        counter = []
        with self.assertRaises(p.ProvenanceError):
            p.evaluate_entry_fixture(lambda: counter.append("opened"), allow_synthetic_fixture=True)
        self.assertEqual(counter, [])

    def test_wrong_anchor_missing_key_or_changed_contract_fail_closed(self):
        p.commit_entry(self.issue())
        original = p._key_path().read_bytes()
        p._key_path().write_bytes(b"z" * 32)
        with self.assertRaises(p.ProvenanceError):
            p.verify_entry_receipt()
        p._key_path().write_bytes(original)
        self.contract["trust_anchor"]["key_sha256"] = "0" * 64
        self.write_contract()
        with self.assertRaises(p.ProvenanceError):
            p.verify_entry_receipt()
        p._key_path().unlink()
        with self.assertRaises(p.ProvenanceError):
            p.verify_entry_receipt()

    def test_source_test_drift_blocks_issue_and_verification(self):
        p.commit_entry(self.issue())
        (self.workspace / p._SOURCES[0]).write_bytes(b"drift")
        with self.assertRaises(p.ProvenanceError):
            p.verify_entry_receipt()
        with self.assertRaises(p.ProvenanceError):
            p.commit_entry(self.issue())

    def test_permissions_domain_run_and_scope_cannot_promote(self):
        for field, value in (("scope", "FINAL_CAMPAIGN"), ("domain", "campaign"),
                             ("run_id", "other"), ("trust_mode", "HOST_TRUSTED")):
            payload = self.payload()
            payload[field] = value
            with self.assertRaises(p.ProvenanceError):
                p.commit_entry(self.issue(payload))
        self.contract["permissions"]["final_labels"] = True
        self.write_contract()
        with self.assertRaises(p.ProvenanceError):
            p.commit_entry(self.issue())

    def test_missing_condition_seed_draw_and_nonfinite_payload_rejected(self):
        alterations = []
        item = self.payload()
        item["outputs"] = []
        alterations.append(item)
        item = self.payload()
        item["outputs"][0]["items"].pop()
        alterations.append(item)
        item = self.payload()
        item["outputs"][0]["items"][0]["seed"] = 419
        alterations.append(item)
        item = self.payload(draws=True)
        item["outputs"][1]["items"][32]["draw"] = 33
        alterations.append(item)
        item = self.payload(draws=True)
        item["outputs"][1]["items"].pop()
        alterations.append(item)
        item = self.payload()
        item["outputs"][0]["items"][0]["score"] = float("nan")
        alterations.append(item)
        for payload in alterations:
            with self.assertRaises(p.ProvenanceError):
                p.commit_entry(self.issue(payload))
        self.assertFalse(p._receipt_path().exists())

    def test_lazy_fixture_callback_only_after_verified_readback(self):
        counter = []
        with self.assertRaises(p.ProvenanceError):
            p.evaluate_entry_fixture(lambda: counter.append("opened"), allow_synthetic_fixture=True)
        p.commit_entry(self.issue())
        with self.assertRaises(p.ProvenanceError):
            p.evaluate_entry_fixture(lambda: counter.append("opened"))
        self.assertEqual(counter, [])
        result = p.evaluate_entry_fixture(lambda: counter.append("opened") or 7,
                                          allow_synthetic_fixture=True)
        self.assertEqual(counter, ["opened"])
        self.assertEqual(result["fixture_result"], 7)

    def test_raw_entry_never_invokes_label_callback_even_with_fixture_flag(self):
        p.commit_entry(self.issue(self.payload(raw=True)))
        counter = []
        with self.assertRaises(p.ProvenanceError):
            p.evaluate_entry_fixture(lambda: counter.append("opened"), allow_synthetic_fixture=True)
        self.assertEqual(counter, [])

    def test_raw_failure_and_unavailable_cases_remain_in_complete_receipt(self):
        payload = self.payload(raw=True)
        payload["outputs"][1]["items"][17]["case_status"] = "PHYSICAL_SOURCE_FAILURE"
        for row in payload["outputs"][1]["items"][18:]:
            row["case_status"] = "NOT_AUDITED_AFTER_SOURCE_FAILURE"
        receipt = p.commit_entry(self.issue(payload))
        self.assertEqual(receipt["planned_items"], 63)
        stored = json.loads(p._receipt_path().read_bytes())["commitment"]["execution"]
        self.assertEqual(stored["outputs"][1]["items"], payload["outputs"][1]["items"])

    def test_raw_ordinal_or_case_state_drift_fails_completeness(self):
        for field, value in (("ordinal", 2), ("case_status", "caller_verified")):
            payload = self.payload(raw=True)
            payload["outputs"][1]["items"][0][field] = value
            with self.assertRaises(p.ProvenanceError):
                p.commit_entry(self.issue(payload))

    def test_host_entry_callback_rejected_even_for_synthetic_scope(self):
        # This denial canary never signs HOST_TRUSTED output with a fixture key.
        counter = []
        with patch.object(p, "verify_entry_receipt", return_value={
                "scope": "ENTRY_SYNTHETIC_DEVELOPMENT", "trust_mode": "HOST_TRUSTED"}):
            with self.assertRaises(p.ProvenanceError):
                p.evaluate_entry_fixture(lambda: counter.append("opened"), allow_synthetic_fixture=True)
        self.assertEqual(counter, [])

    def test_symlink_source_output_or_windows_cache_junction_rejected(self):
        target = self.root / "elsewhere"
        target.write_bytes(b"x")
        try:
            p._receipt_path().symlink_to(target)
        except OSError:
            try:
                import _winapi
            except ImportError:
                self.skipTest("Host cannot create fixture symbolic/reparse paths")
            directory = self.root / "elsewhere-directory"
            directory.mkdir()
            _winapi.CreateJunction(str(directory), str(p._receipt_path().parent / "cache"))
            with self.assertRaises(p.ProvenanceError):
                p.commit_entry(self.issue())
            self.assertFalse(p._receipt_path().exists())
            return
        with self.assertRaises(p.ProvenanceError):
            p.commit_entry(self.issue())
        p._receipt_path().unlink()
        file = self.workspace / p._SOURCES[0]
        file.unlink()
        file.symlink_to(target)
        with self.assertRaises(p.ProvenanceError):
            p.commit_entry(self.issue())

    def test_fresh_process_verifies_without_controller_registry(self):
        receipt = p.commit_entry(self.issue())
        workspace_real = Path(__file__).resolve().parents[2]
        script = (
            "import json,sys,types; from pathlib import Path; "
            "from scripts.task_g import provenance as p; "
            "p._WORKSPACE=Path(sys.argv[1]); p._HOST_TRUST_MODE='ISOLATED_FIXTURE'; "
            "m=types.ModuleType('scripts.task_g.controller'); "
            "conditions=json.loads(sys.argv[2]); "
            "m.prepare_conditions=lambda:{'conditions':conditions,'sha256':p._digest(conditions)}; "
            "sys.modules['scripts.task_g.controller']=m; "
            "print(json.dumps(p.verify_entry_receipt(),sort_keys=True))"
        )
        result = subprocess.run([sys.executable, "-B", "-c", script, str(self.workspace),
                                 json.dumps(self.prepared)],
                                cwd=workspace_real, env=dict(os.environ),
                                capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout), receipt)

    def test_readback_error_blocks_callback_and_preserves_attempt(self):
        original = Path.read_bytes
        def read(path):
            value = original(path)
            if path.parent.name == "cache" and path.name.startswith("entry-attempt-"):
                return value + b"fixture_changed"
            return value
        with patch.object(Path, "read_bytes", read):
            with self.assertRaises(p.ProvenanceError):
                p.commit_entry(self.issue())
        counter = []
        with self.assertRaises(p.ProvenanceError):
            p.evaluate_entry_fixture(lambda: counter.append("opened"), allow_synthetic_fixture=True)
        self.assertEqual(counter, [])
        self.assertFalse(p._receipt_path().exists())
        self.assertEqual(len(list((p._receipt_path().parent / "cache").glob("entry-attempt-*.json"))), 1)

    def test_final_staged_readback_failure_never_publishes(self):
        original = Path.read_bytes
        def read(path):
            value = original(path)
            if path.parent.name == "cache" and b'"hmac_sha256"' in value:
                return value + b"fixture_changed"
            return value
        with patch.object(Path, "read_bytes", read):
            with self.assertRaises(p.ProvenanceError):
                p.commit_entry(self.issue())
        counter = []
        with self.assertRaises(p.ProvenanceError):
            p.evaluate_entry_fixture(lambda: counter.append("opened"), allow_synthetic_fixture=True)
        self.assertEqual(counter, [])
        self.assertFalse(p._receipt_path().exists())

    def test_config_and_source_bindings_cannot_be_caller_selected(self):
        for name in ("config_sha256", "source_snapshot_sha256", "permissions_sha256",
                     "final_condition_matrix_sha256"):
            payload = self.payload()
            payload[name] = "0" * 64
            with self.assertRaises(p.ProvenanceError):
                p.commit_entry(self.issue(payload))
        payload = self.payload()
        payload["prepared_conditions"]["execution_enabled"] = True
        payload["config_sha256"] = p._digest(payload["prepared_conditions"])
        payload["final_condition_matrix_sha256"] = payload["config_sha256"]
        with self.assertRaises(p.ProvenanceError):
            p.commit_entry(self.issue(payload))

    def test_duplicate_json_key_cannot_be_smuggled(self):
        p.commit_entry(self.issue())
        original = p._receipt_path().read_bytes()
        p._receipt_path().write_bytes(original.replace(b'{"commitment":',
                                                      b'{"hmac_sha256":"x","commitment":', 1))
        with self.assertRaises(p.ProvenanceError):
            p.verify_entry_receipt()


if __name__ == "__main__":
    unittest.main()
