from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import MappingProxyType

import numpy as np


W = Path(__file__).resolve().parents[2]
P = Path(r"D:\Project\flash-ticket-platform")
MANIFEST = W / "configs" / "task-f-td13-frozen-release-v2.json"
HANDLE = "96538c0c0d6a11d8"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def code_identity():
    return {path.name: sha(path) for path in sorted((W / "src" / "rca").glob("*.py"))}


def pipeline():
    from rca import FrozenRcaPipeline

    return FrozenRcaPipeline.from_manifest(MANIFEST, code_identity=code_identity())


def qualified_adapter():
    from rca import QualifiedTelemetryAdapter

    return QualifiedTelemetryAdapter.from_manifest(MANIFEST, workspace_root=W)


def c1_numeric_path(handle=HANDLE):
    return (
        W
        / "results"
        / "task-e"
        / "e27-019-development-loader-audit"
        / "intermediates"
        / handle
        / "c1_primary.npz"
    )


def c5_numeric_path(handle=HANDLE):
    return (
        W
        / "results"
        / "task-e"
        / "e27-035-c5-development-full"
        / "predictions"
        / "primary"
        / handle
        / "numeric-input.npz"
    )


def c1_observation(handle=HANDLE, *, node_ids=None):
    from rca.observation import C1Observation

    path = c1_numeric_path(handle)
    with np.load(path, allow_pickle=False) as stored:
        ref = stored["ref"].copy()
        query = stored["query"].copy()
        adjacency = stored["adj"].copy()
        channel_types = tuple(stored["channel_types"])
    nodes = len(ref)
    identities = tuple(f"n{index:02d}" for index in range(nodes)) if node_ids is None else tuple(node_ids)
    return C1Observation(
        handle,
        ref,
        query,
        channel_types,
        adjacency,
        identities,
        MappingProxyType({"numeric": sha(path)}),
        MappingProxyType({"reference_only": True}),
        MappingProxyType({"profile": "TD12-C1-MT"}),
        MappingProxyType({}),
    )


def c5_observation(handle=HANDLE, *, node_ids=None, values=None):
    from rca.observation import C5Observation

    path = c5_numeric_path(handle)
    with np.load(path, allow_pickle=False) as stored:
        all_values = stored["values"].copy() if values is None else np.asarray(values).copy()
        adjacency = stored["adj"].copy()
        channel_types = tuple(stored["channel_types"])
        fit_mask = stored["fit_service_mask"].copy()
        endpoints = stored["endpoints"].copy()
    nodes = all_values.shape[1]
    identities = tuple(f"n{index:02d}" for index in range(nodes)) if node_ids is None else tuple(node_ids)
    return C5Observation(
        handle,
        all_values[:36],
        all_values[36:],
        channel_types,
        adjacency,
        fit_mask,
        identities,
        endpoints[36:],
        MappingProxyType({"numeric": sha(path)}),
        MappingProxyType({"fit_graph_frozen": True}),
        MappingProxyType({"profile": "TD13-C5-EVENT-TIME"}),
        MappingProxyType({}),
    )


def synthetic_c1():
    from rca.observation import C1Observation

    ref = np.ones((4, 3, 5), dtype=np.float64)
    query = ref.copy()
    query[0, 0] = 3.0
    query[1, 1] = 2.0
    ref[:, 1] = np.arange(1, 6)
    query[:, 1] = np.arange(2, 7)
    ref[:, 2] = 0.0
    query[:, 2] = 0.0
    adjacency = np.array(
        [[0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
        dtype=bool,
    )
    return C1Observation(
        "synthetic-c1",
        ref,
        query,
        (0, 1, 2),
        adjacency,
        ("a", "b", "c", "d"),
        MappingProxyType({"fixture": "a" * 64}),
        MappingProxyType({"reference_only": True}),
        MappingProxyType({"fixture": True}),
        MappingProxyType({}),
    )


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))
