"""Fetch the one pre-scoped RE2-TT multimodal case for Task B2B.

The script accepts only the three objects listed in the accompanying scope file,
validates the immutable dataset revision and official LFS hashes, and never
modifies the original six-case raw-download manifest.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download


ROOT = Path(r"D:\Project\flash-ticket-rca-research")
RAW_ROOT = ROOT / "datasets" / "rcaeval" / "raw-samples"
OUTPUT = ROOT / "audits" / "rcaeval" / "b2b-re2tt-multimodal-download-manifest.json"
REPO_ID = "phamquiluan/RCAEval"
REVISION = "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
CASE = "re2tt_ts-auth-service_cpu_2"
EXPECTED = {
    f"{CASE}/logs.parquet": {
        "bytes": 3_351_283,
        "lfs_sha256": "0cc2ed5ff13a20cf776a42d9d4c3914981afe025fbaa69109ac652d9c7502537",
    },
    f"{CASE}/metrics.parquet": {
        "bytes": 933_362,
        "lfs_sha256": "16597725c18258ce0a3bdedc1833fb52ad6638fdc5068e944dce23c1bbde6d93",
    },
    f"{CASE}/traces.parquet": {
        "bytes": 20_050_343,
        "lfs_sha256": "3d704979b684c5450a3ddcd48bb91a71d07c485edc878a2969b04ff152b5857c",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_local(path: Path, expected: dict[str, object]) -> dict[str, object]:
    actual_size = path.stat().st_size
    actual_sha256 = sha256(path)
    if actual_size != expected["bytes"]:
        raise RuntimeError(f"Unexpected byte size for {path}: {actual_size}")
    if actual_sha256 != expected["lfs_sha256"]:
        raise RuntimeError(f"Unexpected SHA-256 for {path}: {actual_sha256}")
    return {"bytes": actual_size, "sha256": actual_sha256}


def main() -> None:
    api = HfApi()
    if api.dataset_info(REPO_ID, revision=REVISION).sha != REVISION:
        raise RuntimeError("Pinned dataset revision did not resolve exactly")

    remote_info = api.get_paths_info(
        REPO_ID,
        paths=sorted(EXPECTED),
        repo_type="dataset",
        revision=REVISION,
    )
    if {item.path for item in remote_info} != set(EXPECTED):
        raise RuntimeError("Official path inventory differs from Task B2B scope")
    for item in remote_info:
        expected = EXPECTED[item.path]
        if item.size != expected["bytes"] or item.lfs is None:
            raise RuntimeError(f"Unexpected official metadata for {item.path}")
        if item.lfs.get("sha256") != expected["lfs_sha256"]:
            raise RuntimeError(f"Unexpected official LFS hash for {item.path}")

    files: list[dict[str, object]] = []
    for remote_path in sorted(EXPECTED):
        local = RAW_ROOT / remote_path
        if not local.exists():
            local = Path(
                hf_hub_download(
                    repo_id=REPO_ID,
                    repo_type="dataset",
                    filename=remote_path,
                    revision=REVISION,
                    local_dir=RAW_ROOT,
                )
            )
        local.resolve().relative_to(RAW_ROOT.resolve())
        verified = verify_local(local, EXPECTED[remote_path])
        files.append(
            {
                "remote_file": remote_path,
                "local_path": str(local),
                "official_lfs_sha256": EXPECTED[remote_path]["lfs_sha256"],
                **verified,
            }
        )

    output = {
        "scope": "RAW SAMPLE FINDING — Task B2B one log-bearing RE2-TT case only",
        "scope_document": str(ROOT / "dataset-audit" / "TASK-B2B-RE2TT-MULTIMODAL-SCOPE.md"),
        "source": {
            "repository": REPO_ID,
            "repository_type": "dataset",
            "url": f"https://huggingface.co/datasets/{REPO_ID}",
            "revision": REVISION,
        },
        "case": CASE,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": files,
        "all_local_hashes_match_official_lfs": True,
    }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
