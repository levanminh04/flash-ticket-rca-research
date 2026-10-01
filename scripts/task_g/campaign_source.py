"""Issued numeric observations for G31 synthetic readiness and dev timing.

Only the fixed artificial fixture and the already pinned development C1 caches
can issue a handle. No API accepts a caller bundle, qualification flag, loader,
truth provider, source directory or final window. Paths, service identities and
absolute clocks stay inside this trusted controller boundary. This is an
ordinary-caller boundary on an intact host, not a Python sandbox.
"""

from __future__ import annotations

import copy
import hashlib
import io
import json
import re
import stat
import weakref
from pathlib import Path

import numpy as np

from rca.observation import C1Observation, C5Observation


WORKSPACE = Path(__file__).resolve().parents[2]
PROJECT = Path("D:/Project/flash-ticket-platform")
RUN_ID = "g31-campaign-readiness"
DOMAIN = "FlashTicketRca/TD13/G31/READINESS/v1"
CONTRACT_REL = f"results/task-g/{RUN_ID}/run-contract.json"
F05_REL = "results/task-f/f05-final-development-validation/run-contract.json"
F05_SHA = "1ae559dcfdbde7cf45b6c249797a1161ba9a8791ec13368007415b3682737d92"
DEVELOPMENT_INVENTORY_SHA = "2db903286747d0e7e1fe52eddc118f4cd19ce94d4d449570f3b50ccbe854be6f"
TD_SHA = "34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971"
F_V2_SHA = "c46b870bccdae1198292abc5850a83a3fa7e7f702286ceeaa07258074391801d"
FINAL_CLOSED = ("final_labels", "final_tau_metadata", "final_answers", "final_outcomes",
                "final_predictions", "final_campaign")
SNAPSHOT_PATHS = frozenset(
    f"{directory}/{name}.py"
    for directory, names in (
        ("scripts/task_g", ("campaign", "campaign_source", "campaign_provenance", "evaluation")),
        ("tests/task_g", ("test_campaign", "test_campaign_source", "test_campaign_provenance", "test_evaluation")),
    )
    for name in names
)
SYNTHETIC_SCOPE = "SYNTHETIC_CAMPAIGN_READINESS"
DEVELOPMENT_SCOPE = "DEVELOPMENT_TIMING_ONLY"
_HEX_HANDLE = re.compile(r"[0-9a-f]{16}\Z")


class CampaignSourceError(ValueError):
    """Sanitized source or registration error; no locators or telemetry text."""


