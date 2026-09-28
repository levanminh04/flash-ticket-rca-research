"""Pure numeric TD-v1.3 C5 forecasting, spatial scores and event state.

The caller supplies only the completed warmup and subsequently one observed bin
at a time. NaN means unavailable input; no labels, absolute times, names, paths,
I/O, cache access or threshold calibration are accepted by this module.
"""

from __future__ import annotations

import numpy as np


class DetectorNumericalError(RuntimeError):
    """A qualifying configuration failed numerically; never a missing target."""


def _finite(value, label):
    if not np.isfinite(value).all():
        raise DetectorNumericalError(label)
    return value


def _q7(values, probability):
    """Scalar type-7 quantile, avoiding an overflowing midpoint sum."""
    ordered = np.sort(np.asarray(values, dtype=np.float64))
    if not len(ordered) or not np.isfinite(ordered).all():
        raise ValueError("Quantiles require nonempty finite observations")
    position = (len(ordered) - 1) * probability
    lower = int(np.floor(position))
    fraction = position - lower
    if fraction == 0:
        return float(ordered[lower])
    with np.errstate(over="ignore", invalid="ignore"):
        result = (1. - fraction) * ordered[lower] + fraction * ordered[lower + 1]
    return float(_finite(result, "Nonfinite type-7 quantile"))


def _config(config):
    cfg = dict(config)
    allowed = {"arm", "modalities", "lambda", "floor", "residual_floor", "lag",
               "bin_seconds", "fit_bins", "cal_bins", "min_fit_rows", "min_cal_rows"}
    if set(cfg) - allowed:
        raise ValueError("Unknown detector configuration fields")
    cfg.setdefault("arm", "G")
    cfg.setdefault("modalities", "MTL")
    cfg.setdefault("lambda", 1.)
    cfg.setdefault("floor", .01)
    cfg.setdefault("residual_floor", .01)
    cfg.setdefault("lag", 1)
    cfg.setdefault("bin_seconds", 5)
    cfg.setdefault("fit_bins", 24 if cfg["bin_seconds"] == 5 else 12)
    cfg.setdefault("cal_bins", 12 if cfg["fit_bins"] == 24 else
                   16 if cfg["fit_bins"] == 32 else 6)
    if any(not isinstance(cfg[key], (int, np.integer)) or isinstance(cfg[key], bool)
           for key in ("bin_seconds", "fit_bins", "cal_bins", "lag")):
        raise ValueError("Bin counts, width and lag must be integral")
    profile = (cfg["bin_seconds"], cfg["fit_bins"], cfg["cal_bins"])
    gates = {(5, 24, 12): (18, 9), (10, 12, 6): (8, 5), (5, 32, 16): (24, 12)}
    if profile not in gates or cfg["lag"] not in (1, 3):
        raise ValueError("Unregistered C5 bin/prefix or lag")
    if cfg["lag"] == 3 and profile != (5, 24, 12):
        raise ValueError("Lag3 is OFAT around the primary prefix, not Cartesian")
    expected_fit, expected_cal = gates[profile]
    if cfg["lag"] == 3:
        expected_fit = 20
    cfg.setdefault("min_fit_rows", expected_fit)
    cfg.setdefault("min_cal_rows", expected_cal)
    if (cfg["min_fit_rows"], cfg["min_cal_rows"]) != (expected_fit, expected_cal):
        raise ValueError("Input row gates must match the registered profile")
    if cfg["arm"] not in ("G", "L", "ALL") or cfg["modalities"] not in ("MT", "MTL"):
        raise ValueError("Unregistered detector arm/modality")
    if cfg["lambda"] not in (.1, 1., 10.):
        raise ValueError("Unregistered lambda")
    if cfg["floor"] not in (.0001, .001, .01):
        raise ValueError("Unregistered relative floor")
    if cfg["residual_floor"] not in (.001, .01, .1):
        raise ValueError("Unregistered residual floor")
    return cfg


