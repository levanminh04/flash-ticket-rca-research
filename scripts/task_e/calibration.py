"""Trusted TD-v1.3 development evaluator; never import in numeric workers.

The controller supplies complete planned case/bin rosters, immutable worker
outputs and evaluator-only scenario/tau data. This module does not load data,
fit forecasting models, select final cases, or perform any I/O. Missing cases
must be explicit records; missing predictions on fixed eligible IDs are errors.
"""
from __future__ import annotations

import math
from collections import defaultdict
from fractions import Fraction
from typing import Callable, Mapping, Sequence

import numpy as np


ARMS = ("G", "L", "ALL")
LAMBDA_PRIORITY = (1.0, 10.0, 0.1)
Q_REGISTRY = (0.95, 0.975, 0.99)
RANK_METRICS = ("rr", "hit1", "hit3", "hit5", "ndcg5")
REGISTERED_FOLDS = (
    (("ts-auth-service", "cpu"), ("ts-order-service", "disk")),
    (("ts-auth-service", "delay"), ("ts-travel-service", "loss")),
    (("ts-train-service", "cpu"), ("ts-route-service", "mem")),
    (("ts-train-service", "delay"), ("ts-travel-service", "disk")),
    (("ts-order-service", "loss"), ("ts-route-service", "socket")),
)


class EvaluationError(ValueError):
    """Malformed evidence or an invalid numerical configuration; do not drop it."""


class CoverageError(EvaluationError):
    """A declared development calibration/eligibility gate did not pass."""


def _ids(records: Mapping, planned_ids: Sequence) -> tuple:
    ids = tuple(planned_ids)
    if not ids or len(set(ids)) != len(ids):
        raise EvaluationError("Planned IDs must be unique and nonempty")
    if set(records) != set(ids):
        raise EvaluationError("Require one explicit record for every planned ID")
    return ids


def _scenario(record: Mapping):
    value = record["scenario"]
    return tuple(value) if isinstance(value, list) else value


def _mean(values) -> float:
    values = tuple(float(v) for v in values)
    if not values or not all(math.isfinite(v) for v in values):
        raise EvaluationError("Mean needs nonempty finite observations")
    # Divide before summation so a sum of large finite losses cannot overflow.
    result = math.fsum(v / len(values) for v in values)
    if not math.isfinite(result):
        raise EvaluationError("Nonfinite aggregate")
    return result


def _bins(record: Mapping) -> tuple[np.ndarray, np.ndarray, float, float]:
    starts = np.asarray(record["starts"], dtype=float)
    ends = np.asarray(record["ends"], dtype=float)
    tau = float(record["tau"])
    warmup = float(record.get("warmup_end", 180.0))
    if (starts.ndim != 1 or ends.shape != starts.shape
            or not np.isfinite(starts).all() or not np.isfinite(ends).all()
            or not math.isfinite(tau) or not math.isfinite(warmup)
            or np.any(ends <= starts) or np.any(starts[1:] < ends[:-1])):
        raise EvaluationError("Invalid, overlapping, or unordered bin boundaries")
    return starts, ends, tau, warmup


def _score_arrays(record: Mapping):
    starts, ends, tau, warmup = _bins(record)
    scores = np.asarray(record["scores"], dtype=float)
    if scores.shape != starts.shape:
        raise EvaluationError("Scalar system score required for every planned bin")
    if not record.get("failed", False) and (np.isinf(scores).any()
                                            or np.any(scores[np.isfinite(scores)] < 0)):
        raise EvaluationError("Infinite/negative score is not data unavailability")
    finite = (np.zeros(scores.shape, dtype=bool) if record.get("failed", False)
              else np.isfinite(scores))
    after = starts >= warmup
    normal = after & (ends <= tau)
    positive = after & (starts >= tau)
    straddle = after & ~(normal | positive)
    return starts, ends, scores, finite, normal, positive, straddle


