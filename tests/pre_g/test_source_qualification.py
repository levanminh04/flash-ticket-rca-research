"""Synthetic PRE-G source tests; no final telemetry or outcome is opened."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from scripts.pre_g import source_qualification as source


def synthetic_metadata() -> tuple[list[dict[str, object]], dict[str, object]]:
    rows: list[dict[str, object]] = []
    development: list[str] = []
    for cell_index in range(30):
        for repetition in (1, 2, 3):
            case = f"opaque-cell-{cell_index:02d}_{repetition}"
            rows.append(
                {
                    "case": case,
                    "dataset": "RE2-TT",
                    "repetition": repetition,
                    "has_logs": not (cell_index == 0 and repetition == 1),
                    "has_traces": True,
                }
            )
            if cell_index < 10:
                development.append(case)
    rows.append({"case": "unrelated_1", "dataset": "RE3-TT"})
    return rows, {"development_ids": development}


class FakeApi:
    def __init__(self, *, revision: str = source.REVISION):
        self.revision = revision
        self.requested: list[str] = []
        self.objects: list[object] | None = None

    def dataset_info(self, repo_id: str, *, revision: str):
        if repo_id != source.REPO_ID or revision != source.REVISION:
            raise AssertionError("Unpinned dataset request")
        return SimpleNamespace(sha=self.revision)

    def get_paths_info(self, repo_id: str, *, paths: list[str], repo_type: str, revision: str):
        if repo_id != source.REPO_ID or repo_type != "dataset" or revision != source.REVISION:
            raise AssertionError("Unpinned object request")
        self.requested = list(paths)
        if self.objects is not None:
            return self.objects
        return [
            SimpleNamespace(
                path=path,
                size=100 + index,
                lfs=SimpleNamespace(sha256=hashlib.sha256(path.encode()).hexdigest()),
            )
            for index, path in enumerate(paths)
        ]


class SourceMetadataTests(unittest.TestCase):
    def test_exact_split_is_opaque_and_three_repeat_grouped(self):
        rows, registry = synthetic_metadata()
        plan = source._plan_final_metadata(rows, registry)
        self.assertEqual(len(plan["final_ids"]), 60)
        self.assertEqual(len(plan["remote_paths"]), 180)
        self.assertTrue(all("answer" not in path for path in plan["remote_paths"]))
        self.assertTrue(all("opaque-cell-00" not in path for path in plan["remote_paths"]))

    def test_split_crossing_or_missing_log_is_rejected(self):
        rows, registry = synthetic_metadata()
        registry["development_ids"][0] = "opaque-cell-10_1"
        with self.assertRaises(source.SourceQualificationError):
            source._plan_final_metadata(rows, registry)
        rows, registry = synthetic_metadata()
        next(row for row in rows if row.get("case") == "opaque-cell-10_1")["has_logs"] = False
        with self.assertRaises(source.SourceQualificationError):
            source._plan_final_metadata(rows, registry)

    def test_wrong_revision_and_inventory_scope_are_rejected(self):
        rows, registry = synthetic_metadata()
        plan = source._plan_final_metadata(rows, registry)
        with self.assertRaises(source.SourceQualificationError):
            source._official_inventory(FakeApi(revision="0" * 40), plan["remote_paths"])
        api = FakeApi()
        api.objects = [SimpleNamespace(path="../answer.txt", size=4, lfs={"sha256": "a" * 64})]
        with self.assertRaises(source.SourceQualificationError):
            source._official_inventory(api, plan["remote_paths"])

    def test_missing_duplicate_bad_sha_and_bad_size_are_rejected(self):
        rows, registry = synthetic_metadata()
        plan = source._plan_final_metadata(rows, registry)
        good = FakeApi().get_paths_info(
            source.REPO_ID, paths=list(plan["remote_paths"]), repo_type="dataset", revision=source.REVISION
        )
        for bad in (
            good[:-1],
            good + good[:1],
            [SimpleNamespace(path=good[0].path, size=good[0].size, lfs={"sha256": "bad"})] + good[1:],
            [SimpleNamespace(path=good[0].path, size=0, lfs=good[0].lfs)] + good[1:],
        ):
            api = FakeApi()
            api.objects = bad
            with self.subTest(length=len(bad)), self.assertRaises(source.SourceQualificationError):
                source._official_inventory(api, plan["remote_paths"])

    def test_public_receipt_discloses_no_case_id_path_or_outcome(self):
        rows, registry = synthetic_metadata()
        manifest = {
            "implementation": {
                "release_id": "TASK-F-TD13-v2",
                "qualified_development_loader": {"adapter_id": "synthetic-qualified-converter"},
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            metadata = root / source.METADATA_RELATIVE
            metadata.parent.mkdir(parents=True)
            metadata.write_bytes(b"synthetic metadata placeholder")
            fake_sha = hashlib.sha256(metadata.read_bytes()).hexdigest()
            api = FakeApi()
            with mock.patch.object(source, "METADATA_SHA256", fake_sha), mock.patch.object(
                source, "_read_frozen_contract", return_value=(manifest, registry)
            ), mock.patch("pyarrow.parquet.read_table") as read_table:
                read_table.return_value.to_pylist.return_value = rows
                receipt = source.qualify_final_source_metadata(
                    workspace_root=root, project_root=root, api=api
                )
                read_table.assert_called_once_with(
                    metadata,
                    columns=["case", "dataset", "repetition", "has_logs", "has_traces"],
                )
            serialized = json.dumps(receipt)
            self.assertEqual(receipt["status"], "SYNTHETIC_TEST_ONLY")
            self.assertEqual(receipt["api_provenance"], "INJECTED_TEST_API")
            self.assertEqual(receipt["official_inventory"]["objects"], 180)
            self.assertEqual(receipt["frozen_conversion"]["adapter_evidence_scope"], "DEVELOPMENT_ONLY")
            for forbidden in ("opaque-cell-", ".parquet", "answer", "inject_time", "root_cause_service"):
                self.assertNotIn(forbidden, serialized)
            self.assertFalse(receipt["this_invocation"]["raw_parquet_opened"])
            self.assertFalse(receipt["this_invocation"]["prediction_code_invoked"])

    def test_pinned_metadata_mismatch_stops_before_api(self):
        rows, registry = synthetic_metadata()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            metadata = root / source.METADATA_RELATIVE
            metadata.parent.mkdir(parents=True)
            metadata.write_bytes(b"wrong bytes")
            api = mock.Mock()
            with mock.patch.object(source, "_read_frozen_contract", return_value=({}, registry)):
                with self.assertRaises(source.SourceQualificationError):
                    source.qualify_final_source_metadata(
                        workspace_root=root, project_root=root, api=api
                    )
            api.dataset_info.assert_not_called()

    def test_default_api_pins_origin_despite_endpoint_override(self):
        from huggingface_hub import HfApi, constants

        rows, registry = synthetic_metadata()
        manifest = {"implementation": {
            "release_id": "TASK-F-TD13-v2",
            "qualified_development_loader": {"adapter_id": "synthetic-converter"},
        }}
        fixture_api = FakeApi()

        def dataset_info(client, *args, **kwargs):
            self.assertEqual(client.endpoint, "https://huggingface.co")
            self.assertIs(client.token, False)
            return fixture_api.dataset_info(*args, **kwargs)

        def paths_info(client, *args, **kwargs):
            self.assertEqual(client.endpoint, "https://huggingface.co")
            return fixture_api.get_paths_info(*args, **kwargs)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            metadata = root / source.METADATA_RELATIVE
            metadata.parent.mkdir(parents=True)
            metadata.write_bytes(b"synthetic metadata placeholder")
            with mock.patch.object(source, "METADATA_SHA256", hashlib.sha256(metadata.read_bytes()).hexdigest()), \
                 mock.patch.object(source, "_read_frozen_contract", return_value=(manifest, registry)), \
                 mock.patch("pyarrow.parquet.read_table") as read_table, \
                 mock.patch.object(constants, "ENDPOINT", "http://127.0.0.1:9"), \
                 mock.patch.object(HfApi, "dataset_info", autospec=True, side_effect=dataset_info), \
                 mock.patch.object(HfApi, "get_paths_info", autospec=True, side_effect=paths_info):
                read_table.return_value.to_pylist.return_value = rows
                receipt = source.qualify_final_source_metadata(
                    workspace_root=root, project_root=root
                )
            self.assertEqual(receipt["api_endpoint"], "https://huggingface.co")
            self.assertEqual(receipt["status"], "PASS_METADATA_ONLY")

    def test_unexpected_default_client_origin_stops_before_inventory(self):
        rows, registry = synthetic_metadata()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            metadata = root / source.METADATA_RELATIVE
            metadata.parent.mkdir(parents=True)
            metadata.write_bytes(b"synthetic metadata placeholder")
            with mock.patch.object(source, "METADATA_SHA256", hashlib.sha256(metadata.read_bytes()).hexdigest()), \
                 mock.patch.object(source, "_read_frozen_contract", return_value=({}, registry)), \
                 mock.patch("pyarrow.parquet.read_table") as read_table, \
                 mock.patch("huggingface_hub.HfApi") as factory:
                read_table.return_value.to_pylist.return_value = rows
                factory.return_value.endpoint = "http://127.0.0.1:9"
                with self.assertRaisesRegex(source.SourceQualificationError, "origin is not pinned"):
                    source.qualify_final_source_metadata(workspace_root=root, project_root=root)
                factory.assert_called_once_with(endpoint="https://huggingface.co", token=False)
                factory.return_value.dataset_info.assert_not_called()

    def test_real_frozen_v2_adapter_sources_and_receipts_remain_pinned(self):
        workspace = Path(__file__).resolve().parents[2]
        project = Path(r"D:/Project/flash-ticket-platform")
        manifest, registry = source._read_frozen_contract(workspace, project)
        self.assertEqual(manifest["implementation"]["release_id"], "TASK-F-TD13-v2")
        self.assertEqual(len(registry["development_ids"]), 30)
        self.assertEqual(
            manifest["implementation"]["qualified_development_loader"]["scope"],
            "DEVELOPMENT_QUALIFIED__PRE_G_REQUALIFICATION_REQUIRED",
        )


class RawSourceAuditTests(unittest.TestCase):
    def _fixture(self, root: Path):
        case = "synthetic-case_1"
        folder = root / case
        folder.mkdir()
        expected: dict[str, dict[str, object]] = {}
        modalities: dict[str, dict[str, object]] = {}
        for modality in ("metrics", "traces"):
            path = folder / f"{modality}.parquet"
            payload = f"synthetic {modality}".encode()
            path.write_bytes(payload)
            digest = hashlib.sha256(payload).hexdigest()
            expected[f"{case}/{modality}.parquet"] = {"bytes": len(payload), "sha256": digest}
            modalities[modality] = {
                "status": "LOADED",
                "source_identity_verified": True,
                "path": str(path),
                "bytes": len(payload),
                "sha256": digest,
            }
        modalities["logs"] = {"status": "MISSING"}
        return case, expected, {"audit": {"modalities": modalities}}

    def test_missing_optional_log_and_exact_local_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case, expected, raw = self._fixture(root)
            result = source.verify_local_telemetry_audit(
                source_root=root, case_id=case, expected_objects=expected, raw_telemetry=raw
            )
            self.assertEqual(result["logs"], "MISSING")
            self.assertEqual(result["metrics"], expected[f"{case}/metrics.parquet"]["sha256"])

    def test_spoofed_audit_cannot_substitute_for_rehash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case, expected, raw = self._fixture(root)
            (root / case / "metrics.parquet").write_bytes(b"changed")
            with self.assertRaises(source.SourceQualificationError):
                source.verify_local_telemetry_audit(
                    source_root=root, case_id=case, expected_objects=expected, raw_telemetry=raw
                )

    def test_path_traversal_and_answer_object_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case, expected, raw = self._fixture(root)
            with self.assertRaises(source.SourceQualificationError):
                source.verify_local_telemetry_audit(
                    source_root=root, case_id="../escape", expected_objects=expected, raw_telemetry=raw
                )
            expected[f"{case}/answer.txt"] = {"bytes": 1, "sha256": "a" * 64}
            with self.assertRaises(source.SourceQualificationError):
                source.verify_local_telemetry_audit(
                    source_root=root, case_id=case, expected_objects=expected, raw_telemetry=raw
                )

    def test_final_style_case_id_is_rejected_before_file_access(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(source.SourceQualificationError):
                source.verify_local_telemetry_audit(
                    source_root=directory,
                    case_id="re2tt_opaque_cpu_1",
                    expected_objects={},
                    raw_telemetry={},
                )


if __name__ == "__main__":
    unittest.main()
