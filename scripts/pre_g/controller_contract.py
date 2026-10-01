"""Pure PRE-G contract for the registered RCD primary comparator.

This is a synthetic-fixture seam, not a Task G campaign controller.  A future
controller must persist the returned prediction seal before it can access an
evaluator-only root.  No corpus discovery, label loading, or final run lives
here.
"""

from __future__ import annotations

import hashlib
import json
import re

import numpy as np
import pandas as pd

from scripts.task_e.evaluator import service_scores_from_metric_ranks, tie_metrics


SCHEMA = "PRE-G-RCD-PREDICTIONS-v1"
METHOD = "RCD-RCAEval-adapted-TD12"
SEEDS = (420, 421, 422)
PRIMARY_BINS = 5
METRICS = ("rr", "hit1", "hit3", "hit5", "ndcg5")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SAFE_CODE = re.compile(r"[A-Za-z0-9_:-]{1,128}\Z")
_ABSOLUTE_PATH = re.compile(r"(?:[A-Za-z]:[\\/]|/|\\\\)")
_SYNTHETIC = "SYNTHETIC_UNQUALIFIED"
_QUALIFIED = "QUALIFIED_CORE_RUN"


class ControllerContractError(ValueError):
    """A prediction, provenance binding, or evaluator transition is invalid."""


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ControllerContractError("Prediction seal is not finite canonical JSON") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _require_sha256(value: object, name: str) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise ControllerContractError(f"{name} must be a lowercase SHA256")
    return value


def _require_name(value: object, name: str) -> str:
    if (
        type(value) is not str
        or not value
        or value in (".", "..")
        or "/" in value
        or "\\" in value
        or _ABSOLUTE_PATH.match(value)
    ):
        raise ControllerContractError(f"{name} must be a non-path identifier")
    return value


def _bind_source(candidate_ids, metric_columns, metric_owners):
    if type(candidate_ids) is not list or type(metric_columns) is not list:
        raise ControllerContractError("Candidate IDs and metric columns must be lists")
    candidates = [_require_name(value, "candidate ID") for value in candidate_ids]
    columns = [_require_name(value, "metric column") for value in metric_columns]
    if len(set(candidates)) != len(candidates) or len(set(columns)) != len(columns):
        raise ControllerContractError("Candidate IDs and metric columns must be unique")
    if "time" in columns:
        raise ControllerContractError("RCD time column is not a rankable metric")
    if type(metric_owners) is not dict or set(metric_owners) != set(columns):
        raise ControllerContractError("Owner map must cover exactly the admitted metric columns")
    for key, owner in metric_owners.items():
        if type(key) is not str or type(owner) is not int or not 0 <= owner < len(candidates):
            raise ControllerContractError("Owner map has an invalid metric or candidate index")
    return candidates, columns, {key: metric_owners[key] for key in sorted(metric_owners)}


