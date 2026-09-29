"""Immutable Task F release-manifest loading and validation.

The manifest references the canonical final-split contract but never contains
materialized final IDs, labels, telemetry, graphs, features, or predictions.
Development selection is read from a separately produced frozen manifest; this
module performs no selection and opens no referenced experiment artifact.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


EXPECTED_TD_SHA256 = "34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971"
EXPECTED_DATASET_REVISION = "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
MANIFEST_KIND = "task-f-frozen-release"


class FrozenConfigError(ValueError):
    """The release manifest is incomplete, mutable in meaning, or out of scope."""


@dataclass(frozen=True)
class RankingSelection:
    operator: str
    direction: str
    damping: float

    def as_dict(self) -> dict[str, object]:
        return {
            "operator": self.operator,
            "direction": self.direction,
            "damping": self.damping,
        }


@dataclass(frozen=True)
class DetectorSelection:
    detector_id: str
    arm: str
    modalities: str
    q: float
    threshold: float


@dataclass(frozen=True)
class FrozenReleaseConfig:
    """Validated immutable view of the Task F frozen release manifest."""

    schema_version: str
    td_sha256: str
    dataset_revision: str
    local: Mapping[str, object]
    primary_ppr: RankingSelection
    secondary_diffusion: RankingSelection
    selected_lambda: float
    detectors: tuple[DetectorSelection, ...]
    r_chains: int
    r_proposals_per_edge: int
    comparators: tuple[str, ...]
    manifest: Mapping[str, object]
    canonical_sha256: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "FrozenReleaseConfig":
        if not isinstance(value, Mapping):
            raise FrozenConfigError("Frozen release manifest must be an object")
        raw = _plain_copy(value)
        _reject_materialized_final_fields(raw)
        required = {
            "schema_version",
            "manifest_kind",
            "td",
            "dataset",
            "split",
            "exposure_ledger",
            "selections",
            "r_control",
            "comparators",
            "provenance",
            "limitations",
        }
        missing = required - set(raw)
        if missing:
            raise FrozenConfigError(f"Missing frozen manifest fields: {sorted(missing)}")
        if raw["manifest_kind"] != MANIFEST_KIND:
            raise FrozenConfigError("Wrong Task F manifest kind")
        schema_version = _nonempty_string(raw["schema_version"], "schema_version")

        td = _mapping(raw["td"], "td")
        td_sha = _sha(td.get("sha256"), "td.sha256")
        if td_sha != EXPECTED_TD_SHA256:
            raise FrozenConfigError("Manifest does not identify frozen executed TD-v1.3")
        _nonempty_string(td.get("path"), "td.path")

        dataset = _mapping(raw["dataset"], "dataset")
        revision = _nonempty_string(dataset.get("revision"), "dataset.revision")
        if revision != EXPECTED_DATASET_REVISION:
            raise FrozenConfigError("Dataset revision differs from the frozen Task E evidence")
        development_scope = _nonempty_string(
            dataset.get("development_scope"), "dataset.development_scope"
        )
        if development_scope.lower() != "development30":
            raise FrozenConfigError("Task F manifest must identify the registered development30 scope")

        split = _mapping(raw["split"], "split")
        for field in ("rule_id", "version", "provenance", "final_split_contract_ref"):
            _nonempty_string(split.get(field), f"split.{field}")
        exposure = _mapping(raw["exposure_ledger"], "exposure_ledger")
        for field in ("path", "sha256", "status"):
            if field == "sha256":
                _sha(exposure.get(field), f"exposure_ledger.{field}")
            else:
                _nonempty_string(exposure.get(field), f"exposure_ledger.{field}")

        selections = _mapping(raw["selections"], "selections")
        c1 = _mapping(selections.get("c1"), "selections.c1")
        c5 = _mapping(selections.get("c5"), "selections.c5")
        _source_reference(c1, "selections.c1")
        local = dict(_mapping(c1.get("local"), "selections.c1.local"))
        expected_local = {"floor": 0.01, "pool": "q90", "fusion": "availablemean"}
        if any(local.get(key) != expected for key, expected in expected_local.items()):
            raise FrozenConfigError("C1 local selection disagrees with sealed development selection")
        allowed_local = {"floor", "pool", "fusion", "temporal", "cap", "include_logs"}
        if set(local) - allowed_local:
            raise FrozenConfigError("Unknown frozen C1 local field")
        if local.get("temporal", "q90") != "q90" or local.get("cap") not in (None,):
            raise FrozenConfigError("Frozen primary C1 cannot adopt a sensitivity setting")
        if local.get("include_logs", False) is not False:
            raise FrozenConfigError("Primary C1 excludes log-count evidence")
        local.setdefault("temporal", "q90")
        local.setdefault("cap", None)
        local.setdefault("include_logs", False)

        primary = _ranking(
            _mapping(c1.get("primary_ppr"), "selections.c1.primary_ppr"),
            operator="ppr",
            direction="undirected",
            damping=0.5,
        )
        secondary_raw = _mapping(
            c1.get("secondary_diffusion"), "selections.c1.secondary_diffusion"
        )
        secondary_damping = secondary_raw.get("alpha", secondary_raw.get("damping"))
        secondary = _ranking(
            {**secondary_raw, "damping": secondary_damping},
            operator="diffusion",
            direction="undirected",
            damping=0.85,
        )

        _source_reference(c5, "selections.c5", require_generic=False)
        selected_lambda = float(c5.get("selected_lambda", math.nan))
        if selected_lambda != 10.0:
            raise FrozenConfigError("C5 lambda disagrees with sealed development selection")
        detector_rows = c5.get("detectors")
        if not isinstance(detector_rows, list) or len(detector_rows) != 8:
            raise FrozenConfigError("Exactly eight frozen C5 detector selections are required")
        detectors = tuple(_detector(row) for row in detector_rows)
        expected_detectors = {
            f"{arm}-{modalities}"
            for arm in ("G", "L", "ALL", "TV")
            for modalities in ("MT", "MTL")
        }
        if {row.detector_id for row in detectors} != expected_detectors:
            raise FrozenConfigError("C5 detector roster must be exact G/L/ALL/TV x MT/MTL")

        controls = _mapping(raw["r_control"], "r_control")
        chains = controls.get("chains")
        proposals = controls.get("proposals_per_edge")
        if chains != 256 or proposals != 200:
            raise FrozenConfigError("R control must retain 256 chains and 200*max(1,E) proposals")
        if "seed_contract" in controls:
            _nonempty_string(controls["seed_contract"], "r_control.seed_contract")

        comparator_rows = raw["comparators"]
        if not isinstance(comparator_rows, list):
            raise FrozenConfigError("comparators must be a list")
        comparator_ids = tuple(
            _nonempty_string(_mapping(row, "comparator").get("id"), "comparator.id")
            for row in comparator_rows
        )
        required_comparators = {
            "Local-MAX-MT",
            "BARO-RANK-adapted-TD12",
            "RCD-RCAEval-adapted-TD12",
        }
        if set(comparator_ids) != required_comparators or len(comparator_ids) != 3:
            raise FrozenConfigError("Frozen release must retain all three exact contextual comparators")

        canonical = _canonical_json(raw)
        return cls(
            schema_version=schema_version,
            td_sha256=td_sha,
            dataset_revision=revision,
            local=MappingProxyType(local),
            primary_ppr=primary,
            secondary_diffusion=secondary,
            selected_lambda=selected_lambda,
            detectors=detectors,
            r_chains=chains,
            r_proposals_per_edge=proposals,
            comparators=comparator_ids,
            manifest=_deep_freeze(raw),
            canonical_sha256=hashlib.sha256(canonical).hexdigest(),
        )

    def detector(self, detector_id: str) -> DetectorSelection:
        matches = [row for row in self.detectors if row.detector_id == detector_id]
        if len(matches) != 1:
            raise FrozenConfigError(f"Unknown detector selection: {detector_id}")
        return matches[0]


def load_frozen_config(path: str | Path) -> FrozenReleaseConfig:
    """Load one JSON manifest without following any referenced artifact path."""
    manifest_path = Path(path)
    raw = manifest_path.read_text(encoding="utf-8-sig")
    try:
        value = json.loads(
            raw,
            object_pairs_hook=_unique_object,
            parse_constant=lambda value: (_raise_nonfinite(value)),
        )
    except (json.JSONDecodeError, FrozenConfigError) as exc:
        raise FrozenConfigError(f"Invalid frozen release JSON: {exc}") from exc
    return FrozenReleaseConfig.from_mapping(value)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise FrozenConfigError(f"Duplicate manifest key: {key}")
        result[key] = value
    return result


def _raise_nonfinite(value):
    raise FrozenConfigError(f"Nonfinite JSON number is forbidden: {value}")


def _plain_copy(value):
    try:
        return json.loads(_canonical_json(value))
    except (TypeError, ValueError) as exc:
        raise FrozenConfigError("Manifest must contain finite JSON values only") from exc


def _canonical_json(value) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _deep_freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({key: _deep_freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _mapping(value, label) -> dict:
    if not isinstance(value, Mapping):
        raise FrozenConfigError(f"{label} must be an object")
    return dict(value)


def _nonempty_string(value, label) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FrozenConfigError(f"{label} must be a nonempty string")
    return value


def _sha(value, label) -> str:
    value = _nonempty_string(value, label).lower()
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise FrozenConfigError(f"{label} must be SHA256 hex")
    return value


def _source_reference(value: Mapping[str, object], label: str, *, require_generic=True):
    if require_generic:
        path = value.get("source_path")
        digest = value.get("source_sha256")
        _nonempty_string(path, f"{label}.source_path")
        _sha(digest, f"{label}.source_sha256")
        return
    pairs = (
        ("lambda_source", "lambda_source_sha256"),
        ("selection_source", "selection_source_sha256"),
    )
    for path_key, hash_key in pairs:
        _nonempty_string(value.get(path_key), f"{label}.{path_key}")
        _sha(value.get(hash_key), f"{label}.{hash_key}")


def _ranking(value, *, operator, direction, damping) -> RankingSelection:
    if value.get("operator") != operator or value.get("direction") != direction:
        raise FrozenConfigError(f"Frozen {operator} operator/direction mismatch")
    actual = float(value.get("damping", math.nan))
    if actual != damping:
        raise FrozenConfigError(f"Frozen {operator} damping mismatch")
    return RankingSelection(operator=operator, direction=direction, damping=actual)


def _detector(value) -> DetectorSelection:
    row = _mapping(value, "detector")
    status = row.get("status", "VALID")
    if status != "VALID":
        raise FrozenConfigError("Every frozen detector entry must be VALID")
    detector_id = row.get("id", row.get("detector"))
    detector_id = _nonempty_string(detector_id, "detector.id")
    try:
        arm, modalities = detector_id.rsplit("-", 1)
    except ValueError as exc:
        raise FrozenConfigError("Detector ID must be ARM-MODALITIES") from exc
    if row.get("arm", arm) != arm or row.get("modalities", modalities) != modalities:
        raise FrozenConfigError("Detector ID disagrees with arm/modalities")
    q = float(row.get("q", row.get("selected_q", math.nan)))
    threshold = float(row.get("threshold", row.get("full_threshold", math.nan)))
    if q != 0.95 or not math.isfinite(threshold) or threshold < 0:
        raise FrozenConfigError("Frozen detector q/threshold is invalid")
    return DetectorSelection(detector_id, arm, modalities, q, threshold)


_FORBIDDEN_FINAL_KEYS = {
    "final_ids",
    "final_case_ids",
    "final_cases",
    "final_labels",
    "final_inputs",
    "final_telemetry",
    "final_graphs",
    "final_features",
    "final_predictions",
    "final60_ids",
}


def _reject_materialized_final_fields(value, path="manifest"):
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in _FORBIDDEN_FINAL_KEYS or normalized.startswith("materialized_final"):
                raise FrozenConfigError(f"Materialized final-split field is forbidden: {path}.{key}")
            _reject_materialized_final_fields(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_materialized_final_fields(item, f"{path}[{index}]")
