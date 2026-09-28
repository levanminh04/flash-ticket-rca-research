"""Trusted loader for the exact TD12 RCD adaptation; stdlib only until admitted.

This is controller code, not a numeric worker. It never installs, patches, or
imports the RCAEval framework. An authorized immutable coordinator run contract,
an isolated pinned environment, and source-byte checks precede third-party code.
The returned bare function still needs real qualification; loading is not proof.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import sys
import types
import warnings
from dataclasses import dataclass
from pathlib import Path


RCAEVAL_REVISION = "7600283af1ea5e2e9fff6f07124951d0e989de42"
ORIGINAL_REVISION = "373882c6982db7a999ec1ff99ea54c644a48b409"
PATCH_SHA256 = "472685d2513a47cefce36640d9de3e21769923f85de48f7cf6feec43e2ae8838"
ORIGINAL_SHA256 = "e6a7df13e4f3256b45da0713b07b6bf41fb9178333e31397701ab2f08872f628"
PATCHED_SHA256 = "036946005d53e5c6a11e2a4b5c099f2194ab104f15df8fd74d74668827278393"
CUSTOM_FILES = (
    "utils/PCUtils/SkeletonDiscovery.py",
    "graph/GraphClass.py",
    "utils/Fas.py",
    "search/ConstraintBased/FCI.py",
)
# Runtime/import closure from RCAEval's lock; matplotlib 3.7.1 is an explicit
# Windows/Python3.9 compatibility choice (the upstream lock omits matplotlib).
PINNED_PACKAGES = {
    "causal-learn": "0.1.2.3", "numpy": "1.23.5", "pandas": "2.0.1",
    "scikit-learn": "1.2.2", "scipy": "1.10.1", "networkx": "2.5",
    "tqdm": "4.65.0", "matplotlib": "3.7.1", "contourpy": "1.0.7",
    "cycler": "0.11.0", "fonttools": "4.39.4", "kiwisolver": "1.4.4",
    "packaging": "23.1", "Pillow": "9.5.0", "pyparsing": "3.0.9",
    "python-dateutil": "2.8.2", "six": "1.16.0", "pytz": "2023.3",
    "tzdata": "2023.3", "joblib": "1.2.0", "threadpoolctl": "3.1.0",
    "decorator": "5.1.1", "colorama": "0.4.6", "pydot": "1.4.2",
    "graphviz": "0.20.1", "statsmodels": "0.14.0", "patsy": "0.5.3",
    "importlib-resources": "5.12.0", "zipp": "3.15.0",
}


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _check_hash(path, expected):
    observed = file_sha256(path)
    if observed != expected:
        raise RuntimeError("Source hash mismatch: " + str(path))
    return observed


def require_run_contract(run_dir, workspace=None):
    """Admit only explicit qualification/development contracts for this source.

    The coordinator supplies config.rcd_runtime_qualification_authorized=true
    only after the C5 resume gate. Its config also pins the manifest hash, and
    source_files pins this loader and the comparator. This flag is scope evidence,
    not a substitute for the coordinator's amendment/review/fixture receipts.
    """
    workspace = Path(workspace or Path(__file__).resolve().parents[2]).resolve()
    run_dir = Path(run_dir).resolve()
    run_dir.relative_to(workspace / "results" / "task-e")
    contract = json.loads((run_dir / "run-contract.json").read_text(encoding="utf-8-sig"))
    config = contract.get("config", {})
    if config.get("rcd_runtime_qualification_authorized") is not True:
        raise RuntimeError("Explicit coordinator RCD execution authorization required")
    if contract.get("run_id") != run_dir.name:
        raise RuntimeError("Run-contract identity mismatch")
    _check_hash(Path(contract["td"]["path"]), contract["td"]["sha256"])
    records = {str(Path(row["path"]).resolve()): row["sha256"]
               for row in contract.get("source_files", [])}
    for relative in ("scripts/task_e/rcd_runtime.py", "scripts/task_e/comparators.py"):
        source = workspace / relative
        if str(source) not in records:
            raise RuntimeError("Run contract omitted owned RCD source: " + relative)
        _check_hash(source, records[str(source)])
    manifest_path = workspace / "baselines/task-e-source-manifest.json"
    expected_manifest = config.get("rcd_source_manifest_sha256")
    if not isinstance(expected_manifest, str) or len(expected_manifest) != 64:
        raise RuntimeError("Run contract must pin RCD source manifest")
    _check_hash(manifest_path, expected_manifest)
    return workspace, contract


def verify_pinned_sources(workspace):
    """Read-only byte/provenance validation; no numeric dependency imports."""
    workspace = Path(workspace).resolve()
    manifest_path = workspace / "baselines/task-e-source-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if manifest["authoritative_rcd_revision"] != RCAEVAL_REVISION:
        raise RuntimeError("Wrong authoritative RCD revision")
    if manifest["original_rcd_lineage_revision"] != ORIGINAL_REVISION:
        raise RuntimeError("Wrong original RCD lineage revision")
    records = {row["local_path"]: row for row in manifest["files"]}
    upstream = workspace / "baselines/upstream" / ("rcaeval-" + RCAEVAL_REVISION)
    required = ["RCAEval/e2e/rcd.py", "RCAEval/io/time_series.py",
                "requirements_rcd.lock", "script/link.sh", "LICENSES/LICENSE-RCD",
                "lib/causallearn/LICENSE"]
    required += ["lib/causallearn/" + relative for relative in CUSTOM_FILES]
    checked = []
    for relative in required:
        path = upstream / relative
        key = path.relative_to(workspace).as_posix()
        record = records[key]
        if record["revision"] != RCAEVAL_REVISION:
            raise RuntimeError("Unpinned source record: " + key)
        checked.append({"path": key, "sha256": _check_hash(path, record["sha256"])})
    patch = workspace / "baselines/rcd-td12.patch"
    original = upstream / "RCAEval/e2e/rcd.py"
    patched = upstream / "RCAEval/e2e/rcd_td12.py"
    _check_hash(patch, PATCH_SHA256)
    _check_hash(original, ORIGINAL_SHA256)
    _check_hash(patched, PATCHED_SHA256)
    before = original.read_text(encoding="utf-8")
    after = patched.read_text(encoding="utf-8")
    anchor = '    anomal_df = data[data["time"] >= inject_time]\n'
    addition = ('    normal_df = normal_df.drop(columns=["time"])\n'
                '    anomal_df = anomal_df.drop(columns=["time"])\n')
    if before.count(anchor) != 1 or after != before.replace(anchor, anchor + addition):
        raise RuntimeError("Patched wrapper is not the exact declared two-line delta")
    return upstream, {"source_manifest_sha256": file_sha256(manifest_path),
                      "files": checked, "patch_sha256": PATCH_SHA256,
                      "original_rcd_sha256": ORIGINAL_SHA256,
                      "patched_rcd_sha256": PATCHED_SHA256}


def _load_file(module_name, path):
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot build pinned module loader")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


@dataclass(frozen=True)
class LoadedRCD:
    module: object
    provenance: dict

    @property
    def rcd(self):
        return self.module.rcd


def load_pinned_rcd(run_dir, workspace=None):
    """Load once in a fresh isolated process; never fall back to stock modules."""
    workspace, contract = require_run_contract(run_dir, workspace)
    expected_env = workspace / "environments/task-e/rcd39"
    if sys.version_info[:2] != (3, 9) or Path(sys.prefix).resolve() != expected_env.resolve():
        raise RuntimeError("RCD requires the declared isolated Python3.9 environment")
    if sys.prefix == sys.base_prefix:
        raise RuntimeError("RCD environment is not isolated")
    if any(name == "causallearn" or name.startswith("causallearn.")
           or name == "RCAEval" or name.startswith("RCAEval.") for name in sys.modules):
        raise RuntimeError("Pinned RCD must load before other RCAEval/causal-learn modules")
    upstream, provenance = verify_pinned_sources(workspace)
    packages = {}
    for package, expected in PINNED_PACKAGES.items():
        version = importlib.metadata.version(package)
        if version != expected:
            raise RuntimeError("Unqualified package version: " + package + "=" + version)
        packages[package] = version
    distribution = importlib.metadata.distribution("causal-learn")
    causal_root = Path(distribution.locate_file("causallearn")).resolve()
    causal_root.relative_to(expected_env.resolve())
    installed = []
    for relative in CUSTOM_FILES:
        source = upstream / "lib/causallearn" / relative
        target = causal_root / relative
        installed.append({"path": str(target), "sha256": _check_hash(target, file_sha256(source))})

    # Only the exact time_series dependency receives the RCAEval namespace.
    # Empty paths prevent discovery of __init__.py/framework modules. Temporary
    # namespaces are removed after import; dataset=None uses no delayed imports.
    names = ("RCAEval", "RCAEval.io", "RCAEval.io.time_series")
    for name in names[:2]:
        namespace = types.ModuleType(name)
        namespace.__path__ = []
        sys.modules[name] = namespace
    try:
        _load_file(names[2], upstream / "RCAEval/io/time_series.py")
        # Upstream globally suppresses warnings; avoid leaking that import side
        # effect into the controller. The algorithm's source remains untouched.
        with warnings.catch_warnings():
            module = _load_file("_task_e_pinned_rcd_td12", upstream / "RCAEval/e2e/rcd_td12.py")
    finally:
        for name in reversed(names):
            sys.modules.pop(name, None)
    skeleton = module.SkeletonDiscovery
    if Path(skeleton.__file__).resolve() != causal_root / CUSTOM_FILES[0]:
        raise RuntimeError("Unexpected loaded skeleton implementation")
    graph_module = sys.modules["causallearn.graph.GraphClass"]
    if Path(graph_module.__file__).resolve() != causal_root / CUSTOM_FILES[1]:
        raise RuntimeError("Unexpected loaded CausalGraph implementation")
    if module.rcd.__module__ != "_task_e_pinned_rcd_td12" or hasattr(module.rcd, "__wrapped__"):
        raise RuntimeError("Expected bare pinned RCD function")
    provenance.update({"packages": packages, "customized_installed_files": installed,
                       "python": sys.version, "executable": sys.executable,
                       "run_id": contract["run_id"], "framework_init_executed": False,
                       "loaded_bare_source": str(Path(module.__file__).resolve()),
                       "status": "LOADED_NOT_YET_NUMERICALLY_QUALIFIED"})
    return LoadedRCD(module, provenance)
