"""Structured diagnosis packet and oracle/firewall validation.

Packets contain suspicion/diagnostic-utility scores, never probabilities or
causal truth.  The ranking is sealed independently so downstream explanation
cannot mutate ordering, scores, or tie intervals.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np


PACKET_SCHEMA = "TD13-F-DIAGNOSIS-PACKET-v1"
SCORE_SEMANTICS = "suspicion/diagnostic utility; not root probability or causal truth"


class PacketValidationError(ValueError):
    """A packet leaks oracle data or violates its immutable numeric contract."""


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
        "answercontents",
        "tau",
        "injectedfault",
        "injectionidentity",
        "casepath",
        "absolutepath",
        "evaluator",
        "evaluatoronly",
        "outcome",
        "finaloutcome",
        "hindsightexplanation",
        "s0",
        "eventms",
        "firstseenms",
        "firstconflictms",
        "injecttime",
        "timemin",
        "timemax",
    }
)
_ABSOLUTE_PATH = re.compile(r"^(?:[A-Za-z]:[\\/]|/|\\\\)")


def _key(value: object) -> str:
    return "".join(character for character in str(value).lower() if character.isalnum())


def _jsonable(value: Any):
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return _jsonable(value.tolist())
    if isinstance(value, np.generic):
        return _jsonable(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise PacketValidationError(f"Packet value is not JSON serializable: {type(value).__name__}")


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            _jsonable(value),
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise PacketValidationError("Packet must be finite canonical JSON") from exc


def _firewall(value: Any, location="packet") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = _key(key)
            if normalized in _FORBIDDEN_KEYS or normalized.startswith("groundtruth"):
                raise PacketValidationError(f"Forbidden oracle field: {location}.{key}")
            _firewall(item, f"{location}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _firewall(item, f"{location}[{index}]")
    elif isinstance(value, str) and _ABSOLUTE_PATH.match(value):
        raise PacketValidationError(f"Absolute path leaked into packet at {location}")


def rank_table(
    scores: Sequence[float],
    candidate_ids: Sequence[str],
    *,
    evidence_ids: Mapping[str, Sequence[str]] | None = None,
) -> dict[str, Any]:
    """Create deterministic descending ranks and average-position tie intervals."""
    values = np.asarray(scores, dtype=np.float64)
    candidates = tuple(candidate_ids)
    if (
        values.ndim != 1
        or len(values) != len(candidates)
        or not np.isfinite(values).all()
        or len(set(candidates)) != len(candidates)
        or any(not isinstance(candidate, str) or not candidate for candidate in candidates)
    ):
        raise PacketValidationError("Finite scores and unique candidate IDs are required")
    rounded = np.round(values, 12)
    order = sorted(range(len(values)), key=lambda index: (-rounded[index], index))
    rows: list[dict[str, Any]] = []
    evidence = {} if evidence_ids is None else evidence_ids
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        while end < len(order) and rounded[order[end]] == rounded[order[cursor]]:
            end += 1
        rank_start, rank_end = cursor + 1, end
        status = "TIE" if rank_end > rank_start else "UNIQUE"
        for position in range(cursor, end):
            index = order[position]
            candidate = candidates[index]
            refs = list(evidence.get(candidate, ()))
            if any(not isinstance(reference, str) or not reference for reference in refs):
                raise PacketValidationError("Evidence references must be nonempty strings")
            rows.append(
                {
                    "candidate": candidate,
                    "candidate_index": index,
                    "score": float(values[index]),
                    "rounded_score": float(rounded[index]),
                    "rank_start": rank_start,
                    "rank_end": rank_end,
                    "tie_status": status,
                    "evidence_ids": refs,
                }
            )
        cursor = end
    table = {
        "candidate_count": len(candidates),
        "rows": rows,
        "tie_rule": "descending score; equality after round(score,12); original candidate index orders display only",
    }
    table["rank_sha256"] = hashlib.sha256(_canonical(table)).hexdigest()
    return table


def _verify_rank_table(table: Mapping[str, Any]) -> None:
    if not isinstance(table, Mapping) or not isinstance(table.get("rows"), list):
        raise PacketValidationError("Ranking table is malformed")
    plain = dict(table)
    supplied = plain.pop("rank_sha256", None)
    if supplied != hashlib.sha256(_canonical(plain)).hexdigest():
        raise PacketValidationError("Immutable ranking hash mismatch")
    rows = plain["rows"]
    count = plain.get("candidate_count")
    if count != len(rows) or count != len({row.get("candidate_index") for row in rows}):
        raise PacketValidationError("Ranking candidate count/index mismatch")
    previous = math.inf
    cursor = 0
    while cursor < len(rows):
        row = rows[cursor]
        score = row.get("rounded_score")
        if not isinstance(score, (int, float)) or not math.isfinite(float(score)) or score > previous:
            raise PacketValidationError("Ranking rows are not finite descending scores")
        end = cursor + 1
        while end < len(rows) and rows[end].get("rounded_score") == score:
            end += 1
        expected_start, expected_end = cursor + 1, end
        expected_status = "TIE" if expected_end > expected_start else "UNIQUE"
        for tied in rows[cursor:end]:
            if (
                tied.get("rank_start") != expected_start
                or tied.get("rank_end") != expected_end
                or tied.get("tie_status") != expected_status
            ):
                raise PacketValidationError("Ranking tie interval/status mismatch")
        previous = float(score)
        cursor = end


def seal_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and seal a new packet without overwriting an existing digest."""
    plain = _jsonable(packet)
    if "packet_sha256" in plain:
        raise PacketValidationError("Refusing to reseal an already sealed packet")
    _validate_unsealed(plain)
    plain["packet_sha256"] = hashlib.sha256(_canonical(plain)).hexdigest()
    validate_packet(plain)
    return plain