def _types(channel_types, channels):
    mapping = {0: 0, 1: 1, 2: 2, "metric": 0, "trace": 1, "log": 2}
    if len(channel_types) != channels:
        raise ValueError("Channel types must match the input channel axis")
    try:
        result = np.array([mapping[value] for value in channel_types], dtype=np.int64)
    except (KeyError, TypeError) as exc:
        raise ValueError("Unknown channel type") from exc
    if np.sum(result == 1) > 1 or np.sum(result == 2) > 1:
        raise ValueError("At most one trace-count and one log-count channel")
    return result


def _normalize(values, center, scale, applicable):
    result = np.full_like(values, np.nan, dtype=np.float64)
    present = np.isfinite(values) & applicable
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        np.subtract(values, center, out=result, where=present)
        np.divide(result, scale, out=result, where=present)
    _finite(result[present], "Nonfinite normalization of a qualifying observation")
    return result


def _pool(z, membership):
    """Mean of available values; denominator is frozen membership cardinality."""
    active = membership & np.isfinite(z)[None, :, :]
    counts = active.sum(axis=1)
    degree = membership.sum(axis=1)
    magnitudes = np.max(np.where(active, np.abs(z)[None, :, :], 0.), axis=1,
                        initial=0.)
    divisors = np.where(magnitudes > 0., magnitudes, 1.)
    with np.errstate(invalid="ignore", over="ignore", divide="ignore"):
        terms = np.where(active, z[None, :, :] / divisors[:, None, :], 0.)
        mean = terms.sum(axis=1) / np.maximum(counts, 1) * divisors
    _finite(mean, "Nonfinite neighbor pooling")
    coverage = np.divide(counts, degree, out=np.zeros_like(mean), where=degree > 0)
    return mean, coverage, counts


def _features(history, state):
    lag = state["config"]["lag"]
    n, channels = state["E"].shape
    result = np.zeros((n, channels, lag + 4), dtype=np.float64)
    for offset in range(lag):
        result[:, :, offset] = history[-1 - offset]
    arm = state["config"]["arm"]
    diagnostics = {}
    if arm == "L":
        return result, diagnostics
    roles = ("out", "in") if arm == "G" else ("all", "all")
    for index, role in enumerate(roles):
        mean, coverage, counts = _pool(history[-1], state["memberships"][role])
        result[:, :, lag + index] = mean
        result[:, :, lag + 2 + index] = coverage
        diagnostics["available_" + role] = counts
    return result, diagnostics


def context_features(state, standardized_history):
    """Expose declared features for audits; history ends at the predictor bin."""
    history = np.asarray(standardized_history, dtype=np.float64)
    if history.ndim != 3 or history.shape[1:] != state["E"].shape:
        raise ValueError("Context history must be (T,N,C)")
    if len(history) < state["config"]["lag"]:
        raise ValueError("Missing required own history")
    return _features(history, state)


def _stable_mean(values, axis=0):
    magnitude = np.max(np.abs(values), axis=axis, keepdims=True)
    divisor = np.where(magnitude > 0., magnitude, 1.)
    return np.mean(values / divisor, axis=axis) * np.squeeze(divisor, axis=axis)


