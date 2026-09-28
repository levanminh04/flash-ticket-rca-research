"""Explicit acquisition of the exact TD12 development telemetry objects only.

Importing this module never contacts a network, downloads, writes, or installs.
``inspect_sources`` is metadata/read-only; ``acquire_development`` must be
called explicitly with an inspected receipt and ``allow_download=True``.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

import pyarrow.parquet as pq

REPO_ID = "phamquiluan/RCAEval"
REVISION = "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
METADATA_SHA256 = "c49a288920dbba2e8e724679a14636d5c7eb2b45426bba14007ef79a6c0ab1bb"
DEV_CELLS = (
    ("ts-auth-service", "cpu"), ("ts-auth-service", "delay"),
    ("ts-order-service", "disk"), ("ts-order-service", "loss"),
    ("ts-route-service", "mem"), ("ts-route-service", "socket"),
    ("ts-train-service", "cpu"), ("ts-train-service", "delay"),
    ("ts-travel-service", "disk"), ("ts-travel-service", "loss"),
)
DEV_IDS = frozenset(f"re2tt_{root}_{fault}_{repeat}"
                    for root, fault in DEV_CELLS for repeat in (1, 2, 3))
NO_LOG_CASE = "re2tt_ts-auth-service_cpu_1"
ALLOWED_PATHS = frozenset(
    f"{case}/{modality}.parquet" for case in DEV_IDS for modality in ("metrics", "traces", "logs")
    if not (case == NO_LOG_CASE and modality == "logs")
)


class AcquisitionError(ValueError):
    """The source identity, object scope, or existing local bytes are invalid."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def development_metadata(metadata_path: str | Path) -> list[dict[str, Any]]:
    """Controller-only exact allowlist from the existing pinned metadata bytes."""
    path = Path(metadata_path)
    if sha256(path) != METADATA_SHA256:
        raise AcquisitionError("Existing metadata differs from the pinned SHA256")
    rows = [row for row in pq.read_table(path).to_pylist() if row["case"] in DEV_IDS]
    if len(rows) != 30 or {r["case"] for r in rows} != DEV_IDS:
        raise AcquisitionError("Pinned metadata does not contain the exact thirty development cases")
    for row in rows:
        if row["dataset"] != "RE2-TT" or not row["has_traces"]:
            raise AcquisitionError("Unexpected development dataset or missing declared trace")
        if bool(row["has_logs"]) != (row["case"] != NO_LOG_CASE):
            raise AcquisitionError("Declared log availability differs from the finite allowlist")
    return sorted(rows, key=lambda row: row["case"])


def _field(value: Any, name: str, default: Any = None) -> Any:
    return value.get(name, default) if isinstance(value, Mapping) else getattr(value, name, default)


def _within(root: Path, remote: str) -> Path:
    if remote not in ALLOWED_PATHS:
        raise AcquisitionError(f"Unapproved remote telemetry path: {remote}")
    target = (root / remote).resolve()
    target.relative_to(root.resolve())
    return target


def _local_receipt(path: Path, expected_bytes: int, expected_sha: str) -> dict[str, Any]:
    if not path.is_file():
        return {"path": str(path), "present": False, "verified": False}
    actual_bytes = path.stat().st_size
    actual_sha = sha256(path)
    return {"path": str(path), "present": True, "bytes": actual_bytes, "sha256": actual_sha,
            "verified": actual_bytes == expected_bytes and actual_sha == expected_sha}


def _separate_roots(originals: Path, destination: Path) -> None:
    """New telemetry cannot be written into or above preserved sample storage."""
    if originals == destination or originals in destination.parents or destination in originals.parents:
        raise AcquisitionError("Development output and preserved original storage must be separate roots")


