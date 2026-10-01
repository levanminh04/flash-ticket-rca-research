"""Entry-only Task G controller; final prediction and label paths are closed.

This prepares the frozen campaign configuration and executes a numeric synthetic
RCD triplet. It does not implement the final campaign. Raw admission is consumed
only through the source module's issued handle. Worker stdin contains numeric
arrays and integer ownership, with no dataset locator or evaluator label.
"""

from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[2]
PROJECT = Path("D:/Project/flash-ticket-platform")
CONTRACT_REL = "results/task-g/g30-entry-validation/entry-contract.json"
MANIFEST_REL = "configs/task-f-td13-frozen-release-v2.json"
RUN_ID = "g30-entry-validation"
DOMAIN = "FlashTicketRca/TD13/G/ENTRY/v1"
MANIFEST_SHA = "c46b870bccdae1198292abc5850a83a3fa7e7f702286ceeaa07258074391801d"
RCD_IDENTITY_SHA = "38253ebbfaa53bdad20b66e655ade3fade363fdd9ef71ee2ab6df722ab4fac04"
FINAL_CLOSED = ("final_labels", "final_tau_metadata", "final_answers", "final_outcomes",
                "final_predictions", "final_campaign")
if str(WORKSPACE / "src") not in sys.path:
    sys.path.insert(0, str(WORKSPACE / "src"))