def weighted_cdf_inverse(values, weights, q: float) -> float:
    """Exact discrete inverse; rational hierarchy weights avoid CDF rounding ties.

    Ordinary float weights are interpreted as their decimal string values.
    This is not NumPy/type-7 interpolated percentile behavior.
    """
    values = tuple(float(v) for v in values)
    weights = tuple(w if isinstance(w, Fraction) else Fraction(str(w)) for w in weights)
    level = Fraction(str(q))
    if (not values or len(values) != len(weights) or not 0 < level <= 1
            or not all(math.isfinite(v) for v in values)
            or any(w <= 0 for w in weights)):
        raise EvaluationError("Invalid weighted CDF arguments")
    total = sum(weights, Fraction())
    cumulative = Fraction()
    for value, weight in sorted(zip(values, weights), key=lambda pair: pair[0]):
        cumulative += weight
        if cumulative >= level * total:
            return value
    raise AssertionError("Positive finite weighted CDF must reach q")


def normal_score_distribution(cases: Mapping, planned_ids: Sequence) -> dict:
    """Equal scored-scenario -> scored-case -> valid normal endpoint weights.

    TD gates are fixed at 100 endpoints and 80% planned training cases. The
    returned IDs allow the controller to persist the exact fitting support.
    """
    ids = _ids(cases, planned_ids)
    groups = defaultdict(list)
    normal_by_case = {}
    for case_id in ids:
        _, ends, scores, finite, normal, _, _ = _score_arrays(cases[case_id])
        positions = np.flatnonzero(finite & normal)
        normal_by_case[case_id] = positions
        if len(positions):
            groups[_scenario(cases[case_id])].append(case_id)
    scored_cases = sum(len(group) for group in groups.values())
    endpoints = sum(len(indices) for indices in normal_by_case.values())
    if endpoints < 100 or 5 * scored_cases < 4 * len(ids):
        raise CoverageError(
            f"Threshold gate: {endpoints} normal endpoints; {scored_cases}/{len(ids)} cases")
    values, weights, support = [], [], []
    for scenario, case_ids in groups.items():
        for case_id in case_ids:
            positions = normal_by_case[case_id]
            weight = Fraction(1, len(groups) * len(case_ids) * len(positions))
            for position in positions:
                values.append(float(cases[case_id]["scores"][position]))
                weights.append(weight)
                support.append((case_id, int(position), float(cases[case_id]["ends"][position])))
    if sum(weights, Fraction()) != 1:
        raise AssertionError("Hierarchical CDF weights must sum exactly to one")
    return {"values": values, "weights": weights, "support_ids": support,
            "planned_cases": len(ids), "scored_cases": scored_cases,
            "scored_scenarios": len(groups), "normal_endpoints": endpoints,
            "case_coverage": scored_cases / len(ids)}


def calibrate_threshold(cases: Mapping, planned_ids: Sequence, q: float) -> dict:
    distribution = normal_score_distribution(cases, planned_ids)
    threshold = weighted_cdf_inverse(distribution["values"], distribution["weights"], q)
    return {**distribution, "q": float(q), "threshold": threshold,
            "weights": [float(w) for w in distribution["weights"]]}


