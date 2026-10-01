"""Durable, host-trusted provenance for G entry receipts only.

No API signs caller dictionaries, accepts a key/anchor/output path, or admits
campaign predictions.  The controller alone issues execution handles.  HMAC
assumes an intact host, configured contract, filesystem and Python runtime; it
is neither independent cryptographic attestation nor a malicious-code sandbox.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import stat
from datetime import datetime, timezone


RUN_ID = "g30-entry-validation"
DOMAIN = "FlashTicketRca/TD13/G/ENTRY/v1"
SCHEMA = "TD13-G-ENTRY-DURABLE-v1"
_WORKSPACE = Path(__file__).resolve().parents[2]
_HOST_TRUST_MODE = "HOST_TRUSTED"
_FINAL_PERMISSIONS = (
    "final_labels", "final_tau_metadata", "final_answers", "final_outcomes",
    "final_predictions", "final_campaign",
)
_SOURCES = (
    "scripts/task_g/source_admission.py", "scripts/task_g/controller.py",
    "scripts/task_g/provenance.py", "tests/task_g/test_source_admission.py",
    "tests/task_g/test_controller.py", "tests/task_g/test_provenance.py",
)
_SCOPES = ("ENTRY_SYNTHETIC_DEVELOPMENT", "ENTRY_RAW_ADMISSION")
_ADMISSION_STATES = (
    "ADMISSION_COMPATIBLE", "ADMISSION_LIMITED__FAILURE_OR_OPEN_RETAINED",
    "PHYSICAL_SOURCE_FAILURE", "NOT_AUDITED_AFTER_SOURCE_FAILURE",
)
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_ID = re.compile(r"[A-Za-z0-9_-]{1,96}\Z")
_FROZEN = {
    "td_v1_3_sha256": "34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971",
    "task_f_v2_manifest_sha256": "c46b870bccdae1198292abc5850a83a3fa7e7f702286ceeaa07258074391801d",
    "metadata_sha256": "c49a288920dbba2e8e724679a14636d5c7eb2b45426bba14007ef79a6c0ab1bb",
}


class ProvenanceError(ValueError):
    """Entry issuance, persistent commitment, or configured trust is invalid."""


def _canonical(value):
    try:
        return json.dumps(
            value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ProvenanceError("Entry payload is not finite canonical JSON") from exc


def _digest(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _require_digest(value):
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise ProvenanceError("Invalid entry SHA256")
    return value


def _pairs_unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProvenanceError("Duplicate JSON key")
        result[key] = value
    return result


def _read_json_bytes(path):
    _require_regular_path(path)
    try:
        data = path.read_bytes()
        if len(data) > 128 * 1024 * 1024:
            raise ProvenanceError("Entry receipt exceeds registered bounded size")
        value = json.loads(data, object_pairs_hook=_pairs_unique,
                           parse_constant=lambda _: (_ for _ in ()).throw(
                               ProvenanceError("Nonfinite JSON number")))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProvenanceError("Entry JSON is unavailable or malformed") from exc
    return data, value


def _require_regular_path(path, *, allow_missing=False):
    """Reject symlinks/junctions anywhere along a configured path."""
    path = Path(path)
    if not path.is_absolute():
        raise ProvenanceError("Configured path must be absolute")
    for component in [*reversed(path.parents), path]:
        try:
            info = component.lstat()
        except FileNotFoundError:
            if allow_missing:
                continue
            raise ProvenanceError("Configured path is missing") from None
        except OSError as exc:
            raise ProvenanceError("Configured path is unavailable") from exc
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ProvenanceError("Configured path has a symbolic or reparse component")
    if path.exists() and not path.is_file():
        raise ProvenanceError("Configured file is not regular")


def _contract_path():
    return _WORKSPACE / "results/task-g" / RUN_ID / "entry-contract.json"


def _receipt_path():
    return _WORKSPACE / "results/task-g" / RUN_ID / "entry-validation.json"


def _staging_path():
    return (_WORKSPACE / "results/task-g" / RUN_ID / "cache"
            / ("entry-attempt-" + secrets.token_hex(16) + ".json"))


def _key_path():
    location = os.environ.get("LOCALAPPDATA")
    if not location or not Path(location).is_absolute():
        raise ProvenanceError("Trusted host LOCALAPPDATA is unavailable")
    return Path(location) / "FlashTicketRca/task-g-trust" / RUN_ID / "issuer.key"


def initialize_entry_key():
    """Exclusive host-key creation, explicitly invoked by the authorized owner.

    Existing or partial keys are retained and rejected; this never silently
    overwrites, rotates, repairs, prints, or writes a key into the output bundle.
    The returned public descriptor must be registered before any commitment.
    """
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
            raise ProvenanceError("Host key readback differs from issued bytes")
    except OSError as exc:
        raise ProvenanceError("Host key already exists or exclusive creation failed") from exc
    return entry_anchor_descriptor()


def entry_anchor_descriptor():
    """Return the existing key's public identity; never select or replace it."""
    path = _key_path()
    _require_regular_path(path)
    try:
        key = path.read_bytes()
    except OSError as exc:
        raise ProvenanceError("Trusted entry key is unavailable") from exc
    if len(key) != 32:
        raise ProvenanceError("Trusted entry key has invalid size")
    return {
        "algorithm": "HMAC-SHA256", "domain": DOMAIN, "run_id": RUN_ID,
        "trust_mode": _HOST_TRUST_MODE,
        "key_sha256": hashlib.sha256(key).hexdigest(),
    }


