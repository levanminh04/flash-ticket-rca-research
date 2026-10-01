"""G32 bridge readiness seal; its key can never qualify an actual final run.

Only the fixed controller's issued execution can be committed. Every numerical
case, diagnostic, failure and cost is persisted, read back and semantically
checked before the authenticated envelope is published exclusively. Consumers
reopen the fixed host contract/anchor and all artifacts before invoking even an
artificial truth callback. This assumes an intact trusted host, not a sandbox.
"""
from __future__ import annotations

from datetime import datetime, timezone
import base64
import binascii
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import re
import secrets
import time

import numpy as np

from scripts.task_g import campaign_provenance as historical

RUN_ID = "g32-final-bridge-readiness"
DOMAIN = "FlashTicketRca/TD13/G32/BRIDGE-READINESS/v1"
PHASE = "FINAL_BRIDGE_READINESS_ONLY"
CONTRACT_SCHEMA = "TD13-G32-BRIDGE-READINESS-CONTRACT-v1"
EXECUTION_SCHEMA = "TD13-G32-BRIDGE-EXECUTION-v1"
SCHEMA = "TD13-G32-DURABLE-BRIDGE-READINESS-v1"
_WORKSPACE = Path(__file__).resolve().parents[2]
_PROJECT = Path("D:/Project/flash-ticket-platform")
_HOST_TRUST_MODE = "HOST_TRUSTED"
_FINAL_PERMISSIONS = (*historical._FINAL_PERMISSIONS, "final_root_fault")
_FROZEN = dict(historical._FROZEN)
_SOURCES = tuple(f"{root}/{prefix}{name}.py"
    for root, prefix in (("scripts/task_g", ""), ("tests/task_g", "test_"))
    for name in ("final_campaign", "final_source", "final_provenance", "final_evaluation"))
_COST_FIELDS = ("cold_io_seconds", "shared_preprocessing_seconds", "control_generation_seconds",
    "c5_fit_seconds", "c5_prediction_seconds", "integrated_seconds", "receipt_write_seconds")
_C1_DIAGNOSTICS = {"input", "evidence", "observed_adjacency", "graph_sha256", "degrees",
    "reachability", "uniform_personalization", "ranking"}
_PSEUDOKEY = re.compile(r"s[0-9a-f]{24}\Z")

FinalProvenanceError = historical.CampaignProvenanceError
_canonical = historical._canonical
_digest = historical._digest
_read_json = historical._read_json
_require_regular_path = historical._require_regular_path
_require_digest = historical._require_digest


def _run_root():
    return _WORKSPACE / "results/task-g" / RUN_ID


def _contract_path():
    return _run_root() / "run-contract.json"


def _receipt_path():
    return _run_root() / "readiness.json"


def _key_path():
    location = os.environ.get("LOCALAPPDATA")
    if not location or not Path(location).is_absolute():
        raise FinalProvenanceError("Trusted LOCALAPPDATA is unavailable")
    return Path(location) / "FlashTicketRca/task-g-trust" / RUN_ID / "issuer.key"


def _authorized_contract():
    raw, contract = _read_json(_contract_path())
    if (type(contract) is not dict or contract.get("schema") != CONTRACT_SCHEMA
            or contract.get("run_id") != RUN_ID or contract.get("domain") != DOMAIN
            or contract.get("phase") != PHASE):
        raise FinalProvenanceError("Wrong G32 registered readiness domain")
    permissions = contract.get("permissions")
    required = ("synthetic_development_conversion_readiness", "synthetic_evaluation",
                "tau_only_input_audit", "readiness_host_key_generation")
    if (type(permissions) is not dict or any(permissions.get(key) is not True for key in required)
            or any(permissions.get(key) is not False for key in _FINAL_PERMISSIONS)
            or permissions.get("telemetry_final60_new_acquisition") is not False):
        raise FinalProvenanceError("G32 readiness cannot grant final predictions, truth or campaign")
    if contract.get("frozen_inputs") != _FROZEN:
        raise FinalProvenanceError("Frozen method/release identity changed")
    return raw, contract


def readiness_anchor_descriptor():
    path = _key_path()
    _require_regular_path(path)
    key = path.read_bytes()
    if len(key) != 32:
        raise FinalProvenanceError("G32 key has invalid length; no repair")
    return {"algorithm": "HMAC-SHA256", "run_id": RUN_ID, "domain": DOMAIN,
            "trust_mode": _HOST_TRUST_MODE, "key_sha256": hashlib.sha256(key).hexdigest()}