def _ridge(design, target, penalty):
    """SVD ridge for mean squared loss; intercept is never penalized.

    Centering removes the intercept exactly. Scaling is only an algebraic
    numerical device: the ridge penalty remains on original standardized-input
    coefficients, and includes the required n*lambda factor.
    """
    n, width = design.shape
    xmean = _stable_mean(design)
    ymean = float(_stable_mean(target))
    with np.errstate(over="ignore", invalid="ignore"):
        x = design - xmean
        y = target - ymean
    _finite(x, "Nonfinite centered design")
    _finite(y, "Nonfinite centered target")
    xscale = max(1., float(np.max(np.abs(x), initial=0.)))
    yscale = max(1., float(np.max(np.abs(y), initial=0.)))
    try:
        left, singular, right = np.linalg.svd(x / xscale, full_matrices=False)
    except np.linalg.LinAlgError as exc:
        raise DetectorNumericalError("Ridge SVD failed") from exc
    regularizer = np.sqrt(n * penalty) / xscale
    hypotenuse = np.hypot(singular, regularizer)
    weights = np.divide(singular, hypotenuse, out=np.zeros_like(singular),
                        where=hypotenuse > 0.)
    weights = np.divide(weights, hypotenuse, out=np.zeros_like(weights),
                        where=hypotenuse > 0.)
    with np.errstate(over="ignore", invalid="ignore"):
        coefficient = (right.T @ (weights * (left.T @ (y / yscale)))) * (yscale / xscale)
        intercept = ymean - xmean @ coefficient
    _finite(coefficient, "Nonfinite ridge coefficients")
    _finite(intercept, "Nonfinite ridge intercept")
    tolerance = np.finfo(np.float64).eps * max(n, width) * np.max(singular, initial=0.)
    rank = int(np.sum(singular > tolerance))
    shrinkage = np.divide(singular, hypotenuse, out=np.zeros_like(singular),
                          where=hypotenuse > 0.)
    diagnostics = {"centered_design_rank": rank, "design_rank_with_intercept": rank + 1,
                   "effective_ridge_df": float(1. + np.sum(shrinkage ** 2)),
                   "scaled_centered_singular_values": singular,
                   "singular_value_scale": xscale,
                   "active_columns": int(np.sum(np.any(x != 0., axis=0))),
                   "fit_rows": n, "nominal_columns": width, "intercept_unpenalized": True}
    return coefficient, float(intercept), diagnostics


def _predict(design, coefficient, intercept):
    with np.errstate(over="ignore", invalid="ignore"):
        prediction = design @ coefficient + intercept
    return _finite(prediction, "Nonfinite prediction on fixed eligible input IDs")


