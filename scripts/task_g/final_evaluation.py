"""Lazy, synthetic-only G32 truth bridge around unchanged frozen evaluators.

Truth is requested only after fresh disk/HMAC/completeness verification. Literal
root identities are mapped against each retained candidate universe, including
trigger-local universes. No alias, owner guess, GT repair or final label reader
exists. The locked planned60 statistics remain the unchanged G31 pure helpers.
"""
from __future__ import annotations

import math
from collections import defaultdict

from scripts.task_g import evaluation as frozen

EvaluationError = frozen.EvaluationError
METRICS = frozen.METRICS
SEEDS = frozen.SEEDS
DETECTORS = frozen.DETECTORS
score_service_vector = frozen.score_service_vector
rcd_seed_metrics = frozen.rcd_seed_metrics
random_control_metrics = frozen.random_control_metrics
signal_starved = frozen.signal_starved
paired_scenario_summary = frozen.paired_scenario_summary
primary_verdict = frozen.primary_verdict
c5_case_metrics = frozen.c5_case_metrics


def literal_root_index(candidate_ids, root_key):
    """Exact literal membership only; unknown roots remain absent."""
    if (type(candidate_ids) is not list or any(type(item) is not str or not item for item in candidate_ids)
            or len(set(candidate_ids)) != len(candidate_ids)
            or (root_key is not None and (type(root_key) is not str or not root_key))):
        raise EvaluationError("Literal evaluator identities are malformed")
    return candidate_ids.index(root_key) if root_key in candidate_ids else None


def map_synthetic_truth(cases, truth):
    """After seal, independently map every C1 and trigger-local root identity."""
    if (type(truth) is not dict or set(truth) != set(range(len(cases)))
            or [case.get("ordinal") for case in cases] != list(range(len(cases)))):
        raise EvaluationError("Artificial truth must preserve every bounded synthetic ordinal")
    mapped = {}
    for case in cases:
        row = truth[case["ordinal"]]
        if (type(row) is not dict or set(row) != {"root_key", "tau_relative"}
                or type(row["tau_relative"]) not in (int, float)
                or not math.isfinite(row["tau_relative"]) or row["tau_relative"] < 0):
            raise EvaluationError("Only exact artificial root/tau fields are accepted after seal")
        binding = case["scientific_diagnostics"]["controller_bindings"]
        root = literal_root_index(binding["candidate_ids"], row["root_key"])
        integrated = {}
        for detector in DETECTORS:
            integrated[detector] = {endpoint: literal_root_index(keys, row["root_key"])
                for endpoint, keys in binding["integrated_candidate_ids"][detector].items()}
        mapped[case["ordinal"]] = {"root_index": root, "tau_relative": float(row["tau_relative"]),
                                   "integrated_root_indices": integrated}
    return mapped