def initialize_readiness_key():
    """Fixed exclusive host key; no caller anchor/path/key and no silent rotation."""
    _authorized_contract()
    path = _key_path()
    _require_regular_path(path, allow_missing=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    _require_regular_path(path, allow_missing=True)
    key = secrets.token_bytes(32)
    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(key)
            stream.flush()
            os.fsync(stream.fileno())
        if path.read_bytes() != key:
            raise FinalProvenanceError("G32 key readback differs")
    except OSError as exc:
        raise FinalProvenanceError("Key creation failed; existing bytes retained") from exc
    return readiness_anchor_descriptor()


def _validate_frozen_files(contract):
    paths = {
        "td_v1_3_sha256": _PROJECT / "docs/research-rca/task-d-method-and-experiment-specification.md",
        "task_f_v2_manifest_sha256": _WORKSPACE / "configs/task-f-td13-frozen-release-v2.json",
        "metadata_sha256": _WORKSPACE / "datasets/rcaeval/metadata/cases.parquet",
    }
    for key, path in paths.items():
        _require_regular_path(path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != _FROZEN[key]:
            raise FinalProvenanceError("Frozen file drift")
    protected = contract.get("protected_sha256")
    if type(protected) is not dict or not protected:
        raise FinalProvenanceError("Protected source/history references are required")
    for relative, expected in protected.items():
        if type(relative) is not str or relative[:2] not in ("P/", "W/"):
            raise FinalProvenanceError("Malformed protected reference")
        suffix = Path(relative[2:])
        if suffix.is_absolute() or ".." in suffix.parts:
            raise FinalProvenanceError("Protected reference escapes root")
        path = (_PROJECT if relative.startswith("P/") else _WORKSPACE) / suffix
        _require_regular_path(path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != _require_digest(expected):
            raise FinalProvenanceError("Protected source/history bytes changed")


def registered_context():
    """Current exact registration, loaded from the host rather than a bundle."""
    raw, contract = _authorized_contract()
    snapshot = contract.get("source_test_snapshot_before_qualification")
    if type(snapshot) is not dict or set(snapshot) != set(_SOURCES):
        raise FinalProvenanceError("Exactly eight stable G32 sources/tests required")
    for relative, expected in snapshot.items():
        path = _WORKSPACE / relative
        _require_regular_path(path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != _require_digest(expected):
            raise FinalProvenanceError("Registered G32 source/test drift")
    _validate_frozen_files(contract)
    historical._validate_environment(contract.get("environment"))
    anchor = readiness_anchor_descriptor()
    if contract.get("trust_anchor") != anchor:
        raise FinalProvenanceError("Registered G32 anchor differs or is absent")
    from scripts.task_g.campaign import prepare_conditions
    prepared = prepare_conditions()
    if (type(prepared) is not dict or prepared.get("conditions") != contract.get("prepared_conditions")
            or prepared.get("sha256") != _digest(contract["prepared_conditions"])):
        raise FinalProvenanceError("Frozen scientific configuration changed")
    return {"contract_sha256": hashlib.sha256(raw).hexdigest(),
        "source_snapshot_sha256": _digest(snapshot), "permissions": contract["permissions"],
        "permissions_sha256": _digest(contract["permissions"]), "config_sha256": prepared["sha256"],
        "environment_sha256": _digest(contract["environment"]),
        "resource_policy_sha256": _digest(contract.get("resource_policy")),
        "entry_bindings_sha256": _digest(contract.get("entry_bindings")),
        "frozen_inputs_sha256": _digest(_FROZEN), "anchor": anchor}, contract


_registered_context = registered_context


def _pseudokeys(values, count):
    if (type(values) is not list or len(values) != count
            or any(type(value) is not str or _PSEUDOKEY.fullmatch(value) is None for value in values)
            or len(set(values)) != count):
        raise FinalProvenanceError("Exact candidate pseudokey universe is incomplete")


def _validate_costs(costs):
    if type(costs) is not dict or any(field not in costs for field in _COST_FIELDS):
        raise FinalProvenanceError("Missing cost must be recorded explicitly, never imputed0")
    arms = {name: dict.fromkeys(("L", "O", "R")) for name in ("primary", "secondary")}
    families = {"arm_wall_seconds": arms, "arm_numeric_components_seconds": arms,
        "rank_seconds": {name: dict.fromkeys(("L", "O")) for name in ("primary", "secondary")},
        "R_rank_seconds": dict.fromkeys(("primary", "secondary"))}
    def duration(value, shape):
        if shape is None:
            if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value < 0):
                raise FinalProvenanceError("Cost seconds are missing or finite nonnegative")
            return
        value = {} if value is None else value
        if type(value) is not dict:
            raise FinalProvenanceError("Registered duration family requires typed components")
        for key, child in shape.items():
            duration(value.get(key), child)
        walk({key: item for key, item in value.items() if key not in shape})
    def walk(value):
        for key, item in value.items():
            if type(key) is not str:
                raise FinalProvenanceError("Cost component requires a name")
            if key in families:
                duration(item, families[key])
            elif key.endswith("_seconds"):
                duration(item, None)
            elif type(item) is dict:
                walk(item)
    walk(costs)


def _numeric(value, name, *, shape=None, kinds="biuf"):
    """Decode a numeric-only envelope without discarding NaN/missing masks."""
    if type(value) is dict:
        if set(value) != {"dtype", "shape", "bytes_b64"}:
            raise FinalProvenanceError("Malformed numeric diagnostic envelope: " + name)
        dimensions = value["shape"]
        if (type(dimensions) is not list or len(dimensions) > 5
                or any(type(size) is not int or size < 0 for size in dimensions)
                or type(value["dtype"]) is not str or type(value["bytes_b64"]) is not str):
            raise FinalProvenanceError("Malformed numeric diagnostic dimensions: " + name)
        try:
            dtype = np.dtype(value["dtype"])
            if dtype.kind not in kinds or dtype.itemsize > 8:
                raise ValueError("Non-numeric diagnostic dtype")
            expected = math.prod(dimensions) * dtype.itemsize
            if expected > historical._MAX_ARTIFACT_BYTES:
                raise ValueError("Numeric diagnostic exceeds bounded artifact size")
            raw = base64.b64decode(value["bytes_b64"], validate=True)
            if len(raw) != expected:
                raise ValueError("Numeric diagnostic bytes differ from shape")
            array = np.frombuffer(raw, dtype=dtype).reshape(dimensions)
        except (ValueError, TypeError, binascii.Error) as exc:
            raise FinalProvenanceError("Invalid numeric diagnostic envelope: " + name) from exc
    else:
        try:
            array = np.asarray(value)
        except (TypeError, ValueError) as exc:
            raise FinalProvenanceError("Invalid numeric diagnostic: " + name) from exc
        if array.dtype.kind not in kinds:
            raise FinalProvenanceError("Numeric diagnostic dtype differs: " + name)
    if shape is not None and array.shape != tuple(shape):
        raise FinalProvenanceError("Numeric diagnostic dimensions differ: " + name)
    if array.dtype.kind == "f" and np.isinf(array).any():
        raise FinalProvenanceError("Infinite diagnostic values cannot represent missing observations")
    return array


def _validate_c5_state(record, case_row, detector, selection):
    """Check scientific dimensions and masks; retain failures without fake state."""
    source, state = record["input"], record["state"]
    if (source == {} and record["status"] != "SUCCESS" and state is None and record["bins"] == []
            and case_row["ends"] == [] and record.get("reason") == "C5_OBSERVATION_UNAVAILABLE"):
        return
    if not {"warmup", "stream", "channel_types", "fit_mask", "adj", "endpoints"}.issubset(source):
        raise FinalProvenanceError("C5 full input provenance missing")
    warmup = _numeric(source["warmup"], "C5 warmup")
    if warmup.ndim != 3:
        raise FinalProvenanceError("C5 warmup must preserve bins, nodes and channels")
    bins, nodes, channels = warmup.shape
    _numeric(source["stream"], "C5 stream", shape=(len(case_row["ends"]), nodes, channels))
    types = _numeric(source["channel_types"], "C5 channel types", shape=(channels,), kinds="iu")
    fitmask = _numeric(source["fit_mask"], "C5 fit service mask", shape=(nodes,), kinds="b")
    adj = _numeric(source["adj"], "C5 adjacency", shape=(nodes, nodes), kinds="biu")
    if not np.isin(types, (0, 1, 2)).all() or not np.isin(adj, (0, 1)).all() or np.diag(adj).any():
        raise FinalProvenanceError("C5 channel/adjacency codes differ from frozen inputs")
    endpoints = _numeric(source["endpoints"], "C5 endpoints", shape=(len(case_row["ends"]),), kinds="iu")
    if endpoints.tolist() != case_row["ends"]:
        raise FinalProvenanceError("C5 input endpoints differ from registered bins")
    if state is None and record["status"] != "SUCCESS":
        if record["bins"]:
            raise FinalProvenanceError("C5 bin diagnostics require retained fit state")
        return
    required = {"config", "E", "centers", "scales", "adj", "channel_types", "fit_service_mask",
        "memberships", "degrees", "coefficients", "intercepts", "fit_model_mask", "model_mask",
        "residual_centers", "residual_scales", "history", "bins_seen", "calibration_errors",
        "calibration_predictions", "fit_target_mask", "calibration_target_mask", "warmup_z", "diagnostics"}
    if type(state) is not dict or not required.issubset(state) or type(state["config"]) is not dict:
        raise FinalProvenanceError("Frozen C5 model/scaler/calibration state incomplete")
    lag = state["config"].get("lag")
    if type(lag) is not int or lag < 1 or lag > bins:
        raise FinalProvenanceError("C5 lag diagnostic is malformed")
    width = lag + 4
    profile = selection.get("profile")
    if profile is not None:
        expected_cfg = {"arm": "G" if detector.startswith("TV-") else detector.split("-")[0],
            "modalities": detector.split("-")[1], "lambda": selection["selected_lambda"],
            "floor": profile["input_relative_floor"], "residual_floor": profile["residual_floor"],
            "lag": profile["lag"], "bin_seconds": profile["bin_seconds"], "fit_bins": profile["fit_bins"],
            "cal_bins": profile["calibration_bins"], "min_fit_rows": profile["min_fit_rows"], "min_cal_rows": profile["min_calibration_rows"]}
        if any(state["config"].get(key) != value for key, value in expected_cfg.items()):
            raise FinalProvenanceError("C5 model configuration differs from frozen selection")
    decoded = {}
    for key in ("E", "fit_model_mask", "model_mask"):
        decoded[key] = _numeric(state[key], key, shape=(nodes, channels), kinds="b")
    for key in ("centers", "scales", "intercepts", "residual_centers", "residual_scales"):
        decoded[key] = _numeric(state[key], key, shape=(nodes, channels))
    coefficients = _numeric(state["coefficients"], "C5 coefficients", shape=(nodes, channels, width))
    if (not np.isfinite(coefficients[decoded["fit_model_mask"]]).all()
            or not np.isfinite(decoded["intercepts"][decoded["fit_model_mask"]]).all()):
        raise FinalProvenanceError("C5 fitted target coefficients/intercepts are missing")
    _numeric(state["history"], "C5 history", shape=(lag, nodes, channels))
    _numeric(state["warmup_z"], "C5 standardized warmup", shape=(bins, nodes, channels))
    fit_targets = _numeric(state["fit_target_mask"], "C5 fit targets", kinds="b")
    cal_targets = _numeric(state["calibration_target_mask"], "C5 calibration targets", kinds="b")
    if (fit_targets.ndim != 3 or cal_targets.ndim != 3 or fit_targets.shape[1:] != (nodes, channels)
            or cal_targets.shape[1:] != (nodes, channels) or len(fit_targets) + len(cal_targets) != bins):
        raise FinalProvenanceError("C5 fit/calibration target masks differ from warmup")
    for key in ("calibration_errors", "calibration_predictions"):
        _numeric(state[key], key, shape=cal_targets.shape)
    for key, expected, kinds in (("adj", adj, "biu"), ("channel_types", types, "iu"), ("fit_service_mask", fitmask, "b")):
        if not np.array_equal(_numeric(state[key], key, shape=expected.shape, kinds=kinds), expected):
            raise FinalProvenanceError("C5 fit state changed the issued numerical input")
    if (np.any(decoded["fit_model_mask"] & ~decoded["E"])
            or np.any(decoded["model_mask"] & ~decoded["fit_model_mask"])
            or np.any(decoded["E"] & ~fitmask[:, None])):
        raise FinalProvenanceError("C5 model/applicability/fit service masks are inconsistent")
    for mask, fields in (("E", ("centers", "scales")), ("model_mask", ("residual_centers", "residual_scales"))):
        for field in fields:
            if not np.isfinite(decoded[field][decoded[mask]]).all():
                raise FinalProvenanceError("Available C5 scaler/residual values are missing")
        if np.any(decoded[fields[1]][decoded[mask]] <= 0):
            raise FinalProvenanceError("Available C5 scale must be positive")
    for family in ("memberships", "degrees"):
        if type(state[family]) is not dict or set(state[family]) != {"out", "in", "all"}:
            raise FinalProvenanceError("C5 neighborhood diagnostics are incomplete")
        for key in state[family]:
            values = _numeric(state[family][key], family + "." + key,
                shape=(nodes, nodes, channels) if family == "memberships" else (nodes, channels),
                kinds="b" if family == "memberships" else "iu")
            topology = adj if key == "out" else adj.T if key == "in" else ~np.eye(nodes, dtype=bool)
            membership = topology[:, :, None] & decoded["E"][None, :, :]
            if not np.array_equal(values, membership if family == "memberships" else membership.sum(axis=1)):
                raise FinalProvenanceError("C5 neighborhood membership/degree differs from graph and masks")
    quality = state["diagnostics"]
    required_quality = {"finite_fit_support", "singleton_scale", "constant_scale", "scale_floor_used",
        "applicability_reasons", "fit_rows", "calibration_rows", "model_count", "ridge",
        "residual_floor_used", "constant_calibration_errors"}
    if (type(quality) is not dict or not required_quality.issubset(quality)
            or type(state["bins_seen"]) is not int or state["bins_seen"] < bins):
        raise FinalProvenanceError("C5 fit quality/counter diagnostics are missing")
    for field in ("finite_fit_support", "fit_rows", "calibration_rows"):
        values = _numeric(quality[field], "C5 quality." + field, shape=(nodes, channels), kinds="iu")
        if field in ("fit_rows", "calibration_rows") and not np.array_equal(values,
                (fit_targets if field == "fit_rows" else cal_targets).sum(axis=0)):
            raise FinalProvenanceError("C5 row support differs from retained target masks")
    for field in ("singleton_scale", "constant_scale", "scale_floor_used", "residual_floor_used", "constant_calibration_errors"):
        _numeric(quality[field], "C5 quality." + field, shape=(nodes, channels), kinds="b")
    if (type(quality["model_count"]) is not int or quality["model_count"] != int(decoded["model_mask"].sum())
            or np.asarray(quality["applicability_reasons"]).shape != (nodes, channels)
            or type(quality["ridge"]) is not list or len(quality["ridge"]) != nodes
            or any(type(row) is not list or len(row) != channels for row in quality["ridge"])):
        raise FinalProvenanceError("C5 model count/reasons/ridge dimensions differ")
    ridge_fields = {"centered_design_rank", "design_rank_with_intercept", "effective_ridge_df", "scaled_centered_singular_values",
        "singular_value_scale", "active_columns", "fit_rows", "nominal_columns", "intercept_unpenalized"}
    for node, channel in np.argwhere(decoded["fit_model_mask"]):
        ridge = quality["ridge"][node][channel]
        if type(ridge) is not dict or not ridge_fields.issubset(ridge) or ridge["intercept_unpenalized"] is not True:
            raise FinalProvenanceError("C5 fitted target ridge diagnostics missing")
        _numeric(ridge["scaled_centered_singular_values"], "C5 ridge singular values")
    from scripts.task_e.detection import create_event_state, event_step
    event_state = create_event_state(case_row["threshold"], bin_seconds=5, streak=3, refractory_seconds=300)
    required_bin = {"score", "residuals", "errors", "predictions", "target_mask", "z", "features",
        "availability", "endpoint", "start", "scored_channels", "tv_score", "tv_channels", "tv_edge_counts",
        "tv_failure", "local_magnitude", "selected_system_score", "event"}
    for index, row in enumerate(record["bins"]):
        if (type(row) is not dict or not required_bin.issubset(row)
                or row["endpoint"] != case_row["ends"][index] or row["start"] != case_row["starts"][index]):
            raise FinalProvenanceError("C5 full bin fields/order/endpoints incomplete")
        target = _numeric(row["target_mask"], "C5 bin targets", shape=(nodes, channels), kinds="b")
        if np.any(target & ~decoded["model_mask"]):
            raise FinalProvenanceError("C5 scored bin exceeds fitted model mask")
        for field in ("residuals", "errors", "predictions", "z"):
            values = _numeric(row[field], "C5 bin." + field, shape=(nodes, channels))
            if field != "z" and not np.isfinite(values[target]).all():
                raise FinalProvenanceError("C5 available target lost prediction/residual")
        _numeric(row["features"], "C5 bin features", shape=(nodes, channels, width))
        availability = row["availability"]
        arm = state["config"].get("arm")
        expected_availability = set() if arm == "L" else {"available_out", "available_in"} if arm == "G" else {"available_all"}
        if type(availability) is not dict or set(availability) != expected_availability:
            raise FinalProvenanceError("C5 neighbor feature availability masks missing")
        for name in availability:
            _numeric(availability[name], "C5 bin availability." + name, shape=(nodes, channels), kinds="iu")
        _numeric(row["tv_channels"], "C5 TV channels", shape=(channels,))
        if row["tv_edge_counts"] is not None:
            _numeric(row["tv_edge_counts"], "C5 TV edge counts", shape=(channels,), kinds="iu")
        if type(row["scored_channels"]) is not int or row["scored_channels"] != int(target.sum()):
            raise FinalProvenanceError("C5 scored-channel count differs from target mask")
        score = row["selected_system_score"]
        if score is not None:
            historical._finite(score)
        if score != row["tv_score" if detector.startswith("TV-") else "score"]:
            raise FinalProvenanceError("C5 selected system score changed the frozen detector arm")
        expected_event = event_step(event_state, np.nan if score is None else score, row["endpoint"])
        if row["event"] != expected_event:
            raise FinalProvenanceError("C5 event diagnostics changed frozen trigger policy")
        if score != case_row["scores"][index]:
            raise FinalProvenanceError("C5 bin system score differs from compact evaluator record")


def _validate_rank_diagnostics(record, count, compact=None, selected=None):
    if type(record) is not dict:
        raise FinalProvenanceError("Rank operator diagnostics missing")
    if record.get("status") in historical._STATUSES - {"SUCCESS"}:
        if compact is not None and compact["status"] == "SUCCESS":
            raise FinalProvenanceError("Successful compact rank lost full operator diagnostics")
        return
    if not {"scores", "rounded_scores", "diagnostics"}.issubset(record):
        raise FinalProvenanceError("Full rank scores/operator diagnostics missing")
    for name in ("scores", "rounded_scores"):
        if not np.isfinite(_numeric(record[name], "Rank " + name, shape=(count,))).all():
            raise FinalProvenanceError("Successful rank diagnostic score missing")
    if compact is not None and (compact["status"] != "SUCCESS"
            or not np.array_equal(_numeric(record["scores"], "Rank scores"), compact["scores"])):
        raise FinalProvenanceError("Full rank diagnostics disagree with compact rank output")
    diag = record["diagnostics"]
    required = {"operator", "direction", "damping", "raw_local_scale", "isolates", "transition", "no_evidence", "residual_inf"}
    if (type(diag) is not dict or not required.issubset(diag)
            or diag["operator"] not in ("ppr", "diffusion") or diag["direction"] not in ("reverse", "undirected")):
        raise FinalProvenanceError("Frozen rank operator state incomplete")
    _numeric(diag["isolates"], "Rank isolates", shape=(count,), kinds="b")
    transition = _numeric(diag["transition"], "Rank transition", shape=(count, count))
    if not np.isfinite(transition).all() or np.any(transition < 0) or not np.allclose(transition.sum(axis=1), 1., atol=1e-12):
        raise FinalProvenanceError("Rank stochastic transition is malformed")
    for name in ("damping", "raw_local_scale", "residual_inf"):
        historical._finite(diag[name])
    if diag["operator"] == "ppr":
        _numeric(diag.get("personalization"), "Rank personalization", shape=(count,))
    if selected is not None and (diag["operator"] != selected["operator"]
            or diag["direction"] != selected["direction"]
            or diag["damping"] != selected.get("damping", selected.get("alpha"))):
        raise FinalProvenanceError("Rank diagnostic operator differs from frozen selection")


def _validate_c1_diagnostics(c1, case, selection=None, *, integrated=False):
    count = case["candidate_count"]
    successful = integrated or any(arm["status"] == "SUCCESS" for group in case["c1"].values()
        for arm in [group["L"], group["O"], *group["R"]])
    if not successful and c1.get("evidence") is None:
        if c1.get("status") not in ("UNAVAILABLE_WORKER_FAILURE", "UNAVAILABLE_SOURCE_OBSERVATION"):
            raise FinalProvenanceError("Missing C1 diagnostics require explicit worker failure")
        _numeric(c1["observed_adjacency"], "Failed C1 issued adjacency", shape=(count, count), kinds="biu")
        return
    source, evidence = c1["input"], c1["evidence"]
    if type(source) is not dict or not {"ref", "query", "adj", "channel_types"}.issubset(source):
        raise FinalProvenanceError("C1 numeric source provenance incomplete")
    ref, query = _numeric(source["ref"], "C1 reference"), _numeric(source["query"], "C1 query")
    if ref.ndim != 3 or query.ndim != 3 or ref.shape[:2] != query.shape[:2] or ref.shape[0] != count:
        raise FinalProvenanceError("C1 reference/query dimensions differ")
    channels = ref.shape[1]
    _numeric(source["channel_types"], "C1 channel types", shape=(channels,), kinds="iu")
    if (type(evidence) is not dict or not {"local", "blocks", "channel_scores", "masks", "diagnostics"}.issubset(evidence)):
        raise FinalProvenanceError("C1 complete local evidence/masks/scalers missing")
    local = _numeric(evidence["local"], "C1 local", shape=(count,))
    channel_scores = _numeric(evidence["channel_scores"], "C1 channel scores", shape=(count, channels))
    if not integrated and case["shared_preprocessing_failed"] is False and not np.array_equal(local, case["local_evidence"]):
        raise FinalProvenanceError("C1 scientific local evidence differs from compact retained input")
    masks, diag = evidence["masks"], evidence["diagnostics"]
    if type(masks) is not dict or set(masks) != {"channels", "blocks", "local"}:
        raise FinalProvenanceError("C1 evidence availability masks missing")
    available = _numeric(masks["channels"], "C1 channel availability", shape=(count, channels), kinds="b")
    if not np.isfinite(channel_scores[available]).all():
        raise FinalProvenanceError("C1 available channel score is missing")
    _numeric(masks["local"], "C1 local availability", shape=(count,), kinds="b")
    for family, kinds in ((evidence["blocks"], "biuf"), (masks["blocks"], "b")):
        if type(family) is not dict or set(family) != {"metric", "trace", "log"}:
            raise FinalProvenanceError("C1 modality scores/masks incomplete")
        for name in family:
            _numeric(family[name], "C1 modality " + name, shape=(count,), kinds=kinds)
    required = {"reference_valid_bins", "query_valid_bins", "reference_min_bins", "query_min_bins", "centers", "scales",
        "channel_reasons", "numerical_channel_failures", "config"}
    if type(diag) is not dict or not required.issubset(diag):
        raise FinalProvenanceError("C1 local scientific quality/scaler diagnostics incomplete")
    for name, kinds in (("reference_valid_bins", "iu"), ("query_valid_bins", "iu"), ("centers", "biuf"), ("scales", "biuf"),
                        ("numerical_channel_failures", "b")):
        _numeric(diag[name], "C1 diagnostics." + name, shape=(count, channels), kinds=kinds)
    if np.asarray(diag["channel_reasons"]).shape != (count, channels) or type(diag["config"]) is not dict:
        raise FinalProvenanceError("C1 channel reasons/config incomplete")
    if selection is not None:
        expected_config = {**selection["local"], **({"include_logs": True} if integrated else {})}
        if diag["config"] != expected_config:
            raise FinalProvenanceError("C1 evidence configuration differs from frozen selection")
    array = _numeric(c1["observed_adjacency"], "C1 observed adjacency", shape=(count, count), kinds="biu")
    if not np.array_equal(_numeric(source["adj"], "C1 issued adjacency", shape=(count, count), kinds="biu"), array):
        raise FinalProvenanceError("C1 diagnostic adjacency differs from issued numeric input")
    if not np.isin(array, (0, 1)).all() or np.any(np.diag(array)):
        raise FinalProvenanceError("Observed directed adjacency lost exact candidate order")
    binary = array.astype(bool)
    digest = hashlib.sha256(str(binary.shape).encode("ascii") + np.packbits(binary).tobytes()).hexdigest()
    if c1["graph_sha256"] != digest:
        raise FinalProvenanceError("Observed graph digest differs from numerical adjacency")
    if type(c1["degrees"]) is not dict or set(c1["degrees"]) != {"in", "out", "undirected"}:
        raise FinalProvenanceError("C1 graph degree diagnostics missing")
    for name, expected in (("in", binary.sum(axis=0)), ("out", binary.sum(axis=1)), ("undirected", (binary | binary.T).sum(axis=1))):
        if not np.array_equal(_numeric(c1["degrees"][name], "C1 degree." + name, shape=(count,), kinds="iu"), expected):
            raise FinalProvenanceError("C1 degree diagnostics differ from adjacency")
    reachable = binary | np.eye(count, dtype=bool)
    for pivot in range(count):
        reachable |= reachable[:, pivot, None] & reachable[None, pivot, :]
    if not np.array_equal(_numeric(c1["reachability"], "C1 reachability", shape=(count, count), kinds="b"), reachable):
        raise FinalProvenanceError("C1 reachability differs from observed graph")
    if type(c1["uniform_personalization"]) is not dict or set(c1["uniform_personalization"]) != {"primary", "secondary"}:
        raise FinalProvenanceError("C1 uniform-personalization nuisance ranks missing")
    for name, row in c1["uniform_personalization"].items():
        selected = None if selection is None else selection["primary_ppr" if name == "primary" else "secondary_diffusion"]
        _validate_rank_diagnostics(row, count, selected=selected)
    if successful:
        if type(c1["ranking"]) is not dict or set(c1["ranking"]) != {"primary", "secondary"}:
            raise FinalProvenanceError("C1 primary/secondary rank operator diagnostics missing")
        for name in ("primary", "secondary"):
            selected = None if selection is None else selection["primary_ppr" if name == "primary" else "secondary_diffusion"]
            for arm in ("L", "O"):
                compact = (case if name == "primary" and arm == "O" else None) if integrated else case["c1"][name][arm]
                _validate_rank_diagnostics(c1["ranking"][name].get(arm), count, compact, selected)
            for row in ([] if integrated else case["c1"][name]["R"]):
                if row["status"] == "SUCCESS":
                    _validate_rank_diagnostics(row.get("operator_diagnostics"), count, row, selected)


def _validate_diagnostics(case, prepared):
    diagnostics = case.get("scientific_diagnostics")
    if type(diagnostics) is not dict or set(diagnostics) != {"c1", "c5", "quality", "controller_bindings"}:
        raise FinalProvenanceError("Full scientific diagnostics/quality/bindings are required")
    c1 = diagnostics["c1"]
    if type(c1) is not dict or not _C1_DIAGNOSTICS.issubset(c1):
        raise FinalProvenanceError("C1 input/evidence/graph/nuisance/ranking diagnostics missing")
    count = case["candidate_count"]
    selections = prepared["scientific_objects"]["selections"]
    _validate_c1_diagnostics(c1, case, selections.get("c1"))
    if type(diagnostics["quality"]) is not dict or not diagnostics["quality"]:
        raise FinalProvenanceError("Scientific input quality is absent")
    c5 = diagnostics["c5"]
    if type(c5) is not dict or set(c5) != historical._DETECTORS:
        raise FinalProvenanceError("All eight C5 scientific diagnostic records are required")
    for name, record in c5.items():
        if (type(record) is not dict or not {"state", "bins", "input", "status"}.issubset(record)
                or record["status"] not in historical._STATUSES
                or type(record["input"]) is not dict or type(record["bins"]) is not list):
            raise FinalProvenanceError("C5 model/scaler/masks/quality/bin state missing")
        if record["status"] == "SUCCESS" and type(record["state"]) is not dict:
            raise FinalProvenanceError("Successful C5 requires full frozen fit state")
        planned_bins = len(case["c5"][name]["ends"])
        if (len(record["bins"]) > planned_bins or record["status"] != case["c5"][name]["status"]
                or (record["status"] == "SUCCESS" and len(record["bins"]) != planned_bins)):
            raise FinalProvenanceError("C5 full diagnostics must preserve every planned bin")
        _validate_c5_state(record, case["c5"][name], name, selections["c5"])
    binding = diagnostics["controller_bindings"]
    if type(binding) is not dict or not {"candidate_ids", "integrated_candidate_ids"}.issubset(binding):
        raise FinalProvenanceError("Evaluator candidate universe bindings are absent")
    _pseudokeys(binding["candidate_ids"], count)
    trigger_maps = binding["integrated_candidate_ids"]
    if type(trigger_maps) is not dict or set(trigger_maps) != historical._DETECTORS:
        raise FinalProvenanceError("Every detector needs its trigger-local candidate universes")
    for name, row in case["c5"].items():
        expected = {str(trigger["endpoint"]) for trigger in row["triggers"]}
        if type(trigger_maps[name]) is not dict or set(trigger_maps[name]) != expected:
            raise FinalProvenanceError("Missing or extra trigger-local universe")
        for trigger in row["triggers"]:
            _pseudokeys(trigger_maps[name][str(trigger["endpoint"])], trigger["candidate_count"])
            if trigger["status"] == "SUCCESS":
                if (trigger.get("candidate_ids") != trigger_maps[name][str(trigger["endpoint"])]
                        or type(trigger.get("quality")) is not dict or not trigger["quality"]
                        or type(trigger.get("graph_provenance")) is not dict or not trigger["graph_provenance"]
                        or type(trigger.get("scientific_diagnostics")) is not dict
                        or not _C1_DIAGNOSTICS.issubset(trigger["scientific_diagnostics"])):
                    raise FinalProvenanceError("Successful integrated trigger lacks full scientific provenance")
                _validate_c1_diagnostics(trigger["scientific_diagnostics"], trigger, selections.get("c1"), integrated=True)
    historical._no_oracles(diagnostics)
    _canonical(diagnostics)
    _validate_costs(case.get("costs"))


def _validate_execution(payload, context, contract):
    if (type(payload) is not dict or payload.get("schema") != EXECUTION_SCHEMA
            or payload.get("run_id") != RUN_ID or payload.get("domain") != DOMAIN
            or payload.get("phase") != PHASE or payload.get("trust_mode") != _HOST_TRUST_MODE
            or payload.get("scope") != "SYNTHETIC_BRIDGE_READINESS"):
        raise FinalProvenanceError("Wrong G32 issued execution scope/domain")
    for key in ("source_snapshot_sha256", "permissions_sha256", "config_sha256"):
        if payload.get(key) != context[key]:
            raise FinalProvenanceError("G32 execution registration drift")
    if payload.get("prepared_conditions") != contract.get("prepared_conditions"):
        raise FinalProvenanceError("G32 execution scientific configuration changed")
    if (type(payload.get("source_summary")) is not dict
            or payload["source_summary"].get("source_kind") != "THREE_DISTINCT_ARTIFICIAL_ARCHIVES"):
        raise FinalProvenanceError("Actual telemetry cannot be signed as readiness predictions")
    count = payload.get("planned_case_count")
    if type(count) is not int or not 1 <= count <= 3 or type(payload.get("cases")) is not list or len(payload["cases"]) != count:
        raise FinalProvenanceError("G32 numerical qualification is bounded to at most3 synthetic cases")
    for ordinal, case in enumerate(payload["cases"]):
        if (type(case) is not dict or case.get("ordinal") != ordinal
                or case.get("cell_ordinal") != ordinal or case.get("repeat") != 0
                or type(case.get("shared_preprocessing_failed")) is not bool):
            raise FinalProvenanceError("Distinct synthetic case identity changed")
        _require_digest(case.get("numeric_input_sha256"))
        historical._no_oracles(case)
        historical._validate_c1(case)
        historical._validate_contextual(case)
        historical._validate_c5(case, payload["prepared_conditions"])
        _validate_diagnostics(case, payload["prepared_conditions"])
    if "orchestration_fixture" in payload:
        fixture = payload["orchestration_fixture"]
        if (type(fixture) is not dict or fixture.get("scope") != "SYNTHETIC_ONLY_ORCHESTRATION"
                or fixture.get("final_prediction_qualified") is not False
                or fixture.get("planned_slots") != 60 or fixture.get("ordinals") != list(range(60))
                or fixture.get("numerical_computations") != 0):
            raise FinalProvenanceError("Orchestration fixture must not manufacture final qualification")
    historical._no_oracles(payload.get("source_summary"))
    _canonical(payload)


def _artifact_path(digest):
    return _run_root() / "cache/artifacts" / (_require_digest(digest) + ".json")


def _write_stage(encoded, target, prefix):
    """Keep every failed staging attempt; publish only fully durable readback."""
    _require_regular_path(target, allow_missing=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    _require_regular_path(target, allow_missing=True)
    stage = target.parent / (prefix + secrets.token_hex(16) + ".json")
    _require_regular_path(stage, allow_missing=True)
    try:
        fd = os.open(str(stage), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        if stage.read_bytes() != encoded:
            raise FinalProvenanceError("Artifact durable readback differs")
        os.link(str(stage), str(target))
    except OSError as exc:
        raise FinalProvenanceError("Artifact publication failed; stage retained") from exc


def _persist_case(case):
    encoded = _canonical(case)
    digest = hashlib.sha256(encoded).hexdigest()
    target = _artifact_path(digest)
    _require_regular_path(target, allow_missing=True)
    if len(encoded) > historical._MAX_ARTIFACT_BYTES:
        raise FinalProvenanceError("Case diagnostic artifact exceeds bounded size")
    if target.exists():
        if target.read_bytes() != encoded:
            raise FinalProvenanceError("Existing content-addressed artifact differs")
    else:
        _write_stage(encoded, target, "artifact-attempt-")
    return {"ordinal": case["ordinal"], "role": "SYNTHETIC_BRIDGE_CASE", "sha256": digest, "bytes": len(encoded)}


def _read_artifacts(header, manifest):
    count = header.get("planned_case_count") if type(header) is dict else None
    if type(count) is not int or not 1 <= count <= 3 or type(manifest) is not list or len(manifest) != count:
        raise FinalProvenanceError("Durable synthetic case manifest incomplete")
    cases = []
    for ordinal, row in enumerate(manifest):
        if (type(row) is not dict or set(row) != {"ordinal", "role", "sha256", "bytes"}
                or row["ordinal"] != ordinal or row["role"] != "SYNTHETIC_BRIDGE_CASE"):
            raise FinalProvenanceError("Missing/duplicate/reordered/stale artifact ordinal")
        raw, case = _read_json(_artifact_path(row["sha256"]))
        if (type(row["bytes"]) is not int or row["bytes"] != len(raw)
                or hashlib.sha256(raw).hexdigest() != row["sha256"] or raw != _canonical(case)):
            raise FinalProvenanceError("Case bytes/hash/canonical readback differ")
        cases.append(case)
    payload = json.loads(_canonical(header))
    payload["cases"] = cases
    return payload


def _verify_envelope(raw, envelope, context, contract):
    if type(envelope) is not dict or set(envelope) != {"commitment", "hmac_sha256"}:
        raise FinalProvenanceError("Complete authenticated G32 envelope required")
    commitment = envelope["commitment"]
    fields = {"schema", "run_id", "domain", "phase", "recorded_at_utc", "context",
        "execution_header", "artifact_manifest", "artifact_manifest_sha256", "execution_sha256",
        "costs", "final_prediction_qualified", "final_labels", "final_campaign"}
    if (type(commitment) is not dict or set(commitment) != fields or commitment["schema"] != SCHEMA
            or commitment["run_id"] != RUN_ID or commitment["domain"] != DOMAIN or commitment["phase"] != PHASE
            or commitment["context"] != context or any(commitment[key] is not False
                for key in ("final_prediction_qualified", "final_labels", "final_campaign"))):
        raise FinalProvenanceError("Wrong G32 seal context or unauthorized final promotion")
    tag = hmac.new(_key_path().read_bytes(), _canonical(commitment), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(tag, _require_digest(envelope["hmac_sha256"])) or raw != _canonical(envelope):
        raise FinalProvenanceError("G32 authentication/canonical readback failed")
    if commitment["artifact_manifest_sha256"] != _digest(commitment["artifact_manifest"]):
        raise FinalProvenanceError("Artifact manifest drift")
    costs = commitment["costs"]
    if (type(costs) is not dict or costs.get("receipt_write_seconds") is not None
            or costs.get("receipt_write_status") != "OPEN_SELF_SEAL_DURATION_NOT_SELF_MEASURABLE"
            or type(costs.get("artifact_write_seconds")) not in (int, float)
            or not math.isfinite(costs["artifact_write_seconds"]) or costs["artifact_write_seconds"] < 0):
        raise FinalProvenanceError("Seal costs must preserve unavailable self-seal duration")
    payload = _read_artifacts(commitment["execution_header"], commitment["artifact_manifest"])
    _validate_execution(payload, context, contract)
    if commitment["execution_sha256"] != _digest(payload):
        raise FinalProvenanceError("Complete issued numeric execution changed")
    return {"status": "PASS_DURABLE_G32_SYNTHETIC_BRIDGE_ONLY", "run_id": RUN_ID, "domain": DOMAIN,
        "phase": PHASE, "scope": payload["scope"], "trust_mode": _HOST_TRUST_MODE,
        "planned_cases": payload["planned_case_count"], "persisted_case_artifacts": len(payload["cases"]),
        "receipt_sha256": hashlib.sha256(raw).hexdigest(), "payload_sha256": commitment["execution_sha256"],
        "artifact_manifest_sha256": commitment["artifact_manifest_sha256"],
        "seal_costs": costs, "final_prediction_qualified": False}, payload


def _bind_committer():
    def commit_readiness(execution_handle):
        from scripts.task_g.final_campaign import _readiness_payload_for_provenance
        context, contract = registered_context()
        payload = _readiness_payload_for_provenance(execution_handle)
        _validate_execution(payload, context, contract)
        payload = json.loads(_canonical(payload))
        target = _receipt_path()
        _require_regular_path(target, allow_missing=True)
        if target.exists():
            raise FinalProvenanceError("G32 receipt exists; no overwrite or favorable rerun")
        started = time.perf_counter()
        manifest = [_persist_case(case) for case in payload["cases"]]
        artifact_seconds = time.perf_counter() - started
        header = {key: value for key, value in payload.items() if key != "cases"}
        commitment = {"schema": SCHEMA, "run_id": RUN_ID, "domain": DOMAIN, "phase": PHASE,
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(), "context": context,
            "execution_header": header, "artifact_manifest": manifest,
            "artifact_manifest_sha256": _digest(manifest), "execution_sha256": _digest(payload),
            "costs": {"artifact_write_seconds": artifact_seconds, "receipt_write_seconds": None,
                "receipt_write_status": "OPEN_SELF_SEAL_DURATION_NOT_SELF_MEASURABLE"},
            "final_prediction_qualified": False, "final_labels": False, "final_campaign": False}
        prefix = b'{"commitment":' + _canonical(commitment)
        stage = _run_root() / "cache" / ("seal-attempt-" + secrets.token_hex(16) + ".json")
        stage.parent.mkdir(parents=True, exist_ok=True)
        _require_regular_path(stage, allow_missing=True)
        try:
            fd = os.open(str(stage), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(prefix)
                stream.flush()
                os.fsync(stream.fileno())
                if stage.read_bytes() != prefix:
                    raise FinalProvenanceError("Numeric commitment readback differs")
                tag = hmac.new(_key_path().read_bytes(), _canonical(commitment), hashlib.sha256).hexdigest()
                envelope = {"commitment": commitment, "hmac_sha256": tag}
                encoded = _canonical(envelope)
                if not encoded.startswith(prefix):
                    raise FinalProvenanceError("Unexpected canonical G32 envelope")
                stream.write(encoded[len(prefix):])
                stream.flush()
                os.fsync(stream.fileno())
            if stage.read_bytes() != encoded:
                raise FinalProvenanceError("Authenticated seal readback differs")
            fresh_context, fresh_contract = registered_context()
            _verify_envelope(encoded, envelope, fresh_context, fresh_contract)
            os.link(str(stage), str(target))
        except OSError as exc:
            raise FinalProvenanceError("G32 seal publication failed; staging retained") from exc
        return verify_readiness_receipt()
    return commit_readiness


commit_readiness = _bind_committer()
del _bind_committer


def verify_readiness_receipt():
    context, contract = registered_context()
    raw, envelope = _read_json(_receipt_path())
    summary, _ = _verify_envelope(raw, envelope, context, contract)
    return summary


def require_verified_readiness_execution():
    context, contract = registered_context()
    raw, envelope = _read_json(_receipt_path())
    summary, payload = _verify_envelope(raw, envelope, context, contract)
    payload["_verified_context"] = {"permissions": dict(context["permissions"]),
        "receipt_sha256": summary["receipt_sha256"], "final_prediction_qualified": False}
    return payload


def require_final_campaign_receipt():
    raise FinalProvenanceError("G32 readiness key/domain cannot authorize final campaign or labels")


__all__ = ["FinalProvenanceError", "registered_context", "initialize_readiness_key",
    "readiness_anchor_descriptor", "commit_readiness", "verify_readiness_receipt",
    "require_verified_readiness_execution", "require_final_campaign_receipt"]