def fixed_eligible_forecast_loss(inputs: Mapping, predictions: Mapping,
                                 planned_ids: Sequence) -> dict:
    """MAE of normalized targets BEFORE residual scaling, on frozen input IDs.

    inputs[id]: scenario, starts, ends, tau, optional warmup_end, targets[T,...],
    eligible[T,...]. predictions[id] has the exact targets shape. All remaining
    dimensions are channels, including service/channel pairs. Nonfinite values
    outside eligibility never become new observations; inside they are errors.
    """
    ids = _ids(inputs, planned_ids)
    _ids(predictions, ids)
    case_losses, support, per_bin = {}, {}, {}
    for case_id in ids:
        record = inputs[case_id]
        starts, ends, tau, warmup = _bins(record)
        target = np.asarray(record["targets"], dtype=float)
        prediction = np.asarray(predictions[case_id], dtype=float)
        eligible = np.asarray(record["eligible"])
        if (target.ndim < 2 or target.shape[0] != len(starts)
                or prediction.shape != target.shape or eligible.shape != target.shape
                or eligible.dtype != np.bool_):
            raise EvaluationError("Fixed forecast target/prediction/mask shape mismatch")
        channels = math.prod(target.shape[1:])
        target = target.reshape(len(starts), channels)
        prediction = prediction.reshape(target.shape)
        eligible = eligible.reshape(target.shape)
        selected = eligible & ((starts >= warmup) & (ends <= tau))[:, None]
        if not np.isfinite(target[selected]).all():
            raise EvaluationError("Input eligibility includes a nonfinite target")
        if not np.isfinite(prediction[selected]).all():
            raise EvaluationError(f"Nonfinite prediction on fixed eligible IDs: {case_id}")
        bin_losses = []
        selected_ids = []
        for b in np.flatnonzero(selected.any(axis=1)):
            channels = np.flatnonzero(selected[b])
            # Python scalar difference can overflow to inf; it is an explicit
            # numerical error, not an invitation to shrink the scoring mask.
            losses = [abs(float(target[b, c]) - float(prediction[b, c])) for c in channels]
            bin_losses.append(_mean(losses))
            selected_ids.extend((int(b), int(c)) for c in channels)
        support[case_id] = selected_ids
        per_bin[case_id] = bin_losses
        if bin_losses:
            case_losses[case_id] = _mean(bin_losses)
    if 5 * len(case_losses) < 4 * len(ids):
        raise CoverageError(f"Forecast eligibility gate: {len(case_losses)}/{len(ids)} cases")
    by_scenario = defaultdict(list)
    for case_id, value in case_losses.items():
        by_scenario[_scenario(inputs[case_id])].append(value)
    scenario_losses = {s: _mean(values) for s, values in by_scenario.items()}
    return {"loss": _mean(scenario_losses.values()), "case_losses": case_losses,
            "scenario_losses": [{"scenario": s, "loss": value}
                                for s, value in scenario_losses.items()], "bin_losses": per_bin,
            "support_ids": support, "planned_cases": len(ids),
            "eligible_cases": len(case_losses), "case_coverage": len(case_losses) / len(ids)}


def select_registered(objectives: Mapping, preference: Sequence, *, maximize=False):
    """TD absolute 1e-12 tie rule, preference first, lexical ID second."""
    if not objectives or not all(math.isfinite(float(v)) for v in objectives.values()):
        raise EvaluationError("Every registered objective must be finite before selection")
    optimum = (max if maximize else min)(float(v) for v in objectives.values())
    tied = [key for key, value in objectives.items() if abs(float(value) - optimum) <= 1e-12]
    priority = {key: i for i, key in enumerate(preference)}
    return min(tied, key=lambda key: (priority.get(key, len(priority)), str(key)))


def grouped_folds(cases: Mapping, planned_ids: Sequence,
                  folds=REGISTERED_FOLDS) -> list[dict]:
    ids = _ids(cases, planned_ids)
    normalized = [tuple(tuple(s) if isinstance(s, list) else s for s in fold) for fold in folds]
    all_scenarios = [s for fold in normalized for s in fold]
    if len(normalized) != 5 or len(set(all_scenarios)) != len(all_scenarios):
        raise EvaluationError("Require five disjoint scenario folds")
    if not {_scenario(cases[i]) for i in ids}.issubset(set(all_scenarios)):
        raise EvaluationError("Case scenario is absent from registered folds")
    result = []
    for index, held in enumerate(normalized):
        validation = tuple(i for i in ids if _scenario(cases[i]) in held)
        training = tuple(i for i in ids if _scenario(cases[i]) not in held)
        if not validation or not training:
            raise EvaluationError("Empty training or held-out fold")
        result.append({"fold": index + 1, "train_ids": training, "heldout_ids": validation})
    return result