def fit_detector(warmup_values, adj, channel_types, fit_service_mask, config=None):
    """Fit once from exactly the declared warmup; return numeric mutable state.

    ``model_mask`` and fit/calibration target masks are input-only. Coefficients
    are computed for fit-eligible targets even if calibration support is too
    small; calibration cannot alter fit coefficients or neighbor membership.
    Log targets are excluded in MT, preserving identical M/T computation.
    """
    cfg = _config({} if config is None else config)
    values = np.asarray(warmup_values, dtype=np.float64)
    fit_bins, cal_bins = cfg["fit_bins"], cfg["cal_bins"]
    if values.ndim != 3 or len(values) != fit_bins + cal_bins:
        raise ValueError("Supply exactly warmup (T,N,C), never a future suffix")
    _, n, channels = values.shape
    types = _types(channel_types, channels)
    fit_services = np.asarray(fit_service_mask)
    if fit_services.dtype != np.bool_ or fit_services.shape != (n,):
        raise ValueError("fit_service_mask must be a boolean Vfit vector")
    adjacency = np.asarray(adj)
    if (adjacency.shape != (n, n) or not np.isfinite(adjacency).all() or
            not np.isin(adjacency, (0, 1)).all() or np.diag(adjacency).any()):
        raise ValueError("Adjacency must be binary, square and have no self edges")
    adjacency = adjacency.astype(bool, copy=True)
    if adjacency[~fit_services].any() or adjacency[:, ~fit_services].any():
        raise ValueError("Calibration-only nodes must be isolated")
    center = np.full((n, channels), np.nan)
    scale = np.full_like(center, np.nan)
    applicable = np.zeros((n, channels), dtype=bool)
    support = np.zeros((n, channels), dtype=np.int64)
    singleton = np.zeros_like(applicable)
    constant = np.zeros_like(applicable)
    floor_used = np.zeros_like(applicable)
    reasons = np.full((n, channels), "NO_FIT_OBSERVATION", dtype=object)
    for node in range(n):
        for channel in range(channels):
            if not fit_services[node]:
                reasons[node, channel] = "CALIBRATION_ONLY_SERVICE"
                continue
            if types[channel] == 2 and cfg["modalities"] == "MT":
                reasons[node, channel] = "EXCLUDED_LOG_CHANNEL"
                continue
            finite = values[:fit_bins, node, channel]
            finite = finite[np.isfinite(finite)]
            support[node, channel] = len(finite)
            if not len(finite):
                continue
            if types[channel] != 0:
                if (finite < 0.).any():
                    raise ValueError("Count channels must be nonnegative log1p counts")
                if not (finite > 0.).any():
                    reasons[node, channel] = "NO_POSITIVE_FIT_COUNT"
                    continue
            location = _q7(finite, .5)
            with np.errstate(over="ignore", invalid="ignore"):
                iqr = _q7(finite, .75) - _q7(finite, .25)
                relative_floor = cfg["floor"] * _q7(np.abs(finite), .5)
            _finite(iqr, "Nonfinite fit IQR")
            denominator = max(iqr, relative_floor, 1e-12)
            _finite(denominator, "Nonfinite fit scale")
            center[node, channel], scale[node, channel] = location, denominator
            applicable[node, channel] = True
            singleton[node, channel] = len(finite) == 1
            constant[node, channel] = np.all(finite == finite[0])
            floor_used[node, channel] = denominator > iqr
            reasons[node, channel] = "SCALER_DEFINED"
    z = _normalize(values, center, scale, applicable)
    out = adjacency[:, :, None] & applicable[None, :, :]
    incoming = adjacency.T[:, :, None] & applicable[None, :, :]
    others = (~np.eye(n, dtype=bool))[:, :, None] & applicable[None, :, :]
    state = {"config": cfg, "E": applicable, "centers": center, "scales": scale,
             "adj": adjacency, "channel_types": types, "fit_service_mask": fit_services.copy(),
             "memberships": {"out": out, "in": incoming, "all": others},
             "degrees": {"out": out.sum(axis=1), "in": incoming.sum(axis=1),
                         "all": others.sum(axis=1)}}
    width, lag = cfg["lag"] + 4, cfg["lag"]
    features = np.full((len(values), n, channels, width), np.nan)
    input_mask = np.zeros((len(values), n, channels), dtype=bool)
    for index in range(lag, len(values)):
        features[index], _ = _features(z[index - lag:index], state)
        input_mask[index] = applicable & np.isfinite(z[index]) & np.all(
            np.isfinite(features[index, :, :, :lag]), axis=-1)
    fit_rows = input_mask[:fit_bins].sum(axis=0)
    cal_rows = input_mask[fit_bins:].sum(axis=0)
    fit_mask = applicable & (fit_rows >= cfg["min_fit_rows"])
    model_mask = fit_mask & (cal_rows >= cfg["min_cal_rows"])
    coefficients = np.full((n, channels, width), np.nan)
    intercepts = np.full((n, channels), np.nan)
    error_center = np.full((n, channels), np.nan)
    error_scale = np.full((n, channels), np.nan)
    calibration_errors = np.full((cal_bins, n, channels), np.nan)
    calibration_predictions = np.full_like(calibration_errors, np.nan)
    ridge_diagnostics = [[None for _ in range(channels)] for _ in range(n)]
    residual_floor_used = np.zeros_like(applicable)
    residual_constant = np.zeros_like(applicable)
    for node, channel in np.argwhere(fit_mask):
        ids = np.flatnonzero(input_mask[:fit_bins, node, channel])
        coefficient, intercept, diag = _ridge(features[ids, node, channel],
                                             z[ids, node, channel], cfg["lambda"])
        coefficients[node, channel], intercepts[node, channel] = coefficient, intercept
        ridge_diagnostics[node][channel] = diag
        ids = np.flatnonzero(input_mask[fit_bins:, node, channel])
        if len(ids):
            prediction = _predict(features[fit_bins + ids, node, channel], coefficient, intercept)
            with np.errstate(over="ignore", invalid="ignore"):
                errors = np.abs(z[fit_bins + ids, node, channel] - prediction)
            _finite(errors, "Nonfinite calibration errors")
            calibration_predictions[ids, node, channel] = prediction
            calibration_errors[ids, node, channel] = errors
        if model_mask[node, channel]:
            errors = calibration_errors[ids, node, channel]
            location = _q7(errors, .5)
            with np.errstate(over="ignore", invalid="ignore"):
                iqr = _q7(errors, .75) - _q7(errors, .25)
            _finite(iqr, "Nonfinite residual IQR")
            denominator = max(iqr, cfg["residual_floor"])
            error_center[node, channel], error_scale[node, channel] = location, denominator
            residual_floor_used[node, channel] = denominator > iqr
            residual_constant[node, channel] = np.all(errors == errors[0])
    state.update(coefficients=coefficients, intercepts=intercepts, fit_model_mask=fit_mask,
                 model_mask=model_mask, residual_centers=error_center,
                 residual_scales=error_scale, history=z[-lag:].copy(), bins_seen=len(values),
                 calibration_errors=calibration_errors,
                 calibration_predictions=calibration_predictions,
                 fit_target_mask=input_mask[:fit_bins].copy(),
                 calibration_target_mask=input_mask[fit_bins:].copy(),
                 warmup_z=z, diagnostics={"finite_fit_support": support,
                     "singleton_scale": singleton, "constant_scale": constant,
                     "scale_floor_used": floor_used, "applicability_reasons": reasons,
                     "fit_rows": fit_rows, "calibration_rows": cal_rows,
                     "model_count": int(model_mask.sum()), "ridge": ridge_diagnostics,
                     "residual_floor_used": residual_floor_used,
                     "constant_calibration_errors": residual_constant})
    return state


