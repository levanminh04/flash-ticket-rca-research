"""G entry-only telemetry acquisition/admission. No labels or predictions.

Locators, service names, epochs and raw audit messages remain internal. Public
handles expose aggregate receipts and opaque ordinal rows only. The trust
boundary is ordinary callers on the registered host, not hostile runtime code.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
import weakref
from collections import Counter
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote, urljoin, urlparse

from scripts.pre_g.source_qualification import (
    FROZEN_V2_SHA256, MANIFEST_RELATIVE, METADATA_RELATIVE, METADATA_SHA256,
    OFFICIAL_ENDPOINT, REPO_ID, REVISION, TD_SHA256, _canonical, _case_component,
    _field, _plan_final_metadata, _read_frozen_contract, _sha256, _valid_digest,
)

WORKSPACE = Path("D:/Project/flash-ticket-rca-research").resolve()
PROJECT = Path("D:/Project/flash-ticket-platform").resolve()
RAW_RELATIVE = Path("datasets/rcaeval/task-g-final")
CONTRACT_RELATIVE = Path("results/task-g/g30-entry-validation/entry-contract.json")
REVIEW_RELATIVE = Path("results/task-g/g30-entry-validation/independent-entry-review.md")
PROJECTION = ("case", "dataset", "repetition", "has_logs", "has_traces")
DESCRIPTOR_SHA256 = "2b51110896bf23f6f2264e85458b814c1cd7871c50e047d814aeda3943b32d94"
DECLARED_BYTES = 1_309_388_082
ROSTER_SHA256 = "f74ba6f11f55729ead8980cfc2df34be2cdb8fd570abe7656b62e31858d24bae"
SNAPSHOT_PATHS = frozenset(
    f"{directory}/{name}.py"
    for directory, names in (("scripts/task_g", ("source_admission", "controller", "provenance")),
                             ("tests/task_g", ("test_source_admission", "test_controller", "test_provenance")))
    for name in names
)
SCHEMA_PROJECTIONS = {
    "metrics": "time + numeric metric columns; unknown mappings counted, never aliased",
    "traces": ["time", "traceID", "spanID", "serviceName", "methodName", "operationName",
               "parentSpanID", "startTimeMillis", "startTime", "duration", "statusCode"],
    "logs": ["timestamp", "container_name", "message"],
}


class SourceAdmissionError(ValueError):
    """A sanitized entry-only boundary error (no case/path/message detail)."""


class SourcePlan:
    __slots__ = ("__weakref__",)

    @property
    def summary(self) -> dict[str, Any]:
        return _plan_summary(self)


class SourceAdmission:
    __slots__ = ("__weakref__",)

    @property
    def summary(self) -> dict[str, Any]:
        return require_issued_admission(self)


def _descriptors(api, paths):
    if _field(api.dataset_info(REPO_ID, revision=REVISION), "sha") != REVISION:
        raise SourceAdmissionError("Pinned official dataset revision mismatch")
    expected = set(paths)
    seen, result = set(), []
    objects = api.get_paths_info(REPO_ID, paths=list(paths), repo_type="dataset", revision=REVISION)
    for obj in objects:
        relative = _field(obj, "path")
        size = _field(obj, "size")
        if relative not in expected or relative in seen or type(size) is not int or size <= 0:
            raise SourceAdmissionError("Unexpected or invalid telemetry-only descriptor")
        digest = _valid_digest(_field(_field(obj, "lfs"), "sha256"))
        seen.add(relative)
        result.append({"path": relative, "bytes": size, "sha256": digest})
    if seen != expected:
        raise SourceAdmissionError("Telemetry descriptor inventory incomplete")
    return tuple(sorted(result, key=lambda row: row["path"]))


def _build_plan(workspace, project, api=None):
    """Issue a metadata-only plan; injected APIs are permanently fixture-only."""
    workspace, project = Path(workspace).resolve(), Path(project).resolve()
    if workspace != WORKSPACE or project != PROJECT:
        raise SourceAdmissionError("Official G plan requires the registered canonical roots")
    try:
        manifest, registry = _read_frozen_contract(workspace, project)
        metadata = workspace / METADATA_RELATIVE
        if _sha256(metadata) != METADATA_SHA256:
            raise SourceAdmissionError("Pinned projected metadata byte drift")
        import pyarrow.parquet as pq

        rows = pq.read_table(metadata, columns=list(PROJECTION)).to_pylist()
        planned = _plan_final_metadata(rows, registry)
        injected = api is not None
        if api is None:
            from huggingface_hub import HfApi

            api = HfApi(endpoint=OFFICIAL_ENDPOINT, token=False)
            if api.endpoint != OFFICIAL_ENDPOINT:
                raise SourceAdmissionError("Official descriptor origin is not pinned")
        descriptors = _descriptors(api, planned["remote_paths"])
        inventory_digest = hashlib.sha256(_canonical(descriptors)).hexdigest()
        total_bytes = sum(row["bytes"] for row in descriptors)
        roster_digest = hashlib.sha256(("\n".join(planned["final_ids"]) + "\n").encode("utf-8")).hexdigest()
        if not injected and (inventory_digest != DESCRIPTOR_SHA256 or total_bytes != DECLARED_BYTES
                             or len(descriptors) != 180 or roster_digest != ROSTER_SHA256):
            raise SourceAdmissionError("Registered official final inventory or split changed")
    except SourceAdmissionError:
        raise
    except Exception:
        raise SourceAdmissionError("Pinned metadata, split or descriptor qualification failed") from None
    summary = {
        "schema": "TD13-G-SOURCE-PLAN-v1",
        "scope": "SYNTHETIC_INJECTED_API_ONLY" if injected else "OFFICIAL_TELEMETRY_PLAN",
        "revision": REVISION, "endpoint": None if injected else OFFICIAL_ENDPOINT,
        "metadata_sha256": METADATA_SHA256, "metadata_projection": list(PROJECTION),
        "planned_cases": len(planned["final_ids"]), "planned_objects": len(descriptors),
        "declared_bytes": total_bytes, "descriptor_sha256": inventory_digest,
        "opaque_roster_sha256": roster_digest, "schema_projections": copy.deepcopy(SCHEMA_PROJECTIONS),
        "case_ids_paths_disclosed": False, "raw_opened": False, "labels_opened": False,
    }
    return {"workspace": workspace, "project": project,
                        "scope": summary["scope"], "summary": summary,
                        "cases": planned["final_ids"], "descriptors": descriptors,
                        "manifest": manifest}


def _registered_gate(state, contract_path):
    """Fail closed before ANY raw bytes/network; no caller qualification flags."""
    expected_path = state["workspace"] / CONTRACT_RELATIVE
    if Path(contract_path).resolve() != expected_path:
        raise SourceAdmissionError("Admission requires the exact registered entry contract")
    try:
        contract = json.loads(expected_path.read_text(encoding="utf-8"))
        permissions = contract["permissions"]
        if permissions.get("telemetry_final60_acquisition_and_admission") is not True:
            raise SourceAdmissionError("Telemetry admission permission absent")
        closed = ("final_labels", "final_tau_metadata", "final_answers", "final_outcomes",
                  "final_predictions", "final_campaign")
        if any(permissions.get(key) is not False for key in closed):
            raise SourceAdmissionError("Entry contract must keep labels, outputs and campaign closed")
        if contract["run_id"] != "g30-entry-validation":
            raise SourceAdmissionError("Wrong entry run domain")
        if contract["raw_admission_gate"] != "OPEN_FOR_TELEMETRY_ONLY_ADMISSION":
            raise SourceAdmissionError("Independent pre-admission gate remains closed")
        frozen = contract["frozen_inputs"]
        if frozen != {"td_v1_3_sha256": TD_SHA256,
                       "task_f_v2_manifest_sha256": FROZEN_V2_SHA256,
                       "metadata_sha256": METADATA_SHA256}:
            raise SourceAdmissionError("Registered frozen input identities drift")
        source = contract["source"]
        if (source["repo_id"] != REPO_ID or source["revision"] != REVISION
                or source["endpoint"] != OFFICIAL_ENDPOINT
                or source["metadata_projection"] != list(PROJECTION)
                or source["descriptor_digest"] != DESCRIPTOR_SHA256
                or source["raw_allowlist_digest"] != DESCRIPTOR_SHA256
                or source["schema_projections"] != SCHEMA_PROJECTIONS
                or source["final_case_ids_digest"] != ROSTER_SHA256):
            raise SourceAdmissionError("Registered source allowlist drift")
        payload = contract["impact_map"]["generated_payload"]
        if payload != {"raw_root": RAW_RELATIVE.as_posix(), "objects": 180,
                       "declared_bytes": DECLARED_BYTES,
                       "official_descriptor_digest": DESCRIPTOR_SHA256}:
            raise SourceAdmissionError("Registered raw root or bounded payload drift")
        snapshot = contract["source_test_snapshot_before_qualification"]
        if not isinstance(snapshot, dict) or set(snapshot) != SNAPSHOT_PATHS:
            raise SourceAdmissionError("Complete reviewed G source/test snapshot absent")
        for relative, digest in snapshot.items():
            if _sha256(state["workspace"] / relative) != _valid_digest(digest):
                raise SourceAdmissionError("Reviewed G source/test bytes drift")
        review = contract["independent_pre_admission_review"]
        if (review["status"] != "PASS_PRE_ADMISSION_REVIEW"
                or review["source_test_snapshot"] != snapshot):
            raise SourceAdmissionError("Independent review does not bind this source snapshot")
        raw_review = review["raw_utf8"]
        if (not isinstance(raw_review, str) or not raw_review
                or hashlib.sha256(raw_review.encode("utf-8")).hexdigest() != review["sha256"]
                or not (state["workspace"] / REVIEW_RELATIVE).read_text(encoding="utf-8").startswith(raw_review)):
            raise SourceAdmissionError("Independent pre-audit review snapshot drift")
        _read_frozen_contract(state["workspace"], state["project"])
        if _sha256(state["workspace"] / METADATA_RELATIVE) != METADATA_SHA256:
            raise SourceAdmissionError("Metadata bytes changed after planning")
    except SourceAdmissionError:
        raise
    except Exception:
        raise SourceAdmissionError("Registered pre-admission contract is incomplete or unreadable") from None
    return {"contract_sha256": _sha256(expected_path),
            "pre_admission_review_sha256": review["sha256"],
            "source_test_snapshot": snapshot}


def _exact_local_path(root, relative):
    parts = Path(relative).parts
    if len(parts) != 2 or parts[1] not in {"metrics.parquet", "traces.parquet", "logs.parquet"}:
        raise SourceAdmissionError("Non-telemetry local locator rejected")
    _case_component(parts[0])
    path = root / relative
    if path.resolve() != path.absolute() or root.resolve() != root.absolute():
        raise SourceAdmissionError("Aliased or escaped source path rejected")
    return path


def _verify_object(path, descriptor):
    if (not path.is_file() or path.stat().st_size != descriptor["bytes"]
            or _sha256(path) != descriptor["sha256"]):
        raise SourceAdmissionError("Local telemetry byte identity mismatch")


def _download_object(root, descriptor):
    """Official resolve URL only; no token/proxy inheritance or arbitrary path."""
    path = _exact_local_path(root, descriptor["path"])
    if path.exists():
        _verify_object(path, descriptor)
        return "REUSED_VERIFIED"
    path.parent.mkdir(parents=True, exist_ok=True)
    _exact_local_path(root, descriptor["path"])
    cache = WORKSPACE / "results/task-g/g30-entry-validation/cache/acquisition"
    cache.mkdir(parents=True, exist_ok=True)
    if cache.resolve() != cache.absolute():
        raise SourceAdmissionError("Aliased acquisition cache rejected")
    from urllib.error import HTTPError
    from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, message, headers, newurl):
            return None

    url = (f"{OFFICIAL_ENDPOINT}/datasets/{REPO_ID}/resolve/{REVISION}/"
           f"{quote(descriptor['path'], safe='/')}?download=true")
    # Standard library TLS verification; no new dependency, proxy or token
    # inheritance. Redirect origins are checked before each request.
    opener = build_opener(ProxyHandler({}), NoRedirect())
    stream = None
    response = None
    temporary = None
    try:
        for _ in range(6):
            parsed = urlparse(url)
            host = parsed.hostname or ""
            if (parsed.scheme != "https" or parsed.username or parsed.password
                    or parsed.port not in (None, 443)
                    or not (host == "huggingface.co" or host.endswith(".huggingface.co")
                            or host.endswith(".hf.co"))):
                raise SourceAdmissionError("Official download redirect origin rejected")
            try:
                response = opener.open(Request(url, headers={"Accept-Encoding": "identity",
                    "User-Agent": "FlashTicketRca-G-entry/1"}), timeout=120)
            except HTTPError as exc:
                response = exc
            if response.status in (301, 302, 303, 307, 308):
                location = response.headers.get("Location")
                response.close()
                if not location:
                    raise SourceAdmissionError("Official download redirect malformed")
                url = urljoin(url, location)
                continue
            if response.status != 200:
                raise SourceAdmissionError("Official telemetry acquisition HTTP failure")
            break
        else:
            raise SourceAdmissionError("Official download redirect limit exceeded")
        stream = tempfile.NamedTemporaryFile(mode="wb", prefix="object-", suffix=".part",
                                             dir=cache, delete=False)
        temporary = Path(stream.name)
        digest, length = hashlib.sha256(), 0
        for block in iter(lambda: response.read(1 << 20), b""):
            if not block:
                continue
            length += len(block)
            if length > descriptor["bytes"]:
                raise SourceAdmissionError("Downloaded object exceeded declared byte budget")
            stream.write(block)
            digest.update(block)
        stream.flush()
        os.fsync(stream.fileno())
        stream.close()
        stream = None
        if length != descriptor["bytes"] or digest.hexdigest() != descriptor["sha256"]:
            raise SourceAdmissionError("Downloaded telemetry identity mismatch")
        _exact_local_path(root, descriptor["path"])
        # Hard-link commits exclusively: never replace an existing source.
        os.link(temporary, path)
        temporary.unlink()
        _verify_object(path, descriptor)
        return "DOWNLOADED_VERIFIED"
    except SourceAdmissionError:
        raise
    except Exception:
        raise SourceAdmissionError("Telemetry acquisition failed; partial file preserved") from None
    finally:
        if stream is not None:
            stream.close()
        if response is not None:
            response.close()


def _read_verified_raw(root, descriptors):
    """Rehash every file before parsing; raw audit is generated here, not caller."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    from scripts.task_e.loader import _validate_schema

    raw = {modality: None for modality in ("metrics", "traces", "logs")}
    audit = {"scope": "G_ENTRY_RAW_INTERNAL", "modalities": {}}
    for descriptor in descriptors:
        modality = Path(descriptor["path"]).stem
        path = _exact_local_path(root, descriptor["path"])
        _verify_object(path, descriptor)
        entry = {"status": "CORRUPT_OR_UNSUPPORTED", "source_identity_verified": True,
                 "sha256": descriptor["sha256"], "bytes": descriptor["bytes"]}
        audit["modalities"][modality] = entry
        try:
            # Inspect schema metadata BEFORE requesting any value. Explicit
            # oracle columns are outside the telemetry scope even if numeric.
            parquet = pq.ParquetFile(path)
            names = parquet.schema_arrow.names
            forbidden = {"root", "root_cause", "root_service", "root_index", "fault", "fault_type",
                         "tau", "answer", "answers", "outcome", "outcomes", "label", "labels",
                         "inject_time", "injection_time", "injection_timestamp", "fault_time"}
            if any(name.casefold() in forbidden for name in names):
                raise SourceAdmissionError("Explicit oracle field rejected before value read")
            if modality != "metrics" and names != SCHEMA_PROJECTIONS[modality]:
                raise SourceAdmissionError("Unexpected trace/log schema rejected before value read")
            if len(names) != len(set(names)) or "time" not in names and modality == "metrics":
                raise SourceAdmissionError("Invalid metric schema rejected before value read")
            if modality == "metrics":
                if not pa.types.is_integer(parquet.schema_arrow.field("time").type):
                    raise SourceAdmissionError("Metric time physical type rejected before value read")
                for field in parquet.schema_arrow:
                    if field.name != "time" and not (pa.types.is_integer(field.type) or pa.types.is_floating(field.type) or pa.types.is_decimal(field.type)):
                        raise SourceAdmissionError("Metric nonnumeric schema rejected before value read")
            table = parquet.read(columns=names)
            _validate_schema(modality, table)
            frame = table.to_pandas()
            raw[modality] = frame
            entry.update(status="LOADED", rows=len(frame),
                         null_cells=int(frame.isna().sum().sum()),
                         full_row_duplicates=int(frame.duplicated().sum()),
                         schema_sha256=hashlib.sha256(str(table.schema).encode()).hexdigest())
        except Exception as exc:
            entry["error_type"] = type(exc).__name__
    for modality in raw:
        audit["modalities"].setdefault(modality, {"status": "MISSING"})
    raw["audit"] = audit
    return raw