def select_lambda(inputs: Mapping, predictions_by_lambda: Mapping,
                  planned_ids: Sequence, *, folds=REGISTERED_FOLDS) -> dict:
    """Joint G/L/ALL equal-arm loss; case-prefix models need no cross-case refit.

    Each planned case supplies held-out observations exactly once through the
    grouped roster. A numeric failure rejects selection pending correction;
    it does not make the remaining lambda values apparent winners.
    """
    ids = _ids(inputs, planned_ids)
    split = grouped_folds(inputs, ids, folds)
    if set(predictions_by_lambda) != set(LAMBDA_PRIORITY):
        raise EvaluationError("Require all three registered lambda candidates")
    results, objectives = {}, {}
    for lam, arms in predictions_by_lambda.items():
        if set(arms) != set(ARMS):
            raise EvaluationError("Common lambda selection requires exactly G/L/ALL")
        arm_results = {arm: fixed_eligible_forecast_loss(inputs, arms[arm], ids) for arm in ARMS}
        # The common input map fixes target IDs before any arm's predictions.
        objectives[lam] = _mean(result["loss"] for result in arm_results.values())
        fold_losses = []
        for fold in split:
            held = fold["heldout_ids"]
            by_arm = {}
            for arm in ARMS:
                scenario_values = defaultdict(list)
                for case_id in held:
                    if case_id in arm_results[arm]["case_losses"]:
                        scenario_values[_scenario(inputs[case_id])].append(
                            arm_results[arm]["case_losses"][case_id])
                by_arm[arm] = (_mean(_mean(v) for v in scenario_values.values())
                               if scenario_values else None)
            fold_losses.append({**fold, "arm_losses": by_arm})
        results[lam] = {"arms": arm_results, "folds": fold_losses}
    selected = select_registered(objectives, LAMBDA_PRIORITY)
    return {"selected_lambda": selected, "objectives": objectives, "details": results,
            "objective": "equal eligible scenario/case/bin/channel; equal G/L/ALL"}


def regime_metrics(case: Mapping, threshold: float) -> dict:
    """Per-case injection-regime metrics; unavailable never becomes negative."""
    if not math.isfinite(float(threshold)):
        raise EvaluationError("Threshold must be finite")
    starts, ends, scores, finite, normal, positive, straddle = _score_arrays(case)
    planned = normal | positive
    valid = finite & planned
    predicted = scores > threshold
    tp = int(np.sum(valid & positive & predicted))
    fp = int(np.sum(valid & normal & predicted))
    fn = int(np.sum(valid & positive & ~predicted))
    tn = int(np.sum(valid & normal & ~predicted))
    pden, rden, fden = tp + fp, tp + fn, 2 * tp + fp + fn
    return {"precision": tp / pden if pden else 0.0,
            "recall": tp / rden if rden else 0.0,
            "f1": 2 * tp / fden if fden else 0.0,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision_undefined": pden == 0, "recall_undefined": rden == 0,
            "f1_undefined": fden == 0, "no_scorable_bins": not valid.any(),
            "failed": bool(case.get("failed", False)),
            "planned_bins": int(planned.sum()), "scored_bins": int(valid.sum()),
            "unavailable_bins": int((planned & ~finite).sum()),
            "excluded_straddle_bins": int(straddle.sum()),
            "normal_planned": int(normal.sum()), "normal_scored": int((normal & finite).sum()),
            "positive_planned": int(positive.sum()), "positive_scored": int((positive & finite).sum()),
            "coverage": float(valid.sum() / planned.sum()) if planned.any() else 0.0,
            "normal_observed_seconds": float(np.sum((ends - starts)[normal])),
            "normal_scored_seconds": float(np.sum((ends - starts)[normal & finite]))}


