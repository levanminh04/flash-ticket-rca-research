"""TD-v1.3 numeric evaluation and sealed SYNTHETIC G31 readiness checks.

No oracle file, telemetry file, model worker or network is opened here. Pure
functions compute descriptive metrics; they do not confer producer provenance.
The readiness entry point reopens and verifies the fixed durable receipt before
calling an artificial label provider. Actual final evaluation remains closed.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict

import numpy as np

from scripts.task_e.calibration import (
    event_diagnostics,
    first_trigger_composition,
    mean_planned_draw_metrics,
    planned_regime_summary,
    regime_metrics,
)
from scripts.task_e.evaluator import service_scores_from_metric_ranks, tie_metrics
from rca.detection import create_event_state, event_step


METRICS = ("rr", "hit1", "hit3", "hit5", "ndcg5")
SEEDS = (420, 421, 422)
DETECTORS = ("G-MTL", "L-MTL", "ALL-MTL", "TV-MTL", "G-MT", "L-MT", "ALL-MT", "TV-MT")
BOOTSTRAP_DRAWS = 50_000
BOOTSTRAP_SEED = 20260926
DELTA = 0.05
_FAILURES = ("FAILURE", "METHOD_FAILURE", "UNAVAILABLE", "INPUT_UNAVAILABLE", "TIMEOUT")
_FINAL_PERMISSIONS = ("final_labels", "final_tau_metadata", "final_answers", "final_outcomes", "final_predictions", "final_campaign")
_SHA = re.compile(r"[0-9a-f]{64}\Z")


class EvaluationError(ValueError):
    """A numeric contract or evaluation authorization is not satisfied."""


def _integer(value, *, minimum=0):
    if type(value) is not int or value < minimum:
        raise EvaluationError("Expected a bounded integer")
    return value


def _number(value, *, minimum=None, maximum=None):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise EvaluationError("Expected a finite numeric value")
    value = float(value)
    if not math.isfinite(value) or (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
        raise EvaluationError("Numeric value is outside its contract")
    return value


def _vector(scores, candidate_count):
    _integer(candidate_count)
    if not isinstance(scores, (list, tuple, np.ndarray)):
        raise EvaluationError("Scores must be a numeric vector")
    if isinstance(scores, np.ndarray) and scores.ndim != 1:
        raise EvaluationError("Scores must be one dimensional")
    values = [_number(value) for value in scores]
    if len(values) != candidate_count:
        raise EvaluationError("Every candidate needs exactly one score")
    return np.asarray(values, dtype=np.float64)


def _root(root_index, candidate_count):
    if root_index is not None and (type(root_index) is not int or not 0 <= root_index < candidate_count):
        raise EvaluationError("Use None for an absent root; never repair candidate visibility")


def score_service_vector(scores, root_index, *, candidate_count=None, failed=False):
    """Validate numerics before absent-root shortcuts; failures explicitly score0."""
    if type(failed) is not bool:
        raise EvaluationError("Failure must be explicit")
    if candidate_count is None:
        if not isinstance(scores, (list, tuple, np.ndarray)):
            raise EvaluationError("Candidate count is required for an absent failure vector")
        candidate_count = len(scores)
    _integer(candidate_count)
    _root(root_index, candidate_count)
    if failed and scores is None:
        values = np.zeros(candidate_count)
    else:
        values = _vector(scores, candidate_count)
    return tie_metrics(values, root_index, failed=failed)


def _score_record(record, root_index, candidate_count):
    if type(record) is not dict or record.get("status") not in ("SUCCESS", *_FAILURES):
        raise EvaluationError("Every ranking needs a success or explicit failure record")
    return score_service_vector(record.get("scores"), root_index, candidate_count=candidate_count,
                                failed=record["status"] != "SUCCESS")


def rcd_seed_metrics(seed_outputs, metric_owners, n_services, root_index):
    """First owning-service occurrence, unknown-key counts, one worst tie.

    All three registered per-seed metrics enter the mean, including failed0.
    Output coverage is aggregate; unknown metric strings are not published.
    """
    _integer(n_services)
    _root(root_index, n_services)
    if type(metric_owners) is not dict or any(type(key) is not str or not key or type(owner) is not int or not 0 <= owner < n_services for key, owner in metric_owners.items()):
        raise EvaluationError("RCD owners must be exact admitted numeric service indices")
    if type(seed_outputs) is not list or len(seed_outputs) != 3:
        raise EvaluationError("RCD requires exactly three planned seeds")
    per_seed = []
    for seed, row in zip(SEEDS, seed_outputs):
        if type(row) is not dict or type(row.get("seed")) is not int or row["seed"] != seed or type(row.get("bins")) is not int or row["bins"] != 5 or row.get("status") not in ("SUCCESS", "FAILURE"):
            raise EvaluationError("RCD seed order, bins or output status changed")
        failed = row["status"] == "FAILURE"
        if failed:
            if row.get("ranks") is not None:
                raise EvaluationError("Failed seeds cannot carry a successful ranking")
            scores, unknown, ranked = np.zeros(n_services), 0, 0
        else:
            ranks = row.get("ranks")
            if type(ranks) is not list or any(type(key) is not str or not key for key in ranks) or len(set(ranks)) != len(ranks):
                raise EvaluationError("RCD ranking is malformed or duplicate")
            scores, mapping = service_scores_from_metric_ranks(ranks, metric_owners, n_services)
            unknown, ranked = len(mapping["unknown_metric_keys"]), mapping["ranked_services"]
        metrics = score_service_vector(scores, root_index, candidate_count=n_services, failed=failed)
        per_seed.append({"seed": seed, "status": row["status"], "metrics": metrics,
                         "unknown_key_count": unknown, "ranked_services": ranked,
                         "worst_tie_services": n_services - ranked})
    return {"per_seed": per_seed, "mean": {name: math.fsum(row["metrics"][name] for row in per_seed) / 3 for name in METRICS},
            "planned_seeds": 3, "failed_seeds": sum(row["status"] == "FAILURE" for row in per_seed),
            "unknown_key_count": sum(row["unknown_key_count"] for row in per_seed),
            "aggregation": "mean of three per-seed metrics; failed seeds0"}


def random_control_metrics(draws, candidate_count, root_index):
    """Exactly256 planned per-draw metrics, failures0 and conditional MCSD/SE."""
    if type(draws) is not list or len(draws) != 256:
        raise EvaluationError("Every one of the256 draws must be retained")
    outcomes = {}
    per_draw = []
    hashes, overlap = [], []
    for index, row in enumerate(draws):
        if type(row) is not dict or type(row.get("draw")) is not int or row["draw"] != index:
            raise EvaluationError("Duplicate, missing or reordered control draw")
        metric = _score_record(row, root_index, candidate_count)
        failed = row["status"] != "SUCCESS"
        outcomes[index] = None if failed else metric
        per_draw.append({"draw": index, "status": row["status"], "metrics": metric})
        digest = row.get("graph_sha256")
        retained = row.get("retained_edge_fraction")
        if failed and digest is None and retained is None:
            # A generation timeout/failure has no realized graph. Preserve its
            # metric0 and denominator slot without inventing a graph or overlap.
            continue
        if type(digest) is not str or _SHA.fullmatch(digest) is None:
            raise EvaluationError("Every realized control graph needs its exact digest")
        hashes.append(digest)
        overlap.append(_number(retained, minimum=0, maximum=1))
    summary = mean_planned_draw_metrics(outcomes, planned_draws=256)
    distinct, retained = len(set(hashes)), float(np.median(overlap)) if overlap else None
    return {**summary, "per_draw": per_draw, "distinct_final_graphs": distinct,
            "generated_graphs": len(hashes), "unmaterialized_graphs": 256 - len(hashes),
            "median_retained_edge_fraction": retained, "mobile": distinct >= 32 and retained is not None and retained <= .8}


def signal_starved(local_evidence, candidate_count):
    values = _vector(local_evidence, candidate_count)
    if (values < 0).any():
        raise EvaluationError("Local evidence must be nonnegative")
    if not len(values) or values.max() == 0:
        return True
    normalized = [round(float(value), 12) for value in values / values.max()]
    return len(set(normalized)) == 1


def _planned60(rows):
    if type(rows) is not list or len(rows) != 60:
        raise EvaluationError("Headline evaluation retains exactly60 planned incidents")
    if any(type(row) is not dict or type(row.get("ordinal")) is not int for row in rows) or [row.get("ordinal") for row in rows] != list(range(60)):
        raise EvaluationError("Planned ordinals must be unique, complete and canonical")
    cells = defaultdict(list)
    for row in rows:
        cell, repeat = _integer(row.get("cell_ordinal")), _integer(row.get("repeat"))
        if cell >= 20 or repeat >= 3:
            raise EvaluationError("Wrong20-cell/three-repeat matrix")
        cells[cell].append(row)
    if set(cells) != set(range(20)) or any(sorted(row["repeat"] for row in items) != [0, 1, 2] for items in cells.values()):
        raise EvaluationError("All three repeats of each of20 cells are required")
    return cells


def paired_scenario_summary(rows):
    """Locked RE2 paired20-cell bootstrap and evaluator-side leaveouts.

    Each row has L/O/R scalar RR, ordinal/cell/repeat and evaluator-only
    root_stratum/fault_stratum. No outcome-guided dropping or weighting occurs.
    """
    cells = _planned60(rows)
    roots = {row.get("root_stratum") for row in rows}
    faults = {row.get("fault_stratum") for row in rows}
    if any(type(value) is not str or not value for value in (*roots, *faults)) or len(roots) != 5 or len(faults) != 6:
        raise EvaluationError("Evaluator requires all five root and six fault strata")
    identities = []
    for cell in range(20):
        pairs = {(row["root_stratum"], row["fault_stratum"]) for row in cells[cell]}
        if len(pairs) != 1:
            raise EvaluationError("Repeats must stay within their planned scenario cell")
        identities.extend(pairs)
    if len(set(identities)) != 20:
        raise EvaluationError("Scenario cells may not be duplicated or relabeled")
    values = np.array([[_number(row[arm], minimum=0, maximum=1) for arm in ("L", "O", "R")] for row in rows])
    differences = np.column_stack((values[:, 1] - values[:, 0], values[:, 1] - values[:, 2]))
    cell_differences = np.array([differences[[row["ordinal"] for row in cells[cell]]].mean(axis=0) for cell in range(20)])
    rng = np.random.Generator(np.random.PCG64(BOOTSTRAP_SEED))
    samples = rng.integers(0, 20, size=(BOOTSTRAP_DRAWS, 20))
    bootstrap = cell_differences[samples].mean(axis=1)
    limits = np.quantile(bootstrap, [.0125, .9875], axis=0, method="linear")
    contrasts = {}
    for index, contrast in enumerate(("delta_L", "delta_R")):
        leaveouts = {}
        for name, labels in (("root", sorted(roots)), ("fault", sorted(faults))):
            leaveouts[name] = [{"excluded_stratum": label,
                "planned_remaining_cases": sum(row[name + "_stratum"] != label for row in rows),
                "effect": float(differences[[row[name + "_stratum"] != label for row in rows], index].mean())}
                for label in labels]
        deletion_effects = [item["effect"] for records in leaveouts.values() for item in records]
        repeats = [{"repeat": repeat, "effect": float(differences[[row["repeat"] == repeat for row in rows], index].mean())} for repeat in range(3)]
        scatter = []
        for cell in range(20):
            incident = differences[[row["ordinal"] for row in cells[cell]], index]
            scatter.append({"cell_ordinal": cell, "mean": float(incident.mean()), "repeat_min": float(incident.min()), "repeat_max": float(incident.max())})
        contrasts[contrast] = {"point": float(differences[:, index].mean()), "lower": float(limits[0, index]), "upper": float(limits[1, index]),
            "leaveouts": leaveouts, "all_deletion_effects_positive": all(value > 0 for value in deletion_effects),
            "deletion_effect_min": min(deletion_effects), "deletion_effect_max": max(deletion_effects),
            "deletion_delta_crossing": min(deletion_effects) <= DELTA < max(deletion_effects),
            "scenario_scatter": scatter, "repeat_effects": repeats,
            "repeat_effect_range": [min(item["effect"] for item in repeats), max(item["effect"] for item in repeats)]}
    return {"planned_cases": 60, "planned_cells": 20, "repeats_per_cell": 3,
            "headline": {arm: float(values[:, index].mean()) for index, arm in enumerate(("L", "O", "R"))},
            "contrasts": contrasts, "bootstrap": {"draws": BOOTSTRAP_DRAWS, "seed": BOOTSTRAP_SEED,
                "generator": "PCG64", "unit": "paired scenario blocks with all three repeats/all arms", "quantiles": [.0125, .9875], "quantile_method": "type7/linear",
                "family_size": 2, "each_interval_level": .975, "nominal_simultaneous_level": .95},
            "interpretation": "conditional benchmark uncertainty; not population significance or independent campaigns"}


def primary_verdict(summary, *, shared_preprocessing_failures, starved_cases, arm_failures, mobility_by_root, invalidity_reasons=()):
    """TD9 order; external-baseline outcomes deliberately do not enter this gate."""
    for count in (shared_preprocessing_failures, starved_cases, arm_failures):
        _integer(count)
    if shared_preprocessing_failures > 60 or starved_cases > 60:
        raise EvaluationError("Quality counts exceed the planned denominator")
    if type(mobility_by_root) is not dict or len(mobility_by_root) != 5:
        raise EvaluationError("Mobility requires all evaluator root strata")
    mobile, planned = 0, 0
    for record in mobility_by_root.values():
        total, good = _integer(record.get("planned"), minimum=1), _integer(record.get("mobile"))
        if good > total:
            raise EvaluationError("Invalid mobility coverage")
        mobile += good
        planned += total
    if planned != 60:
        raise EvaluationError("Mobility may not shrink the planned sample")
    for name in ("delta_L", "delta_R"):
        contrast = summary["contrasts"][name]
        lower = _number(contrast["lower"], minimum=-1, maximum=1)
        upper = _number(contrast["upper"], minimum=-1, maximum=1)
        if lower > upper or type(contrast["all_deletion_effects_positive"]) is not bool:
            raise EvaluationError("Invalid conditional interval or deletion diagnostics")
    reasons = list(invalidity_reasons)
    if any(type(reason) is not str or not reason for reason in reasons):
        raise EvaluationError("Invalidity reasons must be explicit")
    if reasons:
        verdict = "INVALID"
    else:
        if shared_preprocessing_failures > 6:
            reasons.append("SHARED_PREPROCESSING_FAILURE_ABOVE_10_PERCENT")
        if starved_cases >= 48:
            reasons.append("SIGNAL_STARVATION_AT_LEAST_80_PERCENT")
        if arm_failures:
            reasons.append("L_O_R_ARM_EXECUTION_OR_NUMERICAL_FAILURE")
        if mobile < 48 or any(record["mobile"] * 2 < record["planned"] for record in mobility_by_root.values()):
            reasons.append("INSUFFICIENT_CONTROL_MOBILITY")
        contrasts = summary["contrasts"]
        if reasons:
            verdict = "INCONCLUSIVE"
        elif all(contrasts[name]["lower"] > DELTA and contrasts[name]["all_deletion_effects_positive"] for name in ("delta_L", "delta_R")):
            verdict = "BOUNDED_SUPPORT"
        elif any(contrasts[name]["upper"] < DELTA for name in ("delta_L", "delta_R")):
            verdict = "BOUNDED_NEGATIVE_FOR_FROZEN_PRIMARY"
        else:
            verdict = "INCONCLUSIVE"
            reasons.append("INTERVAL_OR_DELETION_STABILITY_DOES_NOT_SUPPORT_CONJUNCTION")
    return {"verdict": verdict, "reasons": reasons, "delta": DELTA,
            "shared_preprocessing_failures": shared_preprocessing_failures, "starved_cases": starved_cases,
            "arm_failures": arm_failures, "mobile_cases": mobile, "mobility_by_root": mobility_by_root,
            "candidate_visibility_limit": "absent roots score0; no graph utility inference where the target was unavailable",
            "scope": "frozen primary benchmark only; no equivalence or all-graph claim"}


def c5_case_metrics(record, tau_relative, *, trigger_root_indices=None):
    """Raw-bin regime metrics and first post-injection composed diagnosis."""
    tau = _number(tau_relative, minimum=0)
    if type(record) is not dict or record.get("status") not in ("SUCCESS", *_FAILURES):
        raise EvaluationError("Every planned detector needs an explicit status")
    threshold = _number(record.get("threshold"), minimum=0)
    starts, ends, scores = record.get("starts"), record.get("ends"), record.get("scores")
    if type(starts) is not list or type(ends) is not list or type(scores) is not list or len(starts) != len(ends) or len(starts) != len(scores):
        raise EvaluationError("Every planned C5 bin must be retained")
    expected = list(range(185, 185 + 5 * len(ends), 5))
    if ends != expected or starts != [endpoint - 5 for endpoint in expected] or any(type(value) is not int for value in (*starts, *ends)):
        raise EvaluationError("C5 primary grid starts185s and includes every consecutive5s bin")
    values = [np.nan if value is None else _number(value, minimum=0) for value in scores]
    bin_statuses = record.get("bin_statuses")
    if bin_statuses is not None:
        if type(bin_statuses) is not list or len(bin_statuses) != len(values) or any(status not in ("SUCCESS", *_FAILURES) for status in bin_statuses):
            raise EvaluationError("Incomplete C5 bin-status coverage")
        if any((status == "SUCCESS") != math.isfinite(value) for status, value in zip(bin_statuses, values)):
            raise EvaluationError("C5 unavailable/failure bins cannot be called healthy scored bins")
    raw_case = {"starts": starts, "ends": ends, "scores": values, "tau": tau, "warmup_end": 180., "failed": False}
    event_state = create_event_state(threshold, bin_seconds=5, streak=3, refractory_seconds=300)
    expected_triggers = [endpoint for value, endpoint in zip(values, ends) if event_step(event_state, value, endpoint)["trigger"]]
    triggers = record.get("triggers")
    if type(triggers) is not list or [item.get("endpoint") for item in triggers] != expected_triggers:
        raise EvaluationError("Trigger history differs from frozen strict/persistence/refractory policy")
    failed = record["status"] in ("FAILURE", "METHOD_FAILURE", "TIMEOUT")
    unavailable = record["status"] in ("UNAVAILABLE", "INPUT_UNAVAILABLE")
    if unavailable and any(math.isfinite(value) for value in values):
        raise EvaluationError("Whole-source unavailability cannot carry successful scored bins")
    bins = regime_metrics({**raw_case, "failed": failed}, threshold)
    bins["unavailable_case"] = unavailable or (bins["no_scorable_bins"] and not failed)
    bins["failed_bins"] = sum(status in ("FAILURE", "METHOD_FAILURE", "TIMEOUT") for status in (bin_statuses or []))
    events = event_diagnostics(expected_triggers, raw_case)
    if failed:
        events.update(scored_normal_hours=0., rate_per_scored_normal_hour=None)
    trigger_root_indices = {} if trigger_root_indices is None else trigger_root_indices
    if type(trigger_root_indices) is not dict:
        raise EvaluationError("Integrated roots are evaluator-side per-trigger indices")
    composed = []
    for item in triggers:
        endpoint = _integer(item["endpoint"])
        status = item.get("status")
        if endpoint < 360:
            if status != "INSUFFICIENT_HISTORY":
                raise EvaluationError("Early triggers require explicit insufficient history")
            metric = score_service_vector(None, None, candidate_count=0, failed=True)
        else:
            if status not in ("SUCCESS", *_FAILURES):
                raise EvaluationError("Integrated diagnosis needs an explicit output/failure")
            count = _integer(item.get("candidate_count"))
            if status == "SUCCESS":
                if str(endpoint) not in trigger_root_indices and endpoint not in trigger_root_indices:
                    raise EvaluationError("Do not guess a root in a trigger-specific candidate universe")
                root = trigger_root_indices.get(str(endpoint), trigger_root_indices.get(endpoint))
            else:
                root = None
            metric = _score_record(item, root, count)
        composed.append({"endpoint": endpoint, "status": "VALID" if status == "SUCCESS" and not failed else status if not failed else "METHOD_FAILURE", "metrics": metric})
    composition = first_trigger_composition(composed, tau)
    return {"regime": bins, "events": events, "composition": composition,
            "diagnostic_triggers": composed, "threshold": threshold,
            "interpretation": "archival injection-regime proxy; not onset truth, node-F1 or operationalFPR"}


def _label_rows(labels, cases):
    if type(labels) is not dict or set(labels) != set(range(60)):
        raise EvaluationError("The artificial evaluator provider must retain all60 ordinals")
    rows = []
    for case in cases:
        label = labels[case["ordinal"]]
        if type(label) is not dict:
            raise EvaluationError("Malformed artificial evaluator label")
        _root(label.get("root_index"), case["candidate_count"])
        _number(label.get("tau_relative"), minimum=0)
        rows.append(label)
    return rows


def _cost_summary(cases):
    """Aggregate declared seconds; preserve metadata and missing timing coverage."""
    _planned60(cases)
    fields, metadata = defaultdict(dict), defaultdict(dict)
    arm_shape = {name: dict.fromkeys(("L", "O", "R")) for name in ("primary", "secondary")}
    duration_families = {
        "arm_wall_seconds": arm_shape,
        "arm_numeric_components_seconds": arm_shape,
        "rank_seconds": {name: dict.fromkeys(("L", "O")) for name in ("primary", "secondary")},
        "R_rank_seconds": dict.fromkeys(("primary", "secondary")),
    }

    def named_keys(value):
        if type(value) is not dict or any(type(key) is not str or not key for key in value):
            raise EvaluationError("Cost receipts require named components")

    def duration(value, path, shape, ordinal):
        if shape is None:
            values = fields[path]
            if value is not None:
                if ordinal in values:
                    raise EvaluationError("Duplicate cost component path")
                values[ordinal] = _number(value, minimum=0)
            return
        value = {} if value is None else value
        named_keys(value)
        for key, child_shape in shape.items():
            duration(value.get(key), path + "." + key, child_shape, ordinal)
        # Future unregistered fields retain their own units or metadata. They
        # never inherit seconds merely from a containing duration-family name.
        walk({key: item for key, item in value.items() if key not in shape}, path, ordinal)

    def walk(value, prefix, ordinal):
        named_keys(value)
        for key, item in value.items():
            path = key if not prefix else prefix + "." + key
            if key in duration_families:
                duration(item, path, duration_families[key], ordinal)
            elif key.endswith("_seconds"):
                duration(item, path, None, ordinal)
            elif type(item) is dict and item:
                walk(item, path, ordinal)
            else:
                if ordinal in metadata[path]:
                    raise EvaluationError("Duplicate cost metadata path")
                metadata[path][ordinal] = type(item).__name__
    reported = 0
    for case in cases:
        costs = case.get("costs", {})
        walk(costs, "", case["ordinal"])
        reported += bool(costs)
    return {"planned_cases": 60, "reported_cost_receipt_cases": reported, "missing_cost_receipt_cases": 60 - reported,
            "components": {name: {"unit": "seconds", "reported_cases": len(values), "missing_cases": 60 - len(values),
                "total": math.fsum(values.values()) if values else None,
                "maximum": max(values.values()) if values else None,
                "mean_over_reported": math.fsum(values.values()) / len(values) if values else None} for name, values in sorted(fields.items())},
            "unaggregated": {name: {"reported_cases": len(values), "missing_cases": 60 - len(values),
                "value_types": sorted(set(values.values()))} for name, values in sorted(metadata.items())},
            "interpretation": "declared seconds only; metadata retained in original costs; absent timings remain OPEN and are not imputed0; component totals may overlap and are not summed into a case walltime"}


def evaluate_numeric_fixture_payload(payload, labels):
    """Pure unqualified numeric fixture aggregation; never a final receipt API."""
    cases = payload.get("cases")
    _planned60(cases)
    label_rows = _label_rows(labels, cases)
    prepared = payload["prepared_conditions"]
    thresholds = {item["id"]: item["threshold"] for item in prepared["scientific_objects"]["selections"]["c5"]["detectors"]}
    if set(thresholds) != set(DETECTORS):
        raise EvaluationError("All eight frozen C5 thresholds are mandatory")
    statistics, case_metrics = {"primary": [], "secondary": []}, []
    contextual = {"Local-MAX-MT": [], "BARO-RANK-adapted-TD12": [], "RCD": []}
    c5 = {name: {} for name in DETECTORS}
    mobility = defaultdict(lambda: {"planned": 0, "mobile": 0})
    shared, starved, arm_failures = 0, 0, 0
    for case, label in zip(cases, label_rows):
        count, root = _integer(case.get("candidate_count")), label["root_index"]
        if type(case.get("shared_preprocessing_failed")) is not bool:
            raise EvaluationError("Shared preprocessing failure must be explicit")
        shared += case["shared_preprocessing_failed"]
        starved += signal_starved(case["local_evidence"], count)
        outcome = {"ordinal": case["ordinal"], "root_in_candidate": root is not None, "ranking": {}}
        for operator in ("primary", "secondary"):
            condition = case["c1"][operator]
            local, observed = (_score_record(condition[arm], root, count) for arm in ("L", "O"))
            controls = random_control_metrics(condition["R"], count, root)
            outcome["ranking"][operator] = {"L": local, "O": observed, "R": controls}
            arm_failures += sum(condition[arm]["status"] != "SUCCESS" for arm in ("L", "O")) + controls["failed_draws"]
            statistics[operator].append({"ordinal": case["ordinal"], "cell_ordinal": case["cell_ordinal"], "repeat": case["repeat"],
                "root_stratum": label.get("root_stratum"), "fault_stratum": label.get("fault_stratum"),
                "L": local["rr"], "O": observed["rr"], "R": controls["metrics"]["rr"]})
        # Both frozen operators use the same realized undirected graphs.
        first, second = (case["c1"][operator]["R"] for operator in ("primary", "secondary"))
        if any(left["graph_sha256"] != right["graph_sha256"] or left.get("seed") != right.get("seed") for left, right in zip(first, second)):
            raise EvaluationError("Secondary must use the same realized registered control graphs")
        bucket = mobility[label["root_stratum"]]
        bucket["planned"] += 1
        bucket["mobile"] += outcome["ranking"]["primary"]["R"]["mobile"]
        for name in ("Local-MAX-MT", "BARO-RANK-adapted-TD12"):
            metric = _score_record(case["contextual"][name], root, count)
            contextual[name].append(metric)
        rcd = case["contextual"]["RCD"]
        if rcd["n_services"] != count:
            raise EvaluationError("RCD may not repair or replace the common candidate universe")
        contextual["RCD"].append(rcd_seed_metrics(rcd["seed_outputs"], rcd["metric_owners"], count, root))
        if set(case["c5"]) != set(DETECTORS):
            raise EvaluationError("A planned detector may not be silently excluded")
        for name in DETECTORS:
            record = case["c5"][name]
            if record["threshold"] != thresholds[name]:
                raise EvaluationError("Final or fixture tails cannot refit frozen thresholds")
            root_map = label.get("integrated_root_indices", {}).get(name, {})
            c5[name][case["ordinal"]] = c5_case_metrics(record, label["tau_relative"], trigger_root_indices=root_map)
        case_metrics.append(outcome)
    summaries = {operator: paired_scenario_summary(rows) for operator, rows in statistics.items()}
    for operator in ("primary", "secondary"):
        summaries[operator]["metrics"] = {arm: {metric: math.fsum(
            item["ranking"][operator][arm]["metrics"][metric] if arm == "R" else item["ranking"][operator][arm][metric]
            for item in case_metrics) / 60 for metric in METRICS} for arm in ("L", "O", "R")}
        summaries[operator]["candidate_absent_cases"] = sum(not item["root_in_candidate"] for item in case_metrics)
    verdict = primary_verdict(summaries["primary"], shared_preprocessing_failures=shared, starved_cases=starved,
                              arm_failures=arm_failures, mobility_by_root=dict(mobility), invalidity_reasons=payload.get("invalidity_reasons", ()))
    detector_summaries = {}
    for name in DETECTORS:
        records = c5[name]
        summary = planned_regime_summary({ordinal: item["regime"] for ordinal, item in records.items()}, tuple(range(60)))
        events = [item["events"] for item in records.values()]
        observed = math.fsum(item["observed_normal_hours"] for item in events)
        scored = math.fsum(item["scored_normal_hours"] for item in events)
        pre = sum(item["pre_injection_triggers"] for item in events)
        detector_summaries[name] = {**summary, "threshold": thresholds[name],
            "unavailable_cases": sum(item["regime"]["unavailable_case"] for item in records.values()),
            "failed_bins": sum(item["regime"]["failed_bins"] for item in records.values()),
            "normal_observed_seconds": observed * 3600, "normal_scored_seconds": scored * 3600,
            "pre_injection_triggers": pre, "rate_per_observed_normal_hour": pre / observed if observed else None,
            "rate_per_scored_normal_hour": pre / scored if scored else None,
            "both_regime_scored_cases": sum(item["regime"]["normal_scored"] > 0 and item["regime"]["positive_scored"] > 0 for item in records.values()),
            "first_post_injection_censored_cases": sum(item["events"]["post_injection_censored"] for item in records.values()),
            "composition_macro": {metric: math.fsum(item["composition"]["metrics"][metric] for item in records.values()) / 60 for metric in METRICS},
            "cases": records}
    monte_carlo = {}
    for operator in ("primary", "secondary"):
        monte_carlo[operator] = {metric: {"aggregate_sd": math.sqrt(math.fsum(item["ranking"][operator]["R"]["mc"][metric]["sd"] ** 2 for item in case_metrics)) / 60,
            "aggregate_se": math.sqrt(math.fsum(item["ranking"][operator]["R"]["mc"][metric]["se"] ** 2 for item in case_metrics)) / 60,
            "planned_cases": 60, "planned_draws_per_case": 256} for metric in METRICS}
    return {"schema": "TD13-G31-SYNTHETIC-EVALUATION-v1", "evidence_scope": "SYNTHETIC_NUMERIC_READINESS_ONLY__NOT_FINAL_EFFICACY",
            "final_prediction_qualified": False, "primary": summaries["primary"], "secondary": summaries["secondary"], "primary_verdict": verdict,
            "contextual": {name: {"mean": {metric: math.fsum(item["mean"][metric] if name == "RCD" else item[metric] for item in records) / 60 for metric in METRICS},
                                  "planned_cases": 60, "failed_cases": sum(item["failed_seeds"] == 3 if name == "RCD" else item["status"] == "METHOD_FAILURE" for item in records),
                                  "failed_seeds": sum(item["failed_seeds"] for item in records) if name == "RCD" else None,
                                  "unknown_key_count": sum(item["unknown_key_count"] for item in records) if name == "RCD" else None,
                                  "cases": records} for name, records in contextual.items()},
            "c5": detector_summaries, "monte_carlo": monte_carlo, "case_metrics": case_metrics,
            "costs": [case.get("costs", {}) for case in cases], "cost_summary": _cost_summary(cases),
            "limitations": ["Historical benchmark exposure remains disclosed.", "Observed relations are not causal ground truth.", "Conditional bootstrap/draw uncertainty is not population significance.", "Synthetic readiness is not efficacy, five-reviewer certification or campaign permission."]}


def evaluate_readiness(lazy_artificial_labels):
    """Fresh durable verification precedes the first artificial label callback."""
    from scripts.task_g.campaign_provenance import require_verified_readiness_execution

    payload = require_verified_readiness_execution()
    context = payload.get("_verified_context", {})
    permissions = context.get("permissions", {})
    if (payload.get("phase") != "CAMPAIGN_READINESS_ONLY" or payload.get("scope") != "SYNTHETIC_CAMPAIGN_READINESS"
            or payload.get("source_summary", {}).get("source_kind") != "SYNTHETIC_NUMERIC"
            or context.get("final_prediction_qualified") is not False or permissions.get("synthetic_evaluation") is not True
            or any(permissions.get(name) is not False for name in _FINAL_PERMISSIONS)):
        raise EvaluationError("Readiness receipts cannot open actual final evaluator labels")
    _planned60(payload.get("cases"))
    if not callable(lazy_artificial_labels):
        raise EvaluationError("A lazy artificial label provider is required")
    result = evaluate_numeric_fixture_payload(payload, lazy_artificial_labels())
    result["verified_receipt_sha256"] = context["receipt_sha256"]
    result["durable_verification_before_label_callback"] = True
    return result


def evaluate_final(*args, **kwargs):
    raise EvaluationError("Actual final labels/campaign are closed in G31 readiness")


__all__ = ["EvaluationError", "score_service_vector", "rcd_seed_metrics", "random_control_metrics", "signal_starved",
           "paired_scenario_summary", "primary_verdict", "c5_case_metrics", "evaluate_numeric_fixture_payload", "evaluate_readiness", "evaluate_final"]