def _numeric_digest(bundle, keys):
    import numpy as np

    digest = hashlib.sha256()
    for key in keys:
        array = np.ascontiguousarray(bundle[key])
        digest.update(key.encode())
        digest.update(str(array.dtype).encode())
        digest.update(_canonical(list(array.shape)))
        digest.update(array.tobytes())
    return digest.hexdigest()


def _same_numeric(a, b, keys):
    import numpy as np

    return (a["service_names"] == b["service_names"]
            and all(np.array_equal(a[key], b[key], equal_nan=True) for key in keys))


def _aggregate_bundle(bundle, profile, keys):
    import numpy as np

    arrays = [np.asarray(bundle[key]) for key in keys]
    return {"status": "CONVERTED_ONLY", "profile": profile,
            "numeric_sha256": _numeric_digest(bundle, keys),
            "nodes": len(bundle["service_names"]),
            "elements": sum(array.size for array in arrays),
            "nonfinite_elements": sum(int((~np.isfinite(array)).sum()) for array in arrays),
            "graph_edges": int(bundle["adj"].sum())}


def _audit_raw(raw):
    """Only frozen numeric conversion. No local anomaly/forecast/rank functions."""
    import numpy as np
    from scripts.task_e.input_adapters import integrated_bundle, rcd_bundle
    from scripts.task_e.loader import c1_bundle, c5_bundle, _metric_mapping
    from scripts.task_e.replay import validate_event_clock

    result = {"modalities": copy.deepcopy(raw["audit"]["modalities"]),
              "case_status": "ADMISSION_COMPATIBLE", "protocol_open": []}
    for modality, field in (("metrics", "time"), ("traces", "startTimeMillis"),
                            ("logs", "timestamp")):
        frame = raw[modality]
        if frame is None:
            continue
        try:
            validate_event_clock(frame[field], field)
            result["modalities"][modality]["event_clock"] = "PLACEABLE_DECLARED_UNITS"
        except Exception:
            result["modalities"][modality]["event_clock"] = "UNQUALIFIABLE_EVENT_CLOCK"
            if modality == "logs":
                # Optional log clock unavailability never vetoes valid M/T.
                raw[modality] = None
                result["modalities"][modality]["status"] = "UNAVAILABLE_LOG_CLOCK_OR_SCHEMA"
    metrics, traces, logs = raw["metrics"], raw["traces"], raw["logs"]
    s0 = (int(metrics.time.min()) if metrics is not None and not metrics.time.empty
          and result["modalities"]["metrics"].get("event_clock") == "PLACEABLE_DECLARED_UNITS" else None)
    if s0 is not None and traces is not None:
        finite = traces.startTimeMillis.dropna()
        intersection = ((finite >= s0 * 1000) &
                        (finite < (int(metrics.time.max()) + 1) * 1000))
        result["clock_alignment"] = {"declared_metric_unit": "seconds", "declared_trace_unit": "milliseconds",
                                     "trace_rows_inside_metric_archive": int(intersection.sum()),
                                     "trace_rows_outside_metric_archive": int((~intersection).sum())}
        if len(finite) and not intersection.any():
            result["protocol_open"].append("OPEN_CLOCK_ALIGNMENT_OR_NO_SHARED_COVERAGE")
        names = sorted(name for name in set(traces.serviceName.dropna()) if isinstance(name, str) and name)
        mapping, unknown = _metric_mapping(metrics, names)
        result["exact_mapping"] = {"metric_keys_matched": len(mapping), "metric_keys_unknown": len(unknown),
                                   "trace_literal_services": len(names),
                                   "log_entities_exactly_matched": int(logs.container_name.isin(names).sum()) if logs is not None else 0,
                                   "log_entities_unmatched": int((~logs.container_name.isin(names)).sum()) if logs is not None else 0}
        # Composite-key parents, no span-ID-only repair or event-ID inference.
        keys = traces[["traceID", "spanID"]].drop_duplicates().rename(columns={"spanID": "parentSpanID"})
        children = traces.loc[traces.parentSpanID.notna() & traces.parentSpanID.ne(""), ["traceID", "parentSpanID"]]
        resolved = children.merge(keys, on=["traceID", "parentSpanID"], how="inner")
        result["archive_parent_key_audit_only"] = {"nonnull_parent_rows": len(children), "composite_keys_resolved": len(resolved)}
        if logs is not None:
            metric_seconds = set(metrics.time.dropna().astype(int))
            result["log_association"] = {"kind": "EXACT_ENTITY_SECOND_NOT_EVENT_ID",
                "rows_with_exact_service_and_observed_metric_second": int((logs.container_name.isin(names) & logs.timestamp.isin(metric_seconds)).sum())}
    c1_keys, c5_keys = ("ref", "query", "adj", "channel_types"), ("values", "adj", "channel_types", "fit_service_mask", "endpoints")
    probes = (("c1", lambda: c1_bundle(raw, s0 + 720), "LABEL_FREE_PROTOCOL_WINDOW__ORIGIN_PLUS_DECLARED_RE2_OFFSET720", c1_keys),
              ("c5", lambda: c5_bundle(raw), "TD13-C5-EVENT-TIME", c5_keys),
              ("integrated", lambda: integrated_bundle(raw, s0 + 360), "LABEL_FREE_PAST_WINDOW__ENDPOINT360", c1_keys))
    for name, build, profile, keys in probes:
        try:
            if s0 is None:
                raise SourceAdmissionError("Observed metric origin unavailable")
            bundle = build()
            result[name] = _aggregate_bundle(bundle, profile, keys)
            if name == "c1":
                try:
                    rcd_input = rcd_bundle(raw, s0 + 720, bundle["service_names"])
                    matrix = rcd_input["values"]
                    result["rcd_input"] = {"status": "NUMERIC_INPUT_CONVERTED_ONLY" if matrix.shape[1] else
                                          "EMPTY_ELIGIBILITY_BASELINE_FAILURE_ONLY",
                        "profile": "LABEL_FREE_PROTOCOL_WINDOW__ORIGIN_PLUS_DECLARED_RE2_OFFSET720",
                        "shape": list(matrix.shape), "eligible_columns": int(matrix.shape[1]),
                        "finite_elements": int(np.isfinite(matrix).sum()),
                        "unknown_metric_keys": len(rcd_input["audit"]["unmatched"]),
                        "numeric_sha256": _numeric_digest(rcd_input, ("values",)),
                        "owners_sha256": hashlib.sha256(_canonical(rcd_input["owners"])).hexdigest(),
                        "eligibility_reason_counts": dict(Counter(row["reason"] for row in rcd_input["audit"]["channels"].values())),
                        "model_predictions_invoked": False, "cannot_veto_c1_scientific_verdict": True}
                except Exception as exc:
                    result["rcd_input"] = {"status": "BASELINE_INPUT_CONVERSION_FAILURE_ONLY", "error_type": type(exc).__name__,
                        "model_predictions_invoked": False, "cannot_veto_c1_scientific_verdict": True}
            if name == "c5":
                checks = []
                for cutoff in (180, 360):
                    if cutoff > int(bundle["endpoints"][-1]):
                        continue
                    prefix = c5_bundle(raw, cutoff_seconds=cutoff)
                    truncated = {"audit": raw["audit"]}
                    for modality, field, multiplier in (("metrics", "time", 1), ("traces", "startTimeMillis", 1000), ("logs", "timestamp", 1)):
                        frame = raw[modality]
                        truncated[modality] = None if frame is None else frame.loc[frame[field] < (s0 + cutoff) * multiplier].copy()
                    short = c5_bundle(truncated, cutoff_seconds=cutoff)
                    shared = {key: bundle[key] for key in c5_keys}
                    shared["values"] = bundle["values"][:cutoff // 5]
                    shared["endpoints"] = bundle["endpoints"][:cutoff // 5]
                    shared["service_names"] = bundle["service_names"]
                    equal = _same_numeric(prefix, short, c5_keys) and _same_numeric(prefix, shared, c5_keys)
                    if not equal:
                        raise SourceAdmissionError("Frozen prefix conversion mismatch")
                    checks.append({"cutoff_seconds": cutoff, "exact_numeric_equal": True,
                                   "numeric_sha256": _numeric_digest(prefix, c5_keys)})
                result["c5"]["prefix_replay_checks"] = checks
            # Conversion availability/quality projection, not outcomes.
            quality = bundle["audit"]
            result[name]["conversion_quality"] = {
                "unmatched_metric_keys": sum(len(quality.get(key, {}).get("unmatched_columns", [])) for key in ("metric", "metric_ref", "metric_query")),
                "conflicting_metric_entity_seconds": sum(sum(len(times) for times in quality.get(key, {}).get("conflicting_seconds", {}).values()) for key in ("metric", "metric_ref", "metric_query")),
                "identical_trace_duplicates_collapsed": int(quality.get("identical_trace_duplicates_collapsed", quality.get("duplicates", 0))),
                "nonnull_selected_reference_parents": int(quality.get("graph", {}).get("nonnull_selected_parents", 0)),
                "resolved_selected_reference_parents": int(quality.get("graph", {}).get("resolved_selected_parents", 0)),
                "trace_masked_service_bins": int(quality.get("trace", {}).get("masked_service_bins", 0)),
                "post_freeze_discredited_support_count": len(quality.get("trace", {}).get("post_freeze_discredited_support", [])),
            }
        except Exception as exc:
            result[name] = {"status": "INPUT_UNAVAILABLE_OR_CONVERSION_FAILURE", "error_type": type(exc).__name__,
                            "profile": profile, "case_retained": True}
    if result["protocol_open"] or any(result[name]["status"] != "CONVERTED_ONLY" for name in ("c1", "c5", "integrated")):
        result["case_status"] = "ADMISSION_LIMITED__FAILURE_OR_OPEN_RETAINED"
    result.setdefault("rcd_input", {"status": "INPUT_UNAVAILABLE_AFTER_C1_CONVERSION_FAILURE", "model_predictions_invoked": False,
                                    "cannot_veto_c1_scientific_verdict": True})
    result["no_labels_or_predictions"] = True
    return result


def _acquire_and_audit(state, contract_path, progress):
    binding = _registered_gate(state, contract_path)
    root = state["workspace"] / RAW_RELATIVE
    if root.resolve() != root.absolute():
        raise SourceAdmissionError("Pinned final raw root is aliased")
    root.mkdir(parents=True, exist_ok=True)
    counts, rows = Counter(), []
    physical_failure = None
    for ordinal, case in enumerate(state["cases"]):
        descriptors = tuple(row for row in state["descriptors"] if row["path"].split("/")[0] == case)
        try:
            # Recheck registration before every case; a changed review cannot
            # silently authorize a continuation on unreviewed code.
            _registered_gate(state, contract_path)
            for descriptor in descriptors:
                counts[_download_object(root, descriptor)] += 1
            raw = _read_verified_raw(root, descriptors)
            audit = _audit_raw(raw)
            rows.append({"ordinal": ordinal, "status": "SUCCESS" if audit["case_status"] == "ADMISSION_COMPATIBLE" else "UNAVAILABLE", **audit})
            counts[audit["case_status"]] += 1
            del raw
        except Exception as exc:
            physical_failure = {"failed_ordinal": ordinal, "error_type": type(exc).__name__,
                                "status": "PHYSICAL_SOURCE_FAILURE_STOPPED_NO_CASE_EXCLUSION"}
            rows.append({"ordinal": ordinal, "status": "FAILURE", "case_status": "PHYSICAL_SOURCE_FAILURE", "case_retained": True})
            for pending in range(ordinal + 1, len(state["cases"])):
                rows.append({"ordinal": pending, "status": "UNAVAILABLE", "case_status": "NOT_AUDITED_AFTER_SOURCE_FAILURE", "case_retained": True})
            break
        if progress is not None:
            progress({"audited_cases": ordinal + 1, "planned_cases": 60,
                      "verified_objects": counts["DOWNLOADED_VERIFIED"] + counts["REUSED_VERIFIED"],
                      "limited_cases": counts["ADMISSION_LIMITED__FAILURE_OR_OPEN_RETAINED"]})
    return {"schema": "TD13-G-TELEMETRY-ADMISSION-v1", "scope": "ENTRY_RAW_ADMISSION",
            "status": "BLOCKED_PHYSICAL_SOURCE_FAILURE" if physical_failure else
                      "PASS_TELEMETRY_ADMISSION" if counts["ADMISSION_LIMITED__FAILURE_OR_OPEN_RETAINED"] == 0 else
                      "PASS_BYTES_WITH_CONVERSION_LIMITATIONS",
            **binding, "planned_cases": 60, "planned_objects": 180,
            "descriptor_sha256": DESCRIPTOR_SHA256, "declared_bytes": DECLARED_BYTES,
            "opaque_roster_sha256": ROSTER_SHA256,
            "actual_counts": dict(counts), "case_audits": rows,
            "physical_failure": physical_failure,
            "audit_sha256": hashlib.sha256(_canonical(rows)).hexdigest(),
            "safety": {"telemetry_only": True, "metadata_projection": list(PROJECTION),
                       "final_tau_read": False, "labels_answers_outcomes_read": False,
                       "prediction_functions_invoked": False, "case_ids_paths_disclosed": False},
            "limitations": ["Declared label-free protocol window is a conversion probe, not actual tau validation.",
                            "Task F remains development-qualified; this is separate G raw compatibility evidence.",
                            "Event-time replay does not certify arrival-time streaming or healthy-state ground truth.",
                            "Ordinary caller boundary assumes trusted runtime and filesystem; no efficacy/gate approval."]}


def audit_synthetic_fixture(root):
    """Local tiny synthetic Parquets only, permanently nonofficial fixture scope."""
    root = Path(root).resolve()
    cases = [path for path in root.iterdir() if path.is_dir()]
    if not cases or any(not path.name.startswith("synthetic-") for path in cases):
        raise SourceAdmissionError("Fixture root accepts synthetic case directories only")
    audits = []
    for case in sorted(cases):
        descriptors = []
        for modality in ("metrics", "traces", "logs"):
            path = _exact_local_path(root, f"{_case_component(case.name)}/{modality}.parquet")
            if path.is_file():
                descriptors.append({"path": f"{case.name}/{modality}.parquet", "bytes": path.stat().st_size,
                                    "sha256": _sha256(path)})
        if not any(row["path"].endswith("metrics.parquet") for row in descriptors) or not any(row["path"].endswith("traces.parquet") for row in descriptors):
            raise SourceAdmissionError("Synthetic conversion needs metric and trace source files")
        audits.append({"ordinal": len(audits), **_audit_raw(_read_verified_raw(root, tuple(descriptors)))})
    return {"scope": "SYNTHETIC_DEVELOPMENT_FIXTURE_ONLY", "case_audits": audits,
            "status": "FIXTURE_EXECUTED", "official_admission": False}


def _bind_issued_boundaries():
    build, execute = _build_plan, _acquire_and_audit
    plans: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()
    admissions: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()

    def issued_plan(handle):
        if type(handle) is not SourcePlan:
            raise SourceAdmissionError("Exact issued SourcePlan type required")
        try:
            return plans[handle]
        except (KeyError, TypeError):
            raise SourceAdmissionError("Source plan was not issued by this controller") from None

    def plan_source(workspace, project, api=None):
        state = build(workspace, project, api)
        handle = SourcePlan()
        plans[handle] = state
        return handle

    def plan_summary(handle):
        return copy.deepcopy(issued_plan(handle)["summary"])

    def acquire_and_audit(plan, contract_path, progress=None):
        state = issued_plan(plan)
        if state["scope"] != "OFFICIAL_TELEMETRY_PLAN":
            raise SourceAdmissionError("Injected API fixture cannot acquire or admit final telemetry")
        receipt = execute(state, contract_path, progress)
        handle = SourceAdmission()
        admissions[handle] = copy.deepcopy(receipt)
        return handle

    def require_issued_admission(handle):
        if type(handle) is not SourceAdmission:
            raise SourceAdmissionError("Exact issued SourceAdmission type required")
        try:
            return copy.deepcopy(admissions[handle])
        except (KeyError, TypeError):
            raise SourceAdmissionError("Raw admission was not issued by trusted source execution") from None

    return plan_source, plan_summary, acquire_and_audit, require_issued_admission


plan_source, _plan_summary, acquire_and_audit, require_issued_admission = _bind_issued_boundaries()
del _bind_issued_boundaries, _build_plan, _acquire_and_audit


__all__ = ["SourceAdmissionError", "SourcePlan", "SourceAdmission", "plan_source",
           "acquire_and_audit", "require_issued_admission", "audit_synthetic_fixture"]