def inspect_sources(metadata_path: str | Path, existing_root: str | Path,
                    destination_root: str | Path, *, api: Any = None) -> dict[str, Any]:
    """Read official pinned object metadata before a download job; no file writes.

    Neither raw rows nor non-development telemetry objects are requested.
    Existing original/B2B files are verified in place and are never overwritten.
    """
    rows = development_metadata(metadata_path)
    if api is None:
        from huggingface_hub import HfApi
        api = HfApi()
    info = api.dataset_info(REPO_ID, revision=REVISION)
    if _field(info, "sha") != REVISION:
        raise AcquisitionError("Official dataset revision did not resolve exactly")
    remote_info = api.get_paths_info(REPO_ID, paths=sorted(ALLOWED_PATHS),
                                     repo_type="dataset", revision=REVISION)
    by_path = {_field(item, "path"): item for item in remote_info}
    if set(by_path) != ALLOWED_PATHS:
        raise AcquisitionError("Official object inventory differs from the exact development allowlist")
    originals = Path(existing_root).resolve()
    destination = Path(destination_root).resolve()
    _separate_roots(originals, destination)
    objects = []
    for remote in sorted(ALLOWED_PATHS):
        item = by_path[remote]
        lfs = _field(item, "lfs")
        checksum = _field(lfs, "sha256")
        size = _field(item, "size")
        if not isinstance(checksum, str) or len(checksum) != 64 or not isinstance(size, int) or size <= 0:
            raise AcquisitionError(f"Missing official LFS identity for {remote}")
        if any(c not in "0123456789abcdef" for c in checksum.lower()):
            raise AcquisitionError(f"Invalid official LFS SHA256 for {remote}")
        candidates = [_local_receipt(_within(originals, remote), size, checksum),
                      _local_receipt(_within(destination, remote), size, checksum)]
        bad = [r for r in candidates if r["present"] and not r["verified"]]
        if bad:
            raise AcquisitionError(f"Existing local bytes differ from official object; preserve and review: {bad}")
        reuse = next((r for r in candidates if r["verified"]), None)
        objects.append({"remote_path": remote, "bytes": size, "official_lfs_sha256": checksum,
                        "blob_id": _field(item, "blob_id"), "local_candidates": candidates,
                        "reuse_path": reuse["path"] if reuse else None})
    return {"receipt_version": "TD12-development-source-v1", "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": {"repo_id": REPO_ID, "repo_type": "dataset", "revision": REVISION,
                       "url": f"https://huggingface.co/datasets/{REPO_ID}/tree/{REVISION}"},
            "metadata": {"path": str(Path(metadata_path).resolve()), "sha256": METADATA_SHA256},
            "development_ids": [r["case"] for r in rows], "planned_objects": len(ALLOWED_PATHS),
            "existing_root": str(originals), "destination_root": str(destination), "objects": objects,
            "reused_objects": sum(bool(o["reuse_path"]) for o in objects),
            "missing_objects": sum(not o["reuse_path"] for o in objects),
            "missing_bytes": sum(o["bytes"] for o in objects if not o["reuse_path"]),
            "no_answer_or_injection_files_requested": True}


def acquire_development(source_receipt: Mapping[str, Any], *, allow_download: bool = False,
                        download: Callable[..., str] | None = None) -> dict[str, Any]:
    """Explicit raw acquisition using a previously frozen official source receipt.

    The caller must persist source/config/run authorization before invoking this.
    This function returns a receipt; the caller owns its immutable persistence.
    """
    if not allow_download:
        raise AcquisitionError("Raw acquisition requires explicit allow_download=True")
    source = source_receipt.get("source", {})
    if source.get("repo_id") != REPO_ID or source.get("revision") != REVISION:
        raise AcquisitionError("Receipt source is not the pinned official dataset")
    if set(source_receipt.get("development_ids", [])) != DEV_IDS:
        raise AcquisitionError("Receipt does not carry the exact development scope")
    objects = list(source_receipt.get("objects", []))
    if len(objects) != len(ALLOWED_PATHS) or {o.get("remote_path") for o in objects} != ALLOWED_PATHS:
        raise AcquisitionError("Receipt telemetry objects differ from the finite allowlist")
    destination = Path(source_receipt["destination_root"]).resolve()
    originals = Path(source_receipt["existing_root"]).resolve()
    _separate_roots(originals, destination)
    if download is None:
        from huggingface_hub import hf_hub_download
        download = hf_hub_download
    files = []
    for obj in objects:
        remote = obj["remote_path"]
        size, checksum = obj["bytes"], obj["official_lfs_sha256"]
        target = _within(destination, remote)
        original = _within(originals, remote)
        available = [_local_receipt(original, size, checksum), _local_receipt(target, size, checksum)]
        if any(r["present"] and not r["verified"] for r in available):
            raise AcquisitionError(f"Existing file mismatch; refusing overwrite: {remote}")
        reuse = next((r for r in available if r["verified"]), None)
        if reuse:
            files.append({"remote_path": remote, "disposition": "REUSED_VERIFIED", **reuse})
            continue
        downloaded = Path(download(repo_id=REPO_ID, repo_type="dataset", filename=remote,
                                   revision=REVISION, local_dir=destination)).resolve()
        downloaded.relative_to(destination)
        if downloaded != target:
            raise AcquisitionError(f"Downloader returned unexpected location for {remote}")
        verified = _local_receipt(downloaded, size, checksum)
        if not verified["verified"]:
            raise AcquisitionError(f"Downloaded bytes do not match official LFS; preserve failure: {verified}")
        files.append({"remote_path": remote, "disposition": "DOWNLOADED_VERIFIED", **verified})
    return {"receipt_version": "TD12-development-acquisition-v1", "source": dict(source),
            "completed_at_utc": datetime.now(timezone.utc).isoformat(), "files": files,
            "planned_objects": len(ALLOWED_PATHS), "verified_objects": len(files),
            "verified_bytes": sum(r["bytes"] for r in files), "no_final_or_other_dataset_objects": True}
