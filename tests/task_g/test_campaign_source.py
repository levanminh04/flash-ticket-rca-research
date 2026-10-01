"""Synthetic and pinned-numeric development source boundary checks only."""

from __future__ import annotations

import copy
import hashlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

from scripts.task_g import campaign_source as source


_REAL_REGISTERED_CONTEXT = source._registered_context
_FIXTURE_CONTEXT = {"contract_sha256": "a" * 64,
                    "permissions": {"development30_timing_only": True},
                    "entry_bindings": {"receipt_sha256": "b" * 64}}


class CampaignSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Registration monkeypatches are isolated test runtime fixtures, never
        # qualification evidence. The public sources retain permanent scopes.
        with patch.object(source, "_registered_context", return_value=copy.deepcopy(_FIXTURE_CONTEXT)):
            cls.synthetic = source.make_synthetic_source()
            cls.development = source.load_development_source()

    def setUp(self):
        self.context_patch = patch.object(source, "_registered_context",
                                          return_value=copy.deepcopy(_FIXTURE_CONTEXT))
        self.context_mock = self.context_patch.start()
        self.addCleanup(self.context_patch.stop)

    def test_exact_synthetic_cohort_sixty_twenty_by_three(self):
        summary = source.source_summary(self.synthetic)
        self.assertEqual(summary["scope"], source.SYNTHETIC_SCOPE)
        self.assertEqual(summary["source_kind"], "SYNTHETIC_NUMERIC")
        self.assertEqual((summary["planned_cases"], summary["planned_cells"], summary["repeats_per_cell"]), (60, 20, 3))
        self.assertEqual(source.case_count(self.synthetic), 60)
        records = [source.get_case(self.synthetic, ordinal) for ordinal in range(60)]
        self.assertEqual([row["ordinal"] for row in records], list(range(60)))
        for cell in range(20):
            selected = [row for row in records if row["cell_ordinal"] == cell]
            self.assertEqual([row["repeat"] for row in selected], [0, 1, 2])
        self.assertEqual(len({row["c1"].handle for row in records}), 60)
        self.assertFalse(summary["final_prediction_qualified"])
        self.assertFalse(summary["actual_truth_read"])
        self.assertFalse(summary["actual_final_telemetry_opened"])

    def test_unissued_dict_and_exact_type_alias_rejected(self):
        class Aliased(source.CampaignSource):
            def __eq__(self, other):
                return True
            def __hash__(self):
                return 123
        for handle in (source.CampaignSource(), Aliased(), None,
                       {"scope": source.SYNTHETIC_SCOPE, "source_identity_verified": True}):
            for method in (source.source_summary, source.case_count):
                with self.assertRaises(source.CampaignSourceError):
                    method(handle)
            with self.assertRaises(source.CampaignSourceError):
                source.get_case(handle, 0)

    def test_no_public_arbitrary_loader_flags_or_issuer(self):
        for method in (source.make_synthetic_source, source.load_development_source):
            for keywords in ({"bundle": {}}, {"loader": lambda: {}},
                             {"source_identity_verified": True}, {"root_index": 0},
                             {"scope": "FINAL_CAMPAIGN"}):
                with self.assertRaises(TypeError):
                    method(**keywords)
        for private in ("_bind_sources", "_synthetic_cases", "_development_cases",
                        "_fixed_fixture_raw", "_issue", "_state", "_lookup"):
            self.assertFalse(hasattr(source, private))

    def test_summary_copy_cannot_promote_or_mutate_issued_source(self):
        summary = self.synthetic.summary
        summary["scope"] = "FINAL_CAMPAIGN"
        summary["final_prediction_qualified"] = True
        summary["planned_cases"] = 1
        self.assertEqual(self.synthetic.summary["scope"], source.SYNTHETIC_SCOPE)
        self.assertEqual(self.synthetic.summary["planned_cases"], 60)
        self.assertFalse(self.synthetic.summary["final_prediction_qualified"])

    def test_model_observations_redact_names_epochs_and_locations(self):
        for handle in (self.synthetic, self.development):
            case = source.get_case(handle, 0)
            one = case["c1"]
            self.assertEqual(one.node_ids, tuple(f"v{i}" for i in range(len(one.adjacency))))
            self.assertRegex(one.handle, r"^[0-9a-f]{16}$")
            self.assertEqual(set(case), {"ordinal", "cell_ordinal", "repeat", "c1", "c5", "rcd", "numeric_input_sha256"})
            payload = json.dumps({"quality": dict(one.quality), "graph": dict(one.graph_provenance),
                                  "source": dict(one.source_hashes), "nodes": one.node_ids})
            for forbidden in ("ts-", "re2tt_", "case-audits", "inject_time", "root_cause", "D:/", "100000"):
                self.assertNotIn(forbidden, payload)
            self.assertFalse(one.quality["actual_final_admission"])

    def test_readonly_detached_observations_do_not_change_internal_bytes(self):
        original = source.get_case(self.synthetic, 0)
        one = original["c1"]
        five = original["c5"]
        with self.assertRaises(ValueError):
            one.ref[0, 0, 0] = 123
        with self.assertRaises(ValueError):
            five.stream_values[0, 0, 0] = 123
        # Even re-enabling a returned array's own write flag mutates only a copy.
        one.ref.setflags(write=True)
        one.ref[0, 0, 0] = 987654
        five.stream_values.setflags(write=True)
        five.stream_values[0, 0, 0] = 987654
        fresh = source.get_case(self.synthetic, 0)
        self.assertNotEqual(fresh["c1"].ref[0, 0, 0], 987654)
        self.assertNotEqual(fresh["c5"].stream_values[0, 0, 0], 987654)
        self.assertEqual(fresh["numeric_input_sha256"], original["numeric_input_sha256"])

    def test_rcd_numeric_owner_and_same_source_copy(self):
        row = source.get_case(self.synthetic, 0)
        rcd = row["rcd"]
        self.assertEqual(set(rcd), {"values", "owners", "candidate_count"})
        self.assertEqual(rcd["values"].shape, (600, 3))
        self.assertEqual(rcd["owners"], [0, 1, 2])
        self.assertEqual(rcd["candidate_count"], 3)
        self.assertTrue(np.isfinite(rcd["values"]).all())
        rcd["values"][:] = 0
        rcd["owners"][0] = 2
        fresh = source.get_case(self.synthetic, 0)["rcd"]
        self.assertTrue(np.any(fresh["values"]))
        self.assertEqual(fresh["owners"], [0, 1, 2])

    def test_ordinal_and_trigger_endpoints_strict_integer_boundary(self):
        for ordinal in (-1, 60, True, 0.0, "0"):
            with self.assertRaises(source.CampaignSourceError):
                source.get_case(self.synthetic, ordinal)
        for endpoint in (-5, True, 360.0, 361, "360"):
            with self.assertRaises(source.CampaignSourceError):
                source.integrated_observation(self.synthetic, 0, endpoint)
        with self.assertRaisesRegex(source.CampaignSourceError, "INSUFFICIENT_HISTORY"):
            source.integrated_observation(self.synthetic, 0, 195)
        with self.assertRaisesRegex(source.CampaignSourceError, "OUTSIDE_OBSERVED_HISTORY"):
            source.integrated_observation(self.synthetic, 0, 1085)

    def test_context_drift_invalidates_previously_issued_handle(self):
        drift = copy.deepcopy(_FIXTURE_CONTEXT)
        drift["contract_sha256"] = "c" * 64
        self.context_mock.return_value = drift
        for method in (source.source_summary, source.case_count):
            with self.assertRaisesRegex(source.CampaignSourceError, "CONTEXT_DRIFT"):
                method(self.synthetic)
        with self.assertRaisesRegex(source.CampaignSourceError, "CONTEXT_DRIFT"):
            source.get_case(self.development, 0)
        with self.assertRaisesRegex(source.CampaignSourceError, "CONTEXT_DRIFT"):
            source.integrated_observation(self.synthetic, 0, 360)

    def test_development_reads_exact_thirty_numeric_caches_without_case_audit(self):
        actual = source._regular_bytes
        accesses = []
        def read(path):
            accesses.append(Path(path))
            return actual(path)
        with patch.object(source, "_regular_bytes", side_effect=read):
            handle = source.load_development_source()
        self.assertEqual(len(accesses), 31)
        self.assertEqual(sum(path.suffix == ".npz" for path in accesses), 30)
        self.assertFalse(any("case-audits" in str(path) for path in accesses))
        summary = source.source_summary(handle)
        self.assertEqual(summary["scope"], source.DEVELOPMENT_SCOPE)
        self.assertEqual(summary["pinned_numeric_inventory_sha256"], source.DEVELOPMENT_INVENTORY_SHA)
        self.assertEqual(source.case_count(handle), 30)
        self.assertEqual((summary["candidate_count_min"], summary["candidate_count_max"]), (20, 27))
        for ordinal in range(30):
            case = source.get_case(handle, ordinal)
            self.assertEqual(case["c1"].ref.shape[1:], (12, 30))
            self.assertIsNone(case["c5"])
            self.assertIsNone(case["rcd"])
        with self.assertRaisesRegex(source.CampaignSourceError, "NO_INTEGRATED_SOURCE"):
            source.integrated_observation(handle, 0, 360)

    def test_development_original_r_seed_handle_retained_controller_side(self):
        contract = json.loads((source.WORKSPACE / source.F05_REL).read_bytes())
        expected = [contract["opaque_handles_by_development_id"][case]
                    for case in contract["development_allowlist"]]
        observed = [source.get_case(self.development, ordinal)["c1"].handle for ordinal in range(30)]
        self.assertEqual(observed, expected)

    def test_development_permission_closed_rejects_before_cache_read(self):
        closed = copy.deepcopy(_FIXTURE_CONTEXT)
        closed["permissions"]["development30_timing_only"] = False
        self.context_mock.return_value = closed
        with patch.object(source, "_regular_bytes") as reader:
            with self.assertRaisesRegex(source.CampaignSourceError, "PERMISSION_CLOSED"):
                source.load_development_source()
        reader.assert_not_called()

    def test_numeric_hash_mismatch_rejected_before_npz_parse(self):
        actual = source._regular_bytes
        def read(path):
            value = actual(path)
            return value + b"tamper" if Path(path).suffix == ".npz" else value
        with patch.object(source, "_regular_bytes", side_effect=read), patch.object(np, "load") as loader:
            with self.assertRaisesRegex(source.CampaignSourceError, "NUMERIC_BYTES_DRIFT"):
                source.load_development_source()
        loader.assert_not_called()

    def test_input_contract_digest_mismatch_before_numeric_parse(self):
        with patch.object(source, "_regular_bytes", return_value=b"{}"), patch.object(np, "load") as loader:
            with self.assertRaisesRegex(source.CampaignSourceError, "CONTRACT_DRIFT"):
                source.load_development_source()
        loader.assert_not_called()

    def _counterfactual_archive(self, change):
        actual = source._regular_bytes
        contract = json.loads(actual(source.WORKSPACE / source.F05_REL))
        row = next(row for row in contract["input_files"] if row["path"].endswith("/c1_primary.npz"))
        target = source.WORKSPACE / row["path"]
        with np.load(io.BytesIO(actual(target)), allow_pickle=False) as archive:
            arrays = {key: archive[key].copy() for key in archive.files}
        change(arrays)
        buffer = io.BytesIO()
        np.savez(buffer, **arrays)
        payload = buffer.getvalue()
        row.update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
        encoded = source._canonical(contract)
        inventory = [row for row in contract["input_files"] if row["path"].endswith("/c1_primary.npz")]
        def read(path):
            if Path(path) == source.WORKSPACE / source.F05_REL:
                return encoded
            if Path(path) == target:
                return payload
            return actual(path)
        return read, hashlib.sha256(encoded).hexdigest(), source._digest(inventory)

    def test_unexpected_oracle_array_rejected_before_any_array_values(self):
        read, contract_hash, inventory_hash = self._counterfactual_archive(
            lambda arrays: arrays.update(root=np.array([987654])))
        actual = np.load
        array_accesses = []
        class FooterOnly:
            def __init__(self, *args, **kwargs):
                self.archive = actual(*args, **kwargs)
                self.files = self.archive.files
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.archive.close()
            def __getitem__(self, key):
                array_accesses.append(key)
                raise AssertionError("Oracle value opened")
        # Counterfactual pins are isolated test runtime overrides. They cannot
        # issue final-qualified sources; the production pins are immutable.
        with patch.object(source, "_regular_bytes", side_effect=read), patch.object(source, "F05_SHA", contract_hash), \
                patch.object(source, "DEVELOPMENT_INVENTORY_SHA", inventory_hash), patch.object(np, "load", FooterOnly):
            with self.assertRaisesRegex(source.CampaignSourceError, "SCHEMA_DRIFT"):
                source.load_development_source()
        self.assertEqual(array_accesses, [])

    def test_infinite_numeric_input_is_failure_not_imputed_success(self):
        read, contract_hash, inventory_hash = self._counterfactual_archive(
            lambda arrays: arrays["ref"].__setitem__((0, 0, 0), np.inf))
        with patch.object(source, "_regular_bytes", side_effect=read), patch.object(source, "F05_SHA", contract_hash), \
                patch.object(source, "DEVELOPMENT_INVENTORY_SHA", inventory_hash):
            with self.assertRaisesRegex(source.CampaignSourceError, "NUMERIC_INPUT_INVALID"):
                source.load_development_source()

    def test_integrated_uses_past_only_windows_and_fixture_has_six_query_bins(self):
        bundle = source.integrated_observation(self.synthetic, 0, 720)
        self.assertEqual(bundle.ref.shape, (3, 12, 30))
        self.assertEqual(bundle.query.shape, (3, 12, 6))
        self.assertTrue(bundle.graph_provenance["past_only"])
        self.assertEqual(bundle.quality["relative_endpoint"], 720)
        # The artificial node0 extra jump is at720, so a past-only query ending
        # at720 contains the pre-jump level near1e6, never the2e6 future level.
        self.assertTrue(np.all(bundle.query[0, 8] < 1_500_000))

    def test_integrated_future_numeric_and_name_suffix_does_not_change_past(self):
        from scripts.task_e.input_adapters import integrated_bundle
        expected = source.integrated_observation(self.synthetic, 0, 720)
        def future_changed(raw, endpoint):
            changed = {key: value.copy(deep=True) for key, value in raw.items()}
            changed["metrics"].loc[changed["metrics"].time >= endpoint, "v0_cpu"] = 1e100
            changed["traces"].loc[changed["traces"].startTimeMillis >= endpoint * 1000, "serviceName"] = "artificial-future-only"
            changed["logs"].loc[changed["logs"].timestamp >= endpoint, "container_name"] = "artificial-future-only"
            return integrated_bundle(changed, endpoint)
        with patch("scripts.task_e.input_adapters.integrated_bundle", side_effect=future_changed):
            changed = source.make_synthetic_source()
        actual = source.integrated_observation(changed, 0, 720)
        for name in ("ref", "query", "adjacency"):
            np.testing.assert_array_equal(getattr(actual, name), getattr(expected, name))
        self.assertEqual(actual.node_ids, expected.node_ids)

    def test_c5_future_suffix_keeps_warmup_and_closed_prefix_bins(self):
        from scripts.task_e.loader import c5_bundle
        expected = source.get_case(self.synthetic, 0)["c5"]
        def future_changed(raw, *args, **kwargs):
            changed = {key: value.copy(deep=True) for key, value in raw.items()}
            endpoint = int(changed["metrics"].time.min()) + 360
            changed["metrics"].loc[changed["metrics"].time >= endpoint, "v0_cpu"] = 1e100
            changed["traces"].loc[changed["traces"].startTimeMillis >= endpoint * 1000, "serviceName"] = "artificial-future-only"
            return c5_bundle(changed, *args, **kwargs)
        with patch("scripts.task_e.loader.c5_bundle", side_effect=future_changed):
            changed = source.make_synthetic_source()
        actual = source.get_case(changed, 0)["c5"]
        np.testing.assert_array_equal(actual.warmup_values, expected.warmup_values)
        np.testing.assert_array_equal(actual.stream_values[:36], expected.stream_values[:36])
        np.testing.assert_array_equal(actual.adjacency, expected.adjacency)
        np.testing.assert_array_equal(actual.fit_service_mask, expected.fit_service_mask)
        np.testing.assert_array_equal(actual.relative_endpoints, expected.relative_endpoints)

    def test_c5_translation_preserves_numeric_worker_inputs(self):
        from scripts.task_e.loader import c5_bundle
        expected = source.get_case(self.synthetic, 0)["c5"]
        def translated(raw, *args, **kwargs):
            changed = {key: value.copy(deep=True) for key, value in raw.items()}
            shift = 1_000_000
            changed["metrics"]["time"] += shift
            changed["traces"]["startTimeMillis"] += shift * 1000
            changed["traces"]["startTime"] += shift
            changed["logs"]["timestamp"] += shift
            return c5_bundle(changed, *args, **kwargs)
        with patch("scripts.task_e.loader.c5_bundle", side_effect=translated):
            changed = source.make_synthetic_source()
        actual = source.get_case(changed, 0)["c5"]
        for name in ("warmup_values", "stream_values", "adjacency", "fit_service_mask", "relative_endpoints"):
            np.testing.assert_array_equal(getattr(actual, name), getattr(expected, name))

    def test_actual_registered_guard_requires_snapshot_and_closed_permissions(self):
        permissions = {key: False for key in source.FINAL_CLOSED}
        permissions["synthetic_development_readiness"] = True
        permissions["telemetry_final60_new_acquisition"] = False
        contract = {"run_id": source.RUN_ID, "domain": source.DOMAIN, "phase": "CAMPAIGN_READINESS_ONLY",
                    "permissions": permissions, "source_test_snapshot_before_qualification": None}
        with patch.object(source, "_regular_bytes", return_value=source._canonical(contract)):
            with self.assertRaisesRegex(source.CampaignSourceError, "STABLE_SOURCE_REGISTRATION_REQUIRED"):
                _REAL_REGISTERED_CONTEXT()
        contract["permissions"]["final_tau_metadata"] = True
        with patch.object(source, "_regular_bytes", return_value=source._canonical(contract)):
            with self.assertRaisesRegex(source.CampaignSourceError, "PERMISSION_OR_DOMAIN_DRIFT"):
                _REAL_REGISTERED_CONTEXT()

    def test_final_source_verifies_host_entry_then_stops_before_any_raw_or_truth(self):
        entry = {"scope": "ENTRY_RAW_ADMISSION", "trust_mode": "HOST_TRUSTED", "receipt_sha256": "b" * 64}
        with patch("scripts.task_g.provenance.verify_entry_receipt", return_value=entry) as verifier, \
                patch.object(source, "_regular_bytes") as reader:
            with self.assertRaisesRegex(source.CampaignSourceError, "FINAL_TAU_AND_CAMPAIGN_PERMISSION_CLOSED"):
                source.open_final_source()
            verifier.assert_called_once_with()
            reader.assert_not_called()
        with self.assertRaises(TypeError):
            source.open_final_source(entry)
        for changed in ({**entry, "trust_mode": "CALLER"}, {**entry, "receipt_sha256": "c" * 64},
                        {**entry, "scope": "ENTRY_SYNTHETIC_DEVELOPMENT"}):
            with patch("scripts.task_g.provenance.verify_entry_receipt", return_value=changed):
                with self.assertRaisesRegex(source.CampaignSourceError, "ENTRY_BINDING_INVALID"):
                    source.open_final_source()

    def test_frozen_adapter_byte_drift_rejected_by_independent_source_guard(self):
        actual = source._regular_bytes
        contract = json.loads(actual(source.WORKSPACE / source.CONTRACT_REL))
        contract["source_test_snapshot_before_qualification"] = {
            relative: hashlib.sha256(b"").hexdigest() for relative in source.SNAPSHOT_PATHS}
        encoded = source._canonical(contract)
        def read(path):
            relative = str(Path(path).relative_to(source.WORKSPACE)).replace("\\", "/") if Path(path).is_relative_to(source.WORKSPACE) else None
            if relative == source.CONTRACT_REL:
                return encoded
            if relative in source.SNAPSHOT_PATHS:
                return b""
            value = actual(path)
            return value + b"\n" if relative == "scripts/task_e/loader.py" else value
        with patch.object(source, "_regular_bytes", side_effect=read):
            with self.assertRaisesRegex(source.CampaignSourceError, "FROZEN_ADAPTER_SOURCE_DRIFT"):
                _REAL_REGISTERED_CONTEXT()


if __name__ == "__main__":
    unittest.main()
