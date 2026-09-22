"""Audit the reproducibility and metadata-level data quality of RCAEval.

This script reads only the already selected ``cases.parquet`` metadata index.
It never enumerates or downloads per-case telemetry.  The optional remote check
uses the official Hugging Face dataset API only to verify the pinned revision
and the presence of the metadata file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq


ROOT = Path(r"D:\Project\flash-ticket-rca-research")
METADATA_DIR = ROOT / "datasets" / "rcaeval" / "metadata"
PARQUET_PATH = METADATA_DIR / "cases.parquet"
MANIFEST_PATH = METADATA_DIR / "metadata-provenance.json"
OUTPUT_PATH = ROOT / "audits" / "rcaeval" / "subagent-g-reproducibility-evidence.json"
REQUIRED_PACKAGES = ("pandas", "pyarrow", "huggingface_hub", "fsspec")
AUDIT_SCRIPT_DIR = ROOT / "scripts" / "audit"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def package_versions() -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for package in REQUIRED_PACKAGES:
        try:
            result[package] = version(package)
        except PackageNotFoundError:
            result[package] = None
    return result


def audit_script_hashes() -> dict[str, str]:
    names = ("fetch_metadata.py", "profile_metadata.py", "audit_reproducibility.py")
    return {
        name: sha256(AUDIT_SCRIPT_DIR / name)
        for name in names
        if (AUDIT_SCRIPT_DIR / name).exists()
    }


def count_mask(mask: pd.Series) -> int:
    return int(mask.fillna(False).sum())


def string_quality(frame: pd.DataFrame, column: str) -> dict[str, int] | None:
    if column not in frame.columns:
        return None
    values = frame[column]
    if not pd.api.types.is_string_dtype(values.dtype):
        return {"not_string_dtype": int(len(values))}
    return {
        "null": int(values.isna().sum()),
        "empty": count_mask(values.eq("")),
        "whitespace_only": count_mask(values.str.fullmatch(r"\s*", na=False)),
        "leading_or_trailing_whitespace": count_mask(values.ne(values.str.strip()).fillna(False)),
    }


def remote_check(manifest: dict[str, Any]) -> dict[str, Any]:
    source = manifest.get("source", {})
    repo_id = source.get("repository")
    revision = source.get("revision")
    if not repo_id or not revision:
        return {"status": "NOT_RUN", "reason": "manifest lacks repository or revision"}
    try:
        from huggingface_hub import HfApi

        info = HfApi().dataset_info(
            repo_id=repo_id,
            revision=revision,
            files_metadata=True,
        )
        sibling_names = sorted(
            sibling.rfilename for sibling in (info.siblings or []) if sibling.rfilename
        )
        return {
            "status": "VERIFIED",
            "repository": repo_id,
            "requested_revision": revision,
            "resolved_revision": info.sha,
            "revision_matches_manifest": info.sha == revision,
            "metadata_file_present": source.get("file") in sibling_names,
            "metadata_file": source.get("file"),
            "remote_file_count": len(sibling_names),
        }
    except Exception as exc:  # Network and remote-service errors remain evidence.
        return {
            "status": "UNKNOWN",
            "repository": repo_id,
            "requested_revision": revision,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-remote",
        action="store_true",
        help="Run only local integrity and data-quality checks.",
    )
    args = parser.parse_args()

    if not PARQUET_PATH.exists():
        raise FileNotFoundError(f"Missing metadata file: {PARQUET_PATH}")
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Missing provenance manifest: {MANIFEST_PATH}")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    actual_size = PARQUET_PATH.stat().st_size
    actual_hash = sha256(PARQUET_PATH)
    table_metadata = pq.ParquetFile(PARQUET_PATH).metadata
    frame = pd.read_parquet(PARQUET_PATH)

    time_start = frame["time_start"]
    time_end = frame["time_end"]
    inject_time = frame["inject_time"]
    time_span = time_end - time_start
    expected_case_prefix = frame["suite"].str.lower() + frame["system"].str.lower() + "_"
    expected_case_suffix = "_" + frame["fault"] + "_" + frame["repetition"].astype(str)
    case_prefix_matches = pd.Series(
        [case.startswith(prefix) for case, prefix in zip(frame["case"], expected_case_prefix)],
        index=frame.index,
    )
    case_suffix_matches = pd.Series(
        [case.endswith(suffix) for case, suffix in zip(frame["case"], expected_case_suffix)],
        index=frame.index,
    )
    time_anomaly_mask = (
        inject_time.lt(time_start)
        | inject_time.gt(time_end)
        | inject_time.sub(time_start).ne(frame["normal_timesteps"])
    )

    flag_consistency = {}
    for flag, count_column in (
        ("has_logs", "n_logs"),
        ("has_traces", "n_traces"),
    ):
        if flag in frame.columns and count_column in frame.columns:
            flag_consistency[f"{flag}_does_not_equal_{count_column}_gt_0"] = count_mask(
                frame[flag].ne(frame[count_column].gt(0))
            )

    integrity = {
        "manifest_recorded_bytes": manifest.get("bytes"),
        "actual_bytes": actual_size,
        "bytes_match_manifest": manifest.get("bytes") == actual_size,
        "manifest_recorded_sha256": manifest.get("sha256"),
        "actual_sha256": actual_hash,
        "sha256_matches_manifest": manifest.get("sha256") == actual_hash,
        "manifest_local_path_matches": (
            Path(manifest.get("local_file", "")).resolve() == PARQUET_PATH.resolve()
        ),
        "parquet_rows": table_metadata.num_rows,
        "pandas_rows": int(len(frame)),
        "row_count_matches": table_metadata.num_rows == len(frame),
        "parquet_row_groups": table_metadata.num_row_groups,
        "parquet_created_by": table_metadata.created_by,
    }

    report = {
        "scope": "DATASET-WIDE METADATA FACT — cases.parquet only; no raw telemetry inspected",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "interpreter": {
            "executable": sys.executable,
            "version": sys.version,
            "platform": platform.platform(),
        },
        "required_package_versions": package_versions(),
        "audit_script_sha256": audit_script_hashes(),
        "manifest": manifest,
        "local_integrity": integrity,
        "parquet_schema": str(pq.ParquetFile(PARQUET_PATH).schema_arrow),
        "metadata_quality": {
            "row_count": int(len(frame)),
            "column_count": int(len(frame.columns)),
            "dtypes": {column: str(dtype) for column, dtype in frame.dtypes.items()},
            "null_counts": {column: int(frame[column].isna().sum()) for column in frame.columns},
            "duplicate_case_ids": int(frame["case"].duplicated().sum()),
            "duplicate_full_rows": int(frame.duplicated().sum()),
            "case_identifier_checks": {
                "case_not_matching_suite_system_prefix": count_mask(~case_prefix_matches),
                "case_not_matching_fault_repetition_suffix": count_mask(~case_suffix_matches),
            },
            "string_quality": {
                column: string_quality(frame, column)
                for column in ("case", "dataset", "suite", "system", "fault", "root_cause_service")
            },
            "time_checks": {
                "time_start_not_before_time_end": count_mask(time_start.ge(time_end)),
                "inject_time_before_time_start": count_mask(inject_time.lt(time_start)),
                "inject_time_after_time_end": count_mask(inject_time.gt(time_end)),
                "n_timesteps_nonpositive": count_mask(frame["n_timesteps"].le(0)),
                "normal_timesteps_negative": count_mask(frame["normal_timesteps"].lt(0)),
                "faulty_timesteps_negative": count_mask(frame["faulty_timesteps"].lt(0)),
                "normal_plus_faulty_not_n_timesteps": count_mask(
                    frame["normal_timesteps"].add(frame["faulty_timesteps"]).ne(frame["n_timesteps"])
                ),
                "time_span_plus_one_not_n_timesteps": count_mask(time_span.add(1).ne(frame["n_timesteps"])),
                "inject_minus_start_not_normal_timesteps": count_mask(
                    inject_time.sub(time_start).ne(frame["normal_timesteps"])
                ),
                "anomaly_case_rows": frame.loc[
                    time_anomaly_mask,
                    [
                        "case",
                        "dataset",
                        "fault",
                        "inject_time",
                        "time_start",
                        "time_end",
                        "normal_timesteps",
                        "faulty_timesteps",
                    ],
                ].to_dict(orient="records"),
            },
            "count_checks": {
                "n_metrics_nonpositive": count_mask(frame["n_metrics"].le(0)),
                "n_logs_negative": count_mask(frame["n_logs"].lt(0)),
                "n_traces_negative": count_mask(frame["n_traces"].lt(0)),
                **flag_consistency,
            },
        },
        "remote_revision_check": (
            {"status": "SKIPPED"} if args.skip_remote else remote_check(manifest)
        ),
        "limitations": [
            "This audit does not establish telemetry schemas, per-case file completeness, or case-level hashes.",
            "A successful pinned-revision API response establishes accessibility of the named revision, not a signed archival guarantee.",
            "The fetch script resolves the default dataset revision before recording it; a later rerun without the recorded revision can retrieve a different revision.",
        ],
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
