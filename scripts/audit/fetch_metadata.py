"""Fetch only the RCAEval metadata index from the official Hugging Face dataset.

This script deliberately never uses snapshot_download and never requests case
telemetry.  It pins the download to the immutable dataset revision returned by
the Hugging Face API and records enough provenance to rerun the metadata audit.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download


REPO_ID = "phamquiluan/RCAEval"
REPO_TYPE = "dataset"
FILENAME = "cases.parquet"
DEFAULT_ROOT = Path(r"D:\Project\flash-ticket-rca-research")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument(
        "--revision",
        help="Existing immutable Hugging Face revision to reproduce; omit only for first capture.",
    )
    args = parser.parse_args()
    root = DEFAULT_ROOT
    metadata_dir = root / "datasets" / "rcaeval" / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)

    api = HfApi()
    info = api.dataset_info(REPO_ID, revision=args.revision)
    revision = info.sha
    if not revision:
        raise RuntimeError("Hugging Face did not return an immutable dataset revision")
    if args.revision and revision != args.revision:
        raise RuntimeError(
            f"Requested revision did not resolve exactly: {args.revision} -> {revision}"
        )

    downloaded = Path(
        hf_hub_download(
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            filename=FILENAME,
            revision=revision,
            local_dir=metadata_dir,
        )
    )
    expected = metadata_dir / FILENAME
    if downloaded.resolve() != expected.resolve():
        # Keep the externally visible path deterministic without copying or
        # downloading a second file.  hf_hub_download normally returns expected.
        if expected.exists():
            downloaded = expected
        else:
            raise RuntimeError(f"Unexpected metadata path: {downloaded}")

    manifest = {
        "scope": "METADATA ONLY — no raw case telemetry downloaded",
        "source": {
            "repository": REPO_ID,
            "repository_type": REPO_TYPE,
            "url": f"https://huggingface.co/datasets/{REPO_ID}",
            "revision": revision,
            "file": FILENAME,
        },
        "requested_revision": args.revision,
        "local_file": str(downloaded),
        "bytes": downloaded.stat().st_size,
        "sha256": sha256(downloaded),
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
        },
    }
    (metadata_dir / "metadata-provenance.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
