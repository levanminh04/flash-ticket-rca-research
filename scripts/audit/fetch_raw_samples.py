"""Fetch only the explicitly approved RCAEval raw sample cases in a plan file.

The plan must be created after independent metadata proposals are reconciled.
This downloader rejects any plan that does not pin the official dataset revision
and never uses a suite-level pattern or snapshot download.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download


ROOT = Path(r"D:\Project\flash-ticket-rca-research")
PLAN_PATH = ROOT / "audits" / "rcaeval" / "raw-sample-plan.json"
RAW_ROOT = ROOT / "datasets" / "rcaeval" / "raw-samples"
MANIFEST_PATH = RAW_ROOT / "raw-download-manifest.json"
REPO_ID = "phamquiluan/RCAEval"
REPO_TYPE = "dataset"
ALLOWED_BASENAMES = {
    "metrics.parquet",
    "logs.parquet",
    "traces.parquet",
    "inject_time.txt",
    "root_cause.txt",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    if not PLAN_PATH.exists():
        raise FileNotFoundError(f"Raw sample plan missing: {PLAN_PATH}")
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    if plan.get("repo_id") != REPO_ID or plan.get("repo_type") != REPO_TYPE:
        raise RuntimeError("Plan does not identify the approved official RCAEval source")
    revision = plan.get("dataset_revision")
    cases = plan.get("cases")
    if not isinstance(revision, str) or len(revision) < 7:
        raise RuntimeError("Plan does not pin an immutable dataset revision")
    if not isinstance(cases, list) or len(cases) != 6:
        raise RuntimeError("Initial Task B plan must contain exactly six explicit cases")

    case_ids = [item.get("case") for item in cases]
    if not all(isinstance(case_id, str) and case_id for case_id in case_ids):
        raise RuntimeError("Every planned case needs a non-empty official case ID")
    if len(set(case_ids)) != len(case_ids):
        raise RuntimeError("Raw sample plan contains duplicate case IDs")

    api = HfApi()
    actual_revision = api.dataset_info(REPO_ID, revision=revision).sha
    if actual_revision != revision:
        raise RuntimeError(
            f"Pinned revision did not resolve exactly: requested {revision}, got {actual_revision}"
        )
    remote_files = set(api.list_repo_files(REPO_ID, repo_type=REPO_TYPE, revision=revision))
    RAW_ROOT.mkdir(parents=True, exist_ok=True)

    manifest_cases = []
    for item in cases:
        case_id = item["case"]
        prefix = f"{case_id}/"
        allowed_remote = sorted(
            file
            for file in remote_files
            if file.startswith(prefix) and Path(file).name in ALLOWED_BASENAMES
        )
        if not allowed_remote:
            raise RuntimeError(f"No approved raw files found for planned case {case_id}")

        downloaded_files = []
        for filename in allowed_remote:
            local = Path(
                hf_hub_download(
                    repo_id=REPO_ID,
                    repo_type=REPO_TYPE,
                    filename=filename,
                    revision=revision,
                    local_dir=RAW_ROOT,
                )
            )
            local.resolve().relative_to(RAW_ROOT.resolve())
            downloaded_files.append(
                {
                    "remote_file": filename,
                    "local_path": str(local),
                    "bytes": local.stat().st_size,
                    "sha256": sha256(local),
                }
            )
        manifest_cases.append({"case": case_id, "files": downloaded_files})

    manifest = {
        "scope": "RAW SAMPLE FINDING — six explicitly planned cases only",
        "source": {
            "repository": REPO_ID,
            "repository_type": REPO_TYPE,
            "url": f"https://huggingface.co/datasets/{REPO_ID}",
            "revision": revision,
        },
        "plan_path": str(PLAN_PATH),
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "cases": manifest_cases,
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
