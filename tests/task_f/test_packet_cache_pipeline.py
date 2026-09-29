from __future__ import annotations

import ast
import copy
import tempfile
import unittest
from pathlib import Path
from types import MappingProxyType

import numpy as np

from rca.cache import CacheIdentityError, cache_identity, read_numeric_cache, write_numeric_cache
from rca.observation import C1Observation, ObservationError, admit_c1_bundle, admit_c5_bundle
from rca.packet import PacketValidationError, rank_table, seal_packet, validate_packet

from _helpers import W, c1_observation, c5_numeric_path, c5_observation, code_identity, pipeline, sha, synthetic_c1


def basic_packet():
    table = rank_table([2.0, 1.0], ["a", "b"], evidence_ids={"a": ["e1"], "b": []})
    return {
        "schema_version": "TD13-F-DIAGNOSIS-PACKET-v1",
        "method_identity": {"td_sha256": "a" * 64},
        "observation": {"opaque_handle": "opaque"},
        "status": "SUCCESS",
        "score_semantics": "suspicion/diagnostic utility; not root probability or causal truth",
        "evidence_catalog": {"e1": {"kind": "fixture"}},
        "quality": {"missing": []},
        "uncertainty": {"fixture": True},
        "ranking": table,
    }


class PacketCachePipelineTests(unittest.TestCase):
    def test_01_packet_seals_and_validates(self):
        packet = seal_packet(basic_packet())
        self.assertTrue(validate_packet(packet))

    def test_02_rank_or_score_tampering_is_rejected(self):
        packet = seal_packet(basic_packet())
        packet["ranking"]["rows"][0]["score"] = 99.0
        with self.assertRaises(PacketValidationError):
            validate_packet(packet)

    def test_03_unresolved_evidence_is_rejected(self):
        packet = basic_packet()
        packet["ranking"]["rows"][1]["evidence_ids"] = ["missing"]
        packet["ranking"].pop("rank_sha256")
        import hashlib, json
        plain = dict(packet["ranking"])
        packet["ranking"]["rank_sha256"] = hashlib.sha256(json.dumps(plain, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        with self.assertRaises(PacketValidationError):
            seal_packet(packet)

    def test_04_oracle_and_absolute_path_fields_are_rejected(self):
        for key, value in (("root", "a"), ("fault_label", "cpu"), ("tau", 720), ("case_path", r"D:\secret")):
            packet = basic_packet()
            packet[key] = value
            with self.subTest(key=key), self.assertRaises(PacketValidationError):
                seal_packet(packet)

    def test_05_cache_raw_and_cached_arrays_are_exact(self):
        identity = cache_identity(
            source_hashes={"metrics": "a" * 64},
            td_hash="b" * 64,
            code_hashes={"core": "c" * 64},
            config={"profile": "frozen"},
            profile="c1-primary",
            cutoff=[300, 600],
        )
        arrays = {"values": np.array([[1.0, np.nan], [2.0, 3.0]])}
        with tempfile.TemporaryDirectory() as directory:
            first = write_numeric_cache(directory, identity, arrays)
            restored = read_numeric_cache(directory, identity)
            second = write_numeric_cache(directory, identity, arrays)
            np.testing.assert_array_equal(restored["values"], arrays["values"])
            self.assertFalse(first["reused"])
            self.assertTrue(second["reused"])

    def test_06_cache_binds_cutoff_config_profile_and_source(self):
        base = dict(
            source_hashes={"metrics": "a" * 64},
            td_hash="b" * 64,
            code_hashes={"core": "c" * 64},
            config={"x": 1},
            profile="c5-primary",
            cutoff=180,
        )
        identities = [cache_identity(**base)]
        for field, value in (("cutoff", 185), ("profile", "c5-other"), ("config", {"x": 2}), ("source_hashes", {"metrics": "d" * 64})):
            changed = dict(base)
            changed[field] = value
            identities.append(cache_identity(**changed))
        self.assertEqual(len({row["key"] for row in identities}), len(identities))

    def test_07_cache_rejects_identity_mutation(self):
        identity = cache_identity(source_hashes={"m": "a" * 64}, td_hash="b" * 64, code_hashes={"c": "c" * 64}, config={}, profile="p", cutoff=5)
        identity["cutoff"] = 10
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(CacheIdentityError):
            write_numeric_cache(directory, identity, {"a": np.ones(1)})

    def test_08_metadata_and_candidate_remap_leave_numeric_outputs_invariant(self):
        original = c1_observation()
        remapped = c1_observation(node_ids=tuple(f"renamed-{index}" for index in range(len(original.node_ids))))
        core = pipeline()
        left = core.run_c1(original, include_structural_control=False)
        right = core.run_c1(remapped, include_structural_control=False)
        np.testing.assert_array_equal(left["L_scores"], right["L_scores"])
        np.testing.assert_array_equal(left["O"]["scores"], right["O"]["scores"])
        self.assertNotEqual(left["packet"]["ranking"]["rows"][0]["candidate"], right["packet"]["ranking"]["rows"][0]["candidate"])

    def test_09_future_suffix_does_not_change_earlier_c5_outputs(self):
        original = c5_observation()
        changed_values = np.concatenate((original.warmup_values.copy(), original.stream_values.copy()))
        changed_values[36 + 30 :] = 1e9
        changed = c5_observation(values=changed_values)
        core = pipeline()
        left = core.run_c5(original, "G-MTL")
        right = core.run_c5(changed, "G-MTL")
        self.assertEqual(left["status"], "SUCCESS")
        self.assertEqual(right["status"], "SUCCESS")
        np.testing.assert_array_equal(
            np.array([row["score"] for row in left["bins"][:30]]),
            np.array([row["score"] for row in right["bins"][:30]]),
        )

    def test_10_c5_absolute_time_translation_is_discarded_at_admission(self):
        path = c5_numeric_path()
        with np.load(path, allow_pickle=False) as stored:
            base = {key: stored[key].copy() for key in stored.files}
        base.update(service_names=[f"n{i}" for i in range(base["values"].shape[1])], audit={
            "graph": {},
            "profile": "TD13-C5-EVENT-TIME",
            "qualification": {
                "status": "QUALIFIED",
                "profile": "TD13-C5-EVENT-TIME",
                "adapter_id": "fixture",
            },
        })
        first = dict(base, s0=1_000)
        second = dict(base, s0=9_999_999)
        common = dict(handle="opaque", source_hashes={"numeric": sha(path)}, fit_bins=24, cal_bins=12)
        a = admit_c5_bundle(first, **common)
        b = admit_c5_bundle(second, **common)
        np.testing.assert_array_equal(a.warmup_values, b.warmup_values)
        np.testing.assert_array_equal(a.relative_endpoints, b.relative_endpoints)
        self.assertFalse(hasattr(a, "s0"))

    def test_11_failures_are_explicit_not_healthy(self):
        base = synthetic_c1()
        broken = C1Observation(
            base.handle,
            base.ref,
            base.query,
            (9, 9, 9),
            base.adjacency,
            base.node_ids,
            base.source_hashes,
            base.graph_provenance,
            base.quality,
            base.evidence_catalog,
        )
        result = pipeline().run_c1(broken, include_structural_control=False)
        self.assertEqual(result["status"], "INPUT_FAILURE")
        self.assertEqual(result["packet"]["status"], "INPUT_FAILURE")

    def test_12_numeric_core_does_not_import_evaluator_or_ground_truth(self):
        forbidden = {"evaluator", "calibration", "root_cause", "ground_truth"}
        for path in (W / "src" / "rca").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imports.append(node.module or "")
            self.assertFalse(any(any(token in item.lower() for token in forbidden) for item in imports), path)

    def test_13_controller_clock_and_trace_identity_are_projected_out(self):
        base = synthetic_c1()
        bundle = {
            "ref": base.ref,
            "query": base.query,
            "adj": base.adjacency,
            "service_names": base.node_ids,
            "channel_types": base.channel_types,
            "audit": {
                "profile": "TD12-INTEGRATED-MTL",
                "qualification": {
                    "status": "QUALIFIED",
                    "profile": "TD12-INTEGRATED-MTL",
                    "adapter_id": "fixture",
                },
                "graph": {"edges": 2},
                "metric_ref": {"conflicting_seconds": {"a_cpu": [1700000001, 1700000002]}},
                "trace": {
                    "events": [
                        {"kind": "TRACE_CONFLICT", "event_ms": 1700000001000, "first_seen_ms": 1700000000000, "bin": 3, "key": ["secret"]}
                    ],
                    "quarantined_keys": [{"key": ["secret"], "first_seen_ms": 1700000000000}],
                },
            },
        }
        observation = admit_c1_bundle(
            bundle,
            handle="opaque",
            source_hashes={"traces": "a" * 64},
        )
        rendered = repr(dict(observation.quality)).lower()
        self.assertNotIn("event_ms", rendered)
        self.assertNotIn("first_seen", rendered)
        self.assertNotIn("170000000", rendered)
        self.assertIn("conflicting_second_counts", rendered)
        self.assertIn("affected_relative_bins", rendered)

    def test_14_unqualified_c5_bundle_is_rejected(self):
        path = c5_numeric_path()
        with np.load(path, allow_pickle=False) as stored:
            bundle = {key: stored[key].copy() for key in stored.files}
        bundle.update(
            service_names=[f"n{i}" for i in range(bundle["values"].shape[1])],
            audit={
                "profile": "TD13-C5-EVENT-TIME",
                "qualification": "UNQUALIFIED_PENDING_EXTERNAL_TD13_REPLAY_RECEIPT",
                "graph": {},
            },
        )
        with self.assertRaises(ObservationError):
            admit_c5_bundle(
                bundle,
                handle="opaque",
                source_hashes={"numeric": sha(path)},
                fit_bins=24,
                cal_bins=12,
            )


if __name__ == "__main__":
    unittest.main()
