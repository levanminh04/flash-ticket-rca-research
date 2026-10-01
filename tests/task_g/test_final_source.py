"""G32 source fixtures: conversion and authority boundaries, never final models.

Registration/byte overrides in this suite are isolated synthetic-only tests.
They do not issue trusted final qualification or read closed metadata fields.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
import unittest
from collections.abc import Mapping
from unittest.mock import patch

import numpy as np
import pandas as pd
import pyarrow as pa

WORKSPACE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKSPACE))
sys.path.insert(0, str(WORKSPACE / "src"))

from scripts.task_g import final_source as source
from scripts.task_e.loader import TRACE_FIELDS


def context():
    return ({"contract_sha256": "a" * 64}, {
        "permissions": {"tau_only_input_audit": True, "telemetry_final60_conversion_only": True,
                        "telemetry_final60_new_acquisition": False, "development30_timing_only": True},
        "tau_source": {"path": source.METADATA_REL, "sha256": source.METADATA_SHA,
                       "roster_projection": list(source.ROSTER_PROJECTION),
                       "projection": list(source.TAU_PROJECTION), "timestamp_unit": "UNIX_SECONDS_METADATA_INJECT_TIME"}})


def raw_fixture(*, shift=0, tau_offset=630, missing_logs=False):
    origin = 1_700_000_000 + shift
    times = np.arange(origin, origin + 1200, dtype=np.int64)
    values = 10 + np.sin(np.arange(1200) / 7)
    values[tau_offset:] += 20
    metrics = pd.DataFrame({"time": times, "literal-a_cpu": values,
                            "literal-a_latency-90": values + 2,
                            "literal-b_cpu": values + 1,
                            "literal-cpu": np.zeros(1200), "unknown_cpu": np.arange(1200)})
    records = []
    for second in times[::5]:
        for n, name in enumerate(("literal-a", "literal-b")):
            records.append(("unused", f"t-{second}", f"s-{second}-{n}", name, "method", "operation",
                            "" if n == 0 else f"s-{second}-0", int(second) * 1000, int(second), 1, 200))
    traces = pd.DataFrame(records, columns=TRACE_FIELDS)
    logs = None if missing_logs else pd.DataFrame({"timestamp": times[::5], "container_name": "literal-a", "message": "synthetic-only"})
    return {"metrics": metrics, "traces": traces, "logs": logs}, origin + tau_offset


def convert(raw, tau):
    return source._convert_raw(raw, tau, "0123456789abcdef", {"synthetic": "b" * 64}, source.SYNTHETIC_SCOPE)


def plain(value):
    if isinstance(value, Mapping):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(item) for item in value]
    return value


class FinalSourceTests(unittest.TestCase):
    def setUp(self):
        self.override = patch.object(source, "_context", return_value=context())
        self.override.start()
        self.addCleanup(self.override.stop)

    def test_three_fixtures_have_different_numeric_inputs_and_dimensions(self):
        handle = source.make_synthetic_source()
        self.assertEqual(source.case_count(handle), 3)
        rows = [source.get_case(handle, n) for n in range(3)]
        self.assertEqual([len(row["c1"].node_ids) for row in rows], [6, 5, 4])
        self.assertEqual(len({row["numeric_input_sha256"] for row in rows}), 3)
        self.assertTrue(all(row["source_metadata"]["conversion_only"] for row in rows))
        self.assertFalse(handle.summary["final_prediction_qualified"])
        self.assertEqual(handle.summary["source_kind"], "THREE_DISTINCT_ARTIFICIAL_ARCHIVES")

    def test_arbitrary_dict_or_subclass_cannot_issue_source(self):
        class Alias(source.FinalSource):
            pass
        for fake in (None, {}, source.FinalSource(), Alias()):
            for operation in (source.source_summary, source.case_count):
                with self.assertRaises(source.FinalSourceError):
                    operation(fake)
            with self.assertRaises(source.FinalSourceError):
                source.get_case(fake, 0)
        for issuer in (source.make_synthetic_source, source.open_final_source, source.load_development_source):
            for arguments in ({"raw": {}}, {"loader": lambda: {}}, {"scope": "FINAL"}, {"root_index": 0}):
                with self.assertRaises(TypeError):
                    issuer(**arguments)
        for name in ("_bind_sources", "_actual_plan", "_read_actual", "_synthetic_raw", "_issue", "_lookup"):
            self.assertFalse(hasattr(source, name))

    def test_context_drift_invalidates_handle_before_conversion(self):
        handle = source.make_synthetic_source()
        changed = context()
        changed[0]["contract_sha256"] = "c" * 64
        with patch.object(source, "_context", return_value=changed), patch.object(source, "_convert_raw") as conversion:
            with self.assertRaisesRegex(source.FinalSourceError, "CONTEXT_DRIFT"):
                source.get_case(handle, 0)
            conversion.assert_not_called()

    def test_detached_numeric_and_summary_cannot_promote_qualification(self):
        handle = source.make_synthetic_source()
        summary = handle.summary
        summary.update(scope="FINAL_CAMPAIGN", final_prediction_qualified=True)
        row = source.get_case(handle, 0)
        row["c1"].ref.setflags(write=True)
        row["c1"].ref[:] = -999
        row["rcd"]["values"][:] = 0
        fresh = source.get_case(handle, 0)
        self.assertFalse(np.all(fresh["c1"].ref == -999))
        self.assertTrue(np.any(fresh["rcd"]["values"]))
        self.assertEqual(handle.summary["scope"], source.SYNTHETIC_SCOPE)
        self.assertFalse(handle.summary["final_prediction_qualified"])

    def test_numeric_observations_remove_names_paths_and_absolute_time(self):
        handle = source.make_synthetic_source()
        row = source.get_case(handle, 0)
        for observation in (row["c1"], row["c5"]):
            self.assertEqual(observation.node_ids, tuple(source.candidate_key(f"synthetic-node-{i}") for i in range(len(observation.adjacency))))
            rendered = json.dumps({"quality": plain(observation.quality),
                                   "source": plain(observation.source_hashes), "graph": plain(observation.graph_provenance)})
            for forbidden in ("synthetic-node", "re2tt_", "ts-", "D:/", "inject_time", "100000"):
                self.assertNotIn(forbidden, rendered)
        self.assertEqual(row["rcd"]["values"].shape, (600, 6))
        self.assertEqual(row["rcd"]["owners"], list(range(6)))

    def test_actual_permissions_close_before_metadata_or_telemetry(self):
        for permission, value in (("tau_only_input_audit", False), ("telemetry_final60_conversion_only", False), ("telemetry_final60_new_acquisition", True)):
            changed = context()
            changed[1]["permissions"][permission] = value
            with patch.object(source, "_context", return_value=changed), patch("scripts.task_g.provenance.verify_entry_receipt") as verify, patch("pyarrow.parquet.read_table") as reader:
                with self.assertRaisesRegex(source.FinalSourceError, "PERMISSION_CLOSED"):
                    source.open_final_source()
                verify.assert_not_called()
                reader.assert_not_called()

    def test_timing_registration_and_entry_integrity_checked_before_projection(self):
        changed = context()
        changed[1]["tau_source"]["projection"] += ["fault"]
        with patch.object(source, "_context", return_value=changed), patch("scripts.task_g.provenance.verify_entry_receipt") as verifier, patch("pyarrow.parquet.read_table") as reader:
            with self.assertRaisesRegex(source.FinalSourceError, "REGISTRATION_DRIFT"):
                source.open_final_source()
            verifier.assert_not_called()
            reader.assert_not_called()
        with patch("scripts.task_g.provenance.verify_entry_receipt", return_value={"scope": "ENTRY_RAW_ADMISSION", "trust_mode": "CALLER", "receipt_sha256": source.ENTRY_SHA}), patch("pyarrow.parquet.read_table") as reader:
            with self.assertRaisesRegex(source.FinalSourceError, "ENTRY_BINDING"):
                source.open_final_source()
            reader.assert_not_called()

    def test_actual_source_projection_is_exact_and_no_raw_or_model_is_opened(self):
        # Entire entry/metadata registry is synthetic in this counterfactual.
        # No official source or final source values are accessed by these mocks.
        rows, development = [], []
        for cell in range(30):
            for repeat in (1, 2, 3):
                case = f"opaque-{cell:02d}_{repeat}"
                rows.append({"case": case, "dataset": "RE2-TT", "repetition": repeat,
                             "has_logs": not (cell == 0 and repeat == 1), "has_traces": True})
                if cell < 10:
                    development.append(case)
        ids = tuple(sorted(row["case"] for row in rows if row["case"] not in development))
        timing = [{key: row[key] for key in ("case", "dataset", "repetition")} | {"inject_time": 1700000630} for row in rows]
        descriptors = [{"path": f"{case}/{modality}.parquet", "bytes": 10, "sha256": "b" * 64}
                       for case in ids for modality in ("metrics", "traces", "logs")]
        descriptors.sort(key=lambda row: row["path"])
        roster_sha = hashlib.sha256(("\n".join(ids) + "\n").encode()).hexdigest()
        descriptor_sha = source._digest(descriptors)
        audits = [{"ordinal": n, "modalities": {modality: {"bytes": 10, "sha256": "b" * 64} for modality in ("metrics", "traces", "logs")},
                   "clock_alignment": {"declared_metric_unit": "seconds", "declared_trace_unit": "milliseconds",
                                       "trace_rows_inside_metric_archive": 100, "trace_rows_outside_metric_archive": 0},
                   "log_association": {"rows_with_exact_service_and_observed_metric_second": 100}}
                  for n in range(60)]
        envelope = {"commitment": {"execution": {"aggregate_report": {"admission": {
            "descriptor_sha256": descriptor_sha, "opaque_roster_sha256": roster_sha,
            "planned_cases": 60, "planned_objects": 180, "case_audits": audits}}}}}
        encoded = source._canonical(envelope)
        receipt_sha = hashlib.sha256(encoded).hexdigest()
        projected = []
        def read(path, *, columns):
            projected.append(columns)
            result = rows if columns == list(source.ROSTER_PROJECTION) else timing
            return type("Table", (), {"to_pylist": lambda self: result})()
        footer = type("Footer", (), {"schema_arrow": pa.schema([pa.field("inject_time", pa.int64())])})()
        with patch.object(source, "ENTRY_SHA", receipt_sha), patch.object(source, "ROSTER_SHA", roster_sha), patch.object(source, "DESCRIPTOR_SHA", descriptor_sha), \
                patch.object(source, "_sha", return_value=source.METADATA_SHA), patch.object(source.previous, "_regular_bytes", return_value=encoded), \
                patch("scripts.task_g.provenance.verify_entry_receipt", return_value={"scope": "ENTRY_RAW_ADMISSION", "trust_mode": "HOST_TRUSTED", "receipt_sha256": receipt_sha}), \
                patch("scripts.pre_g.source_qualification._read_frozen_contract", return_value=({}, {"development_ids": development})), \
                patch("pyarrow.parquet.ParquetFile", return_value=footer), patch("pyarrow.parquet.read_table", side_effect=read), \
                patch("scripts.task_g.source_admission._read_verified_raw") as raw_reader:
            handle = source.open_final_source()
            self.assertEqual(source.case_count(handle), 60)
            self.assertEqual(projected, [list(source.ROSTER_PROJECTION), list(source.TAU_PROJECTION)])
            raw_reader.assert_not_called()
            with self.assertRaisesRegex(source.FinalSourceError, "TRUTH.*CLOSED"):
                source.map_truth(handle, 0, "a-closed-root")
        self.assertFalse(handle.summary["final_prediction_qualified"])

    def test_ordinal_and_trigger_boundaries_are_strict(self):
        handle = source.make_synthetic_source()
        for ordinal in (-1, 3, True, 0.0):
            with self.assertRaises(source.FinalSourceError):
                source.get_case(handle, ordinal)
        for endpoint in (-5, 361, 360.0, True):
            with self.assertRaises(source.FinalSourceError):
                source.integrated_observation(handle, 0, endpoint)
        with self.assertRaisesRegex(source.FinalSourceError, "INSUFFICIENT_HISTORY"):
            source.integrated_observation(handle, 0, 195)
        with self.assertRaisesRegex(source.FinalSourceError, "OUTSIDE_OBSERVED"):
            source.integrated_observation(handle, 0, 1205)

    def test_exact_actual_marker_changes_c1_window_without_changing_c5(self):
        raw, tau = raw_fixture(tau_offset=630)
        a, _ = convert(copy.deepcopy(raw), tau)
        b, _ = convert(copy.deepcopy(raw), tau + 90)
        self.assertFalse(np.array_equal(a["c1"].query, b["c1"].query, equal_nan=True))
        for key in ("warmup_values", "stream_values", "adjacency", "fit_service_mask", "relative_endpoints"):
            np.testing.assert_array_equal(getattr(a["c5"], key), getattr(b["c5"], key))
        self.assertEqual(a["source_metadata"]["clock_windows"]["source_of_window"], "VERIFIED_INJECT_TIME_PROJECTION_NOT_ORIGIN_OFFSET")

    def test_time_translation_and_label_like_metadata_do_not_change_numeric_arrays(self):
        raw, tau = raw_fixture()
        expected, _ = convert(copy.deepcopy(raw), tau)
        translated, translated_tau = raw_fixture(shift=1_000_000)
        translated["audit"] = {"root": "closed-a", "fault": "closed-b", "normal_timesteps": -1}
        observed, _ = convert(translated, translated_tau)
        self.assertEqual(observed["numeric_input_sha256"], expected["numeric_input_sha256"])

    def test_literal_mapping_longest_suffix_unknown_owner_retained(self):
        raw, tau = raw_fixture()
        row, private = convert(raw, tau)
        self.assertEqual(private["names"]["c1"], ("literal-a", "literal-b"))
        self.assertEqual(row["c1"].ref.shape, (2, 12, 30))
        self.assertTrue(np.isfinite(row["c1"].ref[0, 0]).all())
        self.assertTrue(np.isnan(row["c1"].ref[1, 0]).all())
        self.assertEqual(row["source_metadata"]["rcd_quality"]["unknown_column_count"], 2)
        self.assertEqual(row["rcd"]["owners"], [0, 0, 1])
        mapping = row["source_metadata"]["c1_quality"]["metric_ref"]["mapping"]
        self.assertIn(source.candidate_key("literal-a") + "/channel8", mapping)
        self.assertIn(source.candidate_key("literal-a") + "/channel0", mapping)
        self.assertFalse(any(key.startswith("unknown-") for key in mapping))

    def test_missing_logs_is_unavailable_not_zero_and_never_vetoes_mt(self):
        raw, tau = raw_fixture(missing_logs=True)
        row, _ = convert(raw, tau)
        self.assertIsNotNone(row["c1"])
        self.assertIsNotNone(row["c5"])
        self.assertTrue(np.isnan(row["c1"].ref[:, 11]).all())
        self.assertTrue(np.isnan(row["c5"].warmup_values[:, :, 11]).all())

    def test_missing_metrics_preserves_trace_only_c1_and_c5_origin_failure(self):
        raw, tau = raw_fixture()
        raw["metrics"] = None
        row, _ = convert(raw, tau)
        self.assertIsNotNone(row["c1"])
        self.assertTrue(np.isfinite(row["c1"].ref[:, 10]).all())
        self.assertTrue(np.isnan(row["c1"].ref[:, :10]).all())
        self.assertIsNone(row["c5"])
        self.assertIsNone(row["rcd"])
        self.assertIn("c5", row["source_metadata"]["conversion_failures"])
        self.assertIsNone(row["source_metadata"]["clock_windows"]["metric_observed_seconds"])
        self.assertEqual(row["source_metadata"]["clock_windows"]["known_window_coverage_status"], "OPEN_METRIC_COVERAGE_UNAVAILABLE")
        inventory = row["source_metadata"]["numeric_inventory"]
        self.assertEqual(inventory["profiles"]["c1"]["arrays"]["ref"]["shape"], [2, 12, 30])
        self.assertIsNone(inventory["profiles"]["c5"]["binary_bytes"])
        self.assertIsNone(inventory["profiles"]["rcd"]["arrays"])
        self.assertFalse(inventory["comparison_covers_complete_diagnostics"])
        self.assertEqual(inventory["complete_actual_diagnostic_artifact_size_status"], "OPEN_MODELS_AND_PREDICTIONS_NOT_RUN")

    def test_short_archive_preserves_partial_arrays_with_open_window_coverage(self):
        raw, tau = raw_fixture(tau_offset=1000)
        row, _ = convert(raw, tau)
        self.assertIsNotNone(row["c1"])
        self.assertTrue(np.isnan(row["c1"].query[:, :10, 20:]).all())
        report = row["source_metadata"]["clock_windows"]
        self.assertTrue(report["known_window_reference_fully_inside_archive"])
        self.assertFalse(report["known_window_query_fully_inside_archive"])
        self.assertEqual(report["known_window_coverage_status"], "OPEN_REFERENCE_OR_QUERY_ARCHIVE_COVERAGE")

    def test_stable_literal_key_survives_different_query_and_integrated_universes(self):
        from scripts.task_e.input_adapters import integrated_bundle
        raw, tau = raw_fixture()
        extra = raw["traces"].iloc[0].copy()
        extra["traceID"], extra["spanID"], extra["serviceName"] = "extra-query", "extra", "aaa-query-only"
        extra["startTimeMillis"] = (tau + 100) * 1000
        raw["traces"] = pd.concat([raw["traces"], pd.DataFrame([extra])], ignore_index=True)
        case, _ = convert(raw, tau)
        past = integrated_bundle(raw, tau)
        integrated_keys = [source.candidate_key(name) for name in past["service_names"]]
        root_key = source.candidate_key("literal-b")
        self.assertEqual(case["c1"].node_ids.index(root_key), 2)
        self.assertEqual(integrated_keys.index(root_key), 1)
        absent_key = source.candidate_key("aaa-query-only")
        self.assertIn(absent_key, case["c1"].node_ids)
        self.assertNotIn(absent_key, integrated_keys)

    def test_trace_conflict_keeps_c1_failure_and_c5_chronological_masks(self):
        raw, tau = raw_fixture()
        conflict = raw["traces"].iloc[132].copy()
        conflict["startTimeMillis"] = (tau + 10) * 1000
        raw["traces"] = pd.concat([raw["traces"], pd.DataFrame([conflict])], ignore_index=True)
        row, _ = convert(raw, tau)
        self.assertIsNone(row["c1"])
        self.assertIsNone(row["rcd"])
        self.assertIsNotNone(row["c5"])
        self.assertIn("c1", row["source_metadata"]["conversion_failures"])
        self.assertGreater(row["source_metadata"]["c5_quality"]["trace"]["masked_service_bins"], 0)

    def test_future_suffix_does_not_change_c5_prefix_or_integrated_past_window(self):
        from scripts.task_e.input_adapters import integrated_bundle
        raw, tau = raw_fixture()
        expected, _ = convert(copy.deepcopy(raw), tau)
        endpoint = int(raw["metrics"].time.min()) + 360
        prior = integrated_bundle(raw, endpoint)
        changed = copy.deepcopy(raw)
        changed["metrics"].loc[changed["metrics"].time >= endpoint, "literal-a_cpu"] = 1e30
        changed["traces"].loc[changed["traces"].startTimeMillis >= endpoint * 1000, "serviceName"] = "future-only-literal"
        observed, _ = convert(changed, tau)
        np.testing.assert_array_equal(expected["c5"].warmup_values, observed["c5"].warmup_values)
        np.testing.assert_array_equal(expected["c5"].stream_values[:36], observed["c5"].stream_values[:36])
        np.testing.assert_array_equal(expected["c5"].adjacency, observed["c5"].adjacency)
        after = integrated_bundle(changed, endpoint)
        for key in ("ref", "query", "adj"):
            np.testing.assert_array_equal(prior[key], after[key])
        self.assertEqual(prior["service_names"], after["service_names"])

    def test_integrated_mapping_survives_materializing_other_fixture(self):
        handle = source.make_synthetic_source()
        source.integrated_observation(handle, 0, 720)
        self.assertEqual(source.map_truth(handle, 0, "synthetic-node-0", endpoint=720), 0)
        source.get_case(handle, 1)
        self.assertEqual(source.map_truth(handle, 0, "synthetic-node-0", endpoint=720), 0)
        self.assertEqual(source.get_case(handle, 0)["controller_bindings"]["integrated_candidate_ids"]["720"], [source.candidate_key(f"synthetic-node-{i}") for i in range(6)])
        self.assertIsNone(source.map_truth(handle, 0, "unknown-root"))

    def test_unplaceable_clock_and_fractional_timing_fail_without_repair(self):
        raw, tau = raw_fixture()
        with self.assertRaisesRegex(source.FinalSourceError, "TIMING_MARKER"):
            convert(raw, tau + 0.5)
        raw["metrics"].loc[0, "time"] = np.nan
        with self.assertRaises(Exception):
            convert(raw, tau)

    def test_fresh_clock_alignment_counts_each_modality_and_wrong_units_stay_open(self):
        raw, tau = raw_fixture()
        report, _ = source._clock_report(copy.deepcopy(raw), tau)
        self.assertEqual(report["modalities"]["metrics"]["reference_rows"], 300)
        self.assertEqual(report["modalities"]["traces"]["reference_rows"], 120)
        self.assertEqual(report["modalities"]["logs"]["query_rows"], 60)
        for name in ("metrics", "traces", "logs"):
            self.assertEqual(report["modalities"][name]["status"], "DECLARED_UNIT_ALIGNED_NONEMPTY_WINDOWS")
            self.assertEqual(report["modalities"][name]["rows_outside_metric_archive"], 0)
            self.assertGreater(report["modalities"][name]["rows_at_observed_metric_seconds"], 0)
        wrong = copy.deepcopy(raw)
        wrong["traces"]["startTimeMillis"] //= 1000
        changed, _ = source._clock_report(wrong, tau)
        self.assertEqual(changed["clocks"]["traces"], "INTEGER_MILLISECONDS")
        self.assertEqual(changed["modalities"]["traces"]["status"], "OPEN_CLOCK_ALIGNMENT_OR_NO_SHARED_COVERAGE")
        self.assertEqual(changed["modalities"]["traces"]["reference_rows"], 0)
        self.assertEqual(changed["modalities"]["traces"]["rows_inside_metric_archive"], 0)
        empty = copy.deepcopy(raw)
        empty["logs"] = empty["logs"].iloc[:0]
        missing, _ = source._clock_report(empty, tau)
        self.assertEqual(missing["modalities"]["logs"]["status"], "OPEN_EMPTY_TELEMETRY")
        self.assertEqual(missing["modalities"]["logs"]["query_rows"], 0)

    def test_controller_operation_counts_rates_top3_and_duplicate_semantics(self):
        raw, tau = raw_fixture()
        spans = raw["traces"]
        spans.loc[spans.serviceName.eq("literal-a"), "operationName"] = "base"
        query = spans.serviceName.eq("literal-a") & spans.startTimeMillis.ge(tau * 1000) & spans.startTimeMillis.lt((tau + 300) * 1000)
        spans.loc[query, "operationName"] = ["alpha", "beta", "gamma"] * 20
        duplicate = spans.loc[query].iloc[0].copy()
        raw["traces"] = pd.concat([spans, pd.DataFrame([duplicate])], ignore_index=True)
        catalog = source._controller_evidence(raw, ["literal-a", "literal-b"], {"logs": "c" * 64}, tau - 300, tau, tau, tau + 300)["c3-support"]
        service = catalog["operations"][0]
        self.assertEqual((service["reference_span_count"], service["query_span_count"]), (60, 60))
        operations = {item["operation_key"]: item for item in service["operations"]}
        key = lambda text: "o" + hashlib.sha256(("TD13-G32|literal-operation|" + text).encode()).hexdigest()[:24]
        self.assertEqual(operations[key("base")]["reference_count"], 60)
        self.assertEqual(operations[key("base")]["query_count"], 0)
        self.assertAlmostEqual(operations[key("base")]["absolute_rate_change"], 0.2)
        self.assertAlmostEqual(operations[key("alpha")]["query_rate_per_second"], 20 / 300)
        expected = sorted(operations.values(), key=lambda item: (-item["absolute_rate_change"], item["operation_key"]))[:3]
        self.assertEqual(service["top3_absolute_rate_changes"], [item["evidence_id"] for item in expected])
        rendered = json.dumps(catalog)
        for literal in ("literal-a", '"base"', '"alpha"', '"beta"', '"gamma"'):
            self.assertNotIn(literal, rendered)

    def test_log_sampling_uses_file_hash_and_physical_original_ordinal_with_complete_redaction(self):
        raw, tau = raw_fixture()
        logs = raw["logs"]
        logs.index = np.arange(len(logs)) + 5000
        logs.loc[:, "message"] = "root=secret fault=secret D:/oracle/answers.json"
        duplicate = logs.loc[logs.timestamp.eq(tau)].iloc[0].copy()
        raw["logs"] = pd.concat([logs, pd.DataFrame([duplicate])], ignore_index=False)
        file_hash = "c" * 64
        catalog = source._controller_evidence(raw, ["literal-a", "literal-b"], {"logs": file_hash}, tau - 300, tau, tau, tau + 300)["c3-support"]
        support = catalog["query_logs"]
        ordinals = np.flatnonzero(((raw["logs"].timestamp >= tau) & (raw["logs"].timestamp < tau + 300)).to_numpy()).tolist()
        expected = sorted(ordinals, key=lambda ordinal: hashlib.sha256(f"{file_hash}|{ordinal}".encode()).hexdigest())[:3]
        observed = support["services"][0]
        self.assertEqual(observed["query_row_count"], 61)
        self.assertEqual([item["original_row_ordinal"] for item in observed["excerpts"]], expected)
        self.assertEqual(support["services"][1]["excerpts"], [])
        self.assertEqual(support["semantic_excerpt_status"], "SANITIZED_UNTRUSTED_QUERY_LOGS")
        for text in ("secret", "D:/oracle", "answers.json"):
            self.assertNotIn(text, json.dumps(catalog))
        self.assertTrue(all(item["status"] == "SANITIZED_UNTRUSTED_TEXT_RETAINED" for item in observed["excerpts"]))
        self.assertTrue(all(item["untrusted_telemetry_text"] for item in observed["excerpts"]))
        self.assertTrue(all(item["source_message_utf8_bytes"] > 0 for item in observed["excerpts"]))
        raw["logs"] = None
        absent = source._controller_evidence(raw, ["literal-a"], {"logs": "MISSING"}, tau - 300, tau, tau, tau + 300)["c3-support"]["query_logs"]
        self.assertEqual(absent["status"], "MISSING_OR_UNAVAILABLE")
        self.assertIsNone(absent["query_rows"])

    def test_issued_copy_preserves_detached_c3_catalog_and_integrated_past_support(self):
        handle = source.make_synthetic_source()
        observed = source.get_case(handle, 0)["c1"]
        self.assertIn("c3-support", observed.evidence_catalog)
        with self.assertRaises(TypeError):
            observed.evidence_catalog["c3-support"]["status"] = "FAKE"
        fresh = source.get_case(handle, 0)["c1"]
        self.assertEqual(plain(fresh.evidence_catalog), plain(observed.evidence_catalog))
        integrated = source.integrated_observation(handle, 0, 360)
        support = integrated.evidence_catalog["c3-support"]
        self.assertEqual((support["reference_seconds"], support["query_seconds"]), (300, 60))
        self.assertTrue(all(0 <= item["query_relative_second"] < 60
                            for service in support["query_logs"]["services"] for item in service["excerpts"]))

    def test_conversion_audit_keeps_partial_metadata_when_integrated_conversion_fails(self):
        # Single artificial case, fake ordinal orchestration. Never actual I/O.
        raw, tau = raw_fixture(missing_logs=True)
        row, _ = convert(raw, tau)
        marker = object()
        with patch.object(source, "open_final_source", return_value=marker), \
                patch.object(source, "case_count", return_value=1), patch.object(source, "get_case", return_value=row), \
                patch.object(source, "integrated_observation", side_effect=source.FinalSourceError("SYNTHETIC_ONLY_EXPECTED_FAILURE")):
            result = source.audit_actual_conversion()
        record = result["case_records"][0]
        self.assertEqual(record["status"], "CONVERSION_FAILURE_RETAINED")
        self.assertEqual(record["source_metadata"], row["source_metadata"])
        self.assertEqual(record["numeric_input_sha256"], row["numeric_input_sha256"])
        self.assertEqual(record["failure_attempts"], [{"stage": "INTEGRATED360_CONVERSION", "error_type": "FinalSourceError"}])
        self.assertFalse(record["model_functions_invoked"])

    def test_support_conversion_failure_retains_numeric_inputs_and_reports_packet_open(self):
        raw, tau = raw_fixture()
        expected, _ = convert(copy.deepcopy(raw), tau)
        with patch.object(source, "_controller_evidence", side_effect=ValueError("SYNTHETIC_ONLY_REDACTION_FAILURE")):
            observed, _ = convert(raw, tau)
        self.assertEqual(observed["numeric_input_sha256"], expected["numeric_input_sha256"])
        self.assertIsNotNone(observed["c1"])
        self.assertEqual(observed["c1"].evidence_catalog["c3-support"]["status"], "OPEN_SUPPORT_CONVERSION_FAILURE_RETAINED")
        self.assertEqual(observed["c1"].evidence_catalog["c3-support"]["error_type"], "ValueError")
        self.assertIsInstance(observed["source_metadata"]["conversion_costs"]["c1_explanation_support_conversion_seconds"], float)

    def test_log_sanitizer_preserves_diagnostic_meaning_without_semantic_truth_classification(self):
        text = "Timeout waiting for upstream; HTTP 503, retries=3, duration_ms=250. Fault tolerance enabled."
        sanitized = source._sanitize_query_log(text)
        self.assertEqual(sanitized["text"], text)
        self.assertEqual(sanitized["status"], "SANITIZED_UNTRUSTED_TEXT_RETAINED")
        self.assertEqual(sanitized["redaction_counts"], {})
        self.assertTrue(sanitized["untrusted_telemetry_text"])

    def test_log_sanitizer_redacts_identifiers_clocks_locators_and_credentials(self):
        text = ("literal-a request failed for known-case-42 at 2026-10-01T09:12:13.456+07:00 "
                "epoch 1700000630 and 1700000630000; clock 100630; "
                "paths D:/secret/data.json \\\\server\\share\\oracle /var/private/answers.json "
                "https://example.invalid/answer?key=secret; Authorization: Bearer abc.def.ghi "
                "password='private password' api_key=token-value; HTTP 503 retries=3")
        result = source._sanitize_query_log(text, ("literal-a", "known-case-42"), (100630,))
        for item in ("literal-a", "known-case-42", "2026-10-01", "1700000630", "100630", "D:/", "server", "oracle",
                     "answers.json", "example.invalid", "abc.def.ghi", "private password", "token-value"):
            self.assertNotIn(item, result["text"])
        for item in ("request failed", "HTTP 503", "retries=3"):
            self.assertIn(item, result["text"])
        self.assertEqual(result["source_message_utf8_bytes"], len(text.encode()))
        self.assertEqual(result["sanitized_message_utf8_bytes"], len(result["text"].encode()))

    def test_log_sanitizer_removes_nested_and_escaped_structured_closed_fields(self):
        text = ('{"ground_truth":{"root":["secret-name",{"fault":"private-value"}]},'
                '"message":"timeout HTTP 503","labels":["private-label"],'
                '"\\u0072oot":"unicode-value","outcome":"private-outcome","counts":3}')
        result = source._sanitize_query_log(text)
        for item in ("secret-name", "private-value", "private-label", "unicode-value", "private-outcome", "ground_truth", "\\u0072oot"):
            self.assertNotIn(item, result["text"])
        self.assertIn("timeout HTTP 503", result["text"])
        self.assertIn('"counts":3', result["text"])
        self.assertEqual(result["redaction_counts"]["closed_fields"], 4)
        malformed = source._sanitize_query_log('timeout root={"nested":["private-value"]')
        self.assertIn("timeout", malformed["text"])
        self.assertNotIn("private-value", malformed["text"])
        self.assertEqual(source._sanitize_query_log(None)["status"], "MISSING_MESSAGE")
        self.assertEqual(source._sanitize_query_log(123)["status"], "UNSUPPORTED_MESSAGE_TYPE")

    def test_log_content_changes_do_not_change_arrays_or_sampling_selection(self):
        raw, tau = raw_fixture()
        expected, _ = convert(copy.deepcopy(raw), tau)
        changed = copy.deepcopy(raw)
        changed["_controller_redaction_identifiers"] = ("known-case-42",)
        changed["logs"].loc[:, "message"] = "known-case-42 literal-a timeout HTTP 503 root=hidden fault=hidden"
        actual, _ = convert(changed, tau)
        self.assertEqual(actual["numeric_input_sha256"], expected["numeric_input_sha256"])
        old_logs = expected["c1"].evidence_catalog["c3-support"]["query_logs"]["services"]
        new_logs = actual["c1"].evidence_catalog["c3-support"]["query_logs"]["services"]
        self.assertEqual([[item["original_row_ordinal"] for item in service["excerpts"]] for service in old_logs],
                         [[item["original_row_ordinal"] for item in service["excerpts"]] for service in new_logs])
        text = json.dumps(plain(actual["c1"].evidence_catalog))
        self.assertIn("timeout HTTP 503", text)
        for item in ("literal-a", "known-case-42", "hidden"):
            self.assertNotIn(item, text)

    def test_audit_progress_emits_detached_complete_record_and_separate_rcd_empty_count(self):
        # Artificial numeric conversion plus fake one-case orchestration only.
        raw, tau = raw_fixture()
        for column in raw["metrics"]:
            if column != "time":
                raw["metrics"][column] = 1.0
        row, _ = convert(raw, tau)
        self.assertEqual(row["rcd"]["values"].shape[1], 0)
        progress = []
        def completed(payload):
            progress.append(copy.deepcopy(payload))
            payload["completed_case_record"]["c1_candidates"] = -1
            payload["completed_case_record"]["profile_statuses"]["rcd"] = "FAKE_PROMOTION"
        with patch.object(source, "open_final_source", return_value=object()), patch.object(source, "case_count", return_value=1), \
                patch.object(source, "get_case", return_value=row), patch.object(source, "integrated_observation", return_value=row["c1"]):
            result = source.audit_actual_conversion(progress=completed)
        self.assertEqual(len(progress), 1)
        self.assertEqual(progress[0]["completed_case_record"], result["case_records"][0])
        self.assertEqual(result["converted_only_cases"], 1)
        self.assertEqual(result["profile_status_counts"]["rcd"], {"EMPTY_ELIGIBILITY_BASELINE_FAILURE_ONLY": 1})
        self.assertEqual(result["profile_status_counts"]["c1"], {"NUMERIC_INPUT_AVAILABLE": 1})
        self.assertIn("RCD_STATUS_SEPARATE", result["converted_only_cases_definition"])
        rendered = json.dumps(progress[0])
        for item in ("literal-a", "literal-b", str(tau), "D:/", "casepath"):
            self.assertNotIn(item, rendered)
        self.assertFalse(progress[0]["completed_case_record"]["model_functions_invoked"])


if __name__ == "__main__":
    unittest.main()