def cost_summary(cases):
    """Bounded G32 receipts: typed seconds, null coverage and intact metadata."""
    if type(cases) is not list or not cases or [row.get("ordinal") for row in cases] != list(range(len(cases))):
        raise EvaluationError("Cost denominator must preserve each planned bounded case")
    seconds, metadata = defaultdict(dict), defaultdict(dict)
    arms = {name: dict.fromkeys(("L", "O", "R")) for name in ("primary", "secondary")}
    families = {"arm_wall_seconds": arms, "arm_numeric_components_seconds": arms,
        "rank_seconds": {name: dict.fromkeys(("L", "O")) for name in ("primary", "secondary")},
        "R_rank_seconds": dict.fromkeys(("primary", "secondary"))}
    def duration(value, path, shape, ordinal):
        if shape is None:
            if value is None:
                seconds[path]
            else:
                seconds[path][ordinal] = frozen._number(value, minimum=0)
            return
        value = {} if value is None else value
        if type(value) is not dict:
            raise EvaluationError("Registered duration family requires typed components")
        for key, child in shape.items():
            duration(value.get(key), path + "." + key, child, ordinal)
        walk({key: item for key, item in value.items() if key not in shape}, path, ordinal)
    def walk(value, prefix, ordinal):
        if type(value) is not dict or any(type(key) is not str or not key for key in value):
            raise EvaluationError("Cost receipts require named components")
        for key, item in value.items():
            path = prefix + "." + key if prefix else key
            if key in families:
                duration(item, path, families[key], ordinal)
            elif key.endswith("_seconds"):
                duration(item, path, None, ordinal)
            elif type(item) is dict:
                walk(item, path, ordinal)
            else:
                metadata[path][ordinal] = type(item).__name__
    for row in cases:
        walk(row.get("costs"), "", row["ordinal"])
    count = len(cases)
    return {"planned_cases": count,
        "components": {path: {"unit": "seconds", "reported_cases": len(values),
            "missing_cases": count - len(values), "total": math.fsum(values.values()) if values else None,
            "maximum": max(values.values()) if values else None,
            "mean_over_reported": math.fsum(values.values()) / len(values) if values else None}
            for path, values in sorted(seconds.items())},
        "unaggregated": {path: {"reported_cases": len(values), "value_types": sorted(set(values.values()))}
            for path, values in sorted(metadata.items())},
        "interpretation": "Component durations can overlap; missing remains OPEN, no zero imputation."}


def evaluate_bounded_synthetic_payload(payload, truth):
    """Pure unqualified fixture metrics, with no campaign or population verdict."""
    from scripts.task_g.final_provenance import PHASE
    if (payload.get("phase") != PHASE or payload.get("scope") != "SYNTHETIC_BRIDGE_READINESS"
            or payload.get("source_summary", {}).get("source_kind") != "THREE_DISTINCT_ARTIFICIAL_ARCHIVES"):
        raise EvaluationError("Bounded helper accepts declared synthetic bridge fixtures only")
    cases = payload.get("cases")
    if type(cases) is not list or not 1 <= len(cases) <= 3:
        raise EvaluationError("Bounded numerical qualification uses one to three synthetic cases")
    labels = map_synthetic_truth(cases, truth)
    results = []
    for case in cases:
        label = labels[case["ordinal"]]
        root, count = label["root_index"], case["candidate_count"]
        ranking = {}
        for name in ("primary", "secondary"):
            arms = case["c1"][name]
            ranking[name] = {arm: frozen._score_record(arms[arm], root, count) for arm in ("L", "O")}
            ranking[name]["R"] = random_control_metrics(arms["R"], count, root)
        contextual = {name: frozen._score_record(case["contextual"][name], root, count)
            for name in ("Local-MAX-MT", "BARO-RANK-adapted-TD12")}
        rcd = case["contextual"]["RCD"]
        if rcd["n_services"] != count:
            raise EvaluationError("RCD cannot replace the common candidate universe")
        contextual["RCD"] = rcd_seed_metrics(rcd["seed_outputs"], rcd["metric_owners"], count, root)
        detectors = {name: c5_case_metrics(case["c5"][name], label["tau_relative"],
            trigger_root_indices=label["integrated_root_indices"][name]) for name in DETECTORS}
        results.append({"ordinal": case["ordinal"], "root_in_candidate": root is not None,
            "ranking": ranking, "contextual": contextual, "c5": detectors})
    return {"schema": "TD13-G32-SYNTHETIC-BRIDGE-EVALUATION-v1",
        "evidence_scope": "BOUNDED_SYNTHETIC_BRIDGE_ONLY__NOT_FINAL_EFFICACY",
        "planned_cases": len(cases), "case_metrics": results,
        "costs": [case["costs"] for case in cases], "cost_summary": cost_summary(cases),
        "final_prediction_qualified": False,
        "scientific_verdict": "NOT_APPLICABLE_BOUNDED_SYNTHETIC_QUALIFICATION",
        "limitations": ["Synthetic cases are boundary fixtures, not independent benchmark incidents.",
            "Historical exposure, five-reviewer assurance and FlashTicket validation remain unchanged."]}


