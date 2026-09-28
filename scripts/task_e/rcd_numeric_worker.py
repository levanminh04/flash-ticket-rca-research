"""Sequential numeric-only development transport for qualified pinned RCD.

Launch: isolated Python3.9 -m scripts.task_e.rcd_numeric_worker RUN_DIRECTORY
Each input line has exactly {"values": [[...], ...600 rows...], "configs":
[{"seed": 420, "bins": 3}, ...all nine registered combinations exactly once]}.
No metric/service names, case IDs, paths, labels, timestamps or owner map enter
the request. The controller has already enforced TD raw1s eligibility and
reference-median imputation. Relative time and opaque m0... columns are generated
here solely for the pinned wrapper's required split. Empty-width numeric input
is preserved as nine explicit no_eligible_columns failures.

The trusted bootstrap reads only the coordinator contract, its pinned successful
synthetic qualification report, and pinned code/environment metadata. Subsequent
requests never open a data file. This API separation is not an OS filesystem
sandbox. Per-config failure is retained; the worker neither selects a best seed
nor evaluates/averages predictions. Controller scores all three seeds, failures0,
using bins5 as primary and bins3/7 as the registered OFAT sensitivity.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

from .rcd_runtime import file_sha256, load_pinned_rcd, require_run_contract


SCHEMA = "TD13-RCD-NUMERIC-v1"
REGISTERED = frozenset((seed, bins) for bins in (3, 5, 7) for seed in (420, 421, 422))


class RequestError(ValueError):
    """A static, safe error code; never embed request contents in this message."""


def _object_without_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RequestError("duplicate_json_key")
        result[key] = value
    return result


def _reject_json_constant(_value):
    raise RequestError("nonfinite_json_number")


def parse_request(line):
    """Strict stdlib validation before creating a numeric array."""
    try:
        request = json.loads(line, object_pairs_hook=_object_without_duplicates,
                             parse_constant=_reject_json_constant)
    except (json.JSONDecodeError, RecursionError):
        raise RequestError("invalid_json") from None
    if type(request) is not dict or set(request) != {"values", "configs"}:
        raise RequestError("request_fields_must_be_values_and_configs")
    values, configs = request["values"], request["configs"]
    if type(values) is not list or len(values) != 600:
        raise RequestError("expected_600_numeric_rows")
    width = None
    for row in values:
        if type(row) is not list:
            raise RequestError("expected_numeric_row_lists")
        if width is None:
            width = len(row)
        if len(row) != width:
            raise RequestError("ragged_numeric_grid")
        for value in row:
            if type(value) not in (int, float):
                raise RequestError("grid_requires_numbers_without_objects_strings_or_booleans")
            try:
                finite = math.isfinite(value)
            except OverflowError:
                finite = False
            if not finite:
                raise RequestError("nonfinite_or_out_of_float64_range")
    if type(configs) is not list or len(configs) != 9:
        raise RequestError("all_nine_registered_seed_bin_configs_required")
    realized = []
    for config in configs:
        if type(config) is not dict or set(config) != {"seed", "bins"}:
            raise RequestError("config_fields_must_be_seed_and_bins")
        seed, bins = config["seed"], config["bins"]
        if type(seed) is not int or type(bins) is not int or (seed, bins) not in REGISTERED:
            raise RequestError("unregistered_seed_or_bins")
        realized.append((seed, bins))
    if len(set(realized)) != 9 or set(realized) != REGISTERED:
        raise RequestError("all_nine_configs_must_occur_once")
    return values, realized


def _require_qualification(workspace, contract):
    """Verify the real fixture evidence, never substitute a successful import."""
    pointer = contract["config"].get("rcd_qualification_report")
    if type(pointer) is not dict or set(pointer) != {"path", "sha256"}:
        raise RuntimeError("Run config must pin rcd_qualification_report path and sha256")
    report_path = Path(pointer["path"]).resolve()
    report_path.relative_to(workspace / "results/task-e")
    if report_path.name != "rcd-fixture-report.json" or file_sha256(report_path) != pointer["sha256"]:
        raise RuntimeError("Qualification report identity mismatch")
    report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    if report.get("passed") is not True or report.get("tests_run", 0) < 4:
        raise RuntimeError("Real RCD qualification did not pass")
    if report.get("failures") != [] or report.get("errors") != []:
        raise RuntimeError("Qualification contains failures or errors")
    qualification_contract_path = report_path.parent / "run-contract.json"
    qualification_contract = json.loads(qualification_contract_path.read_text(encoding="utf-8-sig"))
    if qualification_contract["td"]["sha256"] != contract["td"]["sha256"]:
        raise RuntimeError("Qualification belongs to a different TD revision")
    if qualification_contract["config"].get("rcd_runtime_qualification_authorized") is not True:
        raise RuntimeError("Qualification was not coordinator-authorized")
    qualification_sources = {str(Path(row["path"]).resolve()): row["sha256"]
                             for row in qualification_contract["source_files"]}
    current_sources = {str(Path(row["path"]).resolve()): row["sha256"]
                       for row in contract["source_files"]}
    for relative in ("scripts/task_e/rcd_runtime.py", "scripts/task_e/comparators.py",
                     "tests/task_e/test_rcd_runtime.py"):
        source = workspace / relative
        if qualification_sources.get(str(source)) != file_sha256(source):
            raise RuntimeError("Qualification source changed or was not pinned: " + relative)
    worker = Path(__file__).resolve()
    if current_sources.get(str(worker)) != file_sha256(worker):
        raise RuntimeError("Numeric worker must be pinned in the current run contract")
    records = report.get("numeric_runs", [])
    if len(records) != 20:
        raise RuntimeError("Expected 18 seeded runs, real empty run and injected CI failure")
    grouped = {}
    for record in records:
        key = (record.get("fixture"), record.get("seed"), record.get("bins"))
        if key in grouped or not record.get("ci_calls") or record.get("ci_call_count", 0) < 1:
            raise RuntimeError("Qualification lacks unique real CI execution receipts")
        grouped[key] = record
    expected_keys = {(name, seed, bins) for name in ("separated-shift", "separated-shift-repeat")
                     for seed, bins in REGISTERED}
    expected_keys |= {("identical-halves", 420, 5), ("injected-CI-exception", 420, 5)}
    if set(grouped) != expected_keys:
        raise RuntimeError("Qualification did not cover the required seed/bin grid")
    for seed, bins in REGISTERED:
        first = grouped[("separated-shift", seed, bins)]
        repeat = grouped[("separated-shift-repeat", seed, bins)]
        if (first["result"].get("status") != "SUCCESS"
                or first["result"].get("ranks") != ["m000"]
                or first["result"] != repeat["result"]
                or first["ci_calls"] != repeat["ci_calls"]):
            raise RuntimeError("Real seeded qualification or determinism failed")
    empty = grouped[("identical-halves", 420, 5)]["result"]
    injected = grouped[("injected-CI-exception", 420, 5)]["result"]
    if empty.get("status") != "SUCCESS" or empty.get("ranks") != []:
        raise RuntimeError("Valid empty-ranking qualification failed")
    if (injected.get("status") != "FAILURE" or injected.get("ranks") is not None
            or injected.get("reason") != "upstream_exception"):
        raise RuntimeError("Explicit exception qualification failed")
    return report, {"report_sha256": pointer["sha256"],
                    "qualification_run_id": qualification_contract["run_id"],
                    "qualification_contract_sha256": file_sha256(qualification_contract_path)}


def bootstrap(run_dir):
    workspace, contract = require_run_contract(run_dir)
    qualification, qualification_identity = _require_qualification(workspace, contract)
    # Import output is also kept off the line-JSON transport.
    with redirect_stdout(sys.stderr):
        loaded = load_pinned_rcd(run_dir, workspace)
        import numpy as np
        import pandas as pd
        from .comparators import rcd_run
    earlier, now = qualification["provenance"], loaded.provenance
    for key in ("source_manifest_sha256", "patch_sha256", "original_rcd_sha256",
                "patched_rcd_sha256", "packages", "customized_installed_files", "python", "executable"):
        if earlier.get(key) != now.get(key):
            raise RuntimeError("Current RCD runtime differs from successful qualification: " + key)
    metadata = {
        "method": "RCD-RCAEval-adapted-TD12", **qualification_identity,
        "source_manifest_sha256": now["source_manifest_sha256"],
        "patch_sha256": now["patch_sha256"], "patched_rcd_sha256": now["patched_rcd_sha256"],
        "worker_sha256": file_sha256(__file__), "packages": now["packages"],
        "parameters": {"gamma": 5, "localized": True, "dk_select_useful": False,
                       "dataset": None, "LOCAL_ALPHA": .01, "START_ALPHA": .001,
                       "ALPHA_STEP": .1, "ALPHA_LIMIT": 1},
        "preprocessing": "controller eligible raw1s metrics; reference-median imputation; common-window kmeans",
        "time_policy": "manufactured relative0..599; split300; exact post-split time-drop patch",
        "transport": "numeric values/configs only; locally manufactured opaque column indices",
        "execution": "all nine configurations sequentially; wrapper resets numpy seed for every call",
        "aggregation": "none here; controller averages seeds420/421/422 with failed seeds0; primary bins5",
        "framework_init_executed": False,
        "limitations": "contextual adapted comparator; neither exact-paper reproduction nor trace-graph causal ground truth",
    }
    return loaded, np, pd, rcd_run, metadata


def run_request(values, configs, runtime):
    loaded, np, pd, rcd_run, metadata = runtime
    numeric = np.asarray(values, dtype=np.float64)
    if numeric.ndim != 2 or numeric.shape[0] != 600 or not np.isfinite(numeric).all():
        raise RequestError("invalid_float64_numeric_grid")
    keys = ["m" + str(index) for index in range(numeric.shape[1])]
    frame = pd.DataFrame(numeric, columns=keys)
    frame.insert(0, "time", np.arange(600, dtype=np.float64))
    indices = {key: index for index, key in enumerate(keys)}
    results = []
    for seed, bins in configs:
        start = time.perf_counter()
        try:
            with redirect_stdout(sys.stderr):
                result = rcd_run(frame, seed=seed, bins=bins, upstream_rcd=loaded.rcd)
        except Exception as exc:
            # An unexpected adapter error cannot erase the other planned draws.
            result = {"method": metadata["method"], "seed": seed, "bins": bins,
                      "status": "FAILURE", "ranks": None, "reason": "adapter_exception",
                      "error": type(exc).__name__}
        result["wall_seconds"] = time.perf_counter() - start
        result["metric_rank_indices"] = (None if result["ranks"] is None else
                                         [indices[key] for key in result["ranks"] if key in indices])
        results.append(result)
    return {"schema": SCHEMA, "status": "COMPLETE", "shape": list(numeric.shape),
            "input_numeric_sha256": hashlib.sha256(numeric.astype("<f8", copy=False).tobytes()).hexdigest(),
            "results": results, "fidelity": metadata}


def emit(value):
    sys.stdout.write(json.dumps(value, allow_nan=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m scripts.task_e.rcd_numeric_worker RUN_DIRECTORY")
    try:
        runtime = bootstrap(Path(sys.argv[1]).resolve())
    except Exception as exc:
        # Bootstrap receipts may contain trusted paths; emit type only, no echo.
        sys.stderr.write(json.dumps({"schema": SCHEMA, "status": "BOOTSTRAP_FAILURE",
                                     "error_type": type(exc).__name__}) + "\n")
        return 2
    for line in sys.stdin:
        try:
            values, configs = parse_request(line)
            response = run_request(values, configs, runtime)
        except RequestError as exc:
            response = {"schema": SCHEMA, "status": "REQUEST_FAILURE",
                        "reason": str(exc), "results": None}
        except Exception as exc:
            response = {"schema": SCHEMA, "status": "WORKER_FAILURE",
                        "error_type": type(exc).__name__, "results": None}
        emit(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
