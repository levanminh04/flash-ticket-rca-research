"""Durable commitments for G31 synthetic/development readiness only.

The fixed host key and receipt are deliberately in a different domain from
ENTRY and any future final run.  This module never signs caller dictionaries,
accepts a caller path/anchor, or grants final-label permission.  HMAC assumes
an intact controller, evaluator, Python runtime and filesystem; a verifier
sharing the key is not independent cryptographic attestation.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import re
import secrets
import stat

import numpy as np


RUN_ID = "g31-campaign-readiness"
DOMAIN = "FlashTicketRca/TD13/G31/READINESS/v1"
PHASE = "CAMPAIGN_READINESS_ONLY"
SCHEMA = "TD13-G31-DURABLE-READINESS-v1"
EXECUTION_SCHEMA = "TD13-G31-NUMERIC-EXECUTION-v1"
_WORKSPACE = Path(__file__).resolve().parents[2]
_PROJECT = Path("D:/Project/flash-ticket-platform")
_HOST_TRUST_MODE = "HOST_TRUSTED"
_FINAL_PERMISSIONS = (
    "final_labels", "final_tau_metadata", "final_answers", "final_outcomes",
    "final_predictions", "final_campaign",
)
_SOURCES = tuple(
    f"{root}/{name}.py"
    for root, prefix in (("scripts/task_g", ""), ("tests/task_g", "test_"))
    for name in (prefix + "campaign", prefix + "campaign_source",
                 prefix + "campaign_provenance", prefix + "evaluation")
)
_FROZEN = {
    "td_v1_3_sha256": "34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971",
    "task_f_v2_manifest_sha256": "c46b870bccdae1198292abc5850a83a3fa7e7f702286ceeaa07258074391801d",
    "metadata_sha256": "c49a288920dbba2e8e724679a14636d5c7eb2b45426bba14007ef79a6c0ab1bb",
}
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DETECTORS = {"G-MTL", "L-MTL", "ALL-MTL", "TV-MTL",
              "G-MT", "L-MT", "ALL-MT", "TV-MT"}
_STATUSES = {"SUCCESS", "FAILURE", "UNAVAILABLE", "TIMEOUT",
             "INPUT_FAILURE", "INPUT_UNAVAILABLE", "METHOD_FAILURE", "INSUFFICIENT_HISTORY"}
_ORACLE_KEYS = {
    "tau", "root_index", "root_cause", "fault_label", "answer", "outcome",
    "case_id", "case_path", "service_names", "absolute_epoch",
}
_MAX_ARTIFACT_BYTES = 128 * 1024 * 1024


class CampaignProvenanceError(ValueError):
    """An issued readiness execution or persistent trusted commitment is invalid."""


def _canonical(value):
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CampaignProvenanceError("Nonfinite or noncanonical readiness payload") from exc


def _digest(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _require_digest(value):
    if type(value) is not str or _SHA.fullmatch(value) is None:
        raise CampaignProvenanceError("Invalid readiness SHA256")
    return value


def _unique_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise CampaignProvenanceError("Duplicate JSON key")
        value[key] = item
    return value


def _require_regular_path(path, *, allow_missing=False):
    path = Path(path)
    if not path.is_absolute():
        raise CampaignProvenanceError("Trusted readiness path must be absolute")
    for component in (*reversed(path.parents), path):
        try:
            info = component.lstat()
        except FileNotFoundError:
            if allow_missing:
                continue
            raise CampaignProvenanceError("Trusted readiness path is missing") from None
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise CampaignProvenanceError("Trusted readiness path has a reparse component")
    if path.exists() and not path.is_file():
        raise CampaignProvenanceError("Trusted readiness file is not regular")


def _read_json(path):
    _require_regular_path(path)
    try:
        raw = path.read_bytes()
        if len(raw) > _MAX_ARTIFACT_BYTES:
            raise CampaignProvenanceError("Readiness artifact exceeds bounded size")
        value = json.loads(raw, object_pairs_hook=_unique_pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(
                               CampaignProvenanceError("Nonfinite JSON number")))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CampaignProvenanceError("Readiness JSON is unavailable or malformed") from exc
    return raw, value


def _run_root():
    return _WORKSPACE / "results/task-g" / RUN_ID


def _contract_path():
    return _run_root() / "run-contract.json"


def _receipt_path():
    return _run_root() / "readiness.json"


def _key_path():
    location = os.environ.get("LOCALAPPDATA")
    if not location or not Path(location).is_absolute():
        raise CampaignProvenanceError("Trusted LOCALAPPDATA is unavailable")
    return Path(location) / "FlashTicketRca/task-g-trust" / RUN_ID / "issuer.key"


def _authorized_contract():
    raw, contract = _read_json(_contract_path())
    if (type(contract) is not dict
            or contract.get("schema") != "TD13-G31-READINESS-CONTRACT-v1"
            or contract.get("run_id") != RUN_ID or contract.get("domain") != DOMAIN
            or contract.get("phase") != PHASE):
        raise CampaignProvenanceError("Wrong registered readiness contract")
    permissions = contract.get("permissions")
    if (type(permissions) is not dict
            or any(permissions.get(key) is not False for key in _FINAL_PERMISSIONS)
            or permissions.get("synthetic_development_readiness") is not True
            or permissions.get("readiness_host_key_generation") is not True
            or permissions.get("telemetry_final60_new_acquisition") is not False):
        raise CampaignProvenanceError("G31 readiness cannot authorize final execution or labels")
    if contract.get("frozen_inputs") != _FROZEN:
        raise CampaignProvenanceError("Frozen scientific identity differs")
    return raw, contract


def initialize_readiness_key():
    """Create the authorized fixed key exclusively; never replace or print it."""
    _authorized_contract()
    path = _key_path()
    _require_regular_path(path, allow_missing=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    _require_regular_path(path, allow_missing=True)
    key = secrets.token_bytes(32)
    try:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(key)
            stream.flush()
            os.fsync(stream.fileno())
        if path.read_bytes() != key:
            raise CampaignProvenanceError("Readiness key readback differs")
    except OSError as exc:
        raise CampaignProvenanceError("Readiness key creation failed; existing bytes retained") from exc
    return readiness_anchor_descriptor()


def readiness_anchor_descriptor():
    """Public identity of the already configured fixed host key."""
    path = _key_path()
    _require_regular_path(path)
    key = path.read_bytes()
    if len(key) != 32:
        raise CampaignProvenanceError("Readiness key has invalid size")
    return {"algorithm": "HMAC-SHA256", "domain": DOMAIN, "run_id": RUN_ID,
            "trust_mode": _HOST_TRUST_MODE,
            "key_sha256": hashlib.sha256(key).hexdigest()}


def _validate_frozen_files(contract):
    paths = {
        "td_v1_3_sha256": _PROJECT / "docs/research-rca/task-d-method-and-experiment-specification.md",
        "task_f_v2_manifest_sha256": _WORKSPACE / "configs/task-f-td13-frozen-release-v2.json",
        "metadata_sha256": _WORKSPACE / "datasets/rcaeval/metadata/cases.parquet",
    }
    for key, path in paths.items():
        _require_regular_path(path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != _FROZEN[key]:
            raise CampaignProvenanceError("Frozen method/release/source bytes changed")
    protected = contract.get("protected_sha256")
    if type(protected) is not dict or not protected:
        raise CampaignProvenanceError("Registered protected references are absent")
    for relative, expected in protected.items():
        if type(relative) is not str or relative[:2] not in ("P/", "W/"):
            raise CampaignProvenanceError("Malformed protected reference")
        suffix = Path(relative[2:])
        if suffix.is_absolute() or ".." in suffix.parts:
            raise CampaignProvenanceError("Protected reference escapes its root")
        path = (_PROJECT if relative.startswith("P/") else _WORKSPACE) / suffix
        _require_regular_path(path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != _require_digest(expected):
            raise CampaignProvenanceError("Protected source or history drifted")


def _validate_environment(environment):
    if type(environment) is not dict or environment.get("main_python") != platform.python_version():
        raise CampaignProvenanceError("Registered readiness Python differs")
    packages = environment.get("packages")
    if type(packages) is not dict or set(packages) != {"numpy", "pandas", "pyarrow", "huggingface-hub"}:
        raise CampaignProvenanceError("Exact preregistered readiness packages are required")
    for name, version in packages.items():
        if importlib.metadata.version(name) != version:
            raise CampaignProvenanceError("Registered readiness package differs")
    if environment.get("dependency_installation") is not False:
        raise CampaignProvenanceError("Readiness dependency scope changed")


def _registered_context():
    raw, contract = _authorized_contract()
    snapshot = contract.get("source_test_snapshot_before_qualification")
    if type(snapshot) is not dict or set(snapshot) != set(_SOURCES):
        raise CampaignProvenanceError("Exact eight-file preregistered snapshot is required")
    for relative, expected in snapshot.items():
        path = _WORKSPACE / relative
        _require_regular_path(path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != _require_digest(expected):
            raise CampaignProvenanceError("Readiness source/test drift invalidates qualification")
    _validate_frozen_files(contract)
    _validate_environment(contract.get("environment"))
    anchor = readiness_anchor_descriptor()
    if contract.get("trust_anchor") != anchor:
        raise CampaignProvenanceError("Registered readiness host anchor differs or is absent")
    from scripts.task_g.campaign import prepare_conditions

    prepared = prepare_conditions()
    if (type(prepared) is not dict or prepared.get("conditions") != contract.get("prepared_conditions")
            or prepared.get("sha256") != _digest(contract["prepared_conditions"])):
        raise CampaignProvenanceError("Frozen prepared conditions changed")
    return {
        "contract_sha256": hashlib.sha256(raw).hexdigest(),
        "source_snapshot_sha256": _digest(snapshot),
        "permissions": contract["permissions"],
        "permissions_sha256": _digest(contract["permissions"]),
        "config_sha256": prepared["sha256"],
        "environment_sha256": _digest(contract["environment"]),
        "resource_policy_sha256": _digest(contract.get("resource_policy")),
        "entry_bindings_sha256": _digest(contract.get("entry_bindings")),
        "development_inputs_sha256": _digest(contract.get("development_inputs")),
        "frozen_inputs_sha256": _digest(_FROZEN),
        "anchor": anchor,
    }, contract


def _integer(value, lower=0, upper=None):
    if type(value) is not int or value < lower or (upper is not None and value > upper):
        raise CampaignProvenanceError("Invalid numerical execution index/count")
    return value


def _finite(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise CampaignProvenanceError("Execution requires a finite numerical value")
    return value


def _scores(item, count):
    if type(item) is not dict or item.get("status") not in _STATUSES:
        raise CampaignProvenanceError("Every planned arm needs an explicit status")
    values = item.get("scores")
    if item["status"] == "SUCCESS":
        if type(values) is not list or len(values) != count:
            raise CampaignProvenanceError("A successful arm must rank its complete candidate set")
        for value in values:
            _finite(value)
    elif values is not None:
        raise CampaignProvenanceError("Failed/unavailable arm must not carry successful scores")


def _no_oracles(value):
    if type(value) is dict:
        for key, item in value.items():
            if key in _ORACLE_KEYS:
                raise CampaignProvenanceError("Oracle/location field leaked into numerical execution")
            _no_oracles(item)
    elif type(value) is list:
        for item in value:
            _no_oracles(item)


def _graph(row, count):
    if row.get("status") != "SUCCESS":
        if row.get("adjacency") is not None or row.get("graph_sha256") is not None:
            raise CampaignProvenanceError("Failed graph generation carries a purported realized graph")
        return
    adjacency = row.get("adjacency")
    if (type(adjacency) is not list or len(adjacency) != count
            or any(type(line) is not list or len(line) != count for line in adjacency)
            or any(type(v) not in (bool, int) or v not in (0, 1) for line in adjacency for v in line)):
        raise CampaignProvenanceError("Saved control graph is not complete binary adjacency")
    array = np.asarray(adjacency, dtype=np.bool_).reshape((count, count))
    if np.any(np.diag(array)) or not np.array_equal(array, array.T):
        raise CampaignProvenanceError("Frozen undirected control graph has invalid edges")
    expected = hashlib.sha256(str(array.shape).encode("ascii") + np.packbits(array).tobytes()).hexdigest()
    if row.get("graph_sha256") != expected:
        raise CampaignProvenanceError("Realized graph bytes differ from their frozen digest")


def _validate_c1(case):
    count = _integer(case.get("candidate_count"))
    graphs = case.get("control_graphs")
    if type(graphs) is not list or len(graphs) != 256:
        raise CampaignProvenanceError("Every case must retain all 256 control graph records")
    for draw, graph in enumerate(graphs):
        if (type(graph) is not dict or graph.get("draw") != draw
                or graph.get("status") not in _STATUSES):
            raise CampaignProvenanceError("Control draw order/status is incomplete")
        _integer(graph.get("seed"), upper=2**64 - 1)
        _graph(graph, count)
    conditions = case.get("c1")
    if type(conditions) is not dict or set(conditions) != {"primary", "secondary"}:
        raise CampaignProvenanceError("Both registered ranking operators must be preserved")
    for operator in ("primary", "secondary"):
        arms = conditions[operator]
        if type(arms) is not dict or set(arms) != {"L", "O", "R"}:
            raise CampaignProvenanceError("Matched L/O/R arm completeness failed")
        _scores(arms["L"], count)
        _scores(arms["O"], count)
        draws = arms["R"]
        if type(draws) is not list or len(draws) != 256:
            raise CampaignProvenanceError("Every ranking operator must retain all 256 draws")
        for draw, (row, graph) in enumerate(zip(draws, graphs, strict=True)):
            _scores(row, count)
            if row.get("draw") != draw or row.get("seed") != graph["seed"]:
                raise CampaignProvenanceError("Rank draw index/seed differs from realized control")
            if row.get("graph_sha256") != graph.get("graph_sha256"):
                raise CampaignProvenanceError("Ranking does not bind the same realized graph")
            if row["status"] == "SUCCESS" and graph["status"] != "SUCCESS":
                raise CampaignProvenanceError("Successful R cannot use a failed graph draw")
            if row["status"] == "SUCCESS":
                retained = _finite(row.get("retained_edge_fraction"))
                if not 0 <= retained <= 1:
                    raise CampaignProvenanceError("Invalid retained-edge coverage")
    if case.get("shared_preprocessing_failed") is True:
        for arms in conditions.values():
            if any(arms[arm]["status"] == "SUCCESS" for arm in ("L", "O")) or any(
                    row["status"] == "SUCCESS" for row in arms["R"]):
                raise CampaignProvenanceError("Shared input failure was silently promoted to success")


def _validate_contextual(case):
    outputs = case.get("contextual")
    expected = {"Local-MAX-MT", "BARO-RANK-adapted-TD12", "RCD"}
    if type(outputs) is not dict or set(outputs) != expected:
        raise CampaignProvenanceError("Mandatory contextual comparators are incomplete")
    for method in expected - {"RCD"}:
        _scores(outputs[method], case["candidate_count"])
    rcd = outputs["RCD"]
    if type(rcd) is not dict:
        raise CampaignProvenanceError("RCD numeric output is missing")
    rows = rcd.get("seed_outputs")
    if (type(rows) is not list or len(rows) != 3
            or [item.get("seed") for item in rows if type(item) is dict] != [420, 421, 422]):
        raise CampaignProvenanceError("RCD must preserve exactly 420/421/422 in order")
    if type(rcd.get("n_services")) is not int or rcd["n_services"] != case["candidate_count"]:
        raise CampaignProvenanceError("RCD owner/candidate set differs from common V")
    owners = rcd.get("metric_owners")
    if (type(owners) is not dict or any(type(key) is not str or re.fullmatch(r"m[0-9]+", key) is None
            or type(owner) is not int or not 0 <= owner < case["candidate_count"]
            for key, owner in owners.items())):
        raise CampaignProvenanceError("RCD requires exact numeric metric ownership")
    _require_digest(rcd.get("input_sha256"))
    identity = rcd.get("qualification_identity_sha256")
    if identity != "38253ebbfaa53bdad20b66e655ade3fade363fdd9ef71ee2ab6df722ab4fac04":
        raise CampaignProvenanceError("RCD output is not bound to the frozen issued runner identity")
    for item in rows:
        if item.get("status") not in ("SUCCESS", "FAILURE") or type(item.get("bins")) is not int or item["bins"] != 5:
            raise CampaignProvenanceError("RCD output lost frozen bins/status")
        ranks = item.get("ranks")
        if item["status"] == "SUCCESS":
            if (type(ranks) is not list or len(set(ranks)) != len(ranks)
                    or any(type(v) is not str or re.fullmatch(r"m[0-9]+", v) is None for v in ranks)):
                raise CampaignProvenanceError("RCD ranking is malformed or contains controller names")
        elif ranks is not None:
            raise CampaignProvenanceError("Failed RCD seed carries successful ranks")


def _validate_c5(case, prepared):
    outputs = case.get("c5")
    if type(outputs) is not dict or set(outputs) != _DETECTORS:
        raise CampaignProvenanceError("Every case must preserve all eight frozen C5 detectors")
    frozen = prepared.get("scientific_objects", {}).get("selections", {}).get("c5", {}).get("detectors")
    if type(frozen) is not list or {row["id"] for row in frozen} != _DETECTORS:
        raise CampaignProvenanceError("Frozen eight-detector registry is absent")
    thresholds = {row["id"]: row["threshold"] for row in frozen}
    for detector_id, output in outputs.items():
        if (type(output) is not dict or output.get("status") not in _STATUSES
                or output.get("threshold") != thresholds[detector_id]):
            raise CampaignProvenanceError("Detector threshold/status differs from freeze")
        starts, ends = output.get("starts"), output.get("ends")
        scores, statuses = output.get("scores"), output.get("bin_statuses")
        if (type(ends) is not list or type(starts) is not list
                or type(scores) is not list or type(statuses) is not list
                or not len(starts) == len(ends) == len(scores) == len(statuses)
                or ends != list(range(185, 185 + len(ends) * 5, 5))
                or starts != [end - 5 for end in ends]):
            raise CampaignProvenanceError("Detector lost a consecutive planned post-warmup bin")
        for endpoint in (*starts, *ends):
            _integer(endpoint, 180)
        for score, status in zip(scores, statuses, strict=True):
            if status not in _STATUSES:
                raise CampaignProvenanceError("C5 bin lacks an explicit status")
            if status == "SUCCESS":
                if _finite(score) < 0:
                    raise CampaignProvenanceError("C5 residual/spatial score cannot be negative")
            elif score is not None:
                raise CampaignProvenanceError("Unavailable C5 bin carries a score")
        triggers = output.get("triggers")
        if type(triggers) is not list:
            raise CampaignProvenanceError("All trigger diagnoses must be retained")
        endpoints = []
        for trigger in triggers:
            if type(trigger) is not dict or trigger.get("endpoint") not in ends:
                raise CampaignProvenanceError("Integrated diagnosis is not tied to a planned bin")
            endpoint = _integer(trigger["endpoint"], 185)
            endpoints.append(endpoint)
            count = _integer(trigger.get("candidate_count"))
            _scores(trigger, count)
            if endpoint < 360 and trigger["status"] != "INSUFFICIENT_HISTORY":
                raise CampaignProvenanceError("Early trigger must retain insufficient history")
            if trigger["status"] == "SUCCESS":
                _require_digest(trigger.get("input_sha256"))
        if endpoints != sorted(set(endpoints)):
            raise CampaignProvenanceError("Duplicate or unordered trigger diagnosis")
        # Recompute the frozen event policy from all raw system-bin outputs.
        expected, streak, last = [], 0, None
        for end, score, status in zip(ends, scores, statuses, strict=True):
            streak = streak + 1 if status == "SUCCESS" and score > thresholds[detector_id] else 0
            if streak >= 3 and (last is None or end - last >= 300):
                expected.append(end)
                last = end
        if endpoints != expected:
            raise CampaignProvenanceError("Missing/fabricated trigger or changed event policy")


def _validate_case(case, ordinal, *, timing, prepared):
    if (type(case) is not dict or case.get("ordinal") != ordinal
            or case.get("cell_ordinal") != ordinal // 3 or case.get("repeat") != ordinal % 3
            or type(case.get("shared_preprocessing_failed")) is not bool):
        raise CampaignProvenanceError("Planned case/cell/repeat identity changed")
    for key in ("ordinal", "cell_ordinal", "repeat"):
        _integer(case[key])
    _require_digest(case.get("numeric_input_sha256"))
    _no_oracles(case)
    _validate_c1(case)
    if type(case.get("costs")) is not dict:
        raise CampaignProvenanceError("Planned timing/failure cost record is absent")
    if timing:
        if case.get("contextual") != {} or case.get("c5") != {}:
            raise CampaignProvenanceError("Timing-only development cannot perform outcome analysis")
    else:
        _validate_contextual(case)
        _validate_c5(case, prepared)


def _validate_cases(cases, *, timing, prepared):
    expected = 30 if timing else 60
    if type(cases) is not list or len(cases) != expected:
        raise CampaignProvenanceError("Planned cases were removed or added")
    for ordinal, case in enumerate(cases):
        _validate_case(case, ordinal, timing=timing, prepared=prepared)


def _validate_execution(payload, context, contract):
    if (type(payload) is not dict or payload.get("schema") != EXECUTION_SCHEMA
            or payload.get("run_id") != RUN_ID or payload.get("domain") != DOMAIN
            or payload.get("phase") != PHASE or payload.get("trust_mode") != _HOST_TRUST_MODE
            or payload.get("scope") not in ("SYNTHETIC_CAMPAIGN_READINESS", "DEVELOPMENT_TIMING_ONLY")):
        raise CampaignProvenanceError("Wrong issued readiness execution domain/scope")
    for key in ("source_snapshot_sha256", "permissions_sha256", "config_sha256"):
        if payload.get(key) != context[key]:
            raise CampaignProvenanceError("Execution binding differs from registered context")
    if payload.get("prepared_conditions") != contract.get("prepared_conditions"):
        raise CampaignProvenanceError("Execution selected a different scientific configuration")
    summary = payload.get("source_summary")
    timing = payload["scope"] == "DEVELOPMENT_TIMING_ONLY"
    if type(summary) is not dict or summary.get("source_kind") != (
            "DEVELOPMENT_NUMERIC_CACHE" if timing else "SYNTHETIC_NUMERIC"):
        raise CampaignProvenanceError("Readiness source cannot promote actual final observations")
    _no_oracles(summary)
    if payload.get("planned_case_count") != (30 if timing else 60):
        raise CampaignProvenanceError("Registered readiness denominator changed")
    _integer(payload["planned_case_count"])
    _no_oracles(payload.get("cases"))
    _validate_cases(payload.get("cases"), timing=timing, prepared=payload["prepared_conditions"])
    report = payload.get("development_timing_report")
    if report is not None:
        if type(report) is not dict:
            raise CampaignProvenanceError("Development timing report is malformed")
        _no_oracles(report)
        _validate_cases(report.get("cases"), timing=True, prepared=payload["prepared_conditions"])
    elif not timing and _HOST_TRUST_MODE == "HOST_TRUSTED":
        raise CampaignProvenanceError("Host readiness requires the complete development30 timing report")
    _canonical(payload)


def _artifact_path(digest):
    return _run_root() / "cache/artifacts" / (_require_digest(digest) + ".json")


def _persist_artifact(case, role):
    encoded = _canonical(case)
    if len(encoded) > _MAX_ARTIFACT_BYTES:
        raise CampaignProvenanceError("Numerical case artifact exceeds bounded size")
    digest = hashlib.sha256(encoded).hexdigest()
    target = _artifact_path(digest)
    _require_regular_path(target, allow_missing=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    _require_regular_path(target, allow_missing=True)
    if target.exists():
        if target.read_bytes() != encoded:
            raise CampaignProvenanceError("Existing content-addressed artifact differs")
    else:
        staged = target.parent / ("attempt-" + secrets.token_hex(16) + ".json")
        _require_regular_path(staged, allow_missing=True)
        try:
            fd = os.open(str(staged), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            if staged.read_bytes() != encoded:
                raise CampaignProvenanceError("Numerical artifact readback differs")
            os.link(str(staged), str(target))
        except OSError as exc:
            raise CampaignProvenanceError("Durable artifact write failed; attempt retained") from exc
    return {"role": role, "ordinal": case["ordinal"], "sha256": digest, "bytes": len(encoded)}


def _split_artifacts(payload):
    header = {key: value for key, value in payload.items() if key != "cases"}
    manifest = [_persist_artifact(case, "EXECUTION_CASE") for case in payload["cases"]]
    report = payload.get("development_timing_report")
    if report is not None:
        header["development_timing_report"] = {key: value for key, value in report.items() if key != "cases"}
        manifest.extend(_persist_artifact(case, "DEVELOPMENT_TIMING_CASE") for case in report["cases"])
    return header, manifest


def _read_artifacts(header, manifest):
    if type(header) is not dict or type(manifest) is not list:
        raise CampaignProvenanceError("Durable artifact manifest is missing")
    expected = 30 if header.get("scope") == "DEVELOPMENT_TIMING_ONLY" else 60
    plan = [("EXECUTION_CASE", ordinal) for ordinal in range(expected)]
    if "development_timing_report" in header:
        plan.extend(("DEVELOPMENT_TIMING_CASE", ordinal) for ordinal in range(30))
    if len(manifest) != len(plan):
        raise CampaignProvenanceError("Durable artifacts do not cover every planned case")
    cases, timing = [], []
    for row, (role, ordinal) in zip(manifest, plan, strict=True):
        if (type(row) is not dict or set(row) != {"role", "ordinal", "sha256", "bytes"}
                or row["role"] != role or row["ordinal"] != ordinal):
            raise CampaignProvenanceError("Missing/duplicate/reordered durable case artifact")
        raw, case = _read_json(_artifact_path(row["sha256"]))
        if (type(row["bytes"]) is not int or row["bytes"] != len(raw)
                or hashlib.sha256(raw).hexdigest() != row["sha256"]
                or raw != _canonical(case)):
            raise CampaignProvenanceError("Persisted case artifact size/hash/canonical bytes differ")
        (cases if role == "EXECUTION_CASE" else timing).append(case)
    payload = json.loads(_canonical(header))
    payload["cases"] = cases
    if "development_timing_report" in payload:
        if type(payload["development_timing_report"]) is not dict:
            raise CampaignProvenanceError("Durable timing header is malformed")
        payload["development_timing_report"]["cases"] = timing
    return payload


def _verify_envelope(raw, envelope, context, contract):
    if type(envelope) is not dict or set(envelope) != {"commitment", "hmac_sha256"}:
        raise CampaignProvenanceError("Complete authenticated readiness envelope is required")
    commitment = envelope["commitment"]
    if (type(commitment) is not dict or set(commitment) != {
            "schema", "run_id", "domain", "phase", "recorded_at_utc", "context",
            "execution_header", "artifact_manifest", "artifact_manifest_sha256",
            "execution_sha256", "final_predictions", "final_labels", "final_campaign"}
            or commitment["schema"] != SCHEMA or commitment["run_id"] != RUN_ID
            or commitment["domain"] != DOMAIN or commitment["phase"] != PHASE
            or commitment["context"] != context
            or any(commitment[name] is not False for name in (
                "final_predictions", "final_labels", "final_campaign"))):
        raise CampaignProvenanceError("Wrong durable readiness context or final promotion")
    key = _key_path().read_bytes()
    expected = hmac.new(key, _canonical(commitment), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, _require_digest(envelope["hmac_sha256"])):
        raise CampaignProvenanceError("Readiness HMAC authentication failed")
    if raw != _canonical(envelope):
        raise CampaignProvenanceError("Readiness envelope is not exact canonical readback")
    if commitment["artifact_manifest_sha256"] != _digest(commitment["artifact_manifest"]):
        raise CampaignProvenanceError("Artifact manifest changed")
    payload = _read_artifacts(commitment["execution_header"], commitment["artifact_manifest"])
    _validate_execution(payload, context, contract)
    if commitment["execution_sha256"] != _digest(payload):
        raise CampaignProvenanceError("Complete numerical execution changed")
    summary = {
        "status": "PASS_DURABLE_READINESS_ONLY", "run_id": RUN_ID, "domain": DOMAIN,
        "phase": PHASE, "scope": payload["scope"], "trust_mode": _HOST_TRUST_MODE,
        "receipt_sha256": hashlib.sha256(raw).hexdigest(),
        "payload_sha256": commitment["execution_sha256"],
        "artifact_manifest_sha256": commitment["artifact_manifest_sha256"],
        "planned_cases": payload["planned_case_count"],
        "persisted_case_artifacts": len(commitment["artifact_manifest"]),
        "final_prediction_qualified": False,
    }
    return summary, payload


def _bind_committer():
    def commit_readiness(execution_handle):
        from scripts.task_g.campaign import _campaign_payload_for_provenance

        context, contract = _registered_context()
        payload = _campaign_payload_for_provenance(execution_handle)
        _validate_execution(payload, context, contract)
        payload = json.loads(_canonical(payload))
        path = _receipt_path()
        _require_regular_path(path, allow_missing=True)
        if path.exists():
            raise CampaignProvenanceError("Readiness receipt already exists; no overwrite")
        header, manifest = _split_artifacts(payload)
        commitment = {
            "schema": SCHEMA, "run_id": RUN_ID, "domain": DOMAIN, "phase": PHASE,
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(), "context": context,
            "execution_header": header, "artifact_manifest": manifest,
            "artifact_manifest_sha256": _digest(manifest), "execution_sha256": _digest(payload),
            "final_predictions": False, "final_labels": False, "final_campaign": False,
        }
        prefix = b'{"commitment":' + _canonical(commitment)
        staged = _run_root() / "cache" / ("readiness-attempt-" + secrets.token_hex(16) + ".json")
        _require_regular_path(staged, allow_missing=True)
        staged.parent.mkdir(parents=True, exist_ok=True)
        _require_regular_path(staged, allow_missing=True)
        try:
            fd = os.open(str(staged), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(prefix)
                stream.flush()
                os.fsync(stream.fileno())
                if staged.read_bytes() != prefix:
                    raise CampaignProvenanceError("Readiness numerical commitment readback differs")
                tag = hmac.new(_key_path().read_bytes(), _canonical(commitment), hashlib.sha256).hexdigest()
                envelope = {"commitment": commitment, "hmac_sha256": tag}
                encoded = _canonical(envelope)
                if not encoded.startswith(prefix):
                    raise CampaignProvenanceError("Unexpected canonical readiness envelope")
                stream.write(encoded[len(prefix):])
                stream.flush()
                os.fsync(stream.fileno())
            if staged.read_bytes() != encoded:
                raise CampaignProvenanceError("Authenticated readiness readback differs")
            fresh_context, fresh_contract = _registered_context()
            _verify_envelope(encoded, envelope, fresh_context, fresh_contract)
            os.link(str(staged), str(path))
        except OSError as exc:
            raise CampaignProvenanceError("Durable readiness publication failed; attempt retained") from exc
        return verify_readiness_receipt()

    return commit_readiness


commit_readiness = _bind_committer()
del _bind_committer


def verify_readiness_receipt():
    """Fresh disk/HMAC/full-artifact verification against the fixed host anchor."""
    context, contract = _registered_context()
    raw, envelope = _read_json(_receipt_path())
    summary, _ = _verify_envelope(raw, envelope, context, contract)
    return summary


def require_verified_readiness_execution():
    """Return a fresh verified copy, before a lazy synthetic evaluator callback."""
    context, contract = _registered_context()
    raw, envelope = _read_json(_receipt_path())
    summary, payload = _verify_envelope(raw, envelope, context, contract)
    payload["_verified_context"] = {
        "permissions": dict(context["permissions"]),
        "receipt_sha256": summary["receipt_sha256"],
        "final_prediction_qualified": False,
    }
    return payload


def require_final_campaign_receipt():
    """G31 domain/key/receipts can never authenticate a future final run."""
    raise CampaignProvenanceError("G31 readiness cannot authorize actual final campaign or labels")


def _checkpoint_path(kind, ordinal):
    if kind not in ("synthetic", "development"):
        raise CampaignProvenanceError("Checkpoint source kind is not admitted")
    _integer(ordinal, upper=29 if kind == "development" else 59)
    return _run_root() / "cache/checkpoints" / f"{kind}-{ordinal:03d}.json"


def _checkpoint_context(context, contract, kind):
    if kind == "synthetic":
        return {"kind": kind, "registered_context": context}
    policy = contract.get("resource_policy")
    keys = (
        "worker_count", "numeric_threads", "thread_environment",
        "development_timing_infrastructure_deadline_seconds", "R_generation_included",
        "secondary_reuses_same_realized_undirected_graphs", "failures_and_attempts_preserved",
        "timing_measurement_repetition",
    )
    if type(policy) is not dict or any(key not in policy for key in keys):
        raise CampaignProvenanceError("Registered development measurement profile is absent")
    stable = {key: context[key] for key in (
        "source_snapshot_sha256", "permissions_sha256", "config_sha256",
        "environment_sha256", "entry_bindings_sha256", "development_inputs_sha256",
        "frozen_inputs_sha256", "anchor",
    )}
    return {"kind": kind, "stable_context": stable,
            "measurement_profile": {key: policy[key] for key in keys},
            "measured_under_contract_sha256": context["contract_sha256"]}


def _require_registered_measurement_snapshot(recorded, context, contract):
    expected = _checkpoint_context(context, contract, "development")
    measured_sha = _require_digest(recorded.get("measured_under_contract_sha256"))
    expected["measured_under_contract_sha256"] = measured_sha
    if recorded != expected:
        raise CampaignProvenanceError("Development checkpoint stable measurement inputs drifted")
    if measured_sha == context["contract_sha256"]:
        return
    # A timeout derived AFTER the predeclared development measurement may be
    # added without invalidating that measurement.  The exact original
    # registered bytes, rather than a caller assertion, must remain preserved.
    history = contract.get("registration_history")
    if type(history) is not list:
        raise CampaignProvenanceError("Original measurement registration is not preserved")
    for entry in history:
        if type(entry) is not dict:
            continue
        raw = entry.get("raw_utf8")
        if type(raw) is not str:
            continue
        encoded = raw.encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
        if digest != measured_sha or entry.get("sha256") != digest:
            continue
        original = json.loads(encoded, object_pairs_hook=_unique_pairs)
        if (original.get("schema") != "TD13-G31-READINESS-CONTRACT-v1"
                or original.get("run_id") != RUN_ID or original.get("domain") != DOMAIN
                or original.get("phase") != PHASE
                or original.get("source_test_snapshot_before_qualification") != contract.get("source_test_snapshot_before_qualification")
                or original.get("environment") != contract.get("environment")
                or original.get("prepared_conditions") != contract.get("prepared_conditions")
                or original.get("permissions") != contract.get("permissions")
                or original.get("trust_anchor") != contract.get("trust_anchor")
                or original.get("entry_bindings") != contract.get("entry_bindings")
                or original.get("development_inputs") != contract.get("development_inputs")
                or original.get("frozen_inputs") != contract.get("frozen_inputs")):
            raise CampaignProvenanceError("Preserved measurement contract differs from stable registration")
        original_policy = original.get("resource_policy")
        if type(original_policy) is not dict or any(original_policy.get(key) != value
                for key, value in recorded["measurement_profile"].items()):
            raise CampaignProvenanceError("Preserved measurement resource profile differs")
        return
    raise CampaignProvenanceError("Measurement contract digest is not registered history")


def _validate_checkpoint_payload(payload, kind, ordinal, input_sha, contract):
    if (type(payload) is not dict or set(payload) != {
            "kind", "ordinal", "numeric_input_sha256", "case", "source_summary"}
            or payload["kind"] != kind or payload["ordinal"] != ordinal
            or payload["numeric_input_sha256"] != input_sha
            or type(payload["source_summary"]) is not dict):
        raise CampaignProvenanceError("Checkpoint execution identity/source changed")
    _require_digest(input_sha)
    if type(payload["case"]) is not dict or payload["case"].get("numeric_input_sha256") != input_sha:
        raise CampaignProvenanceError("Checkpoint case input digest differs")
    _validate_case(payload["case"], ordinal, timing=kind == "development",
                   prepared=contract["prepared_conditions"])
    _canonical(payload)


def _verify_checkpoint_envelope(raw, envelope, kind, ordinal, input_sha, context, contract):
    if type(envelope) is not dict or set(envelope) != {"commitment", "hmac_sha256"}:
        raise CampaignProvenanceError("Complete authenticated case checkpoint is required")
    value = envelope["commitment"]
    if (type(value) is not dict or set(value) != {
            "schema", "domain", "run_id", "phase", "recorded_at_utc", "context",
            "execution", "execution_sha256", "final_prediction_qualified"}
            or value["schema"] != "TD13-G31-CASE-CHECKPOINT-v1"
            or value["domain"] != DOMAIN + "/CASE/v1" or value["run_id"] != RUN_ID
            or value["phase"] != PHASE or value["final_prediction_qualified"] is not False):
        raise CampaignProvenanceError("Case checkpoint cannot promote scope/domain")
    if kind == "development":
        _require_registered_measurement_snapshot(value["context"], context, contract)
    elif value["context"] != _checkpoint_context(context, contract, kind):
        raise CampaignProvenanceError("Synthetic checkpoint registered context drifted")
    tag = hmac.new(_key_path().read_bytes(), _canonical(value), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(tag, _require_digest(envelope["hmac_sha256"])):
        raise CampaignProvenanceError("Case checkpoint HMAC authentication failed")
    if raw != _canonical(envelope):
        raise CampaignProvenanceError("Case checkpoint bytes are not canonical readback")
    payload = value["execution"]
    _validate_checkpoint_payload(payload, kind, ordinal, input_sha, contract)
    if value["execution_sha256"] != _digest(payload):
        raise CampaignProvenanceError("Case checkpoint numerical execution changed")
    return json.loads(_canonical(payload))


def _bind_checkpoint_committer():
    def commit_case_checkpoint(case_execution_handle):
        from scripts.task_g.campaign import _case_payload_for_checkpoint

        context, contract = _registered_context()
        payload = _case_payload_for_checkpoint(case_execution_handle)
        if type(payload) is not dict:
            raise CampaignProvenanceError("Case checkpoint producer did not issue a numerical payload")
        kind, ordinal, input_sha = (payload.get(key) for key in (
            "kind", "ordinal", "numeric_input_sha256"))
        path = _checkpoint_path(kind, ordinal)
        _validate_checkpoint_payload(payload, kind, ordinal, input_sha, contract)
        _require_regular_path(path, allow_missing=True)
        if path.exists():
            raise CampaignProvenanceError("Case checkpoint exists; no overwrite or retry selection")
        path.parent.mkdir(parents=True, exist_ok=True)
        _require_regular_path(path, allow_missing=True)
        value = {
            "schema": "TD13-G31-CASE-CHECKPOINT-v1", "domain": DOMAIN + "/CASE/v1",
            "run_id": RUN_ID, "phase": PHASE,
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
            "context": _checkpoint_context(context, contract, kind),
            "execution": payload, "execution_sha256": _digest(payload),
            "final_prediction_qualified": False,
        }
        prefix = b'{"commitment":' + _canonical(value)
        staged = path.parent / ("case-attempt-" + secrets.token_hex(16) + ".json")
        _require_regular_path(staged, allow_missing=True)
        try:
            fd = os.open(str(staged), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(prefix)
                stream.flush()
                os.fsync(stream.fileno())
                if staged.read_bytes() != prefix:
                    raise CampaignProvenanceError("Case numerical checkpoint readback differs")
                tag = hmac.new(_key_path().read_bytes(), _canonical(value), hashlib.sha256).hexdigest()
                envelope = {"commitment": value, "hmac_sha256": tag}
                encoded = _canonical(envelope)
                if not encoded.startswith(prefix):
                    raise CampaignProvenanceError("Unexpected canonical case checkpoint envelope")
                stream.write(encoded[len(prefix):])
                stream.flush()
                os.fsync(stream.fileno())
            if staged.read_bytes() != encoded:
                raise CampaignProvenanceError("Authenticated case checkpoint readback differs")
            fresh_context, fresh_contract = _registered_context()
            _verify_checkpoint_envelope(encoded, envelope, kind, ordinal, input_sha,
                                        fresh_context, fresh_contract)
            os.link(str(staged), str(path))
        except OSError as exc:
            raise CampaignProvenanceError("Durable case publication failed; attempt retained") from exc
        return verify_case_checkpoint(kind, ordinal, input_sha)

    return commit_case_checkpoint


commit_case_checkpoint = _bind_checkpoint_committer()
del _bind_checkpoint_committer


def verify_case_checkpoint(kind, ordinal, input_sha256):
    """Freshly verify an exact fixed numeric checkpoint, or return None if absent."""
    path = _checkpoint_path(kind, ordinal)
    _require_digest(input_sha256)
    context, contract = _registered_context()
    _require_regular_path(path, allow_missing=True)
    if not path.exists():
        return None
    raw, envelope = _read_json(path)
    return _verify_checkpoint_envelope(raw, envelope, kind, ordinal, input_sha256, context, contract)


__all__ = ["CampaignProvenanceError", "initialize_readiness_key",
           "readiness_anchor_descriptor", "commit_readiness",
           "verify_readiness_receipt", "require_verified_readiness_execution",
           "require_final_campaign_receipt", "commit_case_checkpoint", "verify_case_checkpoint"]