class CampaignSource:
    __slots__ = ("__weakref__",)

    @property
    def summary(self):
        return source_summary(self)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _digest(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _regular_bytes(path):
    path = Path(path)
    if not path.is_absolute():
        raise CampaignSourceError("SOURCE_PATH_NOT_ABSOLUTE")
    try:
        for component in [*reversed(path.parents), path]:
            info = component.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise CampaignSourceError("SOURCE_REPARSE_COMPONENT")
        if not stat.S_ISREG(path.stat().st_mode):
            raise CampaignSourceError("SOURCE_NOT_REGULAR")
        return path.read_bytes()
    except OSError:
        raise CampaignSourceError("SOURCE_UNAVAILABLE") from None


def _registered_context():
    """Require the fixed preregistration and all eight stable source hashes."""
    try:
        encoded = _regular_bytes(WORKSPACE / CONTRACT_REL)
        contract = json.loads(encoded)
        permissions = contract["permissions"]
        if (contract.get("run_id") != RUN_ID
                or contract.get("domain") != DOMAIN
                or contract.get("phase") != "CAMPAIGN_READINESS_ONLY"
                or permissions.get("synthetic_development_readiness") is not True
                or permissions.get("telemetry_final60_new_acquisition") is not False
                or any(permissions.get(key) is not False for key in FINAL_CLOSED)):
            raise CampaignSourceError("READINESS_PERMISSION_OR_DOMAIN_DRIFT")
        snapshot = contract["source_test_snapshot_before_qualification"]
        if type(snapshot) is not dict or set(snapshot) != SNAPSHOT_PATHS:
            raise CampaignSourceError("STABLE_SOURCE_REGISTRATION_REQUIRED")
        for relative, expected in snapshot.items():
            if hashlib.sha256(_regular_bytes(WORKSPACE / relative)).hexdigest() != expected:
                raise CampaignSourceError("REGISTERED_SOURCE_TEST_DRIFT")
        manifest_bytes = _regular_bytes(WORKSPACE / "configs/task-f-td13-frozen-release-v2.json")
        if (contract["frozen_inputs"]["td_v1_3_sha256"] != TD_SHA
                or contract["frozen_inputs"]["task_f_v2_manifest_sha256"] != F_V2_SHA
                or hashlib.sha256(_regular_bytes(PROJECT / "docs/research-rca/task-d-method-and-experiment-specification.md")).hexdigest() != TD_SHA
                or hashlib.sha256(manifest_bytes).hexdigest() != F_V2_SHA):
            raise CampaignSourceError("FROZEN_SOURCE_DRIFT")
        manifest = json.loads(manifest_bytes)
        adapters = manifest["implementation"]["qualified_development_loader"]["source_files"]
        if {row["path"] for row in adapters} != {"scripts/task_e/loader.py", "scripts/task_e/replay.py", "scripts/task_e/input_adapters.py"}:
            raise CampaignSourceError("FROZEN_ADAPTER_REGISTRY_DRIFT")
        for row in adapters:
            if hashlib.sha256(_regular_bytes(WORKSPACE / row["path"])).hexdigest() != row["sha256"]:
                raise CampaignSourceError("FROZEN_ADAPTER_SOURCE_DRIFT")
        for label, expected in contract["protected_sha256"].items():
            prefix, relative = label.split("/", 1)
            root = {"P": PROJECT, "W": WORKSPACE}.get(prefix)
            if root is None or not (root / relative).resolve().is_relative_to(root.resolve()):
                raise CampaignSourceError("PROTECTED_REFERENCE_ESCAPE")
            if hashlib.sha256(_regular_bytes(root / relative)).hexdigest() != expected:
                raise CampaignSourceError("PROTECTED_REFERENCE_DRIFT")
        development = contract["development_inputs"]
        if (development.get("contract_path") != F05_REL
                or development.get("contract_sha256") != F05_SHA
                or development.get("numeric_inventory_sha256") != DEVELOPMENT_INVENTORY_SHA
                or development.get("expected_cases") != 30):
            raise CampaignSourceError("DEVELOPMENT_REGISTRATION_DRIFT")
        return {"contract_sha256": hashlib.sha256(encoded).hexdigest(),
                "permissions": copy.deepcopy(permissions),
                "entry_bindings": copy.deepcopy(contract["entry_bindings"])}
    except CampaignSourceError:
        raise
    except (OSError, ValueError, TypeError, KeyError):
        raise CampaignSourceError("READINESS_REGISTRATION_UNAVAILABLE") from None


def _array_manifest(arrays):
    result = {}
    for key, value in arrays.items():
        value = np.asarray(value)
        if value.dtype.kind not in "biuf" or np.isinf(value).any():
            raise CampaignSourceError("INVALID_NUMERIC_OBSERVATION")
        contiguous = np.ascontiguousarray(value)
        result[key] = {"dtype": contiguous.dtype.str, "shape": list(contiguous.shape),
                       "sha256": hashlib.sha256(contiguous.tobytes()).hexdigest()}
    return result


def _c1_copy(observation):
    return C1Observation(
        handle=observation.handle, ref=observation.ref, query=observation.query,
        channel_types=observation.channel_types, adjacency=observation.adjacency,
        node_ids=observation.node_ids, source_hashes=dict(observation.source_hashes),
        graph_provenance=dict(observation.graph_provenance), quality=dict(observation.quality),
        evidence_catalog={},
    )


def _c5_copy(observation):
    if observation is None:
        return None
    return C5Observation(
        handle=observation.handle, warmup_values=observation.warmup_values,
        stream_values=observation.stream_values, channel_types=observation.channel_types,
        adjacency=observation.adjacency, fit_service_mask=observation.fit_service_mask,
        node_ids=observation.node_ids, relative_endpoints=observation.relative_endpoints,
        source_hashes=dict(observation.source_hashes),
        graph_provenance=dict(observation.graph_provenance), quality=dict(observation.quality),
        evidence_catalog={},
    )


def _case_fingerprint(c1, c5, rcd):
    arrays = {"c1_ref": c1.ref, "c1_query": c1.query, "c1_adj": c1.adjacency,
              "c1_channel_types": np.asarray(c1.channel_types)}
    if c5 is not None:
        arrays.update(c5_warmup=c5.warmup_values, c5_stream=c5.stream_values,
                      c5_adj=c5.adjacency, c5_fit_mask=c5.fit_service_mask,
                      c5_endpoints=c5.relative_endpoints,
                      c5_channel_types=np.asarray(c5.channel_types))
    if rcd is not None:
        arrays.update(rcd_values=rcd["values"], rcd_owners=np.asarray(rcd["owners"], dtype=np.int64))
    return _digest(_array_manifest(arrays))


def _fixed_fixture_raw():
    """Artificial observations only; fixture times are never benchmark truth."""
    import pandas as pd
    from scripts.task_e.loader import TRACE_FIELDS

    origin = 100_000
    relative = np.arange(1080, dtype=np.int64)
    seconds = origin + relative
    metrics = pd.DataFrame({"time": seconds})
    for node in range(3):
        values = 10 + 2 * np.sin(relative / 7 + node) + .1 * np.cos(relative / 13)
        values += (relative >= 180) * (1_000_000.0 * (node + 1))
        if node == 0:
            values += (relative >= 720) * 1_000_000.0
        metrics[f"v{node}_cpu"] = values
    traces = []
    for second in seconds[::5]:
        for node in range(3):
            traces.append(("artificial", f"trace-{second}", f"span-{second}-{node}", f"v{node}",
                           "artificial-method", "artificial-operation",
                           "" if node == 0 else f"span-{second}-{node-1}",
                           int(second) * 1000, int(second), 1, 200))
    logs = pd.DataFrame({"timestamp": np.repeat(seconds[::10], 3),
                         "container_name": np.tile(["v0", "v1", "v2"], len(seconds[::10])),
                         "message": "artificial fixture"})
    return {"metrics": metrics, "traces": pd.DataFrame(traces, columns=TRACE_FIELDS),
            "logs": logs}, origin


def _synthetic_cases(_raw_builder=_fixed_fixture_raw):
    from scripts.task_e.input_adapters import integrated_bundle, rcd_bundle
    from scripts.task_e.loader import c1_bundle, c5_bundle

    raw, origin = _raw_builder()
    c1 = c1_bundle(raw, origin + 720)
    c5 = c5_bundle(raw)
    rcd = rcd_bundle(raw, origin + 720, c1["service_names"])
    rcd_numeric = {"values": rcd["values"].copy(),
                   "owners": list(rcd["owners"].values()), "candidate_count": len(c1["adj"])}
    source_hash = _digest(_array_manifest({"c1_ref": c1["ref"], "c1_query": c1["query"],
                                         "c5_values": c5["values"], "rcd_values": rcd["values"]}))
    cases = []
    for ordinal in range(60):
        route = hashlib.sha256(f"G31|ARTIFICIAL|{ordinal}".encode()).hexdigest()[:16]
        hashes = {"artificial_numeric_source": source_hash}
        quality = {"scope": SYNTHETIC_SCOPE, "candidate_names_redacted": True,
                   "actual_final_admission": False}
        one = C1Observation(route, c1["ref"], c1["query"], tuple(c1["channel_types"]),
                            c1["adj"], tuple(f"v{i}" for i in range(len(c1["adj"]))),
                            hashes, {"reference_only": True}, quality, {})
        five = C5Observation(route, c5["values"][:36], c5["values"][36:],
                             tuple(c5["channel_types"]), c5["adj"], c5["fit_service_mask"],
                             tuple(f"v{i}" for i in range(len(c5["adj"]))),
                             c5["endpoints"][36:], hashes, {"fit_graph_frozen": True}, quality, {})
        cases.append({"ordinal": ordinal, "cell_ordinal": ordinal // 3, "repeat": ordinal % 3,
                      "c1": one, "c5": five, "rcd": rcd_numeric,
                      "numeric_input_sha256": _case_fingerprint(one, five, rcd_numeric)})

    def integrated(ordinal, endpoint):
        if endpoint < 360:
            raise CampaignSourceError("INSUFFICIENT_HISTORY")
        if endpoint > 1080:
            raise CampaignSourceError("INTEGRATED_ENDPOINT_OUTSIDE_OBSERVED_HISTORY")
        # The frozen builder physically slices past windows. Full archive
        # identity is provenance only and never creates a future vocabulary.
        bundle = integrated_bundle(raw, origin + endpoint)
        return C1Observation(
            cases[ordinal]["c1"].handle, bundle["ref"], bundle["query"],
            tuple(bundle["channel_types"]), bundle["adj"],
            tuple(f"v{i}" for i in range(len(bundle["adj"]))),
            {"artificial_numeric_source": source_hash},
            {"reference_only": True, "past_only": True},
            {"scope": SYNTHETIC_SCOPE, "profile": "TD12-INTEGRATED-MTL",
             "relative_endpoint": endpoint, "candidate_names_redacted": True}, {},
        )
    return cases, integrated


def _development_cases():
    encoded = _regular_bytes(WORKSPACE / F05_REL)
    if hashlib.sha256(encoded).hexdigest() != F05_SHA:
        raise CampaignSourceError("PINNED_DEVELOPMENT_CONTRACT_DRIFT")
    try:
        contract = json.loads(encoded)
        references = [row for row in contract["input_files"]
                      if row["path"].endswith("/c1_primary.npz")]
        if len(references) != 30 or _digest(references) != DEVELOPMENT_INVENTORY_SHA:
            raise CampaignSourceError("PINNED_DEVELOPMENT_INVENTORY_DRIFT")
        handles = [contract["opaque_handles_by_development_id"][case]
                   for case in contract["development_allowlist"]]
        if len(handles) != 30 or len(set(handles)) != 30 or any(_HEX_HANDLE.fullmatch(h) is None for h in handles):
            raise CampaignSourceError("PINNED_DEVELOPMENT_ROSTER_DRIFT")
        cases = []
        for ordinal, (row, route) in enumerate(zip(references, handles)):
            expected = f"results/task-e/e27-019-development-loader-audit/intermediates/{route}/c1_primary.npz"
            if row["path"] != expected or row["role"] != "sealed-c1-numeric-input":
                raise CampaignSourceError("PINNED_NUMERIC_REFERENCE_DRIFT")
            payload = _regular_bytes(WORKSPACE / expected)
            if len(payload) != row["bytes"] or hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise CampaignSourceError("PINNED_NUMERIC_BYTES_DRIFT")
            with np.load(io.BytesIO(payload), allow_pickle=False) as stored:
                if set(stored.files) != {"ref", "query", "adj", "channel_types"}:
                    raise CampaignSourceError("NUMERIC_CACHE_SCHEMA_DRIFT")
                arrays = {key: stored[key].copy() for key in stored.files}
            if (arrays["ref"].shape != arrays["query"].shape
                    or arrays["ref"].ndim != 3 or arrays["ref"].shape[1:] != (12, 30)
                    or arrays["channel_types"].dtype.kind not in "iu"
                    or not np.array_equal(arrays["channel_types"], [0] * 10 + [1, 2])):
                raise CampaignSourceError("NUMERIC_CACHE_SHAPE_DRIFT")
            count = arrays["ref"].shape[0]
            one = C1Observation(route, arrays["ref"], arrays["query"], tuple(arrays["channel_types"]),
                                arrays["adj"], tuple(f"v{i}" for i in range(count)),
                                {"numeric": row["sha256"], "pinned_input_contract": F05_SHA},
                                {"reference_only": True},
                                {"scope": DEVELOPMENT_SCOPE, "candidate_names_redacted": True,
                                 "actual_final_admission": False}, {})
            cases.append({"ordinal": ordinal, "cell_ordinal": ordinal // 3, "repeat": ordinal % 3,
                          "c1": one, "c5": None, "rcd": None,
                          "numeric_input_sha256": _case_fingerprint(one, None, None)})
        return cases, None
    except CampaignSourceError:
        raise
    except Exception:
        raise CampaignSourceError("PINNED_NUMERIC_INPUT_INVALID") from None


def _bind_sources():
    """Capture producers and state; expose no arbitrary issuer or mutable lookup."""
    registry = weakref.WeakKeyDictionary()
    synthetic_builder, development_builder = _synthetic_cases, _development_cases

    def require(handle):
        if type(handle) is not CampaignSource or handle not in registry:
            raise CampaignSourceError("UNISSUED_CAMPAIGN_SOURCE")
        state = registry[handle]
        if _registered_context() != state["context"]:
            raise CampaignSourceError("ISSUED_SOURCE_CONTEXT_DRIFT")
        return state

    def create(builder, scope, kind):
        context = _registered_context()
        if scope == DEVELOPMENT_SCOPE and context["permissions"].get("development30_timing_only") is not True:
            raise CampaignSourceError("DEVELOPMENT_TIMING_PERMISSION_CLOSED")
        cases, integrated = builder()
        inventory = [{"ordinal": row["ordinal"], "numeric_input_sha256": row["numeric_input_sha256"],
                      "routing_handle_sha256": hashlib.sha256(row["c1"].handle.encode()).hexdigest()}
                     for row in cases]
        summary = {"schema": "TD13-G31-NUMERIC-SOURCE-v1", "scope": scope, "source_kind": kind,
                   "planned_cases": len(cases), "planned_cells": len(cases) // 3,
                   "repeats_per_cell": 3, "source_sha256": _digest(inventory),
                   "contract_sha256": context["contract_sha256"],
                   "candidate_count_min": min(len(row["c1"].node_ids) for row in cases),
                   "candidate_count_max": max(len(row["c1"].node_ids) for row in cases),
                   "c5_available_cases": sum(row["c5"] is not None for row in cases),
                   "rcd_available_cases": sum(row["rcd"] is not None for row in cases),
                   "case_ids_paths_disclosed": False, "actual_truth_read": False,
                   "actual_final_telemetry_opened": False, "final_prediction_qualified": False}
        if scope == DEVELOPMENT_SCOPE:
            summary.update(pinned_input_contract_sha256=F05_SHA,
                           pinned_numeric_inventory_sha256=DEVELOPMENT_INVENTORY_SHA,
                           input_scope="EXACT30_PINNED_C1_NUMERIC_ONLY_NO_AUDIT_LABELS")
        handle = CampaignSource()
        registry[handle] = {"context": context, "cases": cases, "summary": summary, "integrated": integrated}
        return handle

    def synthetic():
        return create(synthetic_builder, SYNTHETIC_SCOPE, "SYNTHETIC_NUMERIC")

    def development():
        return create(development_builder, DEVELOPMENT_SCOPE, "DEVELOPMENT_NUMERIC_CACHE")

    def summary(handle):
        return copy.deepcopy(require(handle)["summary"])

    def count(handle):
        return len(require(handle)["cases"])

    def ordinal_case(state, ordinal):
        if type(ordinal) is not int or not 0 <= ordinal < len(state["cases"]):
            raise CampaignSourceError("INVALID_CASE_ORDINAL")
        return state["cases"][ordinal]

    def case(handle, ordinal):
        row = ordinal_case(require(handle), ordinal)
        rcd = None if row["rcd"] is None else {"values": row["rcd"]["values"].copy(),
              "owners": list(row["rcd"]["owners"]), "candidate_count": row["rcd"]["candidate_count"]}
        return {"ordinal": row["ordinal"], "cell_ordinal": row["cell_ordinal"], "repeat": row["repeat"],
                "c1": _c1_copy(row["c1"]), "c5": _c5_copy(row["c5"]), "rcd": rcd,
                "numeric_input_sha256": row["numeric_input_sha256"]}

    def integrated(handle, ordinal, relative_endpoint):
        state = require(handle)
        ordinal_case(state, ordinal)
        if type(relative_endpoint) is not int or relative_endpoint < 0 or relative_endpoint % 5:
            raise CampaignSourceError("INVALID_RELATIVE_TRIGGER_ENDPOINT")
        if state["integrated"] is None:
            raise CampaignSourceError("DEVELOPMENT_TIMING_HAS_NO_INTEGRATED_SOURCE")
        return state["integrated"](ordinal, relative_endpoint)

    return synthetic, development, summary, count, case, integrated


(make_synthetic_source, load_development_source, source_summary, case_count,
 get_case, integrated_observation) = _bind_sources()
del _bind_sources, _synthetic_cases, _development_cases, _fixed_fixture_raw


def open_final_source():
    """Verify existing HOST ENTRY independently, then reject the closed phase.

    No raw byte, τ column or caller receipt is opened here. Admission integrity
    is necessary evidence for a future source, and cannot grant campaign rights.
    """
    context = _registered_context()
    from scripts.task_g.provenance import verify_entry_receipt

    verified = verify_entry_receipt()
    if (verified.get("scope") != "ENTRY_RAW_ADMISSION"
            or verified.get("trust_mode") != "HOST_TRUSTED"
            or verified.get("receipt_sha256") != context["entry_bindings"].get("receipt_sha256")):
        raise CampaignSourceError("FINAL_SOURCE_ENTRY_BINDING_INVALID")
    raise CampaignSourceError("FINAL_TAU_AND_CAMPAIGN_PERMISSION_CLOSED")


__all__ = ["CampaignSource", "CampaignSourceError", "make_synthetic_source", "load_development_source",
           "source_summary", "case_count", "get_case", "integrated_observation", "open_final_source"]
