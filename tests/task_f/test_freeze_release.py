from __future__ import annotations

import copy
import hashlib
import json
import unittest

from rca.contracts import EXPECTED_TD_SHA256, FrozenConfigError, FrozenReleaseConfig
from rca.release import verify_frozen_release

from _helpers import MANIFEST, P, W, load_json, sha


class FreezeReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = load_json(MANIFEST)
        cls.verified = verify_frozen_release(
            MANIFEST, workspace_root=W, project_root=P
        )

    def test_01_exact_td_hash(self):
        td = P / "docs" / "research-rca" / "task-d-method-and-experiment-specification.md"
        self.assertEqual(sha(td), EXPECTED_TD_SHA256)
        self.assertEqual(self.raw["td"]["sha256"], EXPECTED_TD_SHA256)

    def test_02_machine_extraction_passes_all_hashes(self):
        self.assertEqual(self.verified["status"], "PASS")
        self.assertGreaterEqual(self.verified["checked_reference_count"], 20)
        self.assertEqual(set(self.verified["checks"].values()), {"PASS"})

    def test_03_local_selection_is_sealed_canary(self):
        extracted = self.verified["extracted"]["c1"]
        self.assertEqual(extracted["selected_local_index"], 6)
        self.assertEqual(
            extracted["local"],
            {"floor": 0.01, "pool": "q90", "fusion": "availablemean"},
        )

    def test_04_graph_selections_are_sealed_canaries(self):
        extracted = self.verified["extracted"]["c1"]
        self.assertEqual(extracted["selected_ppr_index"], 4)
        self.assertEqual(
            extracted["primary_ppr"],
            {"operator": "ppr", "direction": "undirected", "damping": 0.5},
        )
        self.assertEqual(extracted["selected_diffusion_index"], 6)

    def test_05_c5_is_lambda10_eight_valid_q095(self):
        extracted = self.verified["extracted"]["c5"]
        self.assertEqual(extracted["selected_lambda"], 10.0)
        self.assertEqual(len(extracted["detectors"]), 8)
        self.assertTrue(all(row["status"] == "VALID" for row in extracted["detectors"]))
        self.assertTrue(all(row["q"] == 0.95 for row in extracted["detectors"]))

    def test_06_registry_is_not_misread_as_selection(self):
        registered = load_json(W / "configs" / "task-e-td13-development.json")
        self.assertTrue(registered["selection"].startswith("NOT RUN"))
        self.assertTrue(registered["final_evaluation"].startswith("FORBIDDEN"))

    def test_07_no_materialized_final_ids_or_payloads(self):
        text = MANIFEST.read_text(encoding="utf-8").lower()
        for forbidden in (
            '"final_ids"',
            '"final_case_ids"',
            '"final_labels"',
            '"final_telemetry"',
            '"final_predictions"',
        ):
            self.assertNotIn(forbidden, text)
        self.assertFalse(self.raw["split"]["final_metadata_or_case_ids_in_this_manifest"])

    def test_08_sensitivity_is_not_primary(self):
        selections = json.dumps(self.raw["selections"], sort_keys=True).lower()
        self.assertNotIn("e27-036", selections)
        self.assertNotIn("e27-037", selections)
        self.assertTrue(
            all(row["role"] == "diagnostic limitation only" for row in self.raw["provenance"]["sensitivities"])
        )

    def test_09_comparator_roster_is_exact_and_localmax_distinct(self):
        roster = [row["id"] for row in self.raw["comparators"]]
        self.assertEqual(
            set(roster),
            {"Local-MAX-MT", "BARO-RANK-adapted-TD12", "RCD-RCAEval-adapted-TD12"},
        )
        self.assertIn("distinct from C1 L", self.raw["comparators"][0]["role"])

    def test_10_release_manifest_pins_the_complete_implementation(self):
        implementation = self.raw["implementation"]
        rows = implementation["source_files"]
        self.assertEqual(implementation["release_id"], "TASK-F-TD13-v2")
        self.assertEqual(self.raw["schema_version"], "TD13-F-FROZEN-RELEASE-v2")
        self.assertEqual(
            self.raw["predecessor_release"],
            {
                "commit": "e70f40f5549574ac4518436cc476087f8cf2d9f6",
                "manifest": {
                    "path": "configs/task-f-td13-frozen-release.json",
                    "sha256": "18484bc4bb0c1d19e8f6936f12d8365a8ad69e16fffa2bf6ce5968189f0561e5",
                },
            },
        )
        self.assertEqual(sha(W / "configs/task-f-td13-frozen-release.json"), self.raw["predecessor_release"]["manifest"]["sha256"])
        self.assertEqual(
            {row["path"] for row in rows},
            {path.relative_to(W).as_posix() for path in (W / "src/rca").glob("*.py")},
        )
        for row in rows:
            path = W / row["path"]
            self.assertEqual(sha(path), row["sha256"])
            self.assertEqual(path.stat().st_size, row["bytes"])
        material = json.dumps(
            rows,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        self.assertEqual(
            hashlib.sha256(material).hexdigest(),
            implementation["source_manifest_sha256"],
        )

    def test_10a_v2_changes_no_scientific_selection_or_split(self):
        previous = load_json(W / "configs/task-f-td13-frozen-release.json")
        for field in ("td", "dataset", "split", "exposure_ledger", "selections", "r_control", "evaluator", "packet", "selection_policy", "final60_policy", "prohibited_runtime_rules"):
            with self.subTest(field=field):
                self.assertEqual(self.raw[field], previous[field])
        self.assertEqual(self.raw["comparators"][0:2], previous["comparators"][0:2])
        rcd_new = dict(self.raw["comparators"][2])
        rcd_new.pop("qualification_contract")
        self.assertEqual(rcd_new, previous["comparators"][2])

    def test_11_manifest_rejects_wrong_td(self):
        changed = copy.deepcopy(self.raw)
        changed["td"]["sha256"] = "0" * 64
        with self.assertRaises(FrozenConfigError):
            FrozenReleaseConfig.from_mapping(changed)

    def test_12_manifest_rejects_sensitivity_local_config(self):
        changed = copy.deepcopy(self.raw)
        changed["selections"]["c1"]["local"]["cap"] = 20
        with self.assertRaises(FrozenConfigError):
            FrozenReleaseConfig.from_mapping(changed)

    def test_13_manifest_rejects_materialized_final_field(self):
        changed = copy.deepcopy(self.raw)
        changed["split"]["final_ids"] = ["forbidden"]
        with self.assertRaises(FrozenConfigError):
            FrozenReleaseConfig.from_mapping(changed)


if __name__ == "__main__":
    unittest.main()