def spatial_scores(state, standardized_values):
    """Graph-TV and separate local magnitude, independent of forecasting models."""
    z = np.asarray(standardized_values, dtype=np.float64)
    if z.shape != state["E"].shape:
        raise ValueError("Spatial input must be (N,C)")
    available = state["E"] & np.isfinite(z)
    edges = np.argwhere(np.triu(state["adj"] | state["adj"].T, 1))
    per_channel = np.full(z.shape[1], np.nan)
    edge_counts = np.zeros(z.shape[1], dtype=np.int64)
    for channel in range(z.shape[1]):
        if not len(edges):
            continue
        selected = edges[available[edges[:, 0], channel] & available[edges[:, 1], channel]]
        edge_counts[channel] = len(selected)
        if not len(selected):
            continue
        with np.errstate(over="ignore", invalid="ignore"):
            differences = z[selected[:, 0], channel] - z[selected[:, 1], channel]
            squared = differences ** 2
        _finite(squared, "Nonfinite graph-TV edge energy")
        per_channel[channel] = _stable_mean(squared)
    score = float(np.max(per_channel[np.isfinite(per_channel)])) if np.isfinite(per_channel).any() else np.nan
    local = float(np.max(np.abs(z[available]))) if available.any() else np.nan
    return {"tv_score": score, "tv_channels": per_channel, "tv_edge_counts": edge_counts,
            "local_magnitude": local}


