"""Analytic TD13 chronology fixtures; no telemetry files or models are opened.

Expected counts, masks, edges and cutoffs follow TD13 section7.0b. They are
specified before execution, not copied from implementation outputs. Running
this file requires a new preserved run-contract.json supplied by coordinator.
"""
from __future__ import annotations

import io
import json
import math
import sys
import time
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e.loader import LoaderError, c5_bundle


def span(key, millis, owner, parent="", trace="t", duration=1):
    return {"time": "clock-display", "traceID": trace, "spanID": key,
            "serviceName": owner, "methodName": None, "operationName": "op",
            "parentSpanID": parent, "startTimeMillis": millis,
            "startTime": millis * 1000, "duration": duration, "statusCode": None}


def raw_case(extra=(), *, include_logs=True):
    rows = [span("parent", 10000, "a"), span("child", 11000, "b", "parent"),
            span("c-root", 15000, "c"), span("d-root", 16000, "d")]
    ticks = np.arange(601, dtype=np.int64)
    metrics = pd.DataFrame({"time": ticks, **{f"{s}_cpu": np.full(601, i+1.)
                                              for i, s in enumerate("abcde")}})
    logs = pd.DataFrame({"timestamp": [11, 201], "container_name": ["b", "b"],
                         "message": ["fit", "later"]}) if include_logs else None
    return {"metrics": metrics, "traces": pd.DataFrame(rows + list(extra)), "logs": logs}


def node(bundle, name):
    return bundle["service_names"].index(name)


def assert_same_numeric(test, a, b):
    test.assertEqual(a["service_names"], b["service_names"])
    for field in ("values", "adj", "fit_service_mask", "endpoints", "channel_types"):
        np.testing.assert_array_equal(a[field], b[field])


