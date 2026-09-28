"""Trusted controller-side numeric process bridge and immutable exact cache.

This module owns process paths and cache provenance. The child entry point is
worker.py and never imports this module. Source labels/paths may remain in a
controller's separate manifest, never in its worker message or model feature.
The process shares OS account permissions: this is not a hostile-code sandbox.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import threading

import numpy as np

from scripts.task_e.worker import (MAX_WIRE_BYTES, ProtocolError, _read_exact,
                                  decode_message, encode_message, validate_request)


class WorkerError(RuntimeError):
    pass


class CacheIdentityError(ValueError):
    pass


class NumericWorker:
    """Persistent dedicated child; no labels/raw files are process arguments.

    A request is validated here and independently in the child. Transport uses
    JSON plus numeric NPZ arrays with allow_pickle=False. ``pid`` and stderr are
    controller diagnostics, not model input. Each session admits one prefix grid
    but can fit many G/L/ALL, MT/MTL and lambda states on its identical warmup.
    """

    def __init__(self, *, timeout_seconds=300, python_executable=None, workspace=None):
        self.timeout_seconds = float(timeout_seconds)
        if not np.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ValueError("A positive finite worker timeout is required")
        executable = str(python_executable or sys.executable)
        root = Path(workspace) if workspace is not None else Path(__file__).resolve().parents[2]
        env = dict(os.environ)
        # Numeric BLAS threads are fixed for predictable per-worker resources.
        env.update(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
        options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
        self.process = subprocess.Popen([executable, "-B", "-u", "-m", "scripts.task_e.worker"],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, cwd=root, env=env, **options)
        self.pid = self.process.pid
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="numeric-worker-reply")
        self._stderr = bytearray()
        self._closed = False
        self._lock = threading.Lock()
        self._drain = threading.Thread(target=self._drain_errors, daemon=True)
        self._drain.start()

    def _drain_errors(self):
        for block in iter(lambda: self.process.stderr.read(4096), b""):
            self._stderr.extend(block)
            if len(self._stderr) > 65536:
                del self._stderr[:-65536]

    @property
    def stderr(self):
        return bytes(self._stderr).decode("utf-8", errors="replace")

    def _receive(self):
        header = _read_exact(self.process.stdout, 8)
        size = struct.unpack("!Q", header)[0]
        if size > MAX_WIRE_BYTES:
            raise WorkerError("Child output exceeds declared wire bound")
        return decode_message(_read_exact(self.process.stdout, size))

    def request(self, message):
        validate_request(message)
        if self._closed:
            raise WorkerError("Worker is closed")
        payload = encode_message(message)
        with self._lock:
            if self.process.poll() is not None:
                raise WorkerError(f"Worker exited: {self.process.returncode}; {self.stderr}")
            try:
                self.process.stdin.write(struct.pack("!Q", len(payload)))
                self.process.stdin.write(payload)
                self.process.stdin.flush()
                future = self._pool.submit(self._receive)
                response = future.result(timeout=self.timeout_seconds)
            except FutureTimeout as exc:
                self.process.kill()
                self.process.wait()
                raise WorkerError("Numeric worker timed out; preserve this failed run") from exc
            except (BrokenPipeError, EOFError) as exc:
                raise WorkerError(f"Numeric pipe failed; {self.stderr}") from exc
        if not isinstance(response, dict) or not response.get("ok"):
            raise WorkerError(f"{response.get('error_type', 'WorkerError')}: {response.get('error', 'Malformed response')}")
        return response["result"]

    def ping(self):
        return self.request({"op": "ping"})

    def fit_c5(self, warmup, adj, channel_types, fit_service_mask, configs):
        return self.request({"op": "fit_c5", "warmup": warmup, "adj": adj,
                             "channel_types": channel_types, "fit_service_mask": fit_service_mask,
                             "configs": configs})

    def score_c5(self, current_bin, bin_index):
        return self.request({"op": "score_c5", "values": current_bin, "bin_index": bin_index})

    def c1(self, ref, query, adj, channel_types, local_config, rank_configs=None):
        return self.request({"op": "c1", "ref": ref, "query": query, "adj": adj,
                             "channel_types": channel_types, "local_config": local_config,
                             "rank_configs": [] if rank_configs is None else rank_configs})

    def rank(self, local, adj, configs):
        """2D adjacency returns [config]; 3D graph batch returns [graph][config]."""
        return self.request({"op": "rank", "local": local, "adj": adj, "configs": configs})

    def close(self):
        if self._closed:
            return
        try:
            if self.process.poll() is None:
                self.request({"op": "close"})
                self.process.wait(timeout=min(10., self.timeout_seconds))
        except Exception:
            if self.process.poll() is None:
                self.process.kill()
                self.process.wait()
        finally:
            self._closed = True
            self._drain.join(timeout=2.)
            for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
                stream.close()
            self._pool.shutdown(wait=True, cancel_futures=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()


def _canonical(value):
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                          separators=(",", ":")).encode("utf-8")
    except (ValueError, TypeError) as exc:
        raise CacheIdentityError("Cache identity must be finite canonical JSON") from exc


def _hash(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def cache_identity(*, source_hashes, td_hash, code_hashes, config, profile, cutoff):
    """Explicit provenance and cutoff, never a reusable full-case-only key.

    source_hashes records each declared modality as SHA256 or MISSING/CORRUPT.
    cutoff is relative: integer endpoint or a numeric window descriptor list.
    Every entry stays controller-side; it is not sent to the numeric child.
    """
    if not _hash(td_hash):
        raise CacheIdentityError("Valid TD SHA256 required")
    if not isinstance(source_hashes, dict) or not source_hashes or any(
            not isinstance(k, str) or not (_hash(v) or v in ("MISSING", "CORRUPT"))
            for k, v in source_hashes.items()):
        raise CacheIdentityError("Explicit source hashes/absence markers required")
    if not isinstance(code_hashes, dict) or not code_hashes or any(
            not isinstance(k, str) or not _hash(v) for k, v in code_hashes.items()):
        raise CacheIdentityError("Explicit code hashes required")
    if not isinstance(profile, str) or not profile or any(x in profile for x in ("/", "\\", ":")):
        raise CacheIdentityError("Explicit separate cache profile required")
    if not isinstance(config, dict):
        raise CacheIdentityError("Explicit complete configuration required")
    cutoffs = cutoff if isinstance(cutoff, list) else [cutoff]
    if not cutoffs or any(type(x) is not int or x < 0 for x in cutoffs):
        raise CacheIdentityError("Explicit nonnegative relative cutoff/window endpoints required")
    material = {"schema": "TD13-EXACT-NUMERIC-CACHE-v1", "source_hashes": source_hashes,
                "td_sha256": td_hash, "code_hashes": code_hashes, "config": config,
                "profile": profile, "cutoff": cutoff}
    # JSON roundtrip freezes caller-owned dictionaries against later mutation.
    frozen = json.loads(_canonical(material))
    frozen["key"] = hashlib.sha256(_canonical(frozen)).hexdigest()
    return frozen


def _identity_key(identity):
    if not isinstance(identity, dict) or set(identity) != {
            "schema", "source_hashes", "td_sha256", "code_hashes", "config", "profile", "cutoff", "key"}:
        raise CacheIdentityError("Malformed cache identity")
    expected = cache_identity(source_hashes=identity["source_hashes"], td_hash=identity["td_sha256"],
                              code_hashes=identity["code_hashes"], config=identity["config"],
                              profile=identity["profile"], cutoff=identity["cutoff"])
    if identity != expected:
        raise CacheIdentityError("Cache identity checksum/version mismatch")
    return identity["key"]


def _array_manifest(arrays):
    if not isinstance(arrays, dict) or not arrays:
        raise CacheIdentityError("Cache requires named numeric arrays")
    manifest = {}
    for key, value in arrays.items():
        if (not isinstance(key, str) or not key or not key.replace("_", "").isalnum() or
                not isinstance(value, np.ndarray) or value.dtype.kind not in "biuf"):
            raise CacheIdentityError("Cache arrays must have simple keys and numeric nonobject dtype")
        if np.isinf(value).any():
            raise CacheIdentityError("Infinite cache values are numerical failures")
        contiguous = np.ascontiguousarray(value)
        manifest[key] = {"dtype": value.dtype.str, "shape": list(value.shape),
                         "sha256": hashlib.sha256(contiguous.tobytes()).hexdigest()}
    return manifest


def read_numeric_cache(directory, identity):
    key = _identity_key(identity)
    root = Path(directory)
    manifest_path, data_path = root / f"{key}.json", root / f"{key}.npz"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("identity") != identity:
        raise CacheIdentityError("Stale source/TD/code/config/profile/cutoff cache identity")
    payload = data_path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != manifest.get("data_sha256"):
        raise CacheIdentityError("Cache byte hash mismatch")
    with np.load(io.BytesIO(payload), allow_pickle=False) as stored:
        arrays = {name: stored[name].copy() for name in stored.files}
    if _array_manifest(arrays) != manifest.get("arrays"):
        raise CacheIdentityError("Cache numeric content manifest mismatch")
    return arrays


def write_numeric_cache(directory, identity, arrays):
    """Write once; same identity with different values is a reproducibility error."""
    key = _identity_key(identity)
    array_manifest = _array_manifest(arrays)
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    manifest_path, data_path = root / f"{key}.json", root / f"{key}.npz"
    if manifest_path.exists() or data_path.exists():
        existing = read_numeric_cache(root, identity)
        if _array_manifest(existing) != array_manifest:
            raise CacheIdentityError("Refusing to overwrite different values under the same cache identity")
        return {"key": key, "data_path": str(data_path), "manifest_path": str(manifest_path), "reused": True}
    stream = io.BytesIO()
    np.savez(stream, **arrays)
    payload = stream.getvalue()
    manifest = {"identity": identity, "arrays": array_manifest,
                "data_sha256": hashlib.sha256(payload).hexdigest(),
                "semantics": "exact cutoff; extension requires verified-source replay"}
    with data_path.open("xb") as output:
        output.write(payload)
    with manifest_path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(_canonical(manifest).decode("utf-8") + "\n")
    return {"key": key, "data_path": str(data_path), "manifest_path": str(manifest_path), "reused": False}