def _bind_rows(seed_outputs, columns):
    if type(seed_outputs) is not list or len(seed_outputs) != len(SEEDS):
        raise ControllerContractError("Exactly three registered seed outputs are required")
    bound = []
    for row in seed_outputs:
        if type(row) is not dict:
            raise ControllerContractError("Each seed output must be an object")
        if row.get("method") != METHOD or type(row.get("seed")) is not int:
            raise ControllerContractError("Unexpected RCD method or seed")
        if type(row.get("bins")) is not int or row["bins"] != PRIMARY_BINS:
            raise ControllerContractError("Only registered primary bins=5 are admissible")
        if row.get("status") == "SUCCESS":
            required = {
                "method", "seed", "bins", "status", "ranks", "reason", "error",
                "unknown_metric_keys",
            }
            if set(row) != required or row["reason"] is not None or row["error"] is not None:
                raise ControllerContractError("Malformed successful RCD output")
            ranks = row["ranks"]
            if (
                type(ranks) is not list
                or any(
                    type(key) is not str or not key or "/" in key or "\\" in key
                    or key in (".", "..") or _ABSOLUTE_PATH.match(key)
                    for key in ranks
                )
                or len(set(ranks)) != len(ranks)
            ):
                raise ControllerContractError("Unparseable or duplicate metric ranks")
            expected_unknown = [key for key in ranks if key not in columns]
            if type(row["unknown_metric_keys"]) is not list or row["unknown_metric_keys"] != expected_unknown:
                raise ControllerContractError("Unknown-key coverage differs from admitted columns")
            if not columns:
                raise ControllerContractError("RCD cannot succeed with no eligible metric columns")
        elif row.get("status") == "FAILURE":
            required = {"method", "seed", "bins", "status", "ranks", "reason", "error"}
            if set(row) != required or row["ranks"] is not None:
                raise ControllerContractError("Malformed failed RCD output")
            if type(row["reason"]) is not str or _SAFE_CODE.fullmatch(row["reason"]) is None:
                raise ControllerContractError("Failure reason must be a redacted code")
            if row["error"] is not None and (
                type(row["error"]) is not str or _SAFE_CODE.fullmatch(row["error"]) is None
            ):
                raise ControllerContractError("Failure error must be a redacted type")
        else:
            raise ControllerContractError("Unknown RCD seed status")
        bound.append(dict(row))
    if {row["seed"] for row in bound} != set(SEEDS):
        raise ControllerContractError("Missing or duplicate registered RCD seed")
    return sorted(bound, key=lambda row: row["seed"])


def _seal_rcd_predictions(
    seed_outputs,
    *,
    candidate_ids,
    metric_columns,
    metric_owners,
    input_sha256,
    qualification_scope,
    qualification_sha256,
):
    """Bind raw predictions, source mapping and honest qualification scope."""
    if qualification_scope == _SYNTHETIC:
        if qualification_sha256 is not None:
            raise ControllerContractError("Synthetic rows cannot claim RCD qualification")
    elif qualification_scope == _QUALIFIED:
        _require_sha256(qualification_sha256, "qualification_sha256")
    else:
        raise ControllerContractError("Unknown RCD qualification scope")
    candidates, columns, owners = _bind_source(candidate_ids, metric_columns, metric_owners)
    plain = {
        "schema": SCHEMA,
        "method": METHOD,
        "primary_bins": PRIMARY_BINS,
        "qualification_scope": qualification_scope,
        "qualification_sha256": qualification_sha256,
        "input_sha256": _require_sha256(input_sha256, "input_sha256"),
        "candidate_ids": candidates,
        "metric_columns": columns,
        "metric_owners": owners,
        "seed_outputs": _bind_rows(seed_outputs, columns),
    }
    return {**plain, "prediction_sha256": _digest(plain)}


def seal_synthetic_rcd_predictions(
    seed_outputs,
    *,
    candidate_ids,
    metric_columns,
    metric_owners,
    input_sha256,
):
    """Seal caller-supplied rows as SYNTHETIC_UNQUALIFIED only.

    This helper is for PRE-G fixtures.  It cannot produce claim-bearing RCD
    evidence, even when the supplied rows happen to match real method output.
    """
    return _seal_rcd_predictions(
        seed_outputs,
        candidate_ids=candidate_ids,
        metric_columns=metric_columns,
        metric_owners=metric_owners,
        input_sha256=input_sha256,
        qualification_scope=_SYNTHETIC,
        qualification_sha256=None,
    )