def planned_regime_summary(outcomes: Mapping, planned_ids: Sequence) -> dict:
    ids = _ids(outcomes, planned_ids)
    macro = {metric: _mean(outcomes[i][metric] for i in ids)
             for metric in ("precision", "recall", "f1")}
    totals = {field: sum(int(outcomes[i][field]) for i in ids)
              for field in ("tp", "fp", "fn", "tn", "planned_bins", "scored_bins",
                            "unavailable_bins", "excluded_straddle_bins",
                            "normal_planned", "normal_scored", "positive_planned", "positive_scored")}
    tp, fp, fn = (totals[key] for key in ("tp", "fp", "fn"))
    return {"macro": macro, "totals": totals, "planned_cases": len(ids),
            "scored_cases": sum(not outcomes[i]["no_scorable_bins"] for i in ids),
            "failed_cases": sum(outcomes[i]["failed"] for i in ids),
            "pooled_precision": tp / (tp + fp) if tp + fp else 0.0,
            "pooled_recall": tp / (tp + fn) if tp + fn else 0.0,
            "pooled_f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0}


def select_q(cases: Mapping, planned_ids: Sequence, *, folds=REGISTERED_FOLDS,
             q_values=Q_REGISTRY) -> dict:
    """Fold-training CDFs, held-out macro case F1, then full-development refit."""
    ids = _ids(cases, planned_ids)
    if set(q_values) != set(Q_REGISTRY):
        raise EvaluationError("Primary q selection requires all registered candidates")
    split = grouped_folds(cases, ids, folds)
    distributions = []
    for fold in split:
        training = {i: cases[i] for i in fold["train_ids"]}
        distributions.append(normal_score_distribution(training, fold["train_ids"]))
    details, objectives = {}, {}
    for q in q_values:
        outcomes, fold_reports = {}, []
        for fold, distribution in zip(split, distributions):
            threshold = weighted_cdf_inverse(distribution["values"], distribution["weights"], q)
            for case_id in fold["heldout_ids"]:
                outcomes[case_id] = regime_metrics(cases[case_id], threshold)
            fold_reports.append({**fold, "threshold": threshold,
                                 "normal_support_ids": distribution["support_ids"],
                                 "normal_endpoints": distribution["normal_endpoints"],
                                 "case_coverage": distribution["case_coverage"]})
        summary = planned_regime_summary(outcomes, ids)
        objectives[q] = summary["macro"]["f1"]
        details[q] = {"folds": fold_reports, "cases": outcomes, "summary": summary}
    if not any(not outcome["f1_undefined"] for detail in details.values()
               for outcome in detail["cases"].values()):
        raise CoverageError("All held-out regime-F1 objectives are undefined")
    selected = select_registered(objectives, sorted(q_values, reverse=True), maximize=True)
    return {"selected_q": selected, "objectives": objectives, "details": details,
            "full_development_calibration": calibrate_threshold(cases, ids, selected)}


def mean_planned_draw_metrics(draws: Mapping, *, planned_draws: int = 256) -> dict:
    """Mean per-draw METRICS, with explicit None failures; never average scores."""
    if planned_draws < 2 or set(draws) != set(range(planned_draws)):
        raise EvaluationError("Every planned draw needs an explicit metric record or None failure")
    result, mc = {}, {}
    for metric in RANK_METRICS:
        values = [0.0 if draws[j] is None else float(draws[j][metric]) for j in range(planned_draws)]
        if not all(math.isfinite(v) and 0 <= v <= 1 for v in values):
            raise EvaluationError("Invalid ranking metric; record an explicit failed draw")
        mean = _mean(values)
        sd = math.sqrt(math.fsum((value - mean) ** 2 for value in values) / (planned_draws - 1))
        result[metric] = mean
        mc[metric] = {"sd": sd, "se": sd / math.sqrt(planned_draws)}
    return {"metrics": result, "mc": mc, "planned_draws": planned_draws,
            "failed_draws": sum(draw is None for draw in draws.values()),
            "interpretation": "conditional draw variability, not incident independence or mixing proof"}


def event_diagnostics(trigger_endpoints, case: Mapping) -> dict:
    """Descriptive replay events. Endpoint == tau is pre-injection (end<=tau).

    Report both observed-duration and scored-duration rates explicitly. They
    are archival injection-regime descriptors, never operational false alarms.
    """
    times = tuple(float(t) for t in trigger_endpoints)
    if (not all(math.isfinite(t) for t in times) or any(b <= a for a, b in zip(times, times[1:]))):
        raise EvaluationError("Triggers must be strictly ordered finite endpoints")
    _, ends, _, finite, normal, positive, straddle = _score_arrays(case)
    if not set(times).issubset(set(float(t) for t in ends[finite & (normal | positive | straddle)])):
        raise EvaluationError("Trigger must belong to a valid observed score endpoint")
    tau = float(case["tau"])
    metrics = regime_metrics(case, 0.0)
    pre = [t for t in times if t <= tau]
    post = [t for t in times if t > tau]
    observed_hours = metrics["normal_observed_seconds"] / 3600
    scored_hours = metrics["normal_scored_seconds"] / 3600
    return {"triggers": list(times), "pre_injection_triggers": len(pre),
            "observed_normal_hours": observed_hours, "scored_normal_hours": scored_hours,
            "rate_per_observed_normal_hour": len(pre) / observed_hours if observed_hours else None,
            "rate_per_scored_normal_hour": len(pre) / scored_hours if scored_hours else None,
            "first_post_injection_trigger": post[0] if post else None,
            "first_post_injection_delay": post[0] - tau if post else None,
            "post_injection_censored": not bool(post)}


def first_trigger_composition(triggers: Sequence[Mapping], tau: float,
                              *, history_seconds: float = 360.0) -> dict:
    """Use only first post-injection trigger; failures/history deficits stay zero.

    Trigger record: endpoint, status, and metrics with rr/hit1/hit3/hit5/ndcg5.
    Metrics are already produced by the trusted tie evaluator. No later rescue.
    """
    endpoints = [float(record["endpoint"]) for record in triggers]
    if (not math.isfinite(tau) or not all(math.isfinite(t) for t in endpoints)
            or any(b <= a for a, b in zip(endpoints, endpoints[1:]))):
        raise EvaluationError("Composition requires ordered finite trigger endpoints")
    zero = dict.fromkeys(RANK_METRICS, 0.0)
    first = next((record for record in triggers if float(record["endpoint"]) > tau), None)
    if first is None:
        return {"metrics": zero, "status": "NO_POST_INJECTION_TRIGGER", "endpoint": None}
    endpoint = float(first["endpoint"])
    if endpoint < history_seconds:
        return {"metrics": zero, "status": "INSUFFICIENT_HISTORY", "endpoint": endpoint}
    if first.get("status") != "VALID":
        return {"metrics": zero, "status": first.get("status", "METHOD_FAILURE"), "endpoint": endpoint}
    metrics = {name: float(first["metrics"][name]) for name in RANK_METRICS}
    if not all(math.isfinite(value) and 0 <= value <= 1 for value in metrics.values()):
        raise EvaluationError("Invalid composed ranking metrics")
    return {"metrics": metrics, "status": "VALID", "endpoint": endpoint}


def leave_one_cell_reselection(cases: Mapping, planned_ids: Sequence,
                               selector: Callable[[dict, tuple], dict]) -> dict:
    """Rerun an explicit caller selector per deletion; never relabel fixed scores.

    The callback must refit fold/full calibration if selecting q. Failure is
    retained with its type/message. This diagnostic does not replace primary.
    """
    ids = _ids(cases, planned_ids)
    results = []
    for scenario in sorted({_scenario(cases[i]) for i in ids}, key=str):
        kept = tuple(i for i in ids if _scenario(cases[i]) != scenario)
        subset = {i: cases[i] for i in kept}
        try:
            result = {"status": "VALID", "selection": selector(subset, kept)}
        except EvaluationError as error:
            result = {"status": "INVALID", "error_type": type(error).__name__, "error": str(error)}
        results.append({"excluded_scenario": scenario, "kept_cases": len(kept), **result})
    return {"deletions": results, "primary_registry_changed": False}
