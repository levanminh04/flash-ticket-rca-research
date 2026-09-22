"""Verify exact raw-sample plan/manifest/file integrity without reading telemetry rows."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(r"D:\Project\flash-ticket-rca-research")
PLAN = ROOT / "audits" / "rcaeval" / "raw-sample-plan.json"
MANIFEST = ROOT / "datasets" / "rcaeval" / "raw-samples" / "raw-download-manifest.json"
OUTPUT = ROOT / "audits" / "rcaeval" / "raw-manifest-verification.json"
ALLOWED = {"metrics.parquet", "logs.parquet", "traces.parquet", "inject_time.txt", "root_cause.txt"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    planned = [item["case"] for item in plan["cases"]]
    recorded = [item["case"] for item in manifest["cases"]]
    details = []
    for case in manifest["cases"]:
        for item in case["files"]:
            local = Path(item["local_path"])
            relative = local.resolve().relative_to((ROOT / "datasets" / "rcaeval" / "raw-samples").resolve())
            basename_allowed = local.name in ALLOWED
            actual_bytes = local.stat().st_size if local.exists() else None
            actual_sha = sha256(local) if local.exists() else None
            details.append(
                {
                    "case": case["case"],
                    "relative_path": str(relative),
                    "exists": local.exists(),
                    "allowed_basename": basename_allowed,
                    "bytes_match": actual_bytes == item["bytes"],
                    "sha256_match": actual_sha == item["sha256"],
                }
            )
    result = {
        "scope": "RAW SAMPLE FINDING — provenance/integrity only",
        "plan_case_count": len(planned),
        "manifest_case_count": len(recorded),
        "same_case_order": planned == recorded,
        "same_dataset_revision": plan["dataset_revision"] == manifest["source"]["revision"],
        "files": details,
        "all_files_exist": all(item["exists"] for item in details),
        "all_files_allowed": all(item["allowed_basename"] for item in details),
        "all_bytes_match": all(item["bytes_match"] for item in details),
        "all_sha256_match": all(item["sha256_match"] for item in details),
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
