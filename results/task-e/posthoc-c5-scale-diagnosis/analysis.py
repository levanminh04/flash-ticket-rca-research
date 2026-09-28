"""POST-HOC DEVELOPMENT DIAGNOSTIC.

NOT FINAL EFFICACY.
NOT PARAMETER SELECTION.
NO METHOD CHANGE AUTHORIZED.

Read-only analysis of sealed C5 development artifacts.  This script never
imports or calls detector fitting/scoring entry points.  It decodes the saved
numeric wire format, verifies seals, and computes descriptive decompositions.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
import sys

import numpy as np


P = Path(r"D:\Project\flash-ticket-platform")
W = Path(r"D:\Project\flash-ticket-rca-research")
OUT = W / "results/task-e/posthoc-c5-scale-diagnosis"
PRIMARY = W / "results/task-e/e27-035-c5-development-full"
SENSITIVITY = W / "results/task-e/e27-037-c5-development-sensitivity"
AUDIT = W / "results/task-e/e27-019-development-loader-audit"
CONFIG = W / "configs/task-e-td13-development.json"
TD = P / "docs/research-rca/task-d-method-and-experiment-specification.md"
PHASE1 = W / "results/task-e/posthoc-c1-mechanism-analysis"

TD_SHA = "34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971"
P_HEAD = "576be4b6935c9a837e6f2bcc6356a89bfe61c6ac"
W_HEAD = "664d7180f0af3fadc8f11d7747b9d75833aeca34"
PHASE1_HASHES = {
    "analysis.py": "67112f1276a326517d78e8c3ff0f64aebb802f4ec10318017650c8f11310bb8d",
    "case-table.csv": "ee8303a117d28d589a4d5058f97eb07e5a43a79574bdfc16c58d0a3a58501252",
    "report.md": "420742e1eee5b1e52f9ee72cdf5e0bbb5504d66cb3ae2847a273d6e2a628e898",
}
SOURCE_HASHES = {
    "detection.py": "084e48aab3b1a3edd5fe80f43d1dbd6fb3b490163ee6cd7564b9e835f7072122",
    "c5_development.py": "618c75ed188f2769952942fc50b350bac3de631dd1e063367aac281ce6b8c054",
    "calibration.py": "0d27b9c3474645e54a5a1e22ba684359b854bd66076c9d541404627b5b2c572d",
}

CHANNEL_NAMES = (
    "metric:latency-90", "metric:latency-50", "metric:workload",
    "metric:diskio", "metric:latency", "metric:socket", "metric:error",
    "metric:load", "metric:cpu", "metric:mem", "trace-count", "log-count",
)
TYPE_NAMES = {0: "metric", 1: "trace-count", 2: "log-count"}
ARMS = ("G", "L", "ALL")
MODALITIES = ("MTL", "MT")
LAMBDAS = (0.1, 1.0, 10.0)
VARIANTS = {
    "primary": (PRIMARY, "primary"),
    "bin10": (SENSITIVITY, "bin10"),
    "prefix240": (SENSITIVITY, "prefix240"),
    "lag3": (SENSITIVITY, "primary"),
    "residual-floor-0.001": (SENSITIVITY, "primary"),
    "residual-floor-0.1": (SENSITIVITY, "primary"),
    "relative-floor-0.0001": (SENSITIVITY, "primary"),
    "relative-floor-0.001": (SENSITIVITY, "primary"),
}
SCALE_TOL = 1e-24


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def q7(values: np.ndarray, probability: float) -> float:
    ordered = np.sort(np.asarray(values, dtype=np.float64))
    if not len(ordered):
        return math.nan
    position = (len(ordered) - 1) * probability
    lower = int(math.floor(position))
    fraction = position - lower
    if fraction == 0:
        return float(ordered[lower])
    return float((1.0 - fraction) * ordered[lower] + fraction * ordered[lower + 1])


def median_iqr(values):
    values = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    if not values:
        return {"n": 0, "median": None, "q1": None, "q3": None, "min": None, "max": None}
    array = np.asarray(values, dtype=float)
    return {
        "n": len(values), "median": q7(array, 0.5), "q1": q7(array, 0.25),
        "q3": q7(array, 0.75), "min": float(np.min(array)), "max": float(np.max(array)),
    }


def config_id(config: dict) -> str:
    return f"{config['arm']}-{config['modalities']}-lambda{config['lambda']:g}"


def decode_wire(path: Path):
    """Decode worker numeric-wire NPZ without importing detector/model code."""
    with np.load(path, allow_pickle=False) as archive:
        meta = archive["__manifest__"]
        assert meta.dtype == np.uint8 and meta.ndim == 1
        manifest = json.loads(meta.tobytes().decode())
        assert manifest["schema"] == "TD13-NUMERIC-WIRE-v1"
        used = set()

        def decode(value):
            if isinstance(value, dict) and set(value) == {"__array__"}:
                key = value["__array__"]
                array = archive[key]
                assert array.dtype.kind in "biuf"
                used.add(key)
                return array.copy()
            if isinstance(value, dict) and set(value) == {"__float__"}:
                return {"nan": np.nan, "inf": np.inf, "-inf": -np.inf}[value["__float__"]]
            if isinstance(value, dict):
                return {key: decode(item) for key, item in value.items()}
            if isinstance(value, list):
                return [decode(item) for item in value]
            return value

        result = decode(manifest["tree"])
        assert set(archive.files) == used | {"__manifest__"}
        return result


def load_npz(path: Path):
    with np.load(path, allow_pickle=False) as archive:
        return {name: archive[name].copy() for name in archive.files}


def verify_baseline():
    assert sha256(TD) == TD_SHA
    for name, expected in PHASE1_HASHES.items():
        assert sha256(PHASE1 / name) == expected
    for name, expected in SOURCE_HASHES.items():
        assert sha256(W / "scripts/task_e" / name) == expected
    canonical_config = read_json(CONFIG)
    for run in (PRIMARY, SENSITIVITY):
        contract = read_json(run / "run-contract.json")
        assert contract["td"]["sha256"] == TD_SHA
        assert contract["dataset_revision"] == canonical_config["dataset_revision"]
        assert contract["config"] == canonical_config
        assert read_json(run / "execution.json")["exit_code"] == 0
        summary = read_json(run / "c5-summary.json")
        assert summary["status"] == "COMPLETE"
        assert summary["planned"] == 30
        assert summary["prediction_failures"] == 0
        assert summary["input_unavailable"] == 0
        sources = {Path(item["path"]).name: item["sha256"] for item in contract["source_files"]}
        for name, expected in SOURCE_HASHES.items():
            assert sources[name] == expected


def verify_campaign(run: Path, expected_variants: set[str]):
    manifest = read_json(run / "predictions-seal.json")
    assert manifest["before_evaluation"] is True
    assert manifest["contract_sha256"] == sha256(run / "run-contract.json")
    assert len(manifest["entries"]) == 30 * len(expected_variants)
    assert {item["variant"] for item in manifest["entries"]} == expected_variants
    seen = set()
    for item in manifest["entries"]:
        key = (item["variant"], item["handle"])
        assert key not in seen
        seen.add(key)
        directory = run / "predictions" / item["variant"] / item["handle"]
        seal_path = directory / "seal.json"
        assert sha256(seal_path) == item["seal_sha256"]
        seal = read_json(seal_path)
        assert seal["status"] == "COMPLETE"
        assert seal["identity"]["variant"] == item["variant"]
        assert seal["identity"]["handle"] == item["handle"]
        assert seal["identity"]["contract_sha256"] == manifest["contract_sha256"]
        assert {entry["file"] for entry in seal["artifacts"]} == {
            "numeric-input.npz", "frozen-models.npz", "predictions.npz"
        }
        for artifact in seal["artifacts"]:
            assert sha256(directory / artifact["file"]) == artifact["sha256"]


def summary_case_maps():
    result = {}
    for run in (PRIMARY, SENSITIVITY):
        rows = read_json(run / "c5-summary.json")["case_runs"]
        for row in rows:
            key = (run, row["variant"])
            result.setdefault(key, {})[row["case"]] = row["handle"]
    return result


def evaluation_document(variant: str, detector: str):
    if variant == "primary":
        return read_json(PRIMARY / "evaluation" / f"{detector}.json")
    return read_json(SENSITIVITY / "sensitivity-evaluation" / variant / f"{detector}.json")


def evaluation_details(document: dict):
    q = float(document["selected_q"])
    if "details" in document:
        detail = document["details"][str(q)]
        return q, detail["folds"], detail["cases"], detail["summary"], document["full_development_calibration"]
    return q, document["folds"], document["cases"], document["summary"], document["full_development_calibration"]


def outcome_lookup(variant: str):
    result = {}
    for modality in MODALITIES:
        for arm in ARMS:
            detector = f"{arm}-{modality}"
            document = evaluation_document(variant, detector)
            q, folds, cases, summary, full = evaluation_details(document)
            thresholds = {}
            for fold in folds:
                for case in fold["heldout_ids"]:
                    thresholds[case] = float(fold["threshold"])
            result[detector] = {
                "q": q, "folds": folds, "cases": cases, "summary": summary,
                "full": full, "oof_thresholds": thresholds,
            }
    return result


def type_counts(mask: np.ndarray, channel_types: np.ndarray):
    return {
        name: int(np.sum(mask & (channel_types[None, :] == code)))
        for code, name in TYPE_NAMES.items()
    }


def argmax_status(residuals: np.ndarray, target_mask: np.ndarray, score: float,
                  affected: np.ndarray, channel_types: np.ndarray,
                  service_names: list[str]):
    if not math.isfinite(float(score)):
        return "UNAVAILABLE", (), ()
    tied = target_mask & (residuals == score)
    assert tied.any()
    affected_tied = tied & affected
    if affected_tied.any() and np.all(affected[tied]):
        status = "AFFECTED_ONLY"
    elif affected_tied.any():
        status = "MIXED_TIE"
    else:
        status = "UNAFFECTED_ONLY"
    types = tuple(sorted({TYPE_NAMES[int(channel_types[channel])]
                          for _, channel in np.argwhere(affected_tied)}))
    identities = tuple(sorted({f"{service_names[node]}|{CHANNEL_NAMES[channel]}"
                               for node, channel in np.argwhere(affected_tied)}))
    return status, types, identities


def hierarchical_objective(case_rows: dict, field: str) -> float:
    by_scenario = defaultdict(list)
    for row in case_rows.values():
        by_scenario[row["scenario"]].append(float(row[field]))
    scenario_means = [math.fsum(values) / len(values) for values in by_scenario.values()]
    return math.fsum(scenario_means) / len(scenario_means)


def analyze():
    verify_baseline()
    verify_campaign(PRIMARY, {"primary"})
    verify_campaign(SENSITIVITY, set(VARIANTS) - {"primary"})
    case_maps = summary_case_maps()
    selected_lambda = float(read_json(PRIMARY / "c5-selection.json")["selected_lambda"])
    assert selected_lambda == 10.0

    outcome_documents = {variant: outcome_lookup(variant) for variant in VARIANTS}
    csv_rows = []
    prevalence = {}
    affected_id_sets = {}
    support_records = defaultdict(list)
    dominance = defaultdict(Counter)
    dominance_by_type = defaultdict(Counter)
    dominance_lookup = {}
    capacity = defaultdict(lambda: {"df": [], "active": [], "models": 0, "affected_models": 0})
    forecast = {lam: {arm: {} for arm in ARMS} for lam in LAMBDAS}
    scale_case_counts = defaultdict(dict)
    all_case_ids = None

    for variant, (run, profile) in VARIANTS.items():
        handles = case_maps[(run, variant)]
        assert len(handles) == 30
        if all_case_ids is None:
            all_case_ids = tuple(sorted(handles))
        else:
            assert set(handles) == set(all_case_ids)
        outcome = outcome_documents[variant]
        variant_affected_ids = set()
        variant_total = Counter()
        variant_affected = Counter()
        case_aff_counts = []

        for case_id in sorted(handles):
            handle = handles[case_id]
            directory = run / "predictions" / variant / handle
            audit = read_json(AUDIT / "case-audits" / f"{handle}.json")
            assert audit["case"] == case_id and audit["handle"] == handle
            profile_info = audit["profiles"]["c5_" + profile]
            service_names = list(profile_info["service_names"])
            tau = float(profile_info["tau_relative"])
            root = audit["metadata"]["root_cause_service"]
            fault = audit["metadata"]["fault"]
            fitted = decode_wire(directory / "frozen-models.npz")
            models = fitted["models"]
            numeric = load_npz(directory / "numeric-input.npz")
            predictions = load_npz(directory / "predictions.npz")
            configs = [model["config"] for model in models]
            indices = {config_id(config): index for index, config in enumerate(configs)}
            assert len(indices) == len(configs)
            assert np.array_equal(numeric["channel_types"], models[0]["channel_types"])
            channel_types = numeric["channel_types"]
            assert tuple(CHANNEL_NAMES) == CHANNEL_NAMES and len(CHANNEL_NAMES) == len(channel_types)

            reference_index = indices[f"G-MTL-lambda{selected_lambda:g}"]
            reference = models[reference_index]
            qualifying = reference["E"]
            scale_exact = qualifying & (reference["scales"] == 1e-12)
            scale_tolerant = qualifying & (np.abs(reference["scales"] - 1e-12) <= SCALE_TOL)
            assert np.array_equal(scale_exact, scale_tolerant)
            total_by_type = type_counts(qualifying, channel_types)
            affected_by_type = type_counts(scale_exact, channel_types)
            variant_total.update(total_by_type)
            variant_affected.update(affected_by_type)
            case_aff_counts.append(int(scale_exact.sum()))
            scale_case_counts[variant][case_id] = int(scale_exact.sum())

            fit_bins = int(reference["config"]["fit_bins"])
            for node, channel in np.argwhere(scale_exact):
                service = service_names[int(node)]
                channel_name = CHANNEL_NAMES[int(channel)]
                channel_type = TYPE_NAMES[int(channel_types[channel])]
                identity = (case_id, service, channel_name)
                variant_affected_ids.add(identity)
                fit_values = numeric["values"][:fit_bins, node, channel]
                finite = fit_values[np.isfinite(fit_values)]
                center = float(reference["centers"][node, channel])
                iqr = q7(finite, 0.75) - q7(finite, 0.25)
                assert center == q7(finite, 0.5)
                assert iqr == 0.0 and center == 0.0
                record = {
                    "variant": variant, "case": case_id, "service": service,
                    "channel": channel_name, "type": channel_type,
                    "support": int(reference["diagnostics"]["finite_fit_support"][node, channel]),
                    "positive_count_observations": (int(np.sum(finite > 0))
                                                     if channel_types[channel] != 0 else None),
                    "constant": bool(reference["diagnostics"]["constant_scale"][node, channel]),
                    "singleton": bool(reference["diagnostics"]["singleton_scale"][node, channel]),
                    "floor_used": bool(reference["diagnostics"]["scale_floor_used"][node, channel]),
                    "center": center, "iqr": iqr,
                }
                support_records[variant].append(record)

            # Source/controller invariants: all arms share E/scales/target IDs for a modality.
            for modality in MODALITIES:
                selected = [indices[f"{arm}-{modality}-lambda{selected_lambda:g}"] for arm in ARMS]
                base_model = models[selected[0]]
                base_mask = predictions["target_mask"][selected[0]]
                for index in selected[1:]:
                    assert np.array_equal(base_model["E"], models[index]["E"])
                    assert np.array_equal(base_model["scales"], models[index]["scales"], equal_nan=True)
                    assert np.array_equal(base_model["model_mask"], models[index]["model_mask"])
                    assert np.array_equal(base_mask, predictions["target_mask"][index])

            # Primary lambda objective decomposition on exact MTL normal support.
            if variant == "primary":
                reference_targets = predictions["z"][indices["G-MTL-lambda1"]]
                reference_mask = predictions["target_mask"][indices["G-MTL-lambda1"]]
                normal_bins = predictions["endpoints"] <= tau
                for lam in LAMBDAS:
                    for arm in ARMS:
                        index = indices[f"{arm}-MTL-lambda{lam:g}"]
                        assert np.array_equal(reference_targets, predictions["z"][index], equal_nan=True)
                        assert np.array_equal(reference_mask, predictions["target_mask"][index])
                        absolute = np.abs(reference_targets - predictions["predictions"][index])
                        bin_totals, bin_affected = [], []
                        type_contributions = defaultdict(list)
                        raw_total = raw_affected = 0.0
                        eligible_total = eligible_affected = 0
                        for b in np.flatnonzero(normal_bins):
                            mask = reference_mask[b]
                            if not mask.any():
                                continue
                            values = absolute[b][mask]
                            assert np.isfinite(values).all()
                            denominator = int(mask.sum())
                            affected_mask = mask & scale_exact
                            total = math.fsum(float(value) for value in values)
                            affected_loss = math.fsum(float(value) for value in absolute[b][affected_mask])
                            bin_totals.append(total / denominator)
                            bin_affected.append(affected_loss / denominator)
                            raw_total += total
                            raw_affected += affected_loss
                            eligible_total += denominator
                            eligible_affected += int(affected_mask.sum())
                            for code, type_name in TYPE_NAMES.items():
                                selected_type = affected_mask & (channel_types[None, :] == code)
                                type_loss = math.fsum(float(value) for value in absolute[b][selected_type])
                                type_contributions[type_name].append(type_loss / denominator)
                        assert bin_totals
                        forecast[lam][arm][case_id] = {
                            "scenario": (root, fault),
                            "loss": math.fsum(bin_totals) / len(bin_totals),
                            "affected_contribution": math.fsum(bin_affected) / len(bin_affected),
                            "raw_total": raw_total, "raw_affected": raw_affected,
                            "eligible_total": eligible_total, "eligible_affected": eligible_affected,
                            **{f"affected_{name}_contribution":
                               math.fsum(type_contributions[name]) / len(bin_totals)
                               for name in TYPE_NAMES.values()},
                        }

            # Selected-lambda capacity and system-max attribution.
            for modality in MODALITIES:
                for arm in ARMS:
                    detector = f"{arm}-{modality}"
                    index = indices[f"{detector}-lambda{selected_lambda:g}"]
                    model = models[index]
                    affected = model["E"] & (model["scales"] == 1e-12)
                    ridge = [item for row in model["diagnostics"]["ridge"] for item in row if item is not None]
                    cap = capacity[(variant, detector)]
                    cap["df"].extend(float(item["effective_ridge_df"]) for item in ridge)
                    cap["active"].extend(float(item["active_columns"]) for item in ridge)
                    cap["models"] += int(model["model_mask"].sum())
                    cap["affected_models"] += int(np.sum(model["model_mask"] & affected))

                    statuses = Counter()
                    type_hits = Counter()
                    identities_by_bin = {}
                    for b, score in enumerate(predictions["scores"][index]):
                        status, types, identities = argmax_status(
                            predictions["residuals"][index, b],
                            predictions["target_mask"][index, b], float(score), affected,
                            channel_types, service_names)
                        statuses[status] += 1
                        for name in types:
                            type_hits[name] += 1
                        identities_by_bin[b] = identities
                        dominance_lookup[(variant, detector, case_id, b)] = {
                            "status": status, "types": types, "identities": identities,
                            "score": float(score),
                        }
                    dominance[(variant, detector)].update(statuses)
                    dominance_by_type[(variant, detector)].update(type_hits)

                    evaluation = outcome[detector]
                    case_outcome = evaluation["cases"][case_id]
                    config = model["config"]
                    normal_bins = predictions["endpoints"] <= tau
                    selected_mask = predictions["target_mask"][index][normal_bins]
                    affected_eligible = int(np.sum(selected_mask & affected[None, :, :]))
                    eligible = int(selected_mask.sum())
                    abs_total = abs_affected = None
                    if modality == "MTL":
                        absolute = np.abs(predictions["z"][index] - predictions["predictions"][index])
                        abs_total = float(np.sum(absolute[normal_bins][selected_mask]))
                        abs_affected = float(np.sum(absolute[normal_bins][selected_mask & affected[None, :, :]]))
                    diag = model["diagnostics"]
                    affected_support = diag["finite_fit_support"][affected]
                    count_affected = affected & (channel_types[None, :] != 0)
                    positive_counts = []
                    for node, channel in np.argwhere(count_affected):
                        values = numeric["values"][:config["fit_bins"], node, channel]
                        positive_counts.append(int(np.sum(values[np.isfinite(values)] > 0)))
                    by_type_q = type_counts(model["E"], channel_types)
                    by_type_a = type_counts(affected, channel_types)
                    csv_rows.append({
                        "diagnostic_label": "POST-HOC DEVELOPMENT DIAGNOSTIC",
                        "efficacy_label": "NOT FINAL EFFICACY",
                        "selection_label": "NOT PARAMETER SELECTION",
                        "method_change_label": "NO METHOD CHANGE AUTHORIZED",
                        "variant": variant, "profile": profile, "case_id": case_id,
                        "root_service": root, "fault": fault, "handle": handle,
                        "arm": arm, "modality": modality, "lambda": selected_lambda,
                        "relative_floor": config["floor"], "residual_floor": config["residual_floor"],
                        "bin_seconds": config["bin_seconds"], "fit_bins": config["fit_bins"],
                        "cal_bins": config["cal_bins"], "lag": config["lag"],
                        "min_fit_rows": config["min_fit_rows"], "min_cal_rows": config["min_cal_rows"],
                        "qualifying_scalers": int(model["E"].sum()),
                        "qualifying_metric": by_type_q["metric"],
                        "qualifying_trace_count": by_type_q["trace-count"],
                        "qualifying_log_count": by_type_q["log-count"],
                        "scale_1e12": int(affected.sum()),
                        "scale_1e12_metric": by_type_a["metric"],
                        "scale_1e12_trace_count": by_type_a["trace-count"],
                        "scale_1e12_log_count": by_type_a["log-count"],
                        "affected_support_median": (q7(affected_support, .5) if len(affected_support) else None),
                        "affected_support_min": (int(affected_support.min()) if len(affected_support) else None),
                        "affected_support_max": (int(affected_support.max()) if len(affected_support) else None),
                        "affected_positive_count_median": (q7(np.asarray(positive_counts), .5)
                                                           if positive_counts else None),
                        "affected_constant": int(np.sum(diag["constant_scale"] & affected)),
                        "affected_singleton": int(np.sum(diag["singleton_scale"] & affected)),
                        "model_count": int(model["model_mask"].sum()),
                        "affected_model_count": int(np.sum(model["model_mask"] & affected)),
                        "normal_eligible_ids": eligible,
                        "normal_affected_eligible_ids": affected_eligible,
                        "normal_abs_loss": abs_total,
                        "normal_affected_abs_loss": abs_affected,
                        "scored_bins": sum(statuses.values()) - statuses["UNAVAILABLE"],
                        "max_affected_only": statuses["AFFECTED_ONLY"],
                        "max_mixed_tie": statuses["MIXED_TIE"],
                        "max_unaffected_only": statuses["UNAFFECTED_ONLY"],
                        "max_unavailable": statuses["UNAVAILABLE"],
                        "max_affected_metric_bins": type_hits["metric"],
                        "max_affected_trace_count_bins": type_hits["trace-count"],
                        "max_affected_log_count_bins": type_hits["log-count"],
                        "oof_threshold": evaluation["oof_thresholds"][case_id],
                        "full_threshold": float(evaluation["full"]["threshold"]),
                        "case_f1": float(case_outcome["f1"]),
                        "case_precision": float(case_outcome["precision"]),
                        "case_recall": float(case_outcome["recall"]),
                    })

            del fitted, models, numeric, predictions

        prevalence[variant] = {
            "qualifying": int(sum(variant_total.values())),
            "affected": int(sum(variant_affected.values())),
            "fraction": int(sum(variant_affected.values())) / int(sum(variant_total.values())),
            "qualifying_by_type": dict(variant_total),
            "affected_by_type": dict(variant_affected),
            "cases_with_affected": sum(value > 0 for value in case_aff_counts),
            "affected_per_case": median_iqr(case_aff_counts),
            "support": median_iqr(record["support"] for record in support_records[variant]),
            "positive_count_observations": median_iqr(
                record["positive_count_observations"] for record in support_records[variant]
                if record["positive_count_observations"] is not None),
            "constant": sum(record["constant"] for record in support_records[variant]),
            "singleton": sum(record["singleton"] for record in support_records[variant]),
            "center_zero": sum(record["center"] == 0 for record in support_records[variant]),
            "iqr_zero": sum(record["iqr"] == 0 for record in support_records[variant]),
        }
        affected_id_sets[variant] = variant_affected_ids

    # Exact registered lambda objective and linear contribution decomposition.
    saved_lambda = read_json(PRIMARY / "lambda-selection.json")
    forecast_summary = {}
    for lam in LAMBDAS:
        arms = {}
        for arm in ARMS:
            rows = forecast[lam][arm]
            total = hierarchical_objective(rows, "loss")
            affected = hierarchical_objective(rows, "affected_contribution")
            by_type = {name: hierarchical_objective(rows, f"affected_{name}_contribution")
                       for name in TYPE_NAMES.values()}
            raw_total = math.fsum(row["raw_total"] for row in rows.values())
            raw_affected = math.fsum(row["raw_affected"] for row in rows.values())
            eligible_total = sum(row["eligible_total"] for row in rows.values())
            eligible_affected = sum(row["eligible_affected"] for row in rows.values())
            arms[arm] = {
                "objective": total,
                "affected_objective_contribution": affected,
                "affected_objective_fraction": affected / total,
                "affected_contribution_by_type": by_type,
                "raw_abs_loss": raw_total, "affected_raw_abs_loss": raw_affected,
                "affected_raw_abs_loss_fraction": raw_affected / raw_total,
                "eligible_ids": eligible_total, "affected_eligible_ids": eligible_affected,
                "affected_eligible_fraction": eligible_affected / eligible_total,
            }
        joint = math.fsum(arms[arm]["objective"] for arm in ARMS) / len(ARMS)
        joint_affected = math.fsum(arms[arm]["affected_objective_contribution"] for arm in ARMS) / len(ARMS)
        assert math.isclose(joint, float(saved_lambda["objectives"][str(lam)]), rel_tol=1e-14, abs_tol=1e-6)
        forecast_summary[f"{lam:g}"] = {
            "objective": joint,
            "affected_objective_contribution": joint_affected,
            "affected_objective_fraction": joint_affected / joint,
            "raw_abs_loss": math.fsum(arms[arm]["raw_abs_loss"] for arm in ARMS),
            "affected_raw_abs_loss": math.fsum(arms[arm]["affected_raw_abs_loss"] for arm in ARMS),
            "eligible_ids": sum(arms[arm]["eligible_ids"] for arm in ARMS),
            "affected_eligible_ids": sum(arms[arm]["affected_eligible_ids"] for arm in ARMS),
            "arms": arms,
        }
        forecast_summary[f"{lam:g}"]["affected_raw_abs_loss_fraction"] = (
            forecast_summary[f"{lam:g}"]["affected_raw_abs_loss"] /
            forecast_summary[f"{lam:g}"]["raw_abs_loss"])
        forecast_summary[f"{lam:g}"]["affected_eligible_fraction"] = (
            forecast_summary[f"{lam:g}"]["affected_eligible_ids"] /
            forecast_summary[f"{lam:g}"]["eligible_ids"])

    # Threshold upper-tail association with exact saved support IDs and scores.
    threshold_summary = {}
    for variant in VARIANTS:
        threshold_summary[variant] = {}
        for modality in MODALITIES:
            for arm in ARMS:
                detector = f"{arm}-{modality}"
                evaluation = outcome_documents[variant][detector]
                full = evaluation["full"]
                threshold = float(full["threshold"])
                statuses = Counter()
                equal_statuses = Counter()
                weighted_tail = Counter()
                equal_cases = Counter()
                equal_identities = Counter()
                tail_weight = 0.0
                for value, weight, support in zip(full["values"], full["weights"], full["support_ids"]):
                    case_id, position, _endpoint = support
                    evidence = dominance_lookup[(variant, detector, case_id, int(position))]
                    assert math.isclose(float(value), evidence["score"], rel_tol=1e-15, abs_tol=0.0)
                    status = evidence["status"]
                    statuses[status] += 1
                    if float(value) >= threshold:
                        weighted_tail[status] += float(weight)
                        tail_weight += float(weight)
                    if float(value) == threshold:
                        equal_statuses[status] += 1
                        equal_cases[case_id] += 1
                        equal_identities.update(evidence["identities"])
                threshold_summary[variant][detector] = {
                    "threshold": threshold,
                    "normal_support": len(full["values"]),
                    "support_statuses": dict(statuses),
                    "threshold_equal_statuses": dict(equal_statuses),
                    "threshold_equal_cases": dict(equal_cases),
                    "threshold_equal_affected_identities": dict(equal_identities),
                    "upper_tail_weight": tail_weight,
                    "upper_tail_weight_by_status": dict(weighted_tail),
                    "upper_tail_affected_only_fraction": (weighted_tail["AFFECTED_ONLY"] / tail_weight
                                                            if tail_weight else None),
                    "upper_tail_any_affected_fraction": (
                        (weighted_tail["AFFECTED_ONLY"] + weighted_tail["MIXED_TIE"]) / tail_weight
                        if tail_weight else None),
                }

    # Compare affected-set identities against primary.
    identity_comparison = {}
    primary_ids = affected_id_sets["primary"]
    for variant, identities in affected_id_sets.items():
        union = primary_ids | identities
        intersection = primary_ids & identities
        identity_comparison[variant] = {
            "same_as_primary": identities == primary_ids,
            "primary_count": len(primary_ids), "variant_count": len(identities),
            "intersection": len(intersection), "only_primary": len(primary_ids - identities),
            "only_variant": len(identities - primary_ids),
            "jaccard": len(intersection) / len(union) if union else 1.0,
        }

    # Capacity and max-attribution summaries.
    capacity_summary = {}
    dominance_summary = {}
    f1_summary = {}
    for variant in VARIANTS:
        capacity_summary[variant] = {}
        dominance_summary[variant] = {}
        f1_summary[variant] = {}
        for modality in MODALITIES:
            for arm in ARMS:
                detector = f"{arm}-{modality}"
                cap = capacity[(variant, detector)]
                capacity_summary[variant][detector] = {
                    "mean_effective_df": math.fsum(cap["df"]) / len(cap["df"]),
                    "mean_active_columns": math.fsum(cap["active"]) / len(cap["active"]),
                    "model_count": cap["models"],
                    "affected_model_count": cap["affected_models"],
                }
                counts = dominance[(variant, detector)]
                scored = counts["AFFECTED_ONLY"] + counts["MIXED_TIE"] + counts["UNAFFECTED_ONLY"]
                dominance_summary[variant][detector] = {
                    "scored_bins": scored,
                    "affected_only": counts["AFFECTED_ONLY"],
                    "mixed_tie": counts["MIXED_TIE"],
                    "unaffected_only": counts["UNAFFECTED_ONLY"],
                    "unavailable": counts["UNAVAILABLE"],
                    "affected_only_fraction": counts["AFFECTED_ONLY"] / scored,
                    "any_affected_fraction": (counts["AFFECTED_ONLY"] + counts["MIXED_TIE"]) / scored,
                    "affected_argmax_bins_by_type": dict(dominance_by_type[(variant, detector)]),
                }
                f1_summary[variant][detector] = float(
                    outcome_documents[variant][detector]["summary"]["macro"]["f1"])

    # Service/type concentration among affected scalers.
    affected_concentration = {}
    for variant, records in support_records.items():
        affected_concentration[variant] = {
            "by_type": dict(Counter(record["type"] for record in records)),
            "by_channel": dict(Counter(record["channel"] for record in records).most_common()),
            "top_services": dict(Counter(record["service"] for record in records).most_common(15)),
        }

    # CSV is intentionally aggregated at case/config/arm/modality, not channel-row dump.
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / "scale-summary.csv"
    fields = list(csv_rows[0])
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(csv_rows)

    summary = {
        "labels": ["POST-HOC DEVELOPMENT DIAGNOSTIC", "NOT FINAL EFFICACY",
                   "NOT PARAMETER SELECTION", "NO METHOD CHANGE AUTHORIZED"],
        "baseline": {
            "P_HEAD_expected": P_HEAD, "W_HEAD_expected": W_HEAD, "td_sha256": TD_SHA,
            "primary_run": PRIMARY.name, "sensitivity_run": SENSITIVITY.name,
            "primary_run_contract_sha256": sha256(PRIMARY / "run-contract.json"),
            "primary_predictions_seal_sha256": sha256(PRIMARY / "predictions-seal.json"),
            "sensitivity_run_contract_sha256": sha256(SENSITIVITY / "run-contract.json"),
            "sensitivity_predictions_seal_sha256": sha256(SENSITIVITY / "predictions-seal.json"),
            "selected_lambda": selected_lambda,
        },
        "prevalence": prevalence,
        "affected_identity_comparison": identity_comparison,
        "affected_concentration": affected_concentration,
        "forecast_loss": forecast_summary,
        "system_max": dominance_summary,
        "thresholds": threshold_summary,
        "capacity": capacity_summary,
        "f1": f1_summary,
        "csv_rows": len(csv_rows),
        "csv_sha256": sha256(csv_path),
    }
    print(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    analyze()
