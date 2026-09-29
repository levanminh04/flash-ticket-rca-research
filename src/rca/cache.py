"""Exact numeric cache and controller-side provenance for the frozen core.

The cache key binds every source state, the frozen TD, the implementation,
the complete configuration, a distinct profile, and an exact relative cutoff.
It is deliberately not a full-case cache: extending a prefix requires replay
from verified sources.  Nothing in this module accepts evaluator labels.
"""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
from typing import Mapping

import numpy as np


CACHE_SCHEMA = "TD13-EXACT-NUMERIC-CACHE-v1"
_ABSENCE_MARKERS = frozenset(("MISSING", "CORRUPT"))


class CacheIdentityError(ValueError):
    """A cache identity or stored numeric artifact is not exact and reusable."""


def _canonical(value) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (ValueError, TypeError) as exc:
        raise CacheIdentityError("Cache identity must be finite canonical JSON") from exc


def _is_sha256(value) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def file_sha256(path: str | Path) -> str:
    """Hash a controller-owned file without exposing its path to the core."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1_048_576), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value) -> str:
    """Return the digest of finite canonical JSON provenance."""
    return hashlib.sha256(_canonical(value)).hexdigest()


def cache_identity(
    *,
    source_hashes: Mapping[str, str],
    td_hash: str,
    code_hashes: Mapping[str, str],
    config: Mapping[str, object],
    profile: str,
    cutoff: int | list[int] | tuple[int, ...],
) -> dict[str, object]:
    """Construct the exact Task E-compatible cache identity.

    ``source_hashes`` records every declared modality as a lower-case SHA256 or
    the explicit marker ``MISSING``/``CORRUPT``.  ``cutoff`` is relative to the
    admitted observation origin; absolute epochs are not accepted here.
    """
    if not _is_sha256(td_hash):
        raise CacheIdentityError("Valid lower-case TD SHA256 required")
    if not isinstance(source_hashes, Mapping) or not source_hashes or any(
        not isinstance(key, str)
        or not key
        or not (_is_sha256(value) or value in _ABSENCE_MARKERS)
        for key, value in source_hashes.items()
    ):
        raise CacheIdentityError("Explicit source hashes/absence markers required")
    if not isinstance(code_hashes, Mapping) or not code_hashes or any(
        not isinstance(key, str)
        or not key
        or not _is_sha256(value)
        for key, value in code_hashes.items()
    ):
        raise CacheIdentityError("Explicit lower-case code hashes required")
    if (
        not isinstance(profile, str)
        or not profile
        or any(delimiter in profile for delimiter in ("/", "\\", ":"))
    ):
        raise CacheIdentityError("Explicit separate cache profile required")
    if not isinstance(config, Mapping):
        raise CacheIdentityError("Explicit complete configuration required")
    cutoffs = list(cutoff) if isinstance(cutoff, (list, tuple)) else [cutoff]
    if not cutoffs or any(type(value) is not int or value < 0 for value in cutoffs):
        raise CacheIdentityError(
            "Explicit nonnegative relative cutoff/window endpoints required"
        )

    material = {
        "schema": CACHE_SCHEMA,
        "source_hashes": dict(source_hashes),
        "td_sha256": td_hash,
        "code_hashes": dict(code_hashes),
        "config": dict(config),
        "profile": profile,
        "cutoff": list(cutoff) if isinstance(cutoff, tuple) else cutoff,
    }
    # The round trip both validates JSON types and detaches caller-owned maps.
    frozen = json.loads(_canonical(material))
    frozen["key"] = hashlib.sha256(_canonical(frozen)).hexdigest()
    return frozen


def _identity_key(identity: Mapping[str, object]) -> str:
    fields = {
        "schema",
        "source_hashes",
        "td_sha256",
        "code_hashes",
        "config",
        "profile",
        "cutoff",
        "key",
    }
    if not isinstance(identity, Mapping) or set(identity) != fields:
        raise CacheIdentityError("Malformed cache identity")
    expected = cache_identity(
        source_hashes=identity["source_hashes"],
        td_hash=identity["td_sha256"],
        code_hashes=identity["code_hashes"],
        config=identity["config"],
        profile=identity["profile"],
        cutoff=identity["cutoff"],
    )
    if dict(identity) != expected:
        raise CacheIdentityError("Cache identity checksum/version mismatch")
    return str(identity["key"])


def _array_manifest(arrays: Mapping[str, np.ndarray]) -> dict[str, object]:
    if not isinstance(arrays, Mapping) or not arrays:
        raise CacheIdentityError("Cache requires named numeric arrays")
    manifest: dict[str, object] = {}
    for key, value in arrays.items():
        if (
            not isinstance(key, str)
            or not key
            or not key.replace("_", "").isalnum()
            or not isinstance(value, np.ndarray)
            or value.dtype.kind not in "biuf"
        ):
            raise CacheIdentityError(
                "Cache arrays must have simple keys and numeric nonobject dtype"
            )
        if np.isinf(value).any():
            raise CacheIdentityError("Infinite cache values are numerical failures")
        contiguous = np.ascontiguousarray(value)
        manifest[key] = {
            "dtype": value.dtype.str,
            "shape": list(value.shape),
            "sha256": hashlib.sha256(contiguous.tobytes()).hexdigest(),
        }
    return manifest


def read_numeric_cache(
    directory: str | Path, identity: Mapping[str, object]
) -> dict[str, np.ndarray]:
    """Read and verify an exact numeric cache entry with pickle disabled."""
    key = _identity_key(identity)
    root = Path(directory)
    manifest_path = root / f"{key}.json"
    data_path = root / f"{key}.npz"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("identity") != dict(identity):
        raise CacheIdentityError(
            "Stale source/TD/code/config/profile/cutoff cache identity"
        )
    payload = data_path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != manifest.get("data_sha256"):
        raise CacheIdentityError("Cache byte hash mismatch")
    with np.load(io.BytesIO(payload), allow_pickle=False) as stored:
        arrays = {name: stored[name].copy() for name in stored.files}
    if _array_manifest(arrays) != manifest.get("arrays"):
        raise CacheIdentityError("Cache numeric content manifest mismatch")
    return arrays


def write_numeric_cache(
    directory: str | Path,
    identity: Mapping[str, object],
    arrays: Mapping[str, np.ndarray],
) -> dict[str, object]:
    """Write once; different values under one identity are never overwritten."""
    key = _identity_key(identity)
    array_manifest = _array_manifest(arrays)
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / f"{key}.json"
    data_path = root / f"{key}.npz"
    if manifest_path.exists() or data_path.exists():
        existing = read_numeric_cache(root, identity)
        if _array_manifest(existing) != array_manifest:
            raise CacheIdentityError(
                "Refusing to overwrite different values under the same cache identity"
            )
        return {
            "key": key,
            "data_path": str(data_path),
            "manifest_path": str(manifest_path),
            "reused": True,
        }

    stream = io.BytesIO()
    np.savez(stream, **arrays)
    payload = stream.getvalue()
    manifest = {
        "identity": dict(identity),
        "arrays": array_manifest,
        "data_sha256": hashlib.sha256(payload).hexdigest(),
        "semantics": "exact cutoff; extension requires verified-source replay",
    }
    with data_path.open("xb") as output:
        output.write(payload)
    with manifest_path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(_canonical(manifest).decode("utf-8") + "\n")
    return {
        "key": key,
        "data_path": str(data_path),
        "manifest_path": str(manifest_path),
        "reused": False,
    }


# Readable public aliases; the Task E names remain available for equivalence.
load_numeric_cache = read_numeric_cache
save_numeric_cache = write_numeric_cache


__all__ = [
    "CACHE_SCHEMA",
    "CacheIdentityError",
    "cache_identity",
    "canonical_sha256",
    "file_sha256",
    "load_numeric_cache",
    "read_numeric_cache",
    "save_numeric_cache",
    "write_numeric_cache",
]
