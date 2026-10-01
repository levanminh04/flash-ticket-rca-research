"""Telemetry-only synthetic/development probes; no acquisition or final rows."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from scripts.task_g import source_admission as source


class FixtureApi:
    def __init__(self, revision=source.REVISION, bad_path=False):
        self.revision, self.bad_path = revision, bad_path
        self.paths = []

    def dataset_info(self, repo, revision):
        if repo != source.REPO_ID or revision != source.REVISION:
            raise AssertionError("Wrong pinned metadata request")
        return {"sha": self.revision}

    def get_paths_info(self, repo, paths, repo_type, revision):
        self.paths = paths
        if repo != source.REPO_ID or repo_type != "dataset" or revision != source.REVISION:
            raise AssertionError("Wrong telemetry descriptor request")
        rows = [{"path": path, "size": 1, "lfs": {"sha256": "0" * 64}} for path in paths]
        if self.bad_path:
            rows[0]["path"] = "synthetic/root_cause.txt"
        return rows


def synthetic_files(root, *, log_clock_bad=False, trace_null_clock=False, suffix_conflict=False):
    case = root / "synthetic-one"
    case.mkdir()
    origin = 1_700_000_000
    seconds = np.arange(origin, origin + 1080, dtype=np.int64)
    metrics = pd.DataFrame({"time": seconds, "synthetic-a_cpu": 5 + (seconds % 17).astype(float),
                            "synthetic-b_cpu": 4 + (seconds % 19).astype(float),
                            "unmatched_numeric": np.zeros(len(seconds))})
    traces = []
    for second in seconds[::5]:
        for index, service in enumerate(("synthetic-a", "synthetic-b")):
            traces.append(("unused-time", f"synthetic-trace-{second}", f"synthetic-span-{second}-{index}", service,
                           "synthetic-method", "synthetic-operation", "" if index == 0 else f"synthetic-span-{second}-0",
                           int(second) * 1000, int(second), 1, 200))
    frame = pd.DataFrame(traces, columns=source.SCHEMA_PROJECTIONS["traces"])
    if trace_null_clock:
        frame["startTimeMillis"] = pd.array(frame.startTimeMillis, dtype="Int64")
        frame.loc[len(frame) - 1, "startTimeMillis"] = pd.NA
    if suffix_conflict:
        conflict = frame.iloc[0].copy()
        conflict["startTimeMillis"] = (origin + 700) * 1000
        frame = pd.concat([frame, pd.DataFrame([conflict])], ignore_index=True)
    logs = pd.DataFrame({"timestamp": seconds[::5], "container_name": "synthetic-a", "message": "synthetic-only"})
    if log_clock_bad:
        logs["timestamp"] = pd.array(logs.timestamp, dtype="Int64")
        logs.loc[len(logs) - 1, "timestamp"] = pd.NA
    for modality, value in (("metrics", metrics), ("traces", frame), ("logs", logs)):
        pq.write_table(pa.Table.from_pandas(value, preserve_index=False), case / f"{modality}.parquet")
    return case


def descriptors(root, case):
    return tuple({"path": f"{case.name}/{modality}.parquet", "bytes": (case / f"{modality}.parquet").stat().st_size,
                  "sha256": source._sha256(case / f"{modality}.parquet")}
                 for modality in ("metrics", "traces", "logs"))


class SourceAdmissionTests(unittest.TestCase):
    def test_unissued_handles_and_public_dict_cannot_mint_admission(self):
        for forged in (source.SourceAdmission(), {"scope": "ENTRY_RAW_ADMISSION", "status": "PASS_TELEMETRY_ADMISSION"}, None):
            with self.assertRaises(source.SourceAdmissionError):
                source.require_issued_admission(forged)
        with self.assertRaises(source.SourceAdmissionError):
            source.acquire_and_audit(source.SourcePlan(), source.WORKSPACE / source.CONTRACT_RELATIVE)
        for private_issuer in ("_issue_plan", "_issued_plan", "_build_plan", "_acquire_and_audit", "_bind_issued_boundaries"):
            self.assertFalse(hasattr(source, private_issuer))
        class AliasedPlan(source.SourcePlan):
            def __hash__(self):
                return 123
            def __eq__(self, other):
                return True
        class AliasedAdmission(source.SourceAdmission):
            def __hash__(self):
                return 123
            def __eq__(self, other):
                return True
        with self.assertRaises(source.SourceAdmissionError):
            source.acquire_and_audit(AliasedPlan(), source.WORKSPACE / source.CONTRACT_RELATIVE)
        with self.assertRaises(source.SourceAdmissionError):
            source.require_issued_admission(AliasedAdmission())

    def test_injected_api_plan_always_fixture_and_summary_copy_cannot_promote(self):
        api = FixtureApi()
        # Reads ONLY the pinned five metadata columns; API is synthetic.
        plan = source.plan_source(source.WORKSPACE, source.PROJECT, api=api)
        summary = plan.summary
        self.assertEqual(summary["scope"], "SYNTHETIC_INJECTED_API_ONLY")
        self.assertEqual(summary["opaque_roster_sha256"], source.ROSTER_SHA256)
        self.assertEqual(summary["metadata_projection"], list(source.PROJECTION))
        self.assertEqual(len(api.paths), 180)
        self.assertTrue(all(path.endswith(("metrics.parquet", "traces.parquet", "logs.parquet")) for path in api.paths))
        summary["scope"] = "OFFICIAL_TELEMETRY_PLAN"
        summary["declared_bytes"] = source.DECLARED_BYTES
        with patch.object(source, "_download_object") as download, patch.object(source, "_read_verified_raw") as reader:
            with self.assertRaises(source.SourceAdmissionError):
                source.acquire_and_audit(plan, source.WORKSPACE / source.CONTRACT_RELATIVE)
            download.assert_not_called()
            reader.assert_not_called()
        self.assertEqual(plan.summary["scope"], "SYNTHETIC_INJECTED_API_ONLY")
        with self.assertRaises(source.SourceAdmissionError):
            source.require_issued_admission(plan)

    def test_wrong_revision_and_nontelemetry_descriptor_fail(self):
        for api in (FixtureApi(revision="0" * 40), FixtureApi(bad_path=True)):
            with self.assertRaises(source.SourceAdmissionError):
                source.plan_source(source.WORKSPACE, source.PROJECT, api=api)

    def test_default_endpoint_is_explicit_and_wrong_default_origin_fails(self):
        api = FixtureApi()
        api.endpoint = "https://synthetic-invalid.example"
        with patch("huggingface_hub.HfApi", return_value=api) as constructor:
            with self.assertRaises(source.SourceAdmissionError):
                source.plan_source(source.WORKSPACE, source.PROJECT)
            constructor.assert_called_once_with(endpoint=source.OFFICIAL_ENDPOINT, token=False)
            self.assertEqual(api.paths, [])

    def test_metadata_projection_never_requests_oracle_columns(self):
        actual_reader = pq.read_table
        projections = []
        def projected(path, *args, **kwargs):
            projections.append(kwargs.get("columns"))
            return actual_reader(path, *args, **kwargs)
        with patch("pyarrow.parquet.read_table", side_effect=projected):
            source.plan_source(source.WORKSPACE, source.PROJECT, api=FixtureApi())
        self.assertEqual(projections, [list(source.PROJECTION)])

    def test_registered_gate_rejects_wrong_path_or_closed_before_raw(self):
        state = {"workspace": source.WORKSPACE, "project": source.PROJECT}
        with self.assertRaises(source.SourceAdmissionError):
            source._registered_gate(state, source.WORKSPACE / "alternate-contract.json")
        registered = json.loads((source.WORKSPACE / source.CONTRACT_RELATIVE).read_text(encoding="utf-8"))
        registered["raw_admission_gate"] = "CLOSED_PENDING_INDEPENDENT_REVIEW"
        with patch.object(Path, "read_text", return_value=json.dumps(registered)), patch.object(source, "_download_object") as download:
            with self.assertRaises(source.SourceAdmissionError):
                source._registered_gate(state, source.WORKSPACE / source.CONTRACT_RELATIVE)
            download.assert_not_called()

    def test_reviewed_snapshot_drift_and_oracle_permission_fail_closed(self):
        # Entire gate document is a temporary synthetic fixture; no official
        # handle is issued and no raw path/network is invoked.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = json.loads((source.WORKSPACE / source.CONTRACT_RELATIVE).read_text(encoding="utf-8"))
            snapshot = {}
            for relative in source.SNAPSHOT_PATHS:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# synthetic snapshot\n", encoding="utf-8")
                snapshot[relative] = source._sha256(path)
            review = "Synthetic independent gate fixture\n"
            review_path = root / source.REVIEW_RELATIVE
            review_path.parent.mkdir(parents=True, exist_ok=True)
            review_path.write_text(review, encoding="utf-8")
            original["source"].update(schema_projections=source.SCHEMA_PROJECTIONS,
                                       raw_allowlist_digest=source.DESCRIPTOR_SHA256)
            original["raw_admission_gate"] = "OPEN_FOR_TELEMETRY_ONLY_ADMISSION"
            original["source_test_snapshot_before_qualification"] = snapshot
            original["independent_pre_admission_review"] = {"status": "PASS_PRE_ADMISSION_REVIEW",
                "source_test_snapshot": snapshot, "raw_utf8": review,
                "sha256": hashlib.sha256(review.encode()).hexdigest()}
            contract_path = root / source.CONTRACT_RELATIVE
            state = {"workspace": root, "project": source.PROJECT}
            actual_hash = source._sha256
            def fixture_hash(path):
                return source.METADATA_SHA256 if path == root / source.METADATA_RELATIVE else actual_hash(path)
            with patch.object(source, "_sha256", side_effect=fixture_hash), patch.object(source, "_read_frozen_contract", return_value=({}, {})):
                contract_path.write_text(json.dumps(original), encoding="utf-8")
                binding = source._registered_gate(state, contract_path)
                self.assertEqual(binding["pre_admission_review_sha256"], original["independent_pre_admission_review"]["sha256"])
                for mutate in (lambda c: c["permissions"].update(final_labels=True),
                               lambda c: c["source"].update(schema_projections={}),
                               lambda c: c["independent_pre_admission_review"].update(sha256="0" * 64)):
                    changed = json.loads(json.dumps(original))
                    mutate(changed)
                    contract_path.write_text(json.dumps(changed), encoding="utf-8")
                    with self.assertRaises(source.SourceAdmissionError):
                        source._registered_gate(state, contract_path)
                contract_path.write_text(json.dumps(original), encoding="utf-8")
                (root / "scripts/task_g/source_admission.py").write_text("# source drift\n", encoding="utf-8")
                with self.assertRaises(source.SourceAdmissionError):
                    source._registered_gate(state, contract_path)

    def test_download_reuses_only_verified_existing_file_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = synthetic_files(root)
            descriptor = descriptors(root, case)[0]
            with patch("urllib.request.build_opener") as session:
                self.assertEqual(source._download_object(root, descriptor), "REUSED_VERIFIED")
                session.assert_not_called()
            path = case / "metrics.parquet"
            before = path.read_bytes()
            descriptor["sha256"] = "0" * 64
            with patch("urllib.request.build_opener") as session:
                with self.assertRaises(source.SourceAdmissionError):
                    source._download_object(root, descriptor)
                session.assert_not_called()
            self.assertEqual(path.read_bytes(), before)

    def test_hash_mismatch_rejected_before_parquet_schema_or_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = synthetic_files(root)
            expected = list(descriptors(root, case))
            expected[0]["sha256"] = "0" * 64
            with patch("pyarrow.parquet.ParquetFile") as reader:
                with self.assertRaises(source.SourceAdmissionError):
                    source._read_verified_raw(root, tuple(expected))
                reader.assert_not_called()

    def test_nontelemetry_and_escape_paths_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in ("synthetic-one/root_cause.txt", "../metrics.parquet", "synthetic-one/nested/metrics.parquet", "synthetic-one/answer.parquet"):
                with self.assertRaises((source.SourceAdmissionError, ValueError)):
                    source._exact_local_path(root, path)

    def test_explicit_oracle_schema_rejected_before_value_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = root / "synthetic-oracle"
            case.mkdir()
            path = case / "metrics.parquet"
            pq.write_table(pa.table({"time": [1_700_000_000], "root": [987654]}), path)
            expected = ({"path": f"{case.name}/metrics.parquet", "bytes": path.stat().st_size, "sha256": source._sha256(path)},)
            actual_constructor = pq.ParquetFile
            reads = []
            class SchemaOnly:
                def __init__(self, file):
                    self.original = actual_constructor(file)
                    self.schema_arrow = self.original.schema_arrow
                def read(self, *args, **kwargs):
                    reads.append(True)
                    raise AssertionError("Oracle value read attempted")
            with patch("pyarrow.parquet.ParquetFile", SchemaOnly):
                raw = source._read_verified_raw(root, expected)
            self.assertEqual(reads, [])
            self.assertIsNone(raw["metrics"])
            self.assertEqual(raw["audit"]["modalities"]["metrics"]["status"], "CORRUPT_OR_UNSUPPORTED")

    def test_real_tiny_synthetic_parquets_frozen_conversion_and_prefix_equal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            synthetic_files(root)
            receipt = source.audit_synthetic_fixture(root)
            self.assertFalse(receipt["official_admission"])
            self.assertEqual(receipt["scope"], "SYNTHETIC_DEVELOPMENT_FIXTURE_ONLY")
            row = receipt["case_audits"][0]
            self.assertEqual(row["case_status"], "ADMISSION_COMPATIBLE")
            self.assertEqual(row["c1"]["profile"], "LABEL_FREE_PROTOCOL_WINDOW__ORIGIN_PLUS_DECLARED_RE2_OFFSET720")
            self.assertEqual(row["rcd_input"]["shape"], [600, 2])
            self.assertEqual(row["rcd_input"]["finite_elements"], 1200)
            self.assertTrue(row["rcd_input"]["cannot_veto_c1_scientific_verdict"])
            self.assertEqual([check["cutoff_seconds"] for check in row["c5"]["prefix_replay_checks"]], [180, 360])
            encoded = json.dumps(receipt)
            for forbidden in ("synthetic-one", "synthetic-a", "synthetic-trace", "synthetic-only", "1700000000", "parquet"):
                self.assertNotIn(forbidden, encoded)
            with self.assertRaises(source.SourceAdmissionError):
                source.require_issued_admission(receipt)

    def test_optional_log_bad_clock_unavailable_without_veto_valid_mt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            synthetic_files(root, log_clock_bad=True)
            row = source.audit_synthetic_fixture(root)["case_audits"][0]
            self.assertEqual(row["modalities"]["logs"]["status"], "UNAVAILABLE_LOG_CLOCK_OR_SCHEMA")
            self.assertEqual(row["case_status"], "ADMISSION_COMPATIBLE")
            self.assertTrue(row["no_labels_or_predictions"])

    def test_required_trace_unplaceable_clock_retains_conversion_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            synthetic_files(root, trace_null_clock=True)
            row = source.audit_synthetic_fixture(root)["case_audits"][0]
            self.assertEqual(row["modalities"]["traces"]["event_clock"], "UNQUALIFIABLE_EVENT_CLOCK")
            self.assertEqual(row["c5"]["status"], "INPUT_UNAVAILABLE_OR_CONVERSION_FAILURE")
            self.assertEqual(row["case_status"], "ADMISSION_LIMITED__FAILURE_OR_OPEN_RETAINED")

    def test_later_trace_conflict_does_not_retract_prefix_or_frozen_graph(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            synthetic_files(root, suffix_conflict=True)
            row = source.audit_synthetic_fixture(root)["case_audits"][0]
            self.assertEqual(row["c5"]["status"], "CONVERTED_ONLY")
            self.assertGreater(row["c5"]["conversion_quality"]["trace_masked_service_bins"], 0)
            self.assertTrue(all(check["exact_numeric_equal"] for check in row["c5"]["prefix_replay_checks"]))

    def test_external_baseline_input_exception_does_not_veto_c1(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            synthetic_files(root)
            with patch("scripts.task_e.input_adapters.rcd_bundle", side_effect=ValueError("synthetic-failure")):
                row = source.audit_synthetic_fixture(root)["case_audits"][0]
            self.assertEqual(row["c1"]["status"], "CONVERTED_ONLY")
            self.assertEqual(row["case_status"], "ADMISSION_COMPATIBLE")
            self.assertEqual(row["rcd_input"]["status"], "BASELINE_INPUT_CONVERSION_FAILURE_ONLY")
            self.assertNotIn("synthetic-failure", json.dumps(row))

    def test_fixture_path_cannot_admit_final_named_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "re2tt-never-read").mkdir()
            with self.assertRaises(source.SourceAdmissionError):
                source.audit_synthetic_fixture(root)


if __name__ == "__main__":
    unittest.main()