def _run_registered_rcd_triplet(
    frame,
    *,
    qualified_rcd,
    candidate_ids,
    metric_columns,
    metric_owners,
    input_sha256,
):
    """Call the frozen qualified comparator once per registered primary seed.

    The comparator is imported directly, never injected through this public
    API.  A fresh deep copy of the same verified 600-row numeric frame goes to
    each seed.  Unexpected per-seed exceptions become explicit failed seeds;
    neither the error message nor an evaluator label enters the prediction seal.
    """
    from rca.comparators import rcd_run
    from rca.qualified_rcd import QualifiedRcdRunner, qualified_callable

    if type(qualified_rcd) is not QualifiedRcdRunner or qualified_callable(qualified_rcd) is None:
        raise ControllerContractError("An issued QualifiedRcdRunner is required")
    try:
        qualification_sha256 = _digest(qualified_rcd.identity)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ControllerContractError("Qualified RCD identity is unavailable") from exc
    candidates, columns, owners = _bind_source(candidate_ids, metric_columns, metric_owners)
    if not isinstance(frame, pd.DataFrame) or frame.columns.duplicated().any():
        raise ControllerContractError("RCD input must be a nonduplicate numeric frame")
    if len(frame) != 600 or [column for column in frame.columns if column != "time"] != columns:
        raise ControllerContractError("RCD frame must contain the exact admitted metric columns")
    try:
        times = frame["time"].to_numpy(dtype=np.float64)
        values = frame[columns].to_numpy(dtype=np.float64)
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise ControllerContractError("RCD frame is not numeric") from exc
    if not np.array_equal(times, np.arange(600, dtype=np.float64)) or not np.isfinite(values).all():
        raise ControllerContractError("RCD frame has an invalid relative grid or nonfinite metric")
    actual_input_sha256 = hashlib.sha256(
        np.ascontiguousarray(values, dtype="<f8").tobytes()
    ).hexdigest()
    if actual_input_sha256 != _require_sha256(input_sha256, "input_sha256"):
        raise ControllerContractError("RCD numeric input differs from the source audit")

    outputs = []
    for seed in SEEDS:
        try:
            output = rcd_run(
                frame.copy(deep=True),
                seed=seed,
                bins=PRIMARY_BINS,
                qualified_rcd=qualified_rcd,
            )
        except Exception as exc:
            output = {
                "method": METHOD,
                "seed": seed,
                "bins": PRIMARY_BINS,
                "status": "FAILURE",
                "ranks": None,
                "reason": "controller_exception",
                "error": type(exc).__name__,
            }
        outputs.append(output)
    return _seal_rcd_predictions(
        outputs,
        candidate_ids=candidates,
        metric_columns=columns,
        metric_owners=owners,
        input_sha256=actual_input_sha256,
        qualification_scope=_QUALIFIED,
        qualification_sha256=qualification_sha256,
    )


def _bind_issued_triplets():
    """Bind qualification to exact outputs issued by the verified run path.

    The registry stays in a closure and admits no caller-supplied output.
    It is an ordinary-caller integrity boundary in this interpreter, not
    durable provenance or protection against hostile runtime modification.
    """
    issued: set[bytes] = set()
    run = _run_registered_rcd_triplet

    def run_registered_rcd_triplet(
        frame, *, qualified_rcd, candidate_ids, metric_columns, metric_owners, input_sha256
    ):
        sealed = run(
            frame,
            qualified_rcd=qualified_rcd,
            candidate_ids=candidate_ids,
            metric_columns=metric_columns,
            metric_owners=metric_owners,
            input_sha256=input_sha256,
        )
        issued.add(_canonical(sealed))
        return sealed

    def require_issued_triplet(sealed):
        if _canonical(sealed) not in issued:
            raise ControllerContractError("Qualified seal was not issued by this controller run")

    return run_registered_rcd_triplet, require_issued_triplet


run_registered_rcd_triplet, _require_issued_triplet = _bind_issued_triplets()
del _bind_issued_triplets, _run_registered_rcd_triplet


def verify_rcd_seal(sealed: object) -> bool:
    """Check integrity and current-interpreter issuance of qualified seals.

    JSON rehashing cannot promote synthetic output. Reopening a qualified
    seal in a fresh interpreter requires future durable G provenance work.
    """
    if type(sealed) is not dict or set(sealed) != {
        "schema", "method", "primary_bins", "input_sha256", "candidate_ids",
        "metric_columns", "metric_owners", "seed_outputs", "prediction_sha256",
        "qualification_scope", "qualification_sha256",
    }:
        raise ControllerContractError("A complete prediction seal is required")
    if sealed["schema"] != SCHEMA or sealed["method"] != METHOD or sealed["primary_bins"] != PRIMARY_BINS:
        raise ControllerContractError("Wrong PRE-G prediction contract")
    supplied = _require_sha256(sealed["prediction_sha256"], "prediction_sha256")
    plain = {key: value for key, value in sealed.items() if key != "prediction_sha256"}
    if supplied != _digest(plain):
        raise ControllerContractError("Prediction changed after sealing")
    rebuilt = _seal_rcd_predictions(
        sealed["seed_outputs"],
        candidate_ids=sealed["candidate_ids"],
        metric_columns=sealed["metric_columns"],
        metric_owners=sealed["metric_owners"],
        input_sha256=sealed["input_sha256"],
        qualification_scope=sealed["qualification_scope"],
        qualification_sha256=sealed["qualification_sha256"],
    )
    if rebuilt != sealed:
        raise ControllerContractError("Prediction seal is not canonical")
    if sealed["qualification_scope"] == _QUALIFIED:
        _require_issued_triplet(sealed)
    return True