def _validate_unsealed(packet: Mapping[str, Any]) -> None:
    required = {
        "schema_version",
        "method_identity",
        "observation",
        "status",
        "score_semantics",
        "evidence_catalog",
        "quality",
        "uncertainty",
    }
    if required - set(packet):
        raise PacketValidationError(f"Missing packet fields: {sorted(required - set(packet))}")
    if packet["schema_version"] != PACKET_SCHEMA or packet["score_semantics"] != SCORE_SEMANTICS:
        raise PacketValidationError("Wrong packet schema or score semantics")
    if packet["status"] not in ("SUCCESS", "UNAVAILABLE", "INPUT_FAILURE", "METHOD_FAILURE"):
        raise PacketValidationError("Unknown explicit packet status")
    _firewall(packet)
    if "ranking" in packet and packet["ranking"] is not None:
        _verify_rank_table(packet["ranking"])
    alternatives = packet.get("alternatives", {})
    if not isinstance(alternatives, Mapping):
        raise PacketValidationError("Packet alternatives must be a mapping")
    for value in alternatives.values():
        if isinstance(value, Mapping) and "rows" in value:
            _verify_rank_table(value)

    catalog = packet["evidence_catalog"]
    if not isinstance(catalog, Mapping):
        raise PacketValidationError("Evidence catalog must be a mapping")
    references: set[str] = set()

    def collect(value):
        if isinstance(value, Mapping):
            for key, item in value.items():
                if key == "evidence_ids":
                    if not isinstance(item, list):
                        raise PacketValidationError("evidence_ids must be a list")
                    references.update(item)
                else:
                    collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)

    collect(packet)
    missing = references - set(catalog)
    if missing:
        raise PacketValidationError(f"Unresolved evidence IDs: {sorted(missing)}")


def validate_packet(packet: Mapping[str, Any]) -> bool:
    """Validate oracle firewall, evidence resolution, and both content seals."""
    if not isinstance(packet, Mapping):
        raise PacketValidationError("Packet must be a mapping")
    plain = _jsonable(packet)
    supplied = plain.pop("packet_sha256", None)
    if not isinstance(supplied, str) or supplied != hashlib.sha256(_canonical(plain)).hexdigest():
        raise PacketValidationError("Packet content hash mismatch")
    _validate_unsealed(plain)
    return True


__all__ = [
    "PACKET_SCHEMA",
    "PacketValidationError",
    "SCORE_SEMANTICS",
    "rank_table",
    "seal_packet",
    "validate_packet",
]