def score_bin(state, current_values):
    """Consume one complete next bin; only lag history and bin counter mutate."""
    values = np.asarray(current_values, dtype=np.float64)
    if values.shape != state["E"].shape:
        raise ValueError("Current values must match frozen (N,C)")
    count_channels = state["channel_types"] != 0
    if np.any((values[:, count_channels] < 0.) & np.isfinite(values[:, count_channels]) &
              state["E"][:, count_channels]):
        raise ValueError("Count channels must be nonnegative log1p counts")
    z = _normalize(values, state["centers"], state["scales"], state["E"])
    design, availability = _features(state["history"], state)
    lag = state["config"]["lag"]
    target_mask = (state["model_mask"] & np.isfinite(z) &
                   np.all(np.isfinite(design[:, :, :lag]), axis=-1))
    predictions = np.full_like(z, np.nan)
    errors = np.full_like(z, np.nan)
    residuals = np.full_like(z, np.nan)
    for node, channel in np.argwhere(target_mask):
        prediction = _predict(design[node, channel], state["coefficients"][node, channel],
                              state["intercepts"][node, channel])
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            error = np.abs(z[node, channel] - prediction)
            standardized_error = ((error - state["residual_centers"][node, channel]) /
                                  state["residual_scales"][node, channel])
        _finite(error, "Nonfinite forecast error")
        _finite(standardized_error, "Nonfinite normalized residual")
        residual = max(0., standardized_error)
        predictions[node, channel], errors[node, channel] = prediction, error
        residuals[node, channel] = residual
    try:
        spatial = spatial_scores(state, z)
        spatial['tv_failure'] = None
    except DetectorNumericalError as exc:
        # A separate secondary method cannot veto a valid forecast. The caller
        # must retain this as TV execution failure, not missing/healthy data.
        spatial = {'tv_score': np.nan, 'tv_channels': np.full(z.shape[1], np.nan),
                   'tv_edge_counts': None, 'tv_failure': str(exc),
                   'local_magnitude': float(np.max(np.abs(z[np.isfinite(z)])))
                   if np.isfinite(z).any() else np.nan}
    score = float(np.max(residuals[target_mask])) if target_mask.any() else np.nan
    endpoint = (state["bins_seen"] + 1) * state["config"]["bin_seconds"]
    result = {"score": score, "residuals": residuals, "errors": errors,
              "predictions": predictions, "target_mask": target_mask.copy(),
              "z": z, "features": design, "availability": availability,
              "endpoint": endpoint, "start": endpoint - state["config"]["bin_seconds"],
              "scored_channels": int(target_mask.sum()), **spatial}
    state["history"] = np.concatenate((state["history"][1:], z[None]), axis=0)
    state["bins_seen"] += 1
    return result


def create_event_state(threshold, *, bin_seconds=5, streak=3, refractory_seconds=300):
    """Initialize registered event replay; threshold is supplied, never fitted."""
    if not np.isfinite(threshold) or bin_seconds not in (5, 10):
        raise ValueError("Finite threshold and registered bin width required")
    if streak not in (1, 3, 5) or refractory_seconds not in (60, 300, 600):
        raise ValueError("Unregistered event sensitivity")
    return {"threshold": float(threshold), "bin_seconds": int(bin_seconds),
            "required_streak": int(streak), "refractory_seconds": int(refractory_seconds),
            "streak": 0, "last_trigger": None, "last_endpoint": None}


def event_step(state, score, endpoint):
    """Update at each consecutive relative endpoint; NaN alone is unavailable.

    A trigger is allowed when the running positive streak reaches the required
    length and elapsed time since the last trigger is at least refractory.
    Triggering does not turn an otherwise consecutive positive bin negative.
    """
    if not isinstance(endpoint, (int, np.integer)) or endpoint < 0:
        raise ValueError("Event endpoint must be a relative nonnegative integer")
    if state["last_endpoint"] is not None and endpoint != state["last_endpoint"] + state["bin_seconds"]:
        raise ValueError("Supply every consecutive bin, including unavailable bins")
    if np.isinf(score):
        raise DetectorNumericalError("Infinite system score")
    available = bool(np.isfinite(score))
    positive = available and score > state["threshold"]
    state["streak"] = state["streak"] + 1 if positive else 0
    elapsed = None if state["last_trigger"] is None else endpoint - state["last_trigger"]
    trigger = bool(state["streak"] >= state["required_streak"] and
                   (elapsed is None or elapsed >= state["refractory_seconds"]))
    if trigger:
        state["last_trigger"] = int(endpoint)
    state["last_endpoint"] = int(endpoint)
    return {"available": available, "positive": bool(positive), "trigger": trigger,
            "streak": state["streak"], "endpoint": int(endpoint),
            "last_trigger": state["last_trigger"]}