class EntryError(RuntimeError):
    """Entry registration, issuance, or worker boundary failed."""


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _digest(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _registered_context():
    contract = json.loads((WORKSPACE / CONTRACT_REL).read_text(encoding="utf-8"))
    if contract.get("run_id") != RUN_ID or any(
        contract.get("permissions", {}).get(key) is not False for key in FINAL_CLOSED
    ) or contract.get("permissions", {}).get("synthetic_development_fixture_execution") is not True:
        raise EntryError("ENTRY_PERMISSION_OR_RUN_DRIFT")
    snapshot = contract.get("source_test_snapshot_before_qualification")
    if not isinstance(snapshot, dict) or len(snapshot) != 6:
        raise EntryError("SOURCE_TEST_REGISTRATION_REQUIRED")
    for relative, expected in snapshot.items():
        target = (WORKSPACE / relative).resolve()
        if not target.is_relative_to(WORKSPACE.resolve()) or hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            raise EntryError("REGISTERED_SOURCE_TEST_DRIFT")
    manifest_path = WORKSPACE / MANIFEST_REL
    if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != MANIFEST_SHA:
        raise EntryError("FROZEN_MANIFEST_DRIFT")
    from rca.release import verify_frozen_release
    verification = verify_frozen_release(manifest_path, workspace_root=WORKSPACE, project_root=PROJECT)
    return contract, json.loads(manifest_path.read_text(encoding="utf-8")), verification


def prepare_conditions():
    """Return a copy of frozen scientific objects; no source/label enumeration."""
    contract, manifest, verification = _registered_context()
    scientific_keys = ("td", "dataset", "split", "exposure_ledger", "selections",
                       "r_control", "comparators", "evaluator", "packet",
                       "selection_policy", "final60_policy", "prohibited_runtime_rules")
    frozen = {key: copy.deepcopy(manifest[key]) for key in scientific_keys}
    conditions = {
        "schema": "TD13-G-PREPARED-CONDITIONS-v1", "execution_enabled": False,
        "planned_final_cases": 60, "planned_final_cells": 20,
        "scientific_objects": frozen,
        "matrix": [
            {"condition_id": "C1-PPR", "arms": ["L", "O", "R"], "draws_R": 256},
            {"condition_id": "C1-DIFFUSION", "arms": ["L", "O", "R"], "draws_R": 256},
            {"condition_id": "CONTEXTUAL", "methods": [x["id"] for x in manifest["comparators"]]},
            {"condition_id": "C5", "detectors": copy.deepcopy(manifest["selections"]["c5"]["detectors"])},
            {"condition_id": "INTEGRATED", "status": "REGISTERED_FOR_FUTURE_CAMPAIGN_ONLY",
             "reference_seconds": 300, "query_seconds": 60, "past_seconds": 360,
             "earlier_trigger": "INSUFFICIENT_HISTORY", "R_comparator_per_trigger": False},
        ],
        "td_protocol_registry": {
            "source": "LOCKED_TD_V1_3_SECTIONS_5_TO_10",
            "C1": {"reference_seconds": 300, "query_seconds": 300, "bin_seconds": 10,
                   "candidate_set": "TRACE_REFERENCE_UNION_QUERY", "logs_primary": False,
                   "channel_finite_bins_per_side": 24, "trace_reference_positive_required": True},
            "RCD": {"reference_seconds": 300, "query_seconds": 300, "seconds_per_side": 240,
                    "reference_iqr_positive": True, "imputation": "REFERENCE_MEDIAN_ONLY",
                    "metric_owner": "FIRST_RANKED_OWNER", "unknown_keys": "COVERAGE_ONLY",
                    "missing_candidates": "ONE_WORST_TIE", "failed_seed_metric": 0,
                    "headline": "MEAN_PER_SEED_METRIC"},
            "evaluation": {"primary": "TIE_AWARE_MRR", "planned_denominator": 60,
                           "secondary": ["HIT1", "HIT3", "HIT5", "NDCG5"],
                           "failure_or_root_absent": 0, "R_headline": "MEAN_PER_DRAW_METRIC"},
            "uncertainty": {"contrasts": ["O_MINUS_L", "O_MINUS_MEAN_R"], "replicates": 50000,
                            "block": "20_SCENARIO_CELLS_WITH_ALL_3_REPEATS_AND_ALL_ARMS",
                            "rng": "PCG64", "seed": 20260926, "quantile_type": 7,
                            "quantiles": [0.0125, 0.9875], "family_size": 2, "SESOI": 0.05,
                            "mandatory": ["ROOT_LEAVEOUT", "FAULT_LEAVEOUT", "CELL_SCATTER", "REPEAT_RANGES"],
                            "claim": "CONDITIONAL_NOT_POPULATION_CONFIDENCE"},
            "validity": {"shared_preprocessing_failure_fraction_gt": 0.1,
                         "signal_starvation_fraction_gte": 0.8,
                         "any_L_O_R_execution_or_numeric_failure": "ATTRIBUTION_INCONCLUSIVE",
                         "external_baseline_failure": "DOES_NOT_CHANGE_C1_VERDICT",
                         "mobility_distinct_draws_gte": 32, "median_retained_edges_lte": 0.8,
                         "strong_arrangement_case_fraction_gte": 0.8,
                         "strong_arrangement_each_root_stratum_fraction_gte": 0.5,
                         "case_exclusion_or_retuning": False},
            "cost": {"common_L_O_R_timeout_seconds": "max(300,10*max_successful_development_aggregate_case_walltime)",
                     "timeout_numeric_registration": "OPEN_BEFORE_CAMPAIGN",
                     "remaining_R_draws_after_timeout_metric": 0,
                     "separate": ["COLD_IO", "SHARED_PREPROCESSING", "CONTROL", "FIT", "PREDICTION"]},
            "C5_evaluation": {"macro_denominator": 60, "straddling_bin": "EXCLUDE_AND_COUNT",
                              "first_score_endpoint_seconds": 185, "first_trigger_endpoint_seconds": 195,
                              "trigger_at_tau": "PRE_INJECTION", "post_trigger": "STRICTLY_GREATER_THAN_TAU",
                              "normal_duration_denominators": ["OBSERVED", "FINITE_SCORED"],
                              "first_post_diagnosis_absent_or_failure_metric": 0},
            "deferred": ["C3_SCORED_OPERATION_ABLATION", "C4_PLACEMENT_COMPARISON", "EXTENSIONS_C2_H_I"],
        },
        "campaign_implementation": "NOT_IMPLEMENTED_IN_ENTRY_PHASE",
    }
    return {"conditions": conditions, "sha256": _digest(conditions),
            "frozen_release_checked_references": verification["checked_reference_count"],
            "permissions_sha256": _digest(contract["permissions"]),
            "source_snapshot_sha256": _digest(contract["source_test_snapshot_before_qualification"])}


def _numeric_fixture():
    rng = np.random.Generator(np.random.PCG64(20260930))
    values = rng.normal(size=(600, 3))
    values[300:, 1] += 2.0
    return np.ascontiguousarray(values, dtype="<f8")


def _worker_main():
    """Fixed subprocess seam. The caller cannot supply a producer callable."""
    import pandas as pd
    from rca.qualified_rcd import load_qualified_rcd
    from scripts.pre_g.controller_contract import run_registered_rcd_triplet, verify_rcd_seal
    message = json.loads(sys.stdin.read())
    if set(message) != {"values", "owners"} or message["owners"] != [0, 1, 2]:
        raise EntryError("NUMERIC_WORKER_PAYLOAD_REJECTED")
    values = np.asarray(message["values"], dtype="<f8")
    if values.shape != (600, 3) or not np.isfinite(values).all():
        raise EntryError("NUMERIC_WORKER_SHAPE_REJECTED")
    frame = pd.DataFrame(values, columns=["m0", "m1", "m2"])
    frame.insert(0, "time", np.arange(600, dtype=np.float64))
    # Upstream stdout/errors are never forwarded: they could disclose tokens.
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        runner = load_qualified_rcd(workspace_root=WORKSPACE, project_root=PROJECT,
                                    manifest_path=WORKSPACE / MANIFEST_REL)
        sealed = run_registered_rcd_triplet(
            frame, qualified_rcd=runner, candidate_ids=["S0", "S1", "S2"],
            metric_columns=["m0", "m1", "m2"], metric_owners={"m0": 0, "m1": 1, "m2": 2},
            input_sha256=hashlib.sha256(values.tobytes()).hexdigest())
        verify_rcd_seal(sealed)
    print(json.dumps({"schema": "ENTRY-NUMERIC-RCD-WORKER-v1", "sealed": sealed}, allow_nan=False))


def _execute_fixture():
    values = _numeric_fixture()
    interpreter = WORKSPACE / "environments/task-e/rcd39/Scripts/python.exe"
    env = {**os.environ, "PYTHONPATH": os.pathsep.join((str(WORKSPACE), str(WORKSPACE / "src"))),
           "PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
    try:
        completed = subprocess.run(
            [str(interpreter), "-B", str(Path(__file__).resolve()), "--rcd-fixture-worker"],
            input=_canonical({"values": values.tolist(), "owners": [0, 1, 2]}).decode("utf-8"),
            text=True, capture_output=True, cwd=WORKSPACE, env=env, timeout=300, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise EntryError("SYNTHETIC_WORKER_EXECUTION_" + type(exc).__name__) from None
    if completed.returncode != 0:
        raise EntryError("SYNTHETIC_WORKER_FAILED")
    try:
        result = json.loads(completed.stdout)
        sealed = result["sealed"]
        from scripts.pre_g.controller_contract import seal_synthetic_rcd_predictions
        # Validate the exact schema without falsely asserting parent-process
        # PRE-G issuance; durable G issuance belongs to this trusted subprocess.
        rebuilt = seal_synthetic_rcd_predictions(
            sealed["seed_outputs"], candidate_ids=["S0", "S1", "S2"],
            metric_columns=["m0", "m1", "m2"], metric_owners={"m0": 0, "m1": 1, "m2": 2},
            input_sha256=hashlib.sha256(values.tobytes()).hexdigest())
        if (set(result) != {"schema", "sealed"} or set(sealed) != set(rebuilt)
            or result["schema"] != "ENTRY-NUMERIC-RCD-WORKER-v1"
            or sealed["schema"] != rebuilt["schema"] or sealed["method"] != rebuilt["method"]
            or sealed["primary_bins"] != 5
            or sealed["qualification_scope"] != "QUALIFIED_CORE_RUN"
            or sealed["qualification_sha256"] != RCD_IDENTITY_SHA
            or sealed["prediction_sha256"] != _digest({k: v for k, v in sealed.items() if k != "prediction_sha256"})
            or any(sealed[key] != rebuilt[key] for key in ("input_sha256", "candidate_ids", "metric_columns", "metric_owners", "seed_outputs"))):
            raise EntryError("SYNTHETIC_WORKER_BINDING_FAILED")
    except (KeyError, ValueError, TypeError):
        raise EntryError("SYNTHETIC_WORKER_RESULT_REJECTED") from None
    return sealed


class EntryExecution:
    """Opaque execution token. Public construction has no issuance authority."""
    __slots__ = ()


def _bind_entry_execution():
    issued = {}

    def execute(admission_handle=None):
        prepared = prepare_conditions()
        contract, _, verification = _registered_context()
        admission = None
        if admission_handle is not None:
            from scripts.task_g.source_admission import require_issued_admission
            admission = require_issued_admission(admission_handle)
        sealed = _execute_fixture()
        planned = [{"condition_id": "RCD_SYNTHETIC", "kind": "RCD", "expected_items": 3}]
        outputs = [{"condition_id": "RCD_SYNTHETIC", "items": sealed["seed_outputs"]}]
        if admission is not None:
            rows = admission["case_audits"]
            if len(rows) != 60:
                raise EntryError("PLANNED_RAW_CASE_COMPLETENESS_FAILED")
            planned.append({"condition_id": "RAW_ADMISSION", "kind": "ADMISSION", "expected_items": 60})
            outputs.append({"condition_id": "RAW_ADMISSION", "items": rows})
        payload = {
            "scope": "ENTRY_RAW_ADMISSION" if admission is not None else "ENTRY_SYNTHETIC_DEVELOPMENT",
            "execution_kind": "ENTRY_ONLY", "trust_mode": "HOST_TRUSTED", "run_id": RUN_ID, "domain": DOMAIN,
            "planned_matrix": planned, "outputs": outputs,
            "source_snapshot_sha256": prepared["source_snapshot_sha256"],
            "permissions_sha256": prepared["permissions_sha256"],
            "config_sha256": prepared["sha256"], "prepared_conditions": prepared["conditions"],
            "final_condition_matrix_sha256": prepared["sha256"],
            "rcd_seal": sealed,
            "aggregate_report": {
                "status": "ENTRY_EXECUTED__FINAL_CAMPAIGN_CLOSED", "admission": admission,
                "frozen_release_checked_references": verification["checked_reference_count"],
                "synthetic_rcd_success_seeds": sum(r["status"] == "SUCCESS" for r in sealed["seed_outputs"]),
                "synthetic_rcd_failure_seeds": sum(r["status"] == "FAILURE" for r in sealed["seed_outputs"]),
                "final_predictions_executed": False, "final_labels_opened": False,
                "limitations": ["ENTRY_SCOPE_CANNOT_AUTHORIZE_FINAL_EVALUATOR", "TRUSTED_HOST_NOT_SANDBOX",
                                "F_ADAPTER_DEVELOPMENT_QUALIFICATION_UNCHANGED",
                                "FINAL_TAU_WINDOW_AND_EFFICACY_NOT_TESTED", "FIVE_REVIEWER_CERTIFICATION_OPEN"],
            },
        }
        token = EntryExecution()
        issued[token] = _canonical(payload)
        return token

    def payload_for_provenance(handle):
        if type(handle) is not EntryExecution or handle not in issued:
            raise EntryError("EXECUTION_NOT_ISSUED_BY_ENTRY_CONTROLLER")
        _registered_context()
        return json.loads(issued[handle])

    return execute, payload_for_provenance


_execute_entry, _entry_payload_for_provenance = _bind_entry_execution()
del _bind_entry_execution


def run_entry_fixture():
    return _execute_entry()


def run_entry_admission(admission_handle):
    return _execute_entry(admission_handle)


def run_campaign(*args, **kwargs):
    raise EntryError("FINAL_CAMPAIGN_NOT_AUTHORIZED_OR_IMPLEMENTED")


def evaluate_final(*args, **kwargs):
    raise EntryError("FINAL_LABELS_AND_EVALUATOR_CLOSED")


if __name__ == "__main__":
    try:
        if sys.argv[1:] != ["--rcd-fixture-worker"]:
            raise EntryError("ENTRY_WORKER_COMMAND_REQUIRED")
        _worker_main()
    except Exception:
        print("ENTRY_WORKER_FAILED", file=sys.stderr)
        raise SystemExit(1)
