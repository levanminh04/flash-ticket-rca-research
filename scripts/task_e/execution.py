"""Trusted receipts and lossless numeric artifacts for bounded development."""
from __future__ import annotations
import hashlib
import json
import math
import time
from pathlib import Path
import numpy as np


def plain(value):
    if isinstance(value, np.ndarray):
        return plain(value.tolist())
    if isinstance(value, np.generic):
        return plain(value.item())
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None  # JSON audit only; lossless numeric files preserve NaN masks.
    return value


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(plain(value), stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def save_npz(path, **arrays):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    converted = {k: np.asarray(v) for k, v in arrays.items()}
    if any(a.dtype.hasobject for a in converted.values()):
        raise ValueError('Object arrays are forbidden')
    with path.open('xb') as stream:
        np.savez_compressed(stream, **converted)


def failure(run, stage, case, exc):
    record = {'stage': stage, 'case': case, 'type': type(exc).__name__, 'message': str(exc)}
    with (Path(run) / 'failures.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + '\n')
    return record


def require_contract(run, stage_fragment=None):
    run = Path(run)
    contract = json.loads((run / 'run-contract.json').read_text(encoding='utf-8'))
    if stage_fragment and stage_fragment not in contract['stage']:
        raise ValueError('Wrong pre-recorded stage')
    return contract


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()