def evaluate_readiness(lazy_artificial_truth):
    from scripts.task_g.final_provenance import PHASE, require_verified_readiness_execution
    payload = require_verified_readiness_execution()
    context = payload.get("_verified_context", {})
    permissions = context.get("permissions", {})
    if (payload.get("phase") != PHASE or payload.get("scope") != "SYNTHETIC_BRIDGE_READINESS"
            or payload.get("source_summary", {}).get("source_kind") != "THREE_DISTINCT_ARTIFICIAL_ARCHIVES"
            or context.get("final_prediction_qualified") is not False
            or permissions.get("synthetic_evaluation") is not True
            or any(permissions.get(key) is not False for key in (*frozen._FINAL_PERMISSIONS, "final_root_fault"))):
        raise EvaluationError("G32 readiness cannot open actual final truth")
    if not callable(lazy_artificial_truth):
        raise EvaluationError("A lazy artificial truth callback is required")
    cases = payload.get("cases")
    if (type(cases) is not list or not 1 <= len(cases) <= 3
            or payload.get("planned_case_count") != len(cases)
            or [case.get("ordinal") for case in cases] != list(range(len(cases)))):
        raise EvaluationError("Complete bounded issued cases required before artificial truth")
    for case in cases:
        bindings = case.get("scientific_diagnostics", {}).get("controller_bindings", {})
        keys = bindings.get("candidate_ids")
        literal_root_index(keys, None)
        if len(keys) != case.get("candidate_count"):
            raise EvaluationError("Common candidate universe incomplete before artificial truth")
        mapping = bindings.get("integrated_candidate_ids")
        if type(mapping) is not dict or set(mapping) != set(DETECTORS):
            raise EvaluationError("Trigger-local candidate universes incomplete before artificial truth")
        for detector in DETECTORS:
            triggers = case.get("c5", {}).get(detector, {}).get("triggers")
            if type(triggers) is not list or type(mapping[detector]) is not dict:
                raise EvaluationError("Trigger history incomplete before artificial truth")
            if set(mapping[detector]) != {str(row["endpoint"]) for row in triggers}:
                raise EvaluationError("Trigger-local universes stale before artificial truth")
            for row in triggers:
                universe = mapping[detector][str(row["endpoint"])]
                literal_root_index(universe, None)
                if len(universe) != row.get("candidate_count"):
                    raise EvaluationError("Trigger-local universe length differs before artificial truth")
    result = evaluate_bounded_synthetic_payload(payload, lazy_artificial_truth())
    result["verified_receipt_sha256"] = context["receipt_sha256"]
    result["durable_verification_before_truth_callback"] = True
    return result


def evaluate_numeric_fixture_payload(payload, labels):
    """Exact locked60 evaluator, explicitly pure synthetic-only orchestration."""
    if payload.get("scope") != "SYNTHETIC_ONLY_ORCHESTRATION":
        raise EvaluationError("Pure orchestration fixtures must be explicitly synthetic-only")
    result = frozen.evaluate_numeric_fixture_payload(payload, labels)
    result["schema"] = "TD13-G32-SYNTHETIC-ONLY-ORCHESTRATION-EVALUATION-v1"
    result["evidence_scope"] = "SYNTHETIC_ONLY_ORCHESTRATION__NO_NUMERIC_COMPUTATIONS__NOT_FINAL_EFFICACY"
    result["final_prediction_qualified"] = False
    return result


def evaluate_final(*args, **kwargs):
    raise EvaluationError("Actual final truth/campaign remains closed; readiness cannot grant permission")


__all__ = ["EvaluationError", "literal_root_index", "map_synthetic_truth", "cost_summary",
    "score_service_vector", "rcd_seed_metrics", "random_control_metrics", "signal_starved",
    "paired_scenario_summary", "primary_verdict", "c5_case_metrics",
    "evaluate_bounded_synthetic_payload", "evaluate_numeric_fixture_payload", "evaluate_readiness", "evaluate_final"]