class C5ReplayChecks(unittest.TestCase):
    def test_nullable_optional_arrow_integer_fields_are_admitted(self):
        import pyarrow as pa
        from scripts.task_e.loader import _validate_schema, TRACE_FIELDS
        row = span('p', 10000, 'a')
        row.update(duration=None, startTime=None)
        schema = pa.schema([(k, pa.string() if i < 7 else pa.int64())
                            for i, k in enumerate(TRACE_FIELDS)])
        table = pa.Table.from_pylist([row], schema=schema)
        _validate_schema('traces', table)
        raw = raw_case()
        raw['traces'] = table.to_pandas()
        b = c5_bundle(raw)
        self.assertEqual(b['values'][2, 0, 10], math.log(2))
        bad = table.set_column(9, 'duration', pa.array([1.5]))
        with self.assertRaises(LoaderError):
            _validate_schema('traces', bad)

    def test_multi_key_discredit_audit_is_permutation_invariant(self):
        raw = raw_case([span('parent', 200000, 'a'),
                        span('child', 205000, 'b', 'parent')])
        first = c5_bundle(raw)
        raw['traces'] = raw['traces'].iloc[::-1].reset_index(drop=True)
        second = c5_bundle(raw)
        assert_same_numeric(self, first, second)
        self.assertEqual(first['audit']['trace'], second['audit']['trace'])

    def test_clean_unique_keys_have_analytic_counts_and_one_edge(self):
        b = c5_bundle(raw_case())
        self.assertEqual(b["values"].shape, (120, 4, 12))
        self.assertTrue(b["fit_service_mask"].all())
        expected = np.zeros((4, 4), dtype=bool)
        expected[0, 1] = True
        np.testing.assert_array_equal(b["adj"], expected)
        self.assertEqual(b["values"][2, 0, 10], math.log(2))
        self.assertEqual(b["values"][2, 1, 10], math.log(2))
        self.assertEqual(b["values"][3, 1, 10], 0.)

    def test_identical_duplicate_is_one_count_and_one_support(self):
        b = c5_bundle(raw_case([span("child", 11000, "b", "parent")]))
        self.assertEqual(b["values"][2, 1, 10], math.log(2))
        self.assertEqual(b["audit"]["graph"]["edge_observation_counts"], {"0->1": 1})
        self.assertEqual(b["audit"]["identical_trace_duplicates_collapsed"], 1)
        self.assertEqual(b["audit"]["trace"]["masked_service_bins"], 0)

    def test_before_freeze_removes_support_without_rewriting_closed_fit_bin(self):
        b = c5_bundle(raw_case([span("child", 119999, "c", "parent")]))
        self.assertEqual(b["values"][2, 1, 10], math.log(2))
        self.assertTrue(np.isnan(b["values"][23, 1:3, 10]).all())
        self.assertFalse(b["adj"].any())
        self.assertEqual(b["audit"]["graph"]["removed_supports_known_by_freeze"], 1)

    def test_exact_freeze_belongs_to_next_bin_and_cannot_change_graph(self):
        b = c5_bundle(raw_case([span("child", 120000, "c", "parent")]))
        self.assertEqual(b["values"][23, 1, 10], 0.)
        self.assertTrue(np.isnan(b["values"][24, 1:3, 10]).all())
        self.assertTrue(b["adj"][0, 1])
        self.assertEqual(len(b["audit"]["trace"]["post_freeze_discredited_support"]), 1)

    def test_after_freeze_preserves_graph_and_calibration_history(self):
        base = c5_bundle(raw_case())
        b = c5_bundle(raw_case([span("child", 200000, "c", "parent")]))
        np.testing.assert_array_equal(b["values"][:40], base["values"][:40])
        np.testing.assert_array_equal(b["adj"], base["adj"])
        self.assertTrue(np.isnan(b["values"][40, 1:3, 10]).all())

    def test_calibration_only_service_is_appended_with_no_fit_membership(self):
        b = c5_bundle(raw_case([span("e-cal", 179999, "e")]))
        self.assertEqual(b["service_names"], list("abcde"))
        np.testing.assert_array_equal(b["fit_service_mask"], [True, True, True, True, False])
        self.assertTrue(np.isfinite(b["values"][:24, 4, 8]).all())
        self.assertFalse(b["adj"][4].any())
        self.assertFalse(b["adj"][:, 4].any())

    def test_exact_warmup_boundary_does_not_expand_service_universe(self):
        b = c5_bundle(raw_case([span("e-late", 180000, "e")]))
        self.assertEqual(b["service_names"], list("abcd"))
        self.assertEqual(b["audit"]["trace"]["out_of_v_accepted_rows"], 1)

    def test_exact_fit_boundary_service_is_calibration_only(self):
        b = c5_bundle(raw_case([span("e-cal", 120000, "e")]))
        self.assertEqual(b["service_names"], list("abcde"))
        self.assertFalse(b["fit_service_mask"][4])
        self.assertFalse(b["adj"][4].any())
        self.assertEqual(b["values"][24, 4, 10], math.log(2))

    def test_conflict_at_warmup_boundary_preserves_fit_and_cal_bins(self):
        base = c5_bundle(raw_case())
        b = c5_bundle(raw_case([span("child", 180000, "c", "parent")]))
        np.testing.assert_array_equal(b["values"][:36], base["values"][:36])
        self.assertTrue(np.isnan(b["values"][36, 1:3, 10]).all())
        self.assertTrue(b["adj"][0, 1])

    def test_same_time_conflict_is_batch_permutation_invariant(self):
        raw = raw_case([span("child", 11000, "c", "parent")])
        a = c5_bundle(raw)
        shuffled = {**raw, "traces": raw["traces"].iloc[::-1].reset_index(drop=True)}
        b = c5_bundle(shuffled)
        assert_same_numeric(self, a, b)
        self.assertTrue(np.isnan(a["values"][2, 1:3, 10]).all())
        self.assertFalse(a["adj"].any())

    def test_same_open_bin_first_count_is_masked_but_prior_bin_immutable(self):
        b = c5_bundle(raw_case([span("child", 14000, "b", "parent")]))
        self.assertTrue(np.isnan(b["values"][2, 1, 10]))
        self.assertEqual(b["values"][1, 1, 10], 0.)
        self.assertFalse(b["adj"].any())

    def test_repeated_quarantine_and_service_recovery(self):
        b = c5_bundle(raw_case([span("child", 201000, "b", "parent"),
                                span("child", 207000, "b", "parent"),
                                span("fresh", 211000, "b")]))
        self.assertTrue(np.isnan(b["values"][40:42, 1, 10]).all())
        self.assertEqual(b["values"][42, 1, 10], math.log(2))
        self.assertEqual(b["values"][43, 1, 10], 0.)
        self.assertEqual(len(b["audit"]["trace"]["quarantined_keys"]), 1)
        # A lag1 target at end215 still has a missing lag; at end220 it has
        # clean own target+lag again. This checks availability, not model output.
        valid = np.isfinite(b["values"][:, 1, 10])
        self.assertFalse(valid[42] and valid[41])
        self.assertTrue(valid[43] and valid[42])

    def test_owner_union_expands_only_from_its_encounter(self):
        b = c5_bundle(raw_case([span("child", 201000, "c", "parent"),
                                span("child", 207000, "a", "parent")]))
        self.assertEqual(b["values"][40, 0, 10], 0.)
        self.assertTrue(np.isnan(b["values"][40, 1:3, 10]).all())
        self.assertTrue(np.isnan(b["values"][41, :3, 10]).all())
        self.assertEqual(b["values"][41, 3, 10], 0.)

    def test_unknown_owner_masks_all_trace_channels_only_in_that_bin(self):
        b = c5_bundle(raw_case([span("child", 201000, None, "parent")]))
        self.assertTrue(np.isnan(b["values"][40, :, 10]).all())
        self.assertTrue(np.isfinite(b["values"][41, :, 10]).all())
        self.assertTrue(np.isfinite(b["values"][40, :, 8]).all())
        self.assertEqual(b["values"][40, 1, 11], math.log(2))

    def test_missing_key_known_owner_masks_local_trace_without_tombstone(self):
        b = c5_bundle(raw_case([span(None, 201000, "b")]))
        self.assertTrue(np.isnan(b["values"][40, 1, 10]))
        self.assertTrue(np.isfinite(b["values"][40, [0, 2, 3], 10]).all())
        self.assertEqual(b["audit"]["trace"]["quarantined_keys"], [])

    def test_missing_key_unknown_owner_masks_all_without_fabricated_identity(self):
        b = c5_bundle(raw_case([span(None, 201000, "")]))
        self.assertTrue(np.isnan(b["values"][40, :, 10]).all())
        self.assertEqual(b["audit"]["trace"]["quarantined_keys"], [])

    def test_missing_parent_keeps_child_count_and_does_not_invent_edge(self):
        raw = raw_case()
        raw["traces"].loc[1, "parentSpanID"] = "unknown-parent"
        b = c5_bundle(raw)
        self.assertEqual(b["values"][2, 1, 10], math.log(2))
        self.assertFalse(b["adj"].any())
        self.assertEqual(b["audit"]["graph"]["unresolved_selected_parents"], 1)

    def test_clean_independent_edge_witness_survives_other_key_quarantine(self):
        b = c5_bundle(raw_case([span("child", 119999, "c", "parent"),
                                span("other-parent", 20000, "a"),
                                span("other-child", 21000, "b", "other-parent")]))
        self.assertTrue(b["adj"][0, 1])
        self.assertEqual(b["audit"]["graph"]["edge_observation_counts"], {"0->1": 1})

    def test_quarantined_parent_removes_edge_not_clean_child_count(self):
        b = c5_bundle(raw_case([span("parent", 119000, "c")]))
        self.assertFalse(b["adj"].any())
        self.assertEqual(b["values"][2, 1, 10], math.log(2))
        self.assertEqual(b["values"][23, 1, 10], 0.)

    def test_preorigin_records_cannot_poison_identity_or_repair_parent(self):
        b = c5_bundle(raw_case([span("parent", -10000, "e")]))
        self.assertEqual(b["service_names"], list("abcd"))
        self.assertTrue(b["adj"][0, 1])
        self.assertEqual(b["audit"]["trace"]["quarantined_keys"], [])
        self.assertEqual(b["audit"]["trace"]["pre_origin_rows_audit_only"], 1)

    def test_composite_identity_allows_same_span_id_in_different_trace(self):
        b = c5_bundle(raw_case([span("child", 11000, "b", trace="another")]))
        self.assertAlmostEqual(b["values"][2, 1, 10], math.log(3), places=14)
        self.assertEqual(b["audit"]["trace"]["quarantined_keys"], [])

    def test_unplaceable_trace_clock_is_explicit_admission_failure(self):
        for value in (None, np.nan, np.inf, -np.inf, .5, "unknown"):
            with self.subTest(value=value):
                raw = raw_case()
                raw["traces"]["startTimeMillis"] = raw["traces"]["startTimeMillis"].astype(object)
                raw["traces"].loc[0, "startTimeMillis"] = value
                with self.assertRaisesRegex(LoaderError, "UNQUALIFIABLE_EVENT_CLOCK"):
                    c5_bundle(raw)

    def test_future_conflict_cannot_change_cutoff_materialization(self):
        raw = raw_case([span("child", 401000, "c", "parent")])
        past = c5_bundle(raw, cutoff_seconds=300)
        clean_past = c5_bundle(raw_case(), cutoff_seconds=300)
        assert_same_numeric(self, past, clean_past)
        full = c5_bundle(raw)
        np.testing.assert_array_equal(full["values"][:60], past["values"])
        np.testing.assert_array_equal(full["adj"], past["adj"])

    def test_auto_general_and_chunked_replay_are_equal(self):
        for extras in ([], [span("child", 11000, "b", "parent"),
                           span("child", 201000, "c", "parent"),
                           span("fresh", 211000, "b"), span(None, 250000, "a")]):
            raw = raw_case(extras)
            auto = c5_bundle(raw)
            general = c5_bundle(raw, trace_strategy="general")
            chunked = c5_bundle(raw, trace_chunk_size=1)
            assert_same_numeric(self, auto, general)
            assert_same_numeric(self, auto, chunked)
            self.assertEqual(auto["audit"]["trace"], general["audit"]["trace"])

    def test_numeric_cache_roundtrip_preserves_exact_cutoff(self):
        b = c5_bundle(raw_case([span("child", 201000, "c", "parent")]), cutoff_seconds=300)
        numeric = {k: b[k] for k in ("values", "adj", "fit_service_mask", "endpoints", "channel_types")}
        memory = io.BytesIO()
        np.savez(memory, **numeric)
        memory.seek(0)
        with np.load(memory, allow_pickle=False) as restored:
            for key, value in numeric.items():
                np.testing.assert_array_equal(restored[key], value)
        self.assertEqual(int(b["endpoints"][-1]), 300)
        self.assertEqual(b["audit"]["trace"]["cutoff_seconds"], 300)

    def test_trace_conflict_never_changes_metrics_or_logs(self):
        base = c5_bundle(raw_case())
        b = c5_bundle(raw_case([span("child", 201000, "c", "parent")]))
        np.testing.assert_array_equal(base["values"][:, :, :10], b["values"][:, :, :10])
        np.testing.assert_array_equal(base["values"][:, :, 11], b["values"][:, :, 11])

    def test_only_masked_positive_fit_count_does_not_establish_presence(self):
        b = c5_bundle(raw_case([span("child", 11000, "b", "parent", duration=2)]))
        self.assertFalse(b["audit"]["trace_fit_presence"][1])
        self.assertTrue(b["fit_service_mask"][1])

    def test_missing_log_file_is_unavailable_not_zero(self):
        b = c5_bundle(raw_case(include_logs=False))
        self.assertTrue(np.isnan(b["values"][:, :, 11]).all())
        self.assertFalse(any(b["audit"]["log_fit_presence"]))
        self.assertTrue(np.isfinite(b["values"][:, :, 10]).all())

    def test_optional_bad_log_clock_is_explicit_and_does_not_veto_MT(self):
        raw = raw_case()
        base = c5_bundle(raw)
        raw["logs"].loc[0, "timestamp"] = np.nan
        b = c5_bundle(raw)
        np.testing.assert_array_equal(base["values"][:, :, :11], b["values"][:, :, :11])
        self.assertTrue(np.isnan(b["values"][:, :, 11]).all())
        self.assertEqual(b["audit"]["log"]["status"], "UNAVAILABLE_LOG_CLOCK_OR_SCHEMA")
        self.assertIn("error", b["audit"]["log"])

    def test_null_payload_sentinel_does_not_make_identical_copy_conflicting(self):
        copy = span("child", 11000, "b", "parent")
        copy["methodName"] = np.nan
        copy["statusCode"] = np.nan
        b = c5_bundle(raw_case([copy]))
        self.assertEqual(b["audit"]["identical_trace_duplicates_collapsed"], 1)
        self.assertEqual(b["audit"]["trace"]["quarantined_keys"], [])

    def test_metric_conflict_masks_only_its_own_channel_bin(self):
        raw = raw_case()
        base = c5_bundle(raw)
        other = raw["metrics"].iloc[201].copy()
        other["b_cpu"] = 999.
        raw["metrics"] = pd.concat([raw["metrics"], pd.DataFrame([other])], ignore_index=True)
        b = c5_bundle(raw)
        np.testing.assert_array_equal(base["values"][:40], b["values"][:40])
        self.assertTrue(np.isnan(b["values"][40, 1, 8]))
        np.testing.assert_array_equal(base["values"][:, :, 10:], b["values"][:, :, 10:])

    def test_time_translation_preserves_numeric_outputs(self):
        raw = raw_case([span("child", 201000, "c", "parent")])
        a = c5_bundle(raw)
        shift = 1_000_000
        changed = {key: value.copy() for key, value in raw.items()}
        changed["metrics"]["time"] += shift
        changed["logs"]["timestamp"] += shift
        changed["traces"]["startTimeMillis"] += shift * 1000
        changed["traces"]["startTime"] += shift * 1_000_000
        b = c5_bundle(changed)
        assert_same_numeric(self, a, b)


if __name__ == "__main__":
    directory = Path(sys.argv[1])
    if not (directory / "run-contract.json").is_file():
        raise SystemExit("Pre-run contract required")
    started = time.perf_counter()
    outcome = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    report = {"schema": "TD13-C5-REPLAY-FIXTURE-v1", "tests_run": outcome.testsRun,
              "failures": [{"test": str(t), "traceback": e} for t, e in outcome.failures],
              "errors": [{"test": str(t), "traceback": e} for t, e in outcome.errors],
              "seconds": time.perf_counter() - started,
              "scope": "ANALYTIC SYNTHETIC TRACE REPLAY; NO MODELS/RAW/NETWORK"}
    (directory / "c5-replay-report.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    raise SystemExit(0 if outcome.wasSuccessful() else 1)
