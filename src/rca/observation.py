"""Trusted admission boundary from public telemetry to numeric RCA observations.

Raw file paths and absolute event clocks stay on the controller side.  A
qualified loader callable may be injected, but the resulting core observation
contains only relative numeric arrays, literal candidate identities used for
telemetry joins, opaque evidence identifiers, source hashes, and quality data.
Ground truth and evaluator metadata are rejected recursively.
"""

from __future__ import annotations

import copy
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

import numpy as np


class ObservationError(ValueError):
    """Telemetry admission would violate shape, provenance, or firewall rules."""


_FORBIDDEN_KEYS = frozenset(
    {
        "root",
        "rootcause",
        "rootcauseservice",
        "rootpresence",
        "groundtruth",
        "groundtruthroot",
        "fault",
        "faultlabel",
        "label",
        "labels",
        "answer",
        "answerfile",
        "tau",
        "injection",
        "injectedfault",
        "casepath",
        "absolutepath",
        "evaluator",
        "outcome",
        "finaloutcome",
        "s0",
        "eventms",
        "firstseenms",
        "firstconflictms",
        "injecttime",
        "timemin",
        "timemax",
    }
)
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")


def _normalized_key(value: object) -> str:
    return "".join(character for character in str(value).lower() if character.isalnum())


def _firewall(value: Any, location: str = "observation") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = _normalized_key(key)
            if normalized in _FORBIDDEN_KEYS or normalized.startswith("groundtruth"):
                raise ObservationError(f"Forbidden evaluator/oracle field: {location}.{key}")
            _firewall(item, f"{location}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _firewall(item, f"{location}[{index}]")
    elif isinstance(value, str):
        if _WINDOWS_ABSOLUTE.match(value) or value.startswith(("/", "\\\\")):
            raise ObservationError(f"Absolute path is forbidden in core observation: {location}")


def _opaque_handle(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 128
        or any(character in value for character in ("|", "/", "\\"))
    ):
        raise ObservationError("A delimiter-free opaque handle is required")
    return value


def _node_ids(values: Sequence[object], count: int) -> tuple[str, ...]:
    result = tuple(values)
    if (
        len(result) != count
        or len(set(result)) != count
        or any(not isinstance(value, str) or not value for value in result)
    ):
        raise ObservationError("node_ids must be unique nonempty strings matching N")
    _firewall(result, "node_ids")
    return result


def _hashes(values: Mapping[str, str]) -> Mapping[str, str]:
    result = dict(values)
    if not result or any(
        not isinstance(key, str)
        or not key
        or not isinstance(value, str)
        or (
            value not in ("MISSING", "CORRUPT")
            and (
                len(value) != 64
                or any(character not in "0123456789abcdef" for character in value)
            )
        )
        for key, value in result.items()
    ):
        raise ObservationError("Explicit source SHA256/absence markers are required")
    return MappingProxyType(result)


def _deep_frozen(value: Any) -> Any:
    """Detach nested controller data and make containers/arrays read-only."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: _deep_frozen(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_deep_frozen(item) for item in value)
    if isinstance(value, np.ndarray):
        result = value.copy()
        result.setflags(write=False)
        return result
    return copy.deepcopy(value)


def _frozen_mapping(value: Mapping[str, Any], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ObservationError(f"{label} must be a mapping")
    _firewall(value, label)
    return _deep_frozen(dict(value))


def _quality_projection(value: Any) -> Any:
    """Keep model-facing quality diagnostics while dropping controller identity.

    Task E audits intentionally retain absolute clocks and trace-key identity so
    that replay can be defended.  TD-v1.3 keeps those fields controller-side.
    This projection preserves counts, relative bins, masks, graph statistics,
    and availability reasons without serializing absolute time or key payloads.
    """
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            normalized = _normalized_key(key)
            if normalized in {
                "s0",
                "eventms",
                "firstseenms",
                "firstconflictms",
                "injecttime",
                "timemin",
                "timemax",
            } or "absolutepath" in normalized or normalized.endswith("path"):
                continue
            if normalized == "conflictingseconds" and isinstance(item, Mapping):
                result["conflicting_second_counts"] = {
                    str(name): len(times) if isinstance(times, (list, tuple)) else 0
                    for name, times in item.items()
                }
                continue
            if normalized == "events" and isinstance(item, (list, tuple)):
                counts: dict[str, int] = {}
                affected_bins: set[int] = set()
                for event in item:
                    if not isinstance(event, Mapping):
                        continue
                    kind = str(event.get("kind", "UNKNOWN"))
                    counts[kind] = counts.get(kind, 0) + 1
                    relative_bin = event.get("bin")
                    if isinstance(relative_bin, (int, np.integer)) and relative_bin >= 0:
                        affected_bins.add(int(relative_bin))
                result["event_counts_by_kind"] = counts
                result["affected_relative_bins"] = sorted(affected_bins)
                continue
            if normalized == "quarantinedkeys" and isinstance(item, (list, tuple)):
                result["quarantined_key_count"] = len(item)
                continue
            if normalized == "postfreezediscreditedsupport" and isinstance(item, (list, tuple)):
                result["post_freeze_discredited_support_count"] = len(item)
                continue
            projected = _quality_projection(item)
            if projected is not None:
                result[str(key)] = projected
        return result
    if isinstance(value, (list, tuple)):
        return [_quality_projection(item) for item in value]
    if isinstance(value, str) and (_WINDOWS_ABSOLUTE.match(value) or value.startswith(("/", "\\\\"))):
        return None
    return copy.deepcopy(value)


def _require_qualification(audit: Mapping[str, Any], profile: str) -> None:
    qualification = audit.get("qualification")
    if (
        not isinstance(qualification, Mapping)
        or qualification.get("status") != "QUALIFIED"
        or qualification.get("profile") != profile
        or not isinstance(qualification.get("adapter_id"), str)
        or not qualification.get("adapter_id")
    ):
        raise ObservationError(f"Bundle is not qualified for {profile}")


def _adjacency(value: Any, nodes: int) -> np.ndarray:
    result = np.asarray(value)
    if (
        result.shape != (nodes, nodes)
        or not np.isfinite(result).all()
        or not np.isin(result, (0, 1)).all()
        or np.diag(result).any()
    ):
        raise ObservationError("adjacency must be finite binary NxN without self edges")
    result = result.astype(bool, copy=True)
    result.setflags(write=False)
    return result


def _numeric(value: Any, dimensions: int, label: str) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.ndim != dimensions or np.isinf(result).any():
        raise ObservationError(f"{label} must be {dimensions}D finite-or-NaN numeric data")
    result = result.copy()
    result.setflags(write=False)
    return result


def _evidence_catalog(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    result = {} if value is None else dict(value)
    if any(not isinstance(key, str) or not key for key in result):
        raise ObservationError("Evidence IDs must be nonempty strings")
    _firewall(result, "evidence_catalog")
    return _deep_frozen(result)


@dataclass(frozen=True)
class C1Observation:
    handle: str
    ref: np.ndarray
    query: np.ndarray
    channel_types: tuple[object, ...]
    adjacency: np.ndarray
    node_ids: tuple[str, ...]
    source_hashes: Mapping[str, str]
    graph_provenance: Mapping[str, Any]
    quality: Mapping[str, Any]
    evidence_catalog: Mapping[str, Any]

    def __post_init__(self):
        handle = _opaque_handle(self.handle)
        ref = _numeric(self.ref, 3, "ref")
        query = _numeric(self.query, 3, "query")
        if ref.shape[:2] != query.shape[:2]:
            raise ObservationError("C1 ref/query must share (N,K) and be three-dimensional")
        channel_types = tuple(self.channel_types)
        if len(channel_types) != ref.shape[1]:
            raise ObservationError("C1 channel_types must match K")
        adjacency = _adjacency(self.adjacency, ref.shape[0])
        node_ids = _node_ids(self.node_ids, ref.shape[0])
        object.__setattr__(self, "handle", handle)
        object.__setattr__(self, "ref", ref)
        object.__setattr__(self, "query", query)
        object.__setattr__(self, "channel_types", channel_types)
        object.__setattr__(self, "adjacency", adjacency)
        object.__setattr__(self, "node_ids", node_ids)
        object.__setattr__(self, "source_hashes", _hashes(self.source_hashes))
        object.__setattr__(
            self,
            "graph_provenance",
            _frozen_mapping(self.graph_provenance, "graph_provenance"),
        )
        object.__setattr__(self, "quality", _frozen_mapping(self.quality, "quality"))
        object.__setattr__(
            self,
            "evidence_catalog",
            _evidence_catalog(self.evidence_catalog),
        )


@dataclass(frozen=True)
class C5Observation:
    handle: str
    warmup_values: np.ndarray
    stream_values: np.ndarray
    channel_types: tuple[object, ...]
    adjacency: np.ndarray
    fit_service_mask: np.ndarray
    node_ids: tuple[str, ...]
    relative_endpoints: np.ndarray
    source_hashes: Mapping[str, str]
    graph_provenance: Mapping[str, Any]
    quality: Mapping[str, Any]
    evidence_catalog: Mapping[str, Any]

    def __post_init__(self):
        handle = _opaque_handle(self.handle)
        warmup_values = _numeric(self.warmup_values, 3, "warmup_values")
        stream_values = _numeric(self.stream_values, 3, "stream_values")
        if warmup_values.shape[1:] != stream_values.shape[1:]:
            raise ObservationError("C5 warmup/stream must share (N,C) and be three-dimensional")
        nodes, channels = warmup_values.shape[1:]
        channel_types = tuple(self.channel_types)
        node_ids = _node_ids(self.node_ids, nodes)
        if len(channel_types) != channels:
            raise ObservationError("C5 identities/types must match numeric axes")
        adjacency = _adjacency(self.adjacency, nodes)
        fit_service_mask = np.asarray(self.fit_service_mask)
        if fit_service_mask.dtype != np.bool_ or fit_service_mask.shape != (nodes,):
            raise ObservationError("C5 fit_service_mask must be an N-vector")
        fit_service_mask = fit_service_mask.copy()
        fit_service_mask.setflags(write=False)
        if adjacency[~fit_service_mask].any() or adjacency[:, ~fit_service_mask].any():
            raise ObservationError("Calibration-only services must be graph isolates")
        relative_endpoints = np.asarray(self.relative_endpoints)
        if relative_endpoints.dtype.kind not in "iu" or relative_endpoints.shape != (len(stream_values),):
            raise ObservationError("C5 relative_endpoints must match the stream")
        relative_endpoints = relative_endpoints.astype(np.int64, copy=True)
        relative_endpoints.setflags(write=False)
        if len(relative_endpoints) and (
            (relative_endpoints < 0).any()
            or not np.all(np.diff(relative_endpoints) > 0)
        ):
            raise ObservationError("C5 endpoints must be increasing relative times")
        object.__setattr__(self, "handle", handle)
        object.__setattr__(self, "warmup_values", warmup_values)
        object.__setattr__(self, "stream_values", stream_values)
        object.__setattr__(self, "channel_types", channel_types)
        object.__setattr__(self, "adjacency", adjacency)
        object.__setattr__(self, "fit_service_mask", fit_service_mask)
        object.__setattr__(self, "node_ids", node_ids)
        object.__setattr__(self, "relative_endpoints", relative_endpoints)
        object.__setattr__(self, "source_hashes", _hashes(self.source_hashes))
        object.__setattr__(
            self,
            "graph_provenance",
            _frozen_mapping(self.graph_provenance, "graph_provenance"),
        )
        object.__setattr__(self, "quality", _frozen_mapping(self.quality, "quality"))
        object.__setattr__(
            self,
            "evidence_catalog",
            _evidence_catalog(self.evidence_catalog),
        )


def admit_c1_bundle(
    bundle: Mapping[str, Any],
    *,
    handle: str,
    source_hashes: Mapping[str, str],
    evidence_catalog: Mapping[str, Any] | None = None,
) -> C1Observation:
    """Validate a qualified public-data C1 loader result for the core."""
    required = {"ref", "query", "adj", "service_names", "channel_types", "audit"}
    if not isinstance(bundle, Mapping) or required - set(bundle):
        raise ObservationError("Incomplete qualified C1 bundle")
    ref = _numeric(bundle["ref"], 3, "ref")
    query = _numeric(bundle["query"], 3, "query")
    if ref.shape[:2] != query.shape[:2]:
        raise ObservationError("C1 ref/query axes differ")
    node_ids = _node_ids(bundle["service_names"], ref.shape[0])
    audit = dict(bundle["audit"])
    profile = str(audit.get("profile", ""))
    if profile not in {"TD12-C1-MT", "TD12-INTEGRATED-MTL"}:
        raise ObservationError("Unknown C1 bundle profile")
    _require_qualification(audit, profile)
    graph = audit.pop("graph", {})
    quality = _frozen_mapping(_quality_projection(audit), "quality")
    return C1Observation(
        handle=_opaque_handle(handle),
        ref=ref,
        query=query,
        channel_types=tuple(bundle["channel_types"]),
        adjacency=_adjacency(bundle["adj"], ref.shape[0]),
        node_ids=node_ids,
        source_hashes=_hashes(source_hashes),
        graph_provenance=_frozen_mapping(graph, "graph_provenance"),
        quality=quality,
        evidence_catalog=_evidence_catalog(evidence_catalog),
    )


def admit_c5_bundle(
    bundle: Mapping[str, Any],
    *,
    handle: str,
    source_hashes: Mapping[str, str],
    fit_bins: int,
    cal_bins: int,
    evidence_catalog: Mapping[str, Any] | None = None,
) -> C5Observation:
    """Drop absolute origin and admit a qualified chronological C5 bundle."""
    required = {
        "values",
        "adj",
        "service_names",
        "channel_types",
        "fit_service_mask",
        "endpoints",
        "audit",
    }
    if not isinstance(bundle, Mapping) or required - set(bundle):
        raise ObservationError("Incomplete qualified C5 bundle")
    values = _numeric(bundle["values"], 3, "values")
    warmup_bins = fit_bins + cal_bins
    if len(values) < warmup_bins:
        raise ObservationError("C5 bundle is shorter than the frozen warmup")
    node_ids = _node_ids(bundle["service_names"], values.shape[1])
    endpoints = np.asarray(bundle["endpoints"], dtype=np.int64)
    if endpoints.shape != (len(values),):
        raise ObservationError("C5 loader endpoints must match values")
    relative = endpoints[warmup_bins:].copy()
    relative.setflags(write=False)
    fit_mask = np.asarray(bundle["fit_service_mask"])
    if fit_mask.dtype != np.bool_ or fit_mask.shape != (values.shape[1],):
        raise ObservationError("Invalid C5 fit_service_mask")
    fit_mask = fit_mask.copy()
    fit_mask.setflags(write=False)
    audit = dict(bundle["audit"])
    _require_qualification(audit, "TD13-C5-EVENT-TIME")
    graph = audit.pop("graph", {})
    # s0 is intentionally not copied: the model-facing contract uses relative time.
    return C5Observation(
        handle=_opaque_handle(handle),
        warmup_values=_numeric(values[:warmup_bins], 3, "warmup_values"),
        stream_values=_numeric(values[warmup_bins:], 3, "stream_values"),
        channel_types=tuple(bundle["channel_types"]),
        adjacency=_adjacency(bundle["adj"], values.shape[1]),
        fit_service_mask=fit_mask,
        node_ids=node_ids,
        relative_endpoints=relative,
        source_hashes=_hashes(source_hashes),
        graph_provenance=_frozen_mapping(graph, "graph_provenance"),
        quality=_frozen_mapping(_quality_projection(audit), "quality"),
        evidence_catalog=_evidence_catalog(evidence_catalog),
    )


def public_c1_observation(
    raw_telemetry: Mapping[str, Any],
    *,
    qualified_adapter: Any,
    loader_kwargs: Mapping[str, Any],
    handle: str,
    evidence_catalog: Mapping[str, Any] | None = None,
) -> C1Observation:
    """Clear public-telemetry→C1 boundary using a byte-bound adapter."""
    from .adapters import QualifiedTelemetryAdapter

    if not isinstance(qualified_adapter, QualifiedTelemetryAdapter):
        raise ObservationError("A byte-bound QualifiedTelemetryAdapter is required")
    bundle = qualified_adapter.c1(raw_telemetry, **dict(loader_kwargs))
    return admit_c1_bundle(
        bundle,
        handle=handle,
        source_hashes=qualified_adapter.source_hashes(raw_telemetry),
        evidence_catalog=evidence_catalog,
    )


def public_c5_observation(
    raw_telemetry: Mapping[str, Any],
    *,
    qualified_adapter: Any,
    loader_kwargs: Mapping[str, Any],
    handle: str,
    fit_bins: int,
    cal_bins: int,
    evidence_catalog: Mapping[str, Any] | None = None,
) -> C5Observation:
    """Clear public-telemetry→C5 boundary using a byte-bound adapter."""
    from .adapters import QualifiedTelemetryAdapter

    if not isinstance(qualified_adapter, QualifiedTelemetryAdapter):
        raise ObservationError("A byte-bound QualifiedTelemetryAdapter is required")
    bundle = qualified_adapter.c5(raw_telemetry, **dict(loader_kwargs))
    return admit_c5_bundle(
        bundle,
        handle=handle,
        source_hashes=qualified_adapter.source_hashes(raw_telemetry),
        fit_bins=fit_bins,
        cal_bins=cal_bins,
        evidence_catalog=evidence_catalog,
    )


__all__ = [
    "C1Observation",
    "C5Observation",
    "ObservationError",
    "admit_c1_bundle",
    "admit_c5_bundle",
    "public_c1_observation",
    "public_c5_observation",
]
