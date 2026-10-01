"""G32 issued telemetry-to-numeric bridge; actual predictions remain closed.

The trusted controller projects only authorized timing metadata, reuses the
verified G30 telemetry bytes, and invokes unchanged frozen conversion functions.
Literal identities, paths, absolute clocks and timing remain private. Workers
receive numeric arrays and indices through the separate fixed campaign seam.
This is an ordinary-caller boundary on the registered trusted host, not a sandbox.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import time
import weakref
from collections import Counter
from collections.abc import Mapping
from pathlib import Path

import numpy as np

from rca.observation import C1Observation, C5Observation, _quality_projection
from scripts.task_g import campaign_source as previous


WORKSPACE = Path(__file__).resolve().parents[2]
PROJECT = Path("D:/Project/flash-ticket-platform")
RUN_ID = "g32-final-bridge-readiness"
DOMAIN = "FlashTicketRca/TD13/G32/BRIDGE-READINESS/v1"
PHASE = "FINAL_BRIDGE_READINESS_ONLY"
SYNTHETIC_SCOPE = "SYNTHETIC_BRIDGE_READINESS"
DEVELOPMENT_SCOPE = "DEVELOPMENT_TIMING_ONLY"
ACTUAL_SCOPE = "ACTUAL_TELEMETRY_CONVERSION_ONLY"
METADATA_REL = "datasets/rcaeval/metadata/cases.parquet"
METADATA_SHA = "c49a288920dbba2e8e724679a14636d5c7eb2b45426bba14007ef79a6c0ab1bb"
ROSTER_PROJECTION = ("case", "dataset", "repetition", "has_logs", "has_traces")
TAU_PROJECTION = ("case", "dataset", "repetition", "inject_time")
ENTRY_REL = "results/task-g/g30-entry-validation/entry-validation.json"
ENTRY_SHA = "570da401927a71b618a40d0a043354d326ccfd4920d47f6fd72dcc0eba928f34"
ROSTER_SHA = "f74ba6f11f55729ead8980cfc2df34be2cdb8fd570abe7656b62e31858d24bae"
DESCRIPTOR_SHA = "2b51110896bf23f6f2264e85458b814c1cd7871c50e047d814aeda3943b32d94"
RAW_REL = "datasets/rcaeval/task-g-final"


class FinalSourceError(ValueError):
    """Sanitized registration/conversion error; no source text or locators."""


class FinalSource:
    __slots__ = ("__weakref__",)

    @property
    def summary(self):
        return source_summary(self)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _digest(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def candidate_key(literal):
    """Controller identity equality across windows, never a numeric feature."""
    if type(literal) is not str or not literal or literal.startswith(("/", "\\")):
        raise FinalSourceError("LITERAL_CANDIDATE_IDENTITY_REQUIRED")
    return "s" + hashlib.sha256(("TD13-G32|literal-service|" + literal).encode()).hexdigest()[:24]


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _context():
    from scripts.task_g.final_provenance import registered_context
    return registered_context()


def _numeric_fingerprint(c1, c5, rcd):
    arrays = {}
    if c1 is not None:
        arrays.update(ref=c1.ref, query=c1.query, adj=c1.adjacency,
                      types=np.asarray(c1.channel_types))
    if c5 is not None:
        arrays.update(warmup=c5.warmup_values, stream=c5.stream_values,
                      c5_adj=c5.adjacency, fit=c5.fit_service_mask,
                      endpoints=c5.relative_endpoints)
    if rcd is not None:
        arrays.update(rcd=rcd["values"], owners=np.asarray(rcd["owners"], dtype=np.int64))
    return _digest(previous._array_manifest(arrays))


def _project_audit(audit, names, origin=None):
    """Keep scientific counts/masks, replace literal entity/column identities.

    Exact source audit is retained privately. Projection never invents an owner
    for an unknown metric or log entity. Unknown tokens become digest identifiers.
    The frozen projection removes absolute clocks and chronological key payloads.
    """
    name_map = {name: candidate_key(name) for name in names}
    from scripts.task_e.loader import METRIC_SUFFIXES
    metric_map = {f"{name}_{suffix}": f"{candidate_key(name)}/channel{c}"
                  for i, name in enumerate(names)
                  for c, suffix in enumerate(METRIC_SUFFIXES)}
    remap = {**name_map, **metric_map}

    def redact(value):
        if isinstance(value, dict):
            return {remap.get(str(key), str(key)): redact(item)
                    for key, item in value.items() if key != "qualification"}
        if isinstance(value, (list, tuple)):
            return [redact(item) for item in value]
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, str):
            if value in remap:
                return remap[value]
            # Metric/identity keys have no worker meaning. Preserve equality,
            # unmatched coverage and traceability without interpreting tokens.
            if value.startswith(("re2tt_", "ts-")):
                return "opaque-" + hashlib.sha256(value.encode()).hexdigest()[:16]
            return value
        return copy.deepcopy(value)

    projected = redact(_quality_projection(audit))
    # Dynamic metric keys in reports are remapped even when unmatched.
    for report_name in ("metric", "metric_ref", "metric_query"):
        report = projected.get(report_name)
        if not isinstance(report, dict):
            continue
        for key in ("mapping", "conflicting_second_counts", "identical_duplicate_seconds", "finite_bins"):
            if isinstance(report.get(key), dict):
                report[key] = {column if column in metric_map.values() else remap.get(column, "unknown-" + hashlib.sha256(column.encode()).hexdigest()[:16]): val
                               for column, val in report[key].items()}
        if isinstance(report.get("unmatched_columns"), list):
            report["unmatched_column_sha256"] = [hashlib.sha256(str(column).encode()).hexdigest()
                                                  for column in report.pop("unmatched_columns")]
    projected["literal_names_redacted"] = True
    replay = audit.get("trace", {})
    if origin is not None and isinstance(replay, dict):
        def record(item):
            result = {}
            for key in ("kind", "bin", "all_services", "fingerprints", "differing_fields", "support_count"):
                if key in item:
                    result[key] = copy.deepcopy(item[key])
            for key in ("event_ms", "first_seen_ms", "first_conflict_ms"):
                if item.get(key) is not None:
                    result["relative_" + key] = int(item[key]) - origin * 1000
            if "key" in item:
                result["composite_key_sha256"] = _digest(item["key"])
            if "owners" in item:
                result["owner_indices"] = [names.index(name) for name in item["owners"] if name in names]
                result["unmatched_owner_sha256"] = [hashlib.sha256(name.encode()).hexdigest()
                                                     for name in item["owners"] if name not in names]
            return result
        projected["chronological_identity_audit"] = {
            "events": [record(item) for item in replay.get("events", [])],
            "permanent_quarantines": [record(item) for item in replay.get("quarantined_keys", [])],
            "post_freeze_discredited_support": [record(item) for item in replay.get("post_freeze_discredited_support", [])],
            "times_are_case_relative_milliseconds": True,
            "original_absolute_identity_audit_kept_controller_only": True,
        }
    return projected


def _clock_report(raw, tau):
    from scripts.task_e.replay import validate_event_clock
    metrics = raw.get("metrics")
    source_rows = {modality: None if raw.get(modality) is None else len(raw[modality])
                   for modality in ("metrics", "traces", "logs")}
    origin, end = None, None
    clocks = {"metrics": "MISSING_OR_CORRUPT"}
    modality_reports = {}
    if metrics is not None and not metrics.empty:
        validate_event_clock(metrics.time, "metrics.time")
        origin, end = int(metrics.time.min()), int(metrics.time.max()) + 1
        clocks["metrics"] = "INTEGER_UNIX_SECONDS"
    for modality, field, multiplier in (("traces", "startTimeMillis", 1000), ("logs", "timestamp", 1)):
        frame = raw.get(modality)
        if frame is None:
            clocks[modality] = "MISSING_OR_CORRUPT"
            continue
        try:
            validate_event_clock(frame[field], field)
            clocks[modality] = "INTEGER_MILLISECONDS" if multiplier == 1000 else "INTEGER_UNIX_SECONDS"
        except Exception:
            clocks[modality] = "UNQUALIFIABLE_EVENT_CLOCK"
            if modality == "logs":
                raw[modality] = None
    metric_seconds = set() if origin is None else set(metrics.time.astype(np.int64))
    for modality, field, multiplier in (("metrics", "time", 1), ("traces", "startTimeMillis", 1000),
                                        ("logs", "timestamp", 1)):
        frame = raw.get(modality)
        detail = {"declared_unit": "MILLISECONDS" if multiplier == 1000 else "UNIX_SECONDS",
                  "source_rows_before_optional_clock_unavailability": source_rows[modality],
                  "unit_source": "FROZEN_TD13_AND_TASK_E_ADAPTER",
                  "clock_status": clocks.get(modality, "MISSING_OR_CORRUPT"),
                  "half_open_reference_seconds": [-300, 0], "half_open_query_seconds": [0, 300],
                  "observation_range_is_not_complete_window_coverage_proof": True}
        if frame is None or clocks.get(modality) == "UNQUALIFIABLE_EVENT_CLOCK":
            detail.update(status="OPEN_UNAVAILABLE_OR_UNPLACEABLE_CLOCK", observed_rows=None,
                          reference_rows=None, query_rows=None, rows_inside_metric_archive=None,
                          rows_at_observed_metric_seconds=None)
        elif frame.empty:
            detail.update(status="OPEN_EMPTY_TELEMETRY", observed_rows=0, reference_rows=0, query_rows=0,
                          rows_inside_metric_archive=0 if origin is not None else None,
                          rows_at_observed_metric_seconds=0 if origin is not None else None)
        else:
            values = frame[field].to_numpy(dtype=np.int64)
            reference = (values >= (tau - 300) * multiplier) & (values < tau * multiplier)
            query = (values >= tau * multiplier) & (values < (tau + 300) * multiplier)
            seconds = values // multiplier
            inside = None if origin is None else (values >= origin * multiplier) & (values < end * multiplier)
            shared = None if origin is None else np.isin(seconds, list(metric_seconds))
            detail.update(observed_rows=len(frame), reference_rows=int(reference.sum()), query_rows=int(query.sum()),
                          reference_distinct_seconds=int(len(np.unique(seconds[reference]))),
                          query_distinct_seconds=int(len(np.unique(seconds[query]))),
                          observed_range_relative_to_marker_units=[int(values.min()) - tau * multiplier,
                                                                   int(values.max()) - tau * multiplier],
                          rows_inside_metric_archive=None if inside is None else int(inside.sum()),
                          rows_outside_metric_archive=None if inside is None else int((~inside).sum()),
                          rows_at_observed_metric_seconds=None if shared is None else int(shared.sum()))
            detail["status"] = ("OPEN_CLOCK_ALIGNMENT_OR_NO_SHARED_COVERAGE" if inside is None or not inside.any()
                                else "OPEN_EMPTY_REFERENCE_OR_QUERY_TELEMETRY" if not reference.any() or not query.any()
                                else "DECLARED_UNIT_ALIGNED_NONEMPTY_WINDOWS")
        modality_reports[modality] = detail
    full_window = None if origin is None else tau - 300 >= origin and tau + 300 <= end
    return {"clocks": clocks, "modalities": modality_reports,
            "fresh_alignment_check": "DECLARED_UNIT_CONVERSION_AND_EXACT_OBSERVED_SECOND_INTERSECTION",
            "entry_admission_anchor_sha256": ENTRY_SHA,
            "entry_admission_windows_are_historical_label_free_probes": True,
            "verified_entry_archive_alignment": copy.deepcopy(raw.get("audit", {}).get("verified_entry_archive_alignment")),
            "actual_marker_window_checked_independently": True,
            "metric_observed_seconds": None if origin is None else end - origin,
            "known_window_coverage_status": "OPEN_METRIC_COVERAGE_UNAVAILABLE" if full_window is None else
                                            "FULL_ARCHIVE_WINDOW_AVAILABLE" if full_window else
                                            "OPEN_REFERENCE_OR_QUERY_ARCHIVE_COVERAGE",
            "known_window_reference_fully_inside_archive": None if origin is None else tau - 300 >= origin,
            "known_window_query_fully_inside_archive": None if origin is None else tau + 300 <= end,
            "c5_fit_prefix_precedes_timing_marker": None if origin is None else origin + 120 <= tau,
            "c5_warmup_precedes_timing_marker": None if origin is None else origin + 180 <= tau,
            "timing_marker_observed_in_metric_range": None if origin is None else origin <= tau < end,
            "source_of_window": "VERIFIED_INJECT_TIME_PROJECTION_NOT_ORIGIN_OFFSET",
            "known_window_reference_seconds": 300, "known_window_query_seconds": 300,
            "trace_window_half_open": True, "c5_receives_timing_marker": False}, origin


def _sanitize_query_log(message, identifiers=(), clock_values=()):
    """Retain untrusted telemetry meaning under the declared packet redactions.

    This handles known literal identities, locators, clock formats, credential
    patterns and explicitly assigned oracle fields. It never consults metadata
    ground-truth columns, infers an owner or interprets arbitrary prose as truth.
    The retained text remains untrusted input for the later packet renderer.
    """
    if message is None:
        return {"text": None, "status": "MISSING_MESSAGE", "source_message_utf8_bytes": None,
                "sanitized_message_utf8_bytes": None, "untrusted_telemetry_text": True,
                "redaction_counts": {}}
    if not isinstance(message, str):
        return {"text": None, "status": "UNSUPPORTED_MESSAGE_TYPE", "source_message_utf8_bytes": None,
                "sanitized_message_utf8_bytes": None, "untrusted_telemetry_text": True,
                "redaction_counts": {}}
    text, counts = message, {}

    def replace(pattern, replacement, category, flags=0):
        nonlocal text
        text, count = re.subn(pattern, replacement, text, flags=flags)
        if count:
            counts[category] = counts.get(category, 0) + count

    # Credential schemes contain a whitespace-separated value, unlike ordinary
    # key=value tokens. Remove them before generic assigned-field processing.
    replace(r"\b(?:Bearer|Basic)\s+[A-Za-z0-9+/_.=:-]+", "[CREDENTIAL_REDACTED]", "credentials", re.IGNORECASE)
    assignment = re.compile(r'''(?P<key>"[^"\n]{1,64}"|'[^'\n]{1,64}'|[A-Za-z_][A-Za-z0-9_.-]{0,63})\s*[:=]\s*''')
    closed = {"root", "rootcause", "rootcauseservice", "rootservice", "rootindex", "rootpresence",
              "fault", "faulttype", "faultlabel", "injectedfault", "faulttime", "label", "labels",
              "answer", "answers", "answerfile", "outcome", "outcomes", "finaloutcome", "tau",
              "injecttime", "injection", "injectiontime", "injectiontimestamp", "groundtruth",
              "caseid", "casepath", "absolutepath", "evaluator", "prediction", "predictions",
              "finalprediction", "finalpredictions", "normaltimesteps"}
    secrets = {"password", "passwd", "secret", "token", "accesstoken", "refreshtoken", "apikey",
               "authorization", "credential", "credentials", "accesskey", "privatekey", "clientsecret", "auth"}

    def value_end(start):
        if start >= len(text):
            return start
        opener = text[start]
        if opener in "\"'":
            escaped = False
            for position in range(start + 1, len(text)):
                if escaped:
                    escaped = False
                elif text[position] == "\\":
                    escaped = True
                elif text[position] == opener:
                    return position + 1
            return len(text)
        if opener in "[{":
            stack, quote, escaped = [opener], None, False
            for position in range(start + 1, len(text)):
                character = text[position]
                if quote is not None:
                    if escaped:
                        escaped = False
                    elif character == "\\":
                        escaped = True
                    elif character == quote:
                        quote = None
                elif character in "\"'":
                    quote = character
                elif character in "[{":
                    stack.append(character)
                elif character in "]}":
                    if not stack or (stack[-1], character) not in (("[", "]"), ("{", "}")):
                        return len(text)
                    stack.pop()
                    if not stack:
                        return position + 1
            return len(text)
        found = re.search(r"[\s,;\]}]", text[start:])
        return len(text) if found is None else start + found.start()

    spans = []
    consumed = 0
    for match in assignment.finditer(text):
        if match.start() < consumed:
            continue
        raw_key = match.group("key")
        try:
            key = json.loads(raw_key) if raw_key.startswith('"') else raw_key.strip("'")
        except (ValueError, TypeError):
            key = raw_key.strip("\"'")
        key = key.rsplit(".", 1)[-1]
        normalized = re.sub(r"[^a-z0-9]", "", key.lower())
        category = ("closed_fields" if normalized in closed or normalized.startswith("groundtruth")
                    else "secret_fields" if normalized in secrets else None)
        if category is not None:
            consumed = value_end(match.end())
            spans.append((match.start(), consumed, category))
    for start, end, category in reversed(spans):
        text = text[:start] + ("[CLOSED_FIELD_REDACTED]" if category == "closed_fields" else "[SECRET_FIELD_REDACTED]") + text[end:]
        counts[category] = counts.get(category, 0) + 1
    literals = sorted({value for value in identifiers if isinstance(value, str) and value}, key=lambda value: (-len(value), value))
    for value in literals:
        replace(r"(?<![A-Za-z0-9])" + re.escape(value) + r"(?![A-Za-z0-9])", "[IDENTIFIER_REDACTED]", "known_identifiers")
    for value in sorted({str(value) for value in clock_values if isinstance(value, (int, np.integer))}, key=len, reverse=True):
        replace(r"(?<![A-Za-z0-9])" + re.escape(value) + r"(?![A-Za-z0-9])", "[CLOCK_REDACTED]", "known_clocks")
    replace(r"\b(?:re[123](?:tt|ob|ss)[_-][A-Za-z0-9_.-]+|ts-[A-Za-z0-9_.-]+)\b", "[CASE_IDENTIFIER_REDACTED]", "case_identifiers", re.IGNORECASE)
    replace(r"[A-Za-z][A-Za-z0-9+.-]*://[^\s\"'<>]+", "[LOCATOR_REDACTED]", "locators")
    replace(r"(?:[A-Za-z]:[\\/]|\\\\)[^\s\"'<>]+", "[PATH_REDACTED]", "absolute_paths")
    replace(r"(?<![A-Za-z0-9])/(?:[^\s\"'<>]+)", "[PATH_REDACTED]", "absolute_paths")
    replace(r"(?<![A-Za-z0-9])\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?)?", "[CLOCK_REDACTED]", "formatted_clocks")
    replace(r"(?<![A-Za-z0-9])\d{10,19}(?:\.\d+)?(?![A-Za-z0-9])", "[CLOCK_REDACTED]", "epoch_clocks")
    return {"text": text, "status": "SANITIZED_UNTRUSTED_TEXT_RETAINED",
            "source_message_utf8_bytes": len(message.encode("utf-8")),
            "sanitized_message_utf8_bytes": len(text.encode("utf-8")),
            "untrusted_telemetry_text": True, "redaction_counts": counts}


def _controller_evidence(raw, names, hashes, ref_lo, ref_hi, query_lo, query_hi):
    """Fixed C3 support; controller-only, detached from the numeric worker.

    Operation names are projected to equality-preserving digest identities.
    Query log text uses the declared literal/pattern sanitizer. Sampling follows
    the exact frozen file-hash/original-row-ordinal rule, independently of text,
    severity, known answers or root presence. Workers never receive this catalog.
    """
    from scripts.task_e.loader import _trace_slice, _deduplicate_trace
    services = tuple(names)
    ref, _ = _deduplicate_trace(_trace_slice(raw.get("traces"), ref_lo, ref_hi))
    query, _ = _deduplicate_trace(_trace_slice(raw.get("traces"), query_lo, query_hi))
    reference_seconds, query_seconds = ref_hi - ref_lo, query_hi - query_lo
    support = []
    for service in services:
        reference = ref.loc[ref.serviceName.eq(service)]
        observed = query.loc[query.serviceName.eq(service)]
        operations = sorted(set(value for frame in (reference, observed) for value in frame.operationName
                                if isinstance(value, str) and value))
        rows = []
        for operation in operations:
            key = "o" + hashlib.sha256(("TD13-G32|literal-operation|" + operation).encode()).hexdigest()[:24]
            before, after = int(reference.operationName.eq(operation).sum()), int(observed.operationName.eq(operation).sum())
            before_rate, after_rate = before / reference_seconds, after / query_seconds
            rows.append({"operation_key": key, "reference_count": before, "query_count": after,
                         "reference_rate_per_second": before_rate, "query_rate_per_second": after_rate,
                         "absolute_rate_change": abs(after_rate - before_rate),
                         "evidence_id": "operation-" + _digest([hashes, candidate_key(service), key,
                                                               before, after, reference_seconds, query_seconds])})
        top = sorted(rows, key=lambda item: (-item["absolute_rate_change"], item["operation_key"]))[:3]
        support.append({"candidate_id": candidate_key(service), "reference_span_count": len(reference),
                        "query_span_count": len(observed),
                        "reference_missing_operation_count": int((reference.operationName.isna() | reference.operationName.eq("")).sum()),
                        "query_missing_operation_count": int((observed.operationName.isna() | observed.operationName.eq("")).sum()),
                        "operations": rows, "top3_absolute_rate_changes": [item["evidence_id"] for item in top]})
    logs = raw.get("logs")
    log_support = {"association": "EXACT_CONTAINER_SERVICE_AND_TIME_ONLY",
                   "count_semantics": "ROWS_NOT_MESSAGE_DEDUPLICATION",
                   "sampling": "SHA256(source_file_sha|original_row_ordinal)_ASCENDING_MAX3_PER_SERVICE",
                   "semantic_excerpt_status": "SANITIZED_UNTRUSTED_QUERY_LOGS",
                   "redaction": "KNOWN_IDENTIFIERS_LOCATORS_CLOCKS_CREDENTIALS_ASSIGNED_CLOSED_FIELDS",
                   "sanitizer_interprets_unknown_prose_as_truth": False, "services": []}
    if logs is None:
        log_support.update(status="MISSING_OR_UNAVAILABLE", query_rows=None, unknown_entity_query_rows=None)
        log_support["semantic_excerpt_status"] = "UNAVAILABLE_LOG_FILE_OR_CLOCK"
    else:
        selected = (logs.timestamp >= query_lo) & (logs.timestamp < query_hi)
        log_sha = hashes.get("logs") or hashes.get("artificial_archive") or _digest(hashes)
        log_support.update(status="AVAILABLE_EMPTY" if not selected.any() else "AVAILABLE",
                           query_rows=int(selected.sum()),
                           unknown_entity_query_rows=int((selected & ~logs.container_name.isin(services)).sum()),
                           source_file_sha256=log_sha)
        identifiers = set(services) | set(raw.get("_controller_redaction_identifiers", ()))
        identifiers.update(value for value in raw["traces"].serviceName if isinstance(value, str) and value)
        identifiers.update(value for value in logs.container_name if isinstance(value, str) and value)
        for service in services:
            ordinals = np.flatnonzero((selected & logs.container_name.eq(service)).to_numpy()).tolist()
            chosen = sorted(ordinals, key=lambda ordinal: hashlib.sha256(f"{log_sha}|{ordinal}".encode()).hexdigest())[:3]
            log_support["services"].append({"candidate_id": candidate_key(service), "query_row_count": len(ordinals),
                "excerpts": [{"evidence_id": "log-" + hashlib.sha256(f"{log_sha}|{ordinal}".encode()).hexdigest(),
                              "original_row_ordinal": ordinal,
                              "query_relative_second": int(logs.iloc[ordinal].timestamp) - query_lo,
                              **_sanitize_query_log(logs.iloc[ordinal].message, identifiers,
                                                    (ref_lo, ref_hi, query_lo, query_hi))} for ordinal in chosen]})
    return {"c3-support": {"schema": "TD13-G32-CONTROLLER-C3-SUPPORT-v1",
                           "status": "OPERATION_COUNTS_AND_SANITIZED_LOG_SUPPORT",
                           "numeric_prediction_feature": False, "literal_identity_recoverable_from_verified_controller_source": True,
                           "reference_seconds": reference_seconds, "query_seconds": query_seconds,
                           "operation_count_semantics": "EXACT_LITERAL_SERVICE_OPERATION_DISTINCT_TRACE_SPAN",
                           "operations": support, "query_logs": log_support}}


def _evidence_copy(observation):
    if observation is None:
        return None
    fields = {key: value for key, value in vars(observation).items()}
    # Constructors recursively detach immutable controller catalogs and arrays.
    return type(observation)(**fields)


def _plain_catalog(value):
    if isinstance(value, Mapping):
        return {key: _plain_catalog(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain_catalog(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return copy.deepcopy(value)


def _catalog_status(catalog):
    support = catalog.get("c3-support", {})
    if support.get("status") != "OPERATION_COUNTS_AND_SANITIZED_LOG_SUPPORT":
        return support.get("status", "UNAVAILABLE_SUPPORT")
    logs = support.get("query_logs", {})
    if logs.get("status") == "MISSING_OR_UNAVAILABLE":
        return "OPERATION_COUNTS_ONLY_LOGS_UNAVAILABLE"
    excerpts = [item for service in logs.get("services", []) for item in service.get("excerpts", [])]
    if any(item.get("status") != "SANITIZED_UNTRUSTED_TEXT_RETAINED" for item in excerpts):
        return "OPERATION_COUNTS_PARTIAL_QUERY_LOG_MESSAGE_COVERAGE"
    return "OPERATION_COUNTS_AND_SANITIZED_LOG_SUPPORT"


def _safe_controller_evidence(raw, names, hashes, ref_lo, ref_hi, query_lo, query_hi):
    start = time.perf_counter()
    try:
        catalog = _controller_evidence(raw, names, hashes, ref_lo, ref_hi, query_lo, query_hi)
    except Exception as exc:
        catalog = {"c3-support": {"status": "OPEN_SUPPORT_CONVERSION_FAILURE_RETAINED",
                                  "error_type": type(exc).__name__, "numeric_prediction_feature": False}}
    return catalog, time.perf_counter() - start


def _numeric_inventory(c1, c5, rcd):
    profiles = {}
    for profile, arrays in (
        ("c1", None if c1 is None else {"ref": c1.ref, "query": c1.query, "adjacency": c1.adjacency,
                                       "channel_types": np.asarray(c1.channel_types)}),
        ("c5", None if c5 is None else {"warmup": c5.warmup_values, "stream": c5.stream_values,
                                       "adjacency": c5.adjacency, "fit_mask": c5.fit_service_mask,
                                       "relative_endpoints": c5.relative_endpoints}),
        ("rcd", None if rcd is None else {"values": rcd["values"], "owners": np.asarray(rcd["owners"], dtype=np.int64)}),
    ):
        profiles[profile] = {"status": "UNAVAILABLE", "arrays": None, "binary_bytes": None} if arrays is None else {
            "status": "NUMERIC_INPUT_ONLY", "arrays": {name: {"shape": list(value.shape), "dtype": value.dtype.str,
                                                             "binary_bytes": int(value.nbytes)} for name, value in arrays.items()},
            "binary_bytes": sum(int(value.nbytes) for value in arrays.values()),
            # A float64/int64 scalar representation is bounded by32 characters;
            #33/scalar includes separator, plus3/element conservatively covers
            # nested lists. This bounds these INPUT arrays, not worker output.
            "json_numeric_arrays_upper_bound_bytes": sum(int(value.size) * 36 + 256 for value in arrays.values())}
    upper = sum(value.get("json_numeric_arrays_upper_bound_bytes", 0) for value in profiles.values())
    return {"profiles": profiles, "present_input_binary_bytes": sum(value["binary_bytes"] or 0 for value in profiles.values()),
            "json_numeric_input_arrays_upper_bound_bytes": upper,
            "worker_output_comparison_bound_bytes": 128 * 1024 * 1024,
            "input_arrays_bound_fits_worker_output_comparison": upper <= 128 * 1024 * 1024,
            "comparison_covers_complete_diagnostics": False,
            "complete_actual_diagnostic_artifact_size_status": "OPEN_MODELS_AND_PREDICTIONS_NOT_RUN"}


def _convert_raw(raw, tau, route, hashes, scope):
    """Conversion only; no score, forecast, ranking, detection or evaluator."""
    from scripts.task_e.loader import c1_bundle, c5_bundle
    from scripts.task_e.input_adapters import rcd_bundle
    if type(tau) is not int:
        raise FinalSourceError("TIMING_MARKER_NOT_INTEGRAL_SECONDS")
    report, origin = _clock_report(raw, tau)
    bundles, failures, costs = {}, {}, {}
    for profile, builder in (("c1", lambda: c1_bundle(raw, tau)), ("c5", lambda: c5_bundle(raw))):
        start = time.perf_counter()
        try:
            bundles[profile] = builder()
        except Exception as exc:
            failures[profile] = type(exc).__name__
        costs[profile + "_conversion_seconds"] = time.perf_counter() - start
    one, five, rcd = None, None, None
    names = {profile: tuple(bundle["service_names"]) for profile, bundle in bundles.items()}
    quality = {"scope": scope, "names_paths_absolute_clocks_removed": True,
               "actual_prediction_qualified": False}
    if "c1" in bundles:
        bundle = bundles["c1"]
        projected = _project_audit(bundle["audit"], names["c1"])
        catalog, costs["c1_explanation_support_conversion_seconds"] = _safe_controller_evidence(
            raw, names["c1"], hashes, tau - 300, tau, tau, tau + 300)
        one = C1Observation(route, bundle["ref"], bundle["query"], tuple(bundle["channel_types"]),
                            bundle["adj"], tuple(candidate_key(name) for name in names["c1"]),
                            hashes, copy.deepcopy(bundle["audit"]["graph"]), {**projected, **quality}, catalog)
        start = time.perf_counter()
        try:
            original = rcd_bundle(raw, tau, list(names["c1"]))
            rcd = {"values": original["values"].copy(), "owners": list(original["owners"].values()),
                   "candidate_count": len(names["c1"])}
            bundles["rcd"] = original
        except Exception as exc:
            failures["rcd"] = type(exc).__name__
        costs["rcd_conversion_seconds"] = time.perf_counter() - start
    else:
        failures["rcd"] = "C1_CANDIDATE_UNIVERSE_UNAVAILABLE"
        costs["rcd_conversion_seconds"] = None
    if "c5" in bundles:
        bundle = bundles["c5"]
        five = C5Observation(route, bundle["values"][:36], bundle["values"][36:],
                             tuple(bundle["channel_types"]), bundle["adj"], bundle["fit_service_mask"],
                             tuple(candidate_key(name) for name in names["c5"]), bundle["endpoints"][36:],
                             hashes, copy.deepcopy(bundle["audit"]["graph"]),
                             {**_project_audit(bundle["audit"], names["c5"], origin), **quality}, {})
    numeric = _numeric_fingerprint(one, five, rcd)
    public = {"c1": one, "c5": five, "rcd": rcd, "numeric_input_sha256": numeric,
              "source_metadata": {"scope": scope, "conversion_only": True,
                                  "source_hashes": dict(hashes), "clock_windows": report,
                                  "conversion_failures": failures, "conversion_costs": costs,
                                  "numeric_inventory": _numeric_inventory(one, five, rcd),
                                  "c1_quality": {} if one is None else _project_audit(bundles["c1"]["audit"], names["c1"]),
                                  "c5_quality": {} if five is None else _project_audit(bundles["c5"]["audit"], names["c5"], origin),
                                  "rcd_quality": {} if rcd is None else {
                                      "rows": 600, "eligible_columns": rcd["values"].shape[1],
                                      "unknown_column_count": len(bundles["rcd"]["audit"]["unmatched"]),
                                      "channel_reports": list(bundles["rcd"]["audit"]["channels"].values())}},
              "controller_bindings": {"candidate_ids": [] if one is None else list(one.node_ids),
                                      "c5_candidate_ids": [] if five is None else list(five.node_ids),
                                      "integrated_candidate_ids": {}}}
    # Raw source/time/identity audit stays in the closure, never public objects.
    private = {"origin": origin, "tau": tau, "names": names, "bundles": bundles}
    return public, private


def _synthetic_raw(variant):
    """Three different, bounded artificial archives for separate boundary checks."""
    import pandas as pd
    from scripts.task_e.loader import TRACE_FIELDS
    origin, duration = 100_000 + variant * 10_000, 1200
    seconds = np.arange(origin, origin + duration, dtype=np.int64)
    relative = seconds - origin
    metrics = pd.DataFrame({"time": seconds})
    count = 6 - variant
    for node in range(count):
        values = 10 + np.sin(relative / (7 + variant) + node) * (node + 1)
        values += (relative >= 180 + variant * 5) * 1e8 * (node + 1)
        values += (relative >= 620 + variant * 30) * (node + 1) * 1000
        metrics[f"synthetic-node-{node}_cpu"] = values
    metrics["unmatched_cpu"] = np.arange(duration, dtype=float)
    traces = []
    for second in seconds[::5]:
        for node in range(count):
            parent = "" if node == 0 else f"span-{second}-{node-1 if variant != 1 else 0}"
            traces.append(("artificial", f"trace-{second}", f"span-{second}-{node}",
                           f"synthetic-node-{node}", "method", "operation", parent,
                           int(second) * 1000, int(second), 1, 200))
    logs = None if variant == 2 else pd.DataFrame({"timestamp": np.repeat(seconds[::10], count),
               "container_name": np.tile([f"synthetic-node-{i}" for i in range(count)], duration // 10),
               "message": "synthetic-only"})
    return {"metrics": metrics, "traces": pd.DataFrame(traces, columns=TRACE_FIELDS), "logs": logs}, origin + 620 + variant * 30


def _actual_plan(contract):
    """Open exactly two projections after pinned-byte and durable-entry checks."""
    from scripts.task_g.provenance import verify_entry_receipt
    from scripts.pre_g.source_qualification import _read_frozen_contract, _plan_final_metadata
    timing_contract = contract.get("tau_source", {})
    if (timing_contract.get("path") != METADATA_REL or timing_contract.get("sha256") != METADATA_SHA
            or timing_contract.get("roster_projection") != list(ROSTER_PROJECTION)
            or timing_contract.get("projection") != list(TAU_PROJECTION)
            or timing_contract.get("timestamp_unit") != "UNIX_SECONDS_METADATA_INJECT_TIME"):
        raise FinalSourceError("TIMING_SOURCE_REGISTRATION_DRIFT")
    verified = verify_entry_receipt()
    if (verified.get("scope") != "ENTRY_RAW_ADMISSION" or verified.get("trust_mode") != "HOST_TRUSTED"
            or verified.get("receipt_sha256") != ENTRY_SHA):
        raise FinalSourceError("TRUSTED_ENTRY_BINDING_INVALID")
    encoded = previous._regular_bytes(WORKSPACE / ENTRY_REL)
    if hashlib.sha256(encoded).hexdigest() != ENTRY_SHA:
        raise FinalSourceError("ENTRY_READBACK_DRIFT")
    admission = json.loads(encoded)["commitment"]["execution"]["aggregate_report"]["admission"]
    if (admission["descriptor_sha256"] != DESCRIPTOR_SHA or admission["opaque_roster_sha256"] != ROSTER_SHA
            or admission["planned_cases"] != 60 or admission["planned_objects"] != 180):
        raise FinalSourceError("ENTRY_ADMISSION_INVENTORY_DRIFT")
    metadata = WORKSPACE / METADATA_REL
    if _sha(metadata) != METADATA_SHA:
        raise FinalSourceError("TIMING_SOURCE_BYTES_DRIFT")
    import pyarrow as pa
    import pyarrow.parquet as pq
    footer = pq.ParquetFile(metadata)
    if not pa.types.is_int64(footer.schema_arrow.field("inject_time").type):
        raise FinalSourceError("TIMING_SOURCE_PHYSICAL_TYPE_UNSUPPORTED")
    _, registry = _read_frozen_contract(WORKSPACE, PROJECT)
    roster_rows = pq.read_table(metadata, columns=list(ROSTER_PROJECTION)).to_pylist()
    planned = _plan_final_metadata(roster_rows, registry)
    ids = planned["final_ids"]
    if hashlib.sha256(("\n".join(ids) + "\n").encode()).hexdigest() != ROSTER_SHA:
        raise FinalSourceError("TIMING_SOURCE_ROSTER_DRIFT")
    timing_rows = pq.read_table(metadata, columns=list(TAU_PROJECTION)).to_pylist()
    lookup = {}
    for row in timing_rows:
        if row["dataset"] != "RE2-TT":
            continue
        case = row["case"]
        if case in lookup or type(row["inject_time"]) is not int:
            raise FinalSourceError("TIMING_SOURCE_DUPLICATE_OR_UNPLACEABLE")
        lookup[case] = row
    descriptors, entry_proofs = [], []
    for ordinal, case in enumerate(ids):
        if case not in lookup or lookup[case]["repetition"] != int(case.rpartition("_")[2]):
            raise FinalSourceError("TIMING_SOURCE_JOIN_FAILURE")
        audit = admission["case_audits"][ordinal]
        if audit["ordinal"] != ordinal:
            raise FinalSourceError("ENTRY_ORDINAL_DRIFT")
        alignment, association = audit.get("clock_alignment", {}), audit.get("log_association", {})
        if (alignment.get("declared_metric_unit") != "seconds" or alignment.get("declared_trace_unit") != "milliseconds"
                or type(alignment.get("trace_rows_inside_metric_archive")) is not int
                or type(alignment.get("trace_rows_outside_metric_archive")) is not int):
            raise FinalSourceError("ENTRY_CLOCK_PROOF_MISSING_OR_UNREGISTERED")
        entry_proofs.append({"receipt_sha256": ENTRY_SHA, "ordinal": ordinal,
                             "declared_metric_unit": "seconds", "declared_trace_unit": "milliseconds",
                             "trace_rows_inside_metric_archive": alignment["trace_rows_inside_metric_archive"],
                             "trace_rows_outside_metric_archive": alignment["trace_rows_outside_metric_archive"],
                             "exact_entity_second_log_rows": association.get("rows_with_exact_service_and_observed_metric_second"),
                             "historical_archive_proof_does_not_qualify_actual_marker_window": True})
        for modality in ("metrics", "traces", "logs"):
            entry = audit["modalities"][modality]
            descriptors.append({"path": f"{case}/{modality}.parquet", "bytes": entry["bytes"], "sha256": entry["sha256"]})
    descriptors.sort(key=lambda row: row["path"])
    if _digest(descriptors) != DESCRIPTOR_SHA:
        raise FinalSourceError("SIGNED_TELEMETRY_DESCRIPTOR_DRIFT")
    return ids, tuple(lookup[case]["inject_time"] for case in ids), descriptors, tuple(entry_proofs)


def _read_actual(ids, markers, descriptors, ordinal):
    from scripts.task_g.source_admission import _read_verified_raw
    case = ids[ordinal]
    selected = tuple(row for row in descriptors if row["path"].split("/")[0] == case)
    start = time.perf_counter()
    raw = _read_verified_raw(WORKSPACE / RAW_REL, selected)
    # Timing/roster projection already admitted these identities. The frozen
    # converters ignore this private redaction context; it never enters wire.
    raw["_controller_redaction_identifiers"] = tuple(ids)
    elapsed = time.perf_counter() - start
    hashes = {Path(row["path"]).stem: row["sha256"] for row in selected}
    return raw, markers[ordinal], hashes, elapsed


def _bind_sources():
    registry = weakref.WeakKeyDictionary()
    synthetic_builder = _synthetic_raw
    actual_planner, actual_reader = _actual_plan, _read_actual

    def require(handle):
        if type(handle) is not FinalSource or handle not in registry:
            raise FinalSourceError("UNISSUED_FINAL_SOURCE")
        state = registry[handle]
        if _context() != state["context"]:
            raise FinalSourceError("SOURCE_CONTEXT_DRIFT")
        return state

    def issue(scope, kind, size, **specific):
        context = _context()
        handle = FinalSource()
        state = {"scope": scope, "context": context, "size": size, "kind": kind,
                 "last": None, "private": {}, "integrated": {}, **specific}
        registry[handle] = state
        state["summary"] = {"schema": "TD13-G32-ISSUED-SOURCE-v1", "scope": scope,
            "source_kind": kind, "planned_cases": size, "planned_cells": 20 if size == 60 else size,
            "repeats_per_cell": 3 if size == 60 else 1,
            "source_sha256": _digest({"scope": scope, "kind": kind, "size": size,
                                       "metadata": METADATA_SHA if scope == ACTUAL_SCOPE else None,
                                       "entry": ENTRY_SHA if scope == ACTUAL_SCOPE else None}),
            "actual_final_telemetry_opened": False, "actual_truth_read": False,
            "case_ids_paths_disclosed": False, "final_prediction_qualified": False}
        return handle

    def synthetic():
        return issue(SYNTHETIC_SCOPE, "THREE_DISTINCT_ARTIFICIAL_ARCHIVES", 3)

    def development():
        context = _context()
        if context[1]["permissions"].get("development30_timing_only") is not True:
            raise FinalSourceError("DEVELOPMENT_PERMISSION_CLOSED")
        parent = previous.load_development_source()
        handle = issue(DEVELOPMENT_SCOPE, "EXACT_PINNED_DEVELOPMENT_NUMERIC30", previous.case_count(parent), parent=parent)
        registry[handle]["summary"].update(source_sha256=previous.source_summary(parent)["source_sha256"],
                                         planned_cells=10, repeats_per_cell=3)
        return handle

    def actual():
        context = _context()
        permissions = context[1]["permissions"]
        if (permissions.get("tau_only_input_audit") is not True or permissions.get("telemetry_final60_conversion_only") is not True
                or permissions.get("telemetry_final60_new_acquisition") is not False):
            raise FinalSourceError("ACTUAL_TIMING_CONVERSION_PERMISSION_CLOSED")
        ids, markers, descriptors, entry_proofs = actual_planner(context[1])
        return issue(ACTUAL_SCOPE, "VERIFIED_ENTRY_TELEMETRY_AND_TIMING_PROJECTION", 60,
                     ids=ids, markers=markers, descriptors=descriptors, entry_proofs=entry_proofs)

    def ordinal_guard(state, ordinal):
        if type(ordinal) is not int or not 0 <= ordinal < state["size"]:
            raise FinalSourceError("INVALID_CASE_ORDINAL")

    def materialize(state, ordinal):
        ordinal_guard(state, ordinal)
        if state["scope"] == DEVELOPMENT_SCOPE:
            row = previous.get_case(state["parent"], ordinal)
            row["source_metadata"] = {"scope": DEVELOPMENT_SCOPE, "numeric_cache_verified": True,
                                      "conversion_costs": {}, "conversion_only": True}
            row["controller_bindings"] = {"candidate_ids": list(row["c1"].node_ids),
                                          "c5_candidate_ids": [], "integrated_candidate_ids": {}}
            return row
        if state["last"] is not None and state["last"][0] == ordinal:
            return state["last"][1]
        if state["scope"] == SYNTHETIC_SCOPE:
            raw, marker = synthetic_builder(ordinal)
            hashes = {"artificial_archive": _digest({"variant": ordinal, "revision": "G32-v1"})}
            io_cost = None
        else:
            raw, marker, hashes, io_cost = actual_reader(state["ids"], state["markers"], state["descriptors"], ordinal)
            raw.setdefault("audit", {})["verified_entry_archive_alignment"] = copy.deepcopy(state["entry_proofs"][ordinal])
            state["summary"]["actual_final_telemetry_opened"] = True
        route = hashlib.sha256(f"TD13-G32|{state['scope']}|{ordinal}".encode()).hexdigest()[:16]
        row, private = _convert_raw(raw, marker, route, hashes, state["scope"])
        row.update(ordinal=ordinal, cell_ordinal=ordinal // 3 if state["scope"] == ACTUAL_SCOPE else ordinal,
                   repeat=ordinal % 3 if state["scope"] == ACTUAL_SCOPE else 0)
        row["source_metadata"]["conversion_costs"]["cold_io_and_hash_seconds"] = io_cost
        state["private"].setdefault(ordinal, {}).update(
            names=private["names"], origin=private["origin"], tau=private["tau"],
            source_audit=copy.deepcopy(raw.get("audit", {})),
            bundle_audits={profile: copy.deepcopy(bundle["audit"])
                           for profile, bundle in private["bundles"].items()})
        state["last"] = (ordinal, row, raw, hashes)
        return row

    def case(handle, ordinal):
        state = require(handle)
        row = materialize(state, ordinal)
        result = {key: copy.deepcopy(value) for key, value in row.items() if key not in {"c1", "c5"}}
        result["c1"] = _evidence_copy(row["c1"])
        result["c5"] = _evidence_copy(row["c5"])
        result["controller_bindings"]["integrated_candidate_ids"] = copy.deepcopy(state["integrated"].get(ordinal, {}))
        return result

    def integrated(handle, ordinal, endpoint):
        state = require(handle)
        ordinal_guard(state, ordinal)
        if type(endpoint) is not int or endpoint < 0 or endpoint % 5:
            raise FinalSourceError("INVALID_RELATIVE_TRIGGER_ENDPOINT")
        if endpoint < 360:
            raise FinalSourceError("INSUFFICIENT_HISTORY")
        if state["scope"] == DEVELOPMENT_SCOPE:
            raise FinalSourceError("DEVELOPMENT_NUMERIC_HAS_NO_INTEGRATED_SOURCE")
        row = materialize(state, ordinal)
        raw, hashes = state["last"][2:]
        origin = state["private"][ordinal]["origin"]
        if origin is None:
            raise FinalSourceError("INTEGRATED_ORIGIN_UNAVAILABLE")
        if endpoint > int(raw["metrics"].time.max()) + 1 - origin:
            raise FinalSourceError("TRIGGER_OUTSIDE_OBSERVED_HISTORY")
        from scripts.task_e.input_adapters import integrated_bundle
        bundle = integrated_bundle(raw, origin + endpoint)
        names = tuple(bundle["service_names"])
        state["private"][ordinal].setdefault("integrated_names", {})[endpoint] = names
        identities = [candidate_key(name) for name in names]
        state["integrated"].setdefault(ordinal, {})[str(endpoint)] = identities
        catalog, support_cost = _safe_controller_evidence(
            raw, names, hashes, origin + endpoint - 360, origin + endpoint - 60,
            origin + endpoint - 60, origin + endpoint)
        return C1Observation(row["c1"].handle if row["c1"] is not None else hashlib.sha256(f"G32|{ordinal}".encode()).hexdigest()[:16],
            bundle["ref"], bundle["query"], tuple(bundle["channel_types"]), bundle["adj"], tuple(identities),
            hashes, {**bundle["audit"]["graph"], "past_only": True},
            {**_project_audit(bundle["audit"], names), "relative_endpoint": endpoint, "scope": state["scope"],
             "explanation_support_conversion_seconds": support_cost}, catalog)

    def truth(handle, ordinal, root_literal, endpoint=None):
        state = require(handle)
        ordinal_guard(state, ordinal)
        if state["scope"] != SYNTHETIC_SCOPE:
            raise FinalSourceError("ACTUAL_TRUTH_AND_EVALUATION_CLOSED")
        materialize(state, ordinal)
        names = state["private"][ordinal]["names"]["c1"] if endpoint is None else state["private"][ordinal].get("integrated_names", {}).get(endpoint)
        if names is None:
            raise FinalSourceError("INTEGRATED_TRUTH_MAPPING_NOT_MATERIALIZED")
        return names.index(root_literal) if root_literal in names else None

    def summary(handle):
        return copy.deepcopy(require(handle)["summary"])

    def count(handle):
        return require(handle)["size"]

    return synthetic, development, actual, summary, count, case, integrated, truth


(make_synthetic_source, load_development_source, open_final_source, source_summary,
 case_count, get_case, integrated_observation, map_truth) = _bind_sources()
del _bind_sources, _synthetic_raw, _actual_plan, _read_actual


def audit_actual_conversion(progress=None):
    """Retain all60 planned conversion records, without running any model."""
    source = open_final_source()
    rows = []
    for ordinal in range(case_count(source)):
        start = time.perf_counter()
        record = {"ordinal": ordinal, "status": "CONVERSION_FAILURE_RETAINED", "failure_attempts": [],
                  "model_functions_invoked": False,
                  "profile_statuses": {profile: "NOT_REACHED_SOURCE_FAILURE" for profile in
                                       ("c1", "c5", "rcd", "integrated360", "c3_c1", "c3_integrated360")}}
        try:
            case = get_case(source, ordinal)
            record.update({"status": "CONVERTED_ONLY" if case["c1"] is not None and case["c5"] is not None else "CONVERSION_FAILURE_RETAINED",
                "numeric_input_sha256": case["numeric_input_sha256"], "source_metadata": case["source_metadata"],
                "c1_candidates": 0 if case["c1"] is None else len(case["c1"].node_ids),
                "c5_candidates": 0 if case["c5"] is None else len(case["c5"].node_ids),
                "rcd_columns": 0 if case["rcd"] is None else case["rcd"]["values"].shape[1],
                "integrated_profile": "PAST_ONLY_REFERENCE300_QUERY60_END360",
                "window_coverage_status": case["source_metadata"]["clock_windows"]["known_window_coverage_status"],
                "window_coverage_open": case["source_metadata"]["clock_windows"]["known_window_coverage_status"].startswith("OPEN"),
                "c1_explanation_support": {} if case["c1"] is None else _plain_catalog(case["c1"].evidence_catalog)})
            record["profile_statuses"].update({
                "c1": "UNAVAILABLE" if case["c1"] is None else "EMPTY_CANDIDATE_UNIVERSE" if not case["c1"].node_ids else "NUMERIC_INPUT_AVAILABLE",
                "c5": "UNAVAILABLE" if case["c5"] is None else "EMPTY_CANDIDATE_UNIVERSE" if not case["c5"].node_ids else "NUMERIC_INPUT_AVAILABLE",
                "rcd": "UNAVAILABLE" if case["rcd"] is None else "EMPTY_ELIGIBILITY_BASELINE_FAILURE_ONLY" if not case["rcd"]["values"].shape[1] else "NUMERIC_INPUT_AVAILABLE",
                "c3_c1": _catalog_status(record["c1_explanation_support"])})
            record["failure_attempts"].extend({"stage": profile.upper() + "_CONVERSION", "error_type": reason}
                                               for profile, reason in case["source_metadata"]["conversion_failures"].items())
            record["clock_or_modality_coverage_open"] = any(
                value["status"].startswith("OPEN") for value in case["source_metadata"]["clock_windows"]["modalities"].values())
            record["explanation_packet_semantic_log_excerpt_status"] = record["c1_explanation_support"].get("c3-support", {}).get("query_logs", {}).get("semantic_excerpt_status", "UNAVAILABLE_AFTER_SUPPORT_FAILURE")
            integrated_start = time.perf_counter()
            try:
                integrated = integrated_observation(source, ordinal, 360)
                record["integrated_numeric_sha256"] = previous._digest(previous._array_manifest({"ref": integrated.ref, "query": integrated.query, "adj": integrated.adjacency}))
                record["integrated_explanation_support"] = _plain_catalog(integrated.evidence_catalog)
                record["profile_statuses"]["integrated360"] = "EMPTY_CANDIDATE_UNIVERSE" if not integrated.node_ids else "NUMERIC_INPUT_AVAILABLE"
                record["profile_statuses"]["c3_integrated360"] = _catalog_status(record["integrated_explanation_support"])
            except Exception as exc:
                record["status"] = "CONVERSION_FAILURE_RETAINED"
                record["failure_attempts"].append({"stage": "INTEGRATED360_CONVERSION", "error_type": type(exc).__name__})
                record["profile_statuses"]["integrated360"] = "UNAVAILABLE"
                record["profile_statuses"]["c3_integrated360"] = "UNAVAILABLE_AFTER_INTEGRATED360_FAILURE"
            record["integrated_conversion_wall_seconds"] = time.perf_counter() - integrated_start
        except Exception as exc:
            record["failure_attempts"].append({"stage": "ISSUED_SOURCE_CASE_CONVERSION", "error_type": type(exc).__name__})
        record["elapsed_conversion_wall_seconds"] = time.perf_counter() - start
        rows.append(record)
        if progress is not None:
            progress({"converted_planned_cases": ordinal + 1, "planned_cases": 60,
                      "failure_records": sum(row["status"] != "CONVERTED_ONLY" for row in rows),
                      "completed_case_record": copy.deepcopy(record)})
    def measured_max(values):
        observed = [value for value in values if value is not None]
        return max(observed) if observed else None

    return {"schema": "TD13-G32-ACTUAL-CONVERSION-AUDIT-v1", "scope": ACTUAL_SCOPE,
            "planned_cases": 60, "planned_objects": 180, "timing_source_sha256": METADATA_SHA,
            "timing_projection": list(TAU_PROJECTION), "roster_projection": list(ROSTER_PROJECTION),
            "entry_receipt_sha256": ENTRY_SHA, "descriptor_sha256": DESCRIPTOR_SHA,
            "case_records": rows, "case_records_sha256": _digest(rows),
            "converted_only_cases": sum(row["status"] == "CONVERTED_ONLY" for row in rows),
            "converted_only_cases_definition": "C1_AND_C5_OBSERVATIONS_PLUS_INTEGRATED360_CONVERSION_RCD_STATUS_SEPARATE",
            "profile_status_counts": {profile: dict(Counter(row["profile_statuses"][profile] for row in rows))
                                      for profile in ("c1", "c5", "rcd", "integrated360", "c3_c1", "c3_integrated360")},
            "window_coverage_open_records": sum(row.get("window_coverage_open", True) for row in rows),
            "clock_or_modality_coverage_open_records": sum(row.get("clock_or_modality_coverage_open", True) for row in rows),
            "maximum_conversion_wall_seconds": measured_max(row["elapsed_conversion_wall_seconds"] for row in rows),
            "maximum_cold_io_and_hash_seconds": measured_max(row.get("source_metadata", {}).get("conversion_costs", {}).get("cold_io_and_hash_seconds") for row in rows),
            "missing_cold_io_measurements": sum(row.get("source_metadata", {}).get("conversion_costs", {}).get("cold_io_and_hash_seconds") is None for row in rows),
            "maximum_numeric_input_binary_bytes": measured_max(row.get("source_metadata", {}).get("numeric_inventory", {}).get("present_input_binary_bytes") for row in rows),
            "maximum_json_numeric_input_arrays_upper_bound_bytes": measured_max(row.get("source_metadata", {}).get("numeric_inventory", {}).get("json_numeric_input_arrays_upper_bound_bytes") for row in rows),
            "actual_complete_diagnostic_artifact_bound": "OPEN_MODEL_DIAGNOSTICS_NOT_MEASURED",
            "root_fault_answers_outcomes_read": False, "actual_prediction_functions_invoked": False,
            "campaign_executed": False, "final_prediction_qualified": False}


__all__ = ["FinalSource", "FinalSourceError", "make_synthetic_source", "load_development_source",
           "open_final_source", "source_summary", "case_count", "get_case", "integrated_observation",
           "map_truth", "candidate_key", "audit_actual_conversion"]