def score_service_vector(scores, root_index, *, failed=False):
    """Reject malformed numerics before root-absent/failure scoring shortcuts."""
    try:
        values = np.asarray(scores, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ControllerContractError("Service scores are not numeric") from exc
    if values.ndim != 1 or not np.isfinite(values).all():
        raise ControllerContractError("Service scores must be a finite vector")
    if root_index is not None and (
        type(root_index) is not int or not 0 <= root_index < len(values)
    ):
        raise ControllerContractError("Evaluator root index is invalid; use None for absent root")
    return tie_metrics(values, root_index, failed=failed)


def evaluate_rcd_seal(sealed: object, *, root_index, allow_synthetic_fixture=False):
    """Evaluator-side metrics; qualified provenance required by default.

    The explicit synthetic flag is for PRE-G fixtures only.  A future Task G
    controller must durably persist/verify the qualified seal before labels.
    """
    verify_rcd_seal(sealed)
    if sealed["qualification_scope"] != _QUALIFIED and not allow_synthetic_fixture:
        raise ControllerContractError("Synthetic/unqualified rows are not G evidence")
    candidate_count = len(sealed["candidate_ids"])
    if root_index is not None and (
        type(root_index) is not int or not 0 <= root_index < candidate_count
    ):
        raise ControllerContractError("Evaluator root index is invalid; use None for absent root")
    per_seed = []
    for row in sealed["seed_outputs"]:
        failed = row["status"] != "SUCCESS"
        if failed:
            scores = np.zeros(candidate_count, dtype=np.float64)
            mapping = {"unknown_metric_keys": [], "ranked_services": 0}
        else:
            scores, mapping = service_scores_from_metric_ranks(
                row["ranks"], sealed["metric_owners"], candidate_count
            )
        metrics = score_service_vector(scores, root_index, failed=failed)
        per_seed.append({
            "seed": row["seed"],
            "status": row["status"],
            "service_scores": scores.tolist(),
            "mapping": mapping,
            "metrics": metrics,
        })
    return {
        "schema": "PRE-G-RCD-EVALUATION-v1",
        "prediction_sha256": sealed["prediction_sha256"],
        "qualification_scope": sealed["qualification_scope"],
        "evidence_scope": (
            "PRE_G_SYNTHETIC_TEST_ONLY"
            if sealed["qualification_scope"] == _SYNTHETIC
            else "QUALIFIED_CONTROLLER_OUTPUT__PERSISTENCE_STILL_REQUIRED"
        ),
        "planned_seeds": list(SEEDS),
        "root_in_candidate": root_index is not None,
        "per_seed": per_seed,
        "mean": {
            metric: sum(item["metrics"][metric] for item in per_seed) / len(SEEDS)
            for metric in METRICS
        },
        "success_seeds": sum(item["status"] == "SUCCESS" for item in per_seed),
        "failure_seeds": sum(item["status"] == "FAILURE" for item in per_seed),
        "valid_empty_seeds": sum(
            row["status"] == "SUCCESS" and row["ranks"] == []
            for row in sealed["seed_outputs"]
        ),
        "unknown_key_count": sum(
            len(item["mapping"]["unknown_metric_keys"]) for item in per_seed
        ),
    }


__all__ = [
    "ControllerContractError",
    "evaluate_rcd_seal",
    "run_registered_rcd_triplet",
    "score_service_vector",
    "seal_synthetic_rcd_predictions",
    "verify_rcd_seal",
]