def _registered_context():
    raw, contract = _read_json_bytes(_contract_path())
    if (type(contract) is not dict or contract.get("run_id") != RUN_ID
            or contract.get("schema") != "TD13-G-ENTRY-CONTRACT-v1"):
        raise ProvenanceError("Wrong registered G entry contract")
    permissions = contract.get("permissions")
    if (type(permissions) is not dict
            or any(permissions.get(name) is not False for name in _FINAL_PERMISSIONS)
            or permissions.get("synthetic_development_fixture_execution") is not True):
        raise ProvenanceError("Entry contract cannot authorize final execution or labels")
    if contract.get("frozen_inputs") != _FROZEN:
        raise ProvenanceError("Frozen method/release/source identity changed")
    snapshot = contract.get("source_test_snapshot_before_qualification")
    if type(snapshot) is not dict or set(snapshot) != set(_SOURCES):
        raise ProvenanceError("Exact six-file reviewed source/test snapshot is required")
    for relative, expected in snapshot.items():
        _require_digest(expected)
        path = _WORKSPACE / relative
        _require_regular_path(path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ProvenanceError("Source/test drift invalidates entry qualification")
    anchor = contract.get("trust_anchor")
    if type(anchor) is not dict or anchor != entry_anchor_descriptor():
        raise ProvenanceError("Configured trusted anchor is missing or differs")
    return {
        "contract_sha256": hashlib.sha256(raw).hexdigest(),
        "permissions_sha256": _digest(permissions),
        "source_test_sha256": _digest(snapshot),
        "frozen_inputs_sha256": _digest(_FROZEN),
        "anchor": anchor,
    }


def _validate_execution(payload):
    if type(payload) is not dict or payload.get("scope") not in _SCOPES:
        raise ProvenanceError("Only issued G entry scopes may be committed")
    if payload.get("run_id") != RUN_ID or payload.get("domain") != DOMAIN:
        raise ProvenanceError("Execution domain or run differs from registered entry")
    if payload.get("execution_kind") != "ENTRY_ONLY":
        raise ProvenanceError("Entry issuer cannot authenticate a campaign execution")
    if payload.get("trust_mode") != _HOST_TRUST_MODE:
        raise ProvenanceError("Fixture and trusted host executions cannot be promoted")
    matrix, outputs = payload.get("planned_matrix"), payload.get("outputs")
    if type(matrix) is not list or not matrix or type(outputs) is not list:
        raise ProvenanceError("An exact planned entry matrix and outputs are required")
    identifiers = []
    for condition in matrix:
        if (type(condition) is not dict or set(condition) != {
                "condition_id", "kind", "expected_items"}
                or type(condition["condition_id"]) is not str
                or _ID.fullmatch(condition["condition_id"]) is None
                or type(condition["expected_items"]) is not int
                or not 1 <= condition["expected_items"] <= 256
                or condition["kind"] not in ("R", "RCD", "NUMERIC", "ADMISSION")):
            raise ProvenanceError("Malformed planned entry condition")
        identifiers.append(condition["condition_id"])
        if condition["kind"] == "R" and condition["expected_items"] != 256:
            raise ProvenanceError("Registered R condition must retain all 256 draws")
        if condition["kind"] == "RCD" and condition["expected_items"] != 3:
            raise ProvenanceError("Registered RCD condition must retain all three seeds")
    if len(set(identifiers)) != len(identifiers) or len(outputs) != len(matrix):
        raise ProvenanceError("Duplicate or missing entry condition")
    if _HOST_TRUST_MODE == "HOST_TRUSTED":
        expected = [{"condition_id": "RCD_SYNTHETIC", "kind": "RCD", "expected_items": 3}]
        if payload["scope"] == "ENTRY_RAW_ADMISSION":
            expected.append({"condition_id": "RAW_ADMISSION", "kind": "ADMISSION", "expected_items": 60})
        if matrix != expected:
            raise ProvenanceError("Production entry matrix differs from the authorized phase")
    for condition, row in zip(matrix, outputs):
        if (type(row) is not dict or set(row) != {"condition_id", "items"}
                or row["condition_id"] != condition["condition_id"]
                or type(row["items"]) is not list
                or len(row["items"]) != condition["expected_items"]):
            raise ProvenanceError("Entry outputs do not cover the registered matrix")
        if any(type(item) is not dict for item in row["items"]):
            raise ProvenanceError("Malformed planned entry item")
        if condition["kind"] == "RCD" and [item.get("seed") for item in row["items"]] != [420, 421, 422]:
            raise ProvenanceError("RCD durable outputs must retain registered seed order")
        if condition["kind"] == "R" and [item.get("draw") for item in row["items"]] != list(range(256)):
            raise ProvenanceError("R durable outputs must retain every registered draw")
        if condition["kind"] == "ADMISSION":
            if ([item.get("ordinal") for item in row["items"]] != list(range(condition["expected_items"]))
                    or any(item.get("case_status") not in _ADMISSION_STATES for item in row["items"])):
                raise ProvenanceError("Admission must retain every planned ordinal and explicit case state")
            continue
        for item in row["items"]:
            if type(item) is not dict or item.get("status") not in ("SUCCESS", "FAILURE", "UNAVAILABLE"):
                raise ProvenanceError("Every planned item needs an explicit output or failure")
    _canonical(payload)
    return True


def _validate_bindings(payload, context):
    from scripts.task_g.controller import prepare_conditions

    prepared = prepare_conditions()
    if (payload.get("source_snapshot_sha256") != context["source_test_sha256"]
            or payload.get("permissions_sha256") != context["permissions_sha256"]
            or payload.get("prepared_conditions") != prepared["conditions"]
            or payload.get("config_sha256") != prepared["sha256"]
            or payload.get("config_sha256") != _digest(payload["prepared_conditions"])
            or payload.get("final_condition_matrix_sha256") != prepared["sha256"]):
        raise ProvenanceError("Execution source/config/permissions differ from registered preparation")


def _bind_committer():
    """Keep arbitrary-payload signing inaccessible outside issued execution."""
    def commit_entry(execution_handle):
        from scripts.task_g.controller import _entry_payload_for_provenance

        context = _registered_context()
        payload = _entry_payload_for_provenance(execution_handle)
        _validate_execution(payload)
        _validate_bindings(payload, context)
        payload = json.loads(_canonical(payload))
        commitment = {
            "schema": SCHEMA, "domain": DOMAIN, "run_id": RUN_ID,
            "phase": "ENTRY_ONLY", "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
            "context": context, "execution": payload,
            "matrix_sha256": _digest(payload["planned_matrix"]),
            "outputs_sha256": _digest(payload["outputs"]),
            "payload_sha256": _digest(payload),
            "final_predictions": False, "final_labels": False, "final_campaign": False,
        }
        # A crash before the first fsync/readback leaves intentionally
        # incomplete JSON, incapable of authenticating a premature callback.
        prefix = b'{"commitment":' + _canonical(commitment)
        path = _receipt_path()
        _require_regular_path(path, allow_missing=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        _require_regular_path(path, allow_missing=True)
        staged = _staging_path()
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
                    raise ProvenanceError("Persisted numerical payload readback changed")
                key = _key_path().read_bytes()
                tag = hmac.new(key, _canonical(commitment), hashlib.sha256).hexdigest()
                envelope = {"commitment": commitment, "hmac_sha256": tag}
                encoded = _canonical(envelope)
                if not encoded.startswith(prefix):
                    raise ProvenanceError("Unexpected durable canonical envelope")
                stream.write(encoded[len(prefix):])
                stream.flush()
                os.fsync(stream.fileno())
            if staged.read_bytes() != encoded:
                raise ProvenanceError("Persisted commitment readback changed")
            # A complete authenticated cache file is still not an accepted
            # receipt.  Publish the fixed name exclusively only after both
            # fsyncs and readbacks and all semantic verification succeed.
            current_context = _registered_context()
            _verify_envelope(encoded, envelope, current_context)
            os.link(str(staged), str(path))
            result = verify_entry_receipt()
        except OSError as exc:
            raise ProvenanceError("Exclusive durable entry write failed; existing bytes retained") from exc
        return result

    return commit_entry


commit_entry = _bind_committer()
del _bind_committer


def verify_entry_receipt():
    """Fresh-process verification using independently configured host anchor."""
    context = _registered_context()
    raw, envelope = _read_json_bytes(_receipt_path())
    return _verify_envelope(raw, envelope, context)


def _verify_envelope(raw, envelope, context):
    """Verification only; no issuance, alternate trust anchor or signing path."""
    if type(envelope) is not dict or set(envelope) != {"commitment", "hmac_sha256"}:
        raise ProvenanceError("A complete durable entry envelope is required")
    commitment = envelope["commitment"]
    supplied = _require_digest(envelope["hmac_sha256"])
    if (type(commitment) is not dict or set(commitment) != {
            "schema", "domain", "run_id", "phase", "recorded_at_utc", "context",
            "execution", "matrix_sha256", "outputs_sha256", "payload_sha256",
            "final_predictions", "final_labels", "final_campaign"}
            or commitment["schema"] != SCHEMA or commitment["domain"] != DOMAIN
            or commitment["run_id"] != RUN_ID or commitment["phase"] != "ENTRY_ONLY"
            or commitment["context"] != context
            or any(commitment[name] is not False for name in (
                "final_predictions", "final_labels", "final_campaign"))):
        raise ProvenanceError("Wrong or drifted durable entry context")
    key = _key_path().read_bytes()
    expected = hmac.new(key, _canonical(commitment), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, supplied):
        raise ProvenanceError("Durable entry authentication failed")
    _validate_execution(commitment["execution"])
    payload = commitment["execution"]
    _validate_bindings(payload, context)
    if (commitment["matrix_sha256"] != _digest(payload["planned_matrix"])
            or commitment["outputs_sha256"] != _digest(payload["outputs"])
            or commitment["payload_sha256"] != _digest(payload)):
        raise ProvenanceError("Durable entry numerical payload differs")
    if raw != _canonical(envelope):
        raise ProvenanceError("Durable entry bytes are not canonical readback")
    return {
        "status": "PASS_DURABLE_ENTRY_ONLY", "scope": payload["scope"],
        "trust_mode": _HOST_TRUST_MODE, "run_id": RUN_ID, "domain": DOMAIN,
        "receipt_sha256": hashlib.sha256(raw).hexdigest(),
        "payload_sha256": commitment["payload_sha256"],
        "matrix_sha256": commitment["matrix_sha256"],
        "planned_conditions": len(payload["planned_matrix"]),
        "planned_items": sum(row["expected_items"] for row in payload["planned_matrix"]),
        "final_prediction_qualified": False,
    }


def evaluate_entry_fixture(label_provider, *, allow_synthetic_fixture=False):
    """Exercise lazy callback ordering only in isolated synthetic test scope.

    Host entry/raw receipts and all final scopes are rejected before invoking
    the callback.  Actual final evaluator/label rights require a later reviewed
    campaign implementation, contract, domain and authorization.
    """
    receipt = verify_entry_receipt()
    if (allow_synthetic_fixture is not True
            or receipt["trust_mode"] != "ISOLATED_FIXTURE"
            or receipt["scope"] != "ENTRY_SYNTHETIC_DEVELOPMENT"):
        raise ProvenanceError("Entry phase does not permit actual label opening")
    if not callable(label_provider):
        raise ProvenanceError("Synthetic fixture callback must be lazy")
    return {"receipt": receipt, "fixture_result": label_provider()}


__all__ = [
    "ProvenanceError", "initialize_entry_key", "entry_anchor_descriptor",
    "commit_entry", "verify_entry_receipt", "evaluate_entry_fixture",
]
