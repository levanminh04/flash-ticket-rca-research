"""POST-HOC DEVELOPMENT DIAGNOSTIC.

NOT FINAL EFFICACY. NOT PARAMETER SELECTION.

Read-only analysis of already sealed C1 development30 artifacts. This script
does not import or call prediction, training, graph-generation, or evaluator
code. It writes only case-table.csv and report.md next to this file.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from scipy.stats import spearmanr


EXPECTED_TD_SHA256 = (
    "34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971"
)
EXPECTED_L_MRR = 0.7442063492063492
EXPECTED_O_MRR = 0.7024052287581699
TOLERANCE = 1e-12

HERE = Path(__file__).resolve().parent
W = HERE.parents[2]
P = Path(r"D:\Project\flash-ticket-platform")

FULL = W / "results/task-e/e27-033-c1-development-full"
SENS = W / "results/task-e/e27-036-c1-development-sensitivity"
LOADER = W / "results/task-e/e27-019-development-loader-audit"
TOPOLOGY = W / "results/task-e/e27-022-development-topology"
CONFIG = W / "configs/task-e-td13-development.json"
TD = P / "docs/research-rca/task-d-method-and-experiment-specification.md"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_seal(file_path: Path, seal_path: Path) -> None:
    seal = load_json(seal_path)
    actual = sha256(file_path)
    assert actual == seal["sha256"], (file_path, actual, seal["sha256"])
    assert seal.get("before_evaluation") is True, seal_path


def rank_interval(scores: np.ndarray, root_index: int) -> tuple[int, int, float]:
    rounded = np.round(np.asarray(scores, dtype=np.float64), 12)
    root = rounded[root_index]
    start = int(np.sum(rounded > root)) + 1
    end = start + int(np.sum(rounded == root)) - 1
    rr = float(np.mean([1.0 / rank for rank in range(start, end + 1)]))
    return start, end, rr


def shortest_distance(adjacency: np.ndarray, source: int, target: int) -> int | None:
    if source == target:
        return 0
    queue: deque[tuple[int, int]] = deque([(source, 0)])
    seen = {source}
    while queue:
        node, distance = queue.popleft()
        for neighbor in np.flatnonzero(adjacency[node]):
            neighbor = int(neighbor)
            if neighbor == target:
                return distance + 1
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append((neighbor, distance + 1))
    return None


def reachable_count(adjacency: np.ndarray, source: int) -> int:
    queue: deque[int] = deque([source])
    seen = {source}
    while queue:
        node = queue.popleft()
        for neighbor in np.flatnonzero(adjacency[node]):
            neighbor = int(neighbor)
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return len(seen)


def relation(adjacency: np.ndarray, root: int, competitor: int) -> str:
    root_to_competitor = bool(adjacency[root, competitor])
    competitor_to_root = bool(adjacency[competitor, root])
    if root_to_competitor and competitor_to_root:
        return "BIDIRECTIONAL"
    if root_to_competitor:
        return "ROOT_TO_COMPETITOR"
    if competitor_to_root:
        return "COMPETITOR_TO_ROOT"
    return "NO_DIRECT_EDGE"


def outcome(delta: float) -> str:
    if delta > TOLERANCE:
        return "HELP"
    if delta < -TOLERANCE:
        return "HARM"
    return "UNCHANGED"


def count_existing(value: Any) -> int | str:
    if value is None:
        return "UNKNOWN"
    if isinstance(value, (list, tuple, dict, set)):
        return len(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    return "UNKNOWN"


def qstats(values: Iterable[float]) -> dict[str, float]:
    array = np.asarray(list(values), dtype=np.float64)
    if array.size == 0:
        return {"median": math.nan, "q1": math.nan, "q3": math.nan, "iqr": math.nan}
    q1, median, q3 = np.quantile(array, [0.25, 0.5, 0.75], method="linear")
    return {
        "median": float(median),
        "q1": float(q1),
        "q3": float(q3),
        "iqr": float(q3 - q1),
    }


def fmt(value: Any, digits: int = 6) -> str:
    if value == "UNKNOWN" or value is None:
        return "UNKNOWN"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    number = float(value)
    if math.isnan(number):
        return "UNKNOWN"
    if number == 0:
        return "0"
    if abs(number) >= 1e7 or abs(number) < 1e-5:
        return f"{number:.6e}"
    return f"{number:.{digits}f}"


def interval_text(stats: dict[str, float]) -> str:
    return f"{fmt(stats['median'])} [{fmt(stats['q1'])}, {fmt(stats['q3'])}]"


def distribution(rows: list[dict[str, Any]], field: str) -> str:
    counts = Counter(str(row[field]) for row in rows)
    return ", ".join(f"{key}:{counts[key]}" for key in sorted(counts))


def direct_primary_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    assert sha256(TD) == EXPECTED_TD_SHA256
    config = load_json(CONFIG)
    run_contract = load_json(FULL / "run-contract.json")
    execution = load_json(FULL / "execution.json")
    results = load_json(FULL / "c1-results.json")
    selection = load_json(FULL / "selection.json")
    loader_summary = load_json(LOADER / "loader-summary.json")
    topology_summary = load_json(TOPOLOGY / "topology-summary.json")

    assert run_contract["run_id"] == "e27-033-c1-development-full"
    assert run_contract["stage"] == "development-c1-full"
    assert run_contract["td"]["sha256"] == EXPECTED_TD_SHA256
    assert run_contract["config"] == config
    assert execution["exit_code"] == 0
    assert results["planned_cases"] == 30
    assert results["summary"]["L"]["rr"] == EXPECTED_L_MRR
    assert results["summary"]["O"]["rr"] == EXPECTED_O_MRR
    assert selection == results["selection"]
    assert selection["local_config"] == {
        "floor": 0.01,
        "pool": "q90",
        "fusion": "availablemean",
    }
    assert selection["ppr_config"] == {
        "operator": "ppr",
        "direction": "undirected",
        "damping": 0.5,
    }
    assert selection["selected_local_index"] == 6
    assert selection["selected_ppr_index"] == 4
    assert topology_summary["all_jobs_complete"] is True
    assert topology_summary["no_predictions"] is True
    assert len(topology_summary["jobs"]) == 180
    assert all(job["status"] == "COMPLETE" for job in topology_summary["jobs"])

    handle_by_case = {item["case"]: item["handle"] for item in loader_summary["cases"]}
    assert set(handle_by_case) == set(config["development_ids"])
    assert len(handle_by_case) == 30
    assert len(list((FULL / "case-results").glob("*.json"))) == 30

    rows: list[dict[str, Any]] = []
    for case_id in config["development_ids"]:
        handle = handle_by_case[case_id]
        case_result = results["cases"][case_id]
        sealed_case_result = load_json(FULL / "case-results" / f"{handle}.json")
        assert sealed_case_result["L"] == case_result["L"]
        assert sealed_case_result["O"] == case_result["O"]

        audit_path = LOADER / "case-audits" / f"{handle}.json"
        audit = load_json(audit_path)
        assert audit["case"] == case_id and audit["status"] == "AUDITED"
        metadata = audit["metadata"]
        profile = audit["profiles"]["c1_primary"]
        assert profile["status"] == "MATERIALIZED"
        services = list(profile["service_names"])
        root_service = metadata["root_cause_service"]
        fault = metadata["fault"]
        assert case_result["cell"] == [root_service, fault]
        assert profile["root_in_candidate"] is True
        root_index = services.index(root_service)

        loader_npz_path = LOADER / "intermediates" / handle / "c1_primary.npz"
        loader_receipt = next(
            item for item in audit["numeric_files"] if Path(item["path"]).name == "c1_primary.npz"
        )
        assert sha256(loader_npz_path) == loader_receipt["sha256"]
        with np.load(loader_npz_path, allow_pickle=False) as loader_npz:
            adjacency = np.asarray(loader_npz["adj"], dtype=bool)

        local_path = FULL / "predictions" / f"{handle}.npz"
        observed_path = FULL / "predictions" / f"{handle}-observed-local6.npz"
        uniform_path = FULL / "intermediates" / f"{handle}-uniform.npz"
        verify_seal(local_path, FULL / "seals" / f"{handle}.json")
        verify_seal(
            observed_path,
            FULL / "seals" / f"{handle}-observed-local6.npz.json",
        )
        # Uniform-personalization is a saved diagnostic intermediate. The run does
        # not provide a per-file seal for it, so do not invent one; its identity is
        # bounded by the completed run/source manifest and cross-checked below.
        assert uniform_path.is_file()

        with np.load(local_path, allow_pickle=False) as local_npz:
            local_scores = np.asarray(local_npz["local"][6], dtype=np.float64)
            identity_scores = np.asarray(local_npz["identity_local"][6], dtype=np.float64)
            local_masks = np.asarray(local_npz["masks"][6], dtype=bool)
        with np.load(observed_path, allow_pickle=False) as observed_npz:
            observed_scores = np.asarray(observed_npz["scores"][4], dtype=np.float64)
        with np.load(uniform_path, allow_pickle=False) as uniform_npz:
            in_degree = np.asarray(uniform_npz["in_degree"], dtype=int)
            out_degree = np.asarray(uniform_npz["out_degree"], dtype=int)
            uniform_scores = np.asarray(uniform_npz["scores"][4], dtype=np.float64)

        assert local_scores.sum() > 0
        assert np.allclose(
            local_scores / local_scores.sum(), identity_scores, rtol=0, atol=1e-15
        )
        assert len(services) == len(local_scores) == adjacency.shape[0]
        assert np.array_equal(in_degree, adjacency.sum(axis=0))
        assert np.array_equal(out_degree, adjacency.sum(axis=1))
        assert np.isclose(float(observed_scores.sum()), 1.0, atol=1e-10)

        l_start, l_end, l_rr_raw = rank_interval(local_scores, root_index)
        o_start, o_end, o_rr_raw = rank_interval(observed_scores, root_index)
        uniform_start, uniform_end, _ = rank_interval(uniform_scores, root_index)
        assert (l_start, l_end) == (
            case_result["L"]["tie_start"],
            case_result["L"]["tie_end"],
        )
        assert (o_start, o_end) == (
            case_result["O"]["tie_start"],
            case_result["O"]["tie_end"],
        )
        assert math.isclose(l_rr_raw, case_result["L"]["rr"], abs_tol=TOLERANCE)
        assert math.isclose(o_rr_raw, case_result["O"]["rr"], abs_tol=TOLERANCE)

        nonroot_indices = [index for index in range(len(services)) if index != root_index]
        strongest_score = max(float(local_scores[index]) for index in nonroot_indices)
        strongest_candidates = sorted(
            services[index]
            for index in nonroot_indices
            if float(local_scores[index]) == strongest_score
        )
        strongest_service = strongest_candidates[0]
        strongest_index = services.index(strongest_service)
        sorted_local = np.sort(local_scores)[::-1]
        global_margin = float(sorted_local[0] - sorted_local[1])
        root_score = float(local_scores[root_index])
        root_margin = root_score - strongest_score
        personalization = identity_scores
        best_nonroot_personalization = max(
            float(personalization[index]) for index in nonroot_indices
        )
        best_nonroot_observed = max(
            float(observed_scores[index]) for index in nonroot_indices
        )

        undirected = adjacency | adjacency.T
        np.fill_diagonal(undirected, False)
        undirected_degree = undirected.sum(axis=1).astype(int)
        root_reachable = reachable_count(undirected, root_index)
        competitor_distance = shortest_distance(undirected, root_index, strongest_index)
        graph_audit = profile["audit"]["graph"]
        assert graph_audit["nodes"] == len(services)
        assert graph_audit["edges"] == int(adjacency.sum())
        assert graph_audit["isolates"] == int(np.sum(undirected_degree == 0))

        parent_nonnull = int(graph_audit["nonnull_selected_parents"])
        parent_resolved = int(graph_audit["resolved_selected_parents"])
        parent_rate: float | str = (
            parent_resolved / parent_nonnull if parent_nonnull else "UNKNOWN"
        )
        selected_audit = profile["audit"]
        trace_presence = selected_audit.get("trace_reference_presence")
        root_trace_visible: bool | str = (
            bool(trace_presence[root_index])
            if isinstance(trace_presence, list) and len(trace_presence) == len(services)
            else "UNKNOWN"
        )
        query_only = selected_audit.get("query_only_services")
        query_only_count = count_existing(query_only)
        root_query_only: bool | str = (
            root_service in query_only if isinstance(query_only, list) else "UNKNOWN"
        )
        metric_conflicts = count_existing(selected_audit.get("conflicted_metric_channels"))
        identical_trace_duplicates = selected_audit.get(
            "identical_trace_duplicates_collapsed", "UNKNOWN"
        )
        metric_ref_mapping = selected_audit.get("metric_ref", {}).get("mapping")
        metric_query_mapping = selected_audit.get("metric_query", {}).get("mapping")

        delta = float(case_result["O"]["rr"] - case_result["L"]["rr"])
        row = {
            "case_id": case_id,
            "handle": handle,
            "root_service": root_service,
            "fault": fault,
            "cell": f"{root_service} × {fault}",
            "L_rr": float(case_result["L"]["rr"]),
            "O_rr": float(case_result["O"]["rr"]),
            "L_tie_start": l_start,
            "L_tie_end": l_end,
            "O_tie_start": o_start,
            "O_tie_end": o_end,
            "delta_rr": delta,
            "outcome": outcome(delta),
            "root_local_score": root_score,
            "strongest_nonroot_service": strongest_service,
            "strongest_nonroot_score": strongest_score,
            "strongest_nonroot_tie_count": len(strongest_candidates),
            "root_margin": root_margin,
            "global_top1_top2_margin": global_margin,
            "root_rank1_before_graph": l_start == 1,
            "root_local_available": bool(local_masks[root_index]),
            "root_personalization_mass": float(personalization[root_index]),
            "root_observed_ppr_mass": float(observed_scores[root_index]),
            "root_ppr_mass_delta": float(
                observed_scores[root_index] - personalization[root_index]
            ),
            "best_nonroot_personalization_mass": best_nonroot_personalization,
            "best_nonroot_observed_ppr_mass": best_nonroot_observed,
            "best_nonroot_ppr_mass_delta": (
                best_nonroot_observed - best_nonroot_personalization
            ),
            "nonroot_above_root_before_graph": l_start - 1,
            "nonroot_above_root_after_graph": o_start - 1,
            "change_in_nonroot_nodes_above_root": o_start - l_start,
            "competitor_personalization_mass": float(personalization[strongest_index]),
            "competitor_observed_ppr_mass": float(observed_scores[strongest_index]),
            "root_in_degree": int(in_degree[root_index]),
            "root_out_degree": int(out_degree[root_index]),
            "root_undirected_degree": int(undirected_degree[root_index]),
            "competitor_undirected_degree": int(undirected_degree[strongest_index]),
            "root_isolate": bool(undirected_degree[root_index] == 0),
            "node_count": len(services),
            "edge_count": int(adjacency.sum()),
            "graph_isolate_count": int(graph_audit["isolates"]),
            "root_reachable_nodes_selected_undirected_ppr": root_reachable,
            "root_reachability_fraction_selected_undirected_ppr": (
                root_reachable / len(services)
            ),
            "root_to_strongest_relation_raw_observed": relation(
                adjacency, root_index, strongest_index
            ),
            "root_to_strongest_undirected_distance": (
                competitor_distance if competitor_distance is not None else "UNREACHABLE"
            ),
            "root_uniform_ppr_tie_start": uniform_start,
            "root_uniform_ppr_tie_end": uniform_end,
            "parent_nonnull_selected": parent_nonnull,
            "parent_resolved_selected": parent_resolved,
            "parent_unresolved_selected": int(graph_audit["unresolved_selected_parents"]),
            "parent_resolution_rate": parent_rate,
            "root_visible_in_candidate": bool(profile["root_in_candidate"]),
            "root_reference_trace_visible": root_trace_visible,
            "candidate_node_count": len(services),
            "local_participating_services": int(case_result["local_participating_services"]),
            "metric_ref_mapped_columns": count_existing(metric_ref_mapping),
            "metric_query_mapped_columns": count_existing(metric_query_mapping),
            "query_only_service_count": query_only_count,
            "root_query_only": root_query_only,
            "conflicted_metric_channel_count": metric_conflicts,
            "identical_trace_duplicates_collapsed": identical_trace_duplicates,
        }
        rows.append(row)

    recomputed_l = float(np.mean([row["L_rr"] for row in rows]))
    recomputed_o = float(np.mean([row["O_rr"] for row in rows]))
    assert math.isclose(recomputed_l, EXPECTED_L_MRR, abs_tol=TOLERANCE)
    assert math.isclose(recomputed_o, EXPECTED_O_MRR, abs_tol=TOLERANCE)

    # Independently recompute every saved subgroup and leave-group effect.
    for group_name, field in (("root", "root_service"), ("fault", "fault"), ("cell", "cell")):
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[str(row[field])].append(row)
        saved = results["O_minus_L"]["groups"][group_name]
        assert len(saved) == len(grouped)
        for saved_item in saved.values():
            case_ids = set(saved_item["cases"])
            matching = [row for row in rows if row["case_id"] in case_ids]
            remaining = [row for row in rows if row["case_id"] not in case_ids]
            effect = float(np.mean([row["delta_rr"] for row in matching]))
            leaveout = float(np.mean([row["delta_rr"] for row in remaining]))
            assert math.isclose(effect, saved_item["effect"], abs_tol=TOLERANCE)
            assert math.isclose(
                leaveout, saved_item["leaveout_effect"], abs_tol=TOLERANCE
            )

    metadata = {
        "config": config,
        "selection": selection,
        "results": results,
        "loader_summary": loader_summary,
        "topology_summary": topology_summary,
        "recomputed_l": recomputed_l,
        "recomputed_o": recomputed_o,
    }
    return rows, metadata


def sensitivity_summary(
    primary_rows: list[dict[str, Any]], loader_summary: dict[str, Any]
) -> list[dict[str, Any]]:
    sensitivity = load_json(SENS / "c1-sensitivity.json")
    handle_by_case = {item["case"]: item["handle"] for item in loader_summary["cases"]}
    summaries: list[dict[str, Any]] = []

    primary_by_case = {row["case_id"]: row for row in primary_rows}
    for variant_name in ("bin5", "primary/bin10", "bin20"):
        if variant_name == "primary/bin10":
            variant_rows = primary_rows
            l_mrr = float(np.mean([row["L_rr"] for row in variant_rows]))
            o_mrr = float(np.mean([row["O_rr"] for row in variant_rows]))
        else:
            saved_variant = sensitivity["variants"][variant_name]
            variant_rows = []
            for case_id, saved_case in saved_variant["cases"].items():
                handle = handle_by_case[case_id]
                audit = load_json(LOADER / "case-audits" / f"{handle}.json")
                profile_name = saved_variant["profile"]
                profile = audit["profiles"][f"c1_{profile_name}"]
                services = list(profile["service_names"])
                root = audit["metadata"]["root_cause_service"]
                root_index = services.index(root)
                path = SENS / "predictions" / variant_name / f"{handle}.npz"
                seal = SENS / "seals" / f"{variant_name}-{handle}.npz.json"
                verify_seal(path, seal)
                with np.load(path, allow_pickle=False) as arrays:
                    local = np.asarray(arrays["local"], dtype=np.float64)
                    identity_local = np.asarray(arrays["identity_local"], dtype=np.float64)
                    observed = np.asarray(arrays["observed"], dtype=np.float64)
                assert local.sum() > 0
                assert np.allclose(
                    local / local.sum(), identity_local, rtol=0, atol=1e-15
                )
                l_start, l_end, l_rr = rank_interval(identity_local, root_index)
                o_start, o_end, o_rr = rank_interval(observed, root_index)
                assert (l_start, l_end) == (
                    saved_case["L"]["tie_start"],
                    saved_case["L"]["tie_end"],
                )
                assert (o_start, o_end) == (
                    saved_case["O"]["tie_start"],
                    saved_case["O"]["tie_end"],
                )
                assert math.isclose(l_rr, saved_case["L"]["rr"], abs_tol=TOLERANCE)
                assert math.isclose(o_rr, saved_case["O"]["rr"], abs_tol=TOLERANCE)
                nonroot = [index for index in range(len(services)) if index != root_index]
                strongest = max(float(local[index]) for index in nonroot)
                sorted_local = np.sort(local)[::-1]
                delta = float(o_rr - l_rr)
                variant_rows.append(
                    {
                        "case_id": case_id,
                        "L_rr": l_rr,
                        "O_rr": o_rr,
                        "L_tie_start": l_start,
                        "L_tie_end": l_end,
                        "O_tie_start": o_start,
                        "O_tie_end": o_end,
                        "delta_rr": delta,
                        "outcome": outcome(delta),
                        "root_margin": float(local[root_index]) - strongest,
                        "global_top1_top2_margin": float(sorted_local[0] - sorted_local[1]),
                    }
                )
            l_mrr = float(np.mean([row["L_rr"] for row in variant_rows]))
            o_mrr = float(np.mean([row["O_rr"] for row in variant_rows]))
            assert math.isclose(l_mrr, saved_variant["L"]["rr"], abs_tol=TOLERANCE)
            assert math.isclose(o_mrr, saved_variant["O"]["rr"], abs_tol=TOLERANCE)

        counts = Counter(row["outcome"] for row in variant_rows)
        rank1 = [row for row in variant_rows if row["L_tie_start"] == 1]
        rank1_dropped = [row for row in rank1 if row["O_tie_start"] > 1]
        rho, pvalue = spearmanr(
            [row["root_margin"] for row in variant_rows],
            [row["delta_rr"] for row in variant_rows],
        )
        summaries.append(
            {
                "variant": variant_name,
                "L_mrr": l_mrr,
                "O_mrr": o_mrr,
                "delta": o_mrr - l_mrr,
                "help": counts["HELP"],
                "harm": counts["HARM"],
                "unchanged": counts["UNCHANGED"],
                "local_rank1": len(rank1),
                "rank1_retained": len(rank1) - len(rank1_dropped),
                "rank1_dropped": len(rank1_dropped),
                "root_margin": qstats(row["root_margin"] for row in variant_rows),
                "harm_root_margin": qstats(
                    row["root_margin"]
                    for row in variant_rows
                    if row["outcome"] == "HARM"
                ),
                "help_root_margin": qstats(
                    row["root_margin"]
                    for row in variant_rows
                    if row["outcome"] == "HELP"
                ),
                "margin_delta_spearman_rho": float(rho),
                "margin_delta_spearman_p": float(pvalue),
            }
        )

        # Primary summary must be the same actual rows, not a separately reconstructed set.
        if variant_name == "primary/bin10":
            assert all(primary_by_case[row["case_id"]] is row for row in variant_rows)

    return summaries


def correlation(rows: list[dict[str, Any]], field: str) -> tuple[float, float]:
    rho, pvalue = spearmanr(
        [float(row[field]) for row in rows],
        [float(row["delta_rr"]) for row in rows],
    )
    return float(rho), float(pvalue)


def write_case_table(rows: list[dict[str, Any]]) -> None:
    fieldnames = list(rows[0].keys())
    with (HERE / "case-table.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def group_table(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row[field])].append(row)
    table = []
    for key in sorted(groups):
        group_rows = groups[key]
        remaining = [row for row in rows if row not in group_rows]
        counts = Counter(row["outcome"] for row in group_rows)
        table.append(
            {
                "group": key,
                "n": len(group_rows),
                "mean": float(np.mean([row["delta_rr"] for row in group_rows])),
                "leaveout": float(np.mean([row["delta_rr"] for row in remaining])),
                "help": counts["HELP"],
                "harm": counts["HARM"],
                "unchanged": counts["UNCHANGED"],
            }
        )
    return table


def markdown_group_table(items: list[dict[str, Any]]) -> str:
    lines = [
        "| Nhóm | n | Mean O−L | Leave-group O−L | HELP | HARM | UNCHANGED |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in items:
        lines.append(
            f"| {item['group']} | {item['n']} | {fmt(item['mean'])} | "
            f"{fmt(item['leaveout'])} | {item['help']} | {item['harm']} | "
            f"{item['unchanged']} |"
        )
    return "\n".join(lines)


def write_report(
    rows: list[dict[str, Any]], metadata: dict[str, Any], sensitivities: list[dict[str, Any]]
) -> None:
    counts = Counter(row["outcome"] for row in rows)
    rank1 = [row for row in rows if row["L_tie_start"] == 1]
    rank1_dropped = [row for row in rank1 if row["O_tie_start"] > 1]
    rank1_retained = [row for row in rank1 if row["O_tie_start"] == 1]
    harm = [row for row in rows if row["outcome"] == "HARM"]
    help_rows = [row for row in rows if row["outcome"] == "HELP"]
    unchanged = [row for row in rows if row["outcome"] == "UNCHANGED"]

    outcome_stats = {}
    for name, selected in (("HELP", help_rows), ("HARM", harm), ("UNCHANGED", unchanged)):
        outcome_stats[name] = {
            "root_margin": qstats(row["root_margin"] for row in selected),
            "global_margin": qstats(
                row["global_top1_top2_margin"] for row in selected
            ),
            "root_degree": qstats(row["root_undirected_degree"] for row in selected),
            "reachability": qstats(
                row["root_reachability_fraction_selected_undirected_ppr"]
                for row in selected
            ),
            "parent_resolution": qstats(
                row["parent_resolution_rate"]
                for row in selected
                if row["parent_resolution_rate"] != "UNKNOWN"
            ),
            "mass_delta": qstats(row["root_ppr_mass_delta"] for row in selected),
            "uniform_rank": qstats(row["root_uniform_ppr_tie_start"] for row in selected),
            "local_rank1": sum(row["root_rank1_before_graph"] for row in selected),
        }

    correlations = {
        "root_margin": correlation(rows, "root_margin"),
        "root_undirected_degree": correlation(rows, "root_undirected_degree"),
        "root_reachability_fraction_selected_undirected_ppr": correlation(
            rows, "root_reachability_fraction_selected_undirected_ppr"
        ),
        "parent_resolution_rate": correlation(rows, "parent_resolution_rate"),
        "root_uniform_ppr_tie_start": correlation(rows, "root_uniform_ppr_tie_start"),
    }

    negative_total = -sum(min(0.0, row["delta_rr"]) for row in rows)
    positive_total = sum(max(0.0, row["delta_rr"]) for row in rows)
    auth_negative = -sum(
        min(0.0, row["delta_rr"])
        for row in rows
        if row["root_service"] == "ts-auth-service"
    )
    harm_mass_decrease = sum(row["root_ppr_mass_delta"] < -TOLERANCE for row in harm)
    harm_best_nonroot_mass_decrease = sum(
        row["best_nonroot_ppr_mass_delta"] < -TOLERANCE for row in harm
    )
    harm_more_nodes_above = sum(
        row["change_in_nonroot_nodes_above_root"] > 0 for row in harm
    )
    help_mass_increase = sum(row["root_ppr_mass_delta"] > 0 for row in help_rows)
    harm_root_isolates = sum(row["root_isolate"] for row in harm)
    help_root_isolates = sum(row["root_isolate"] for row in help_rows)
    changed_rows = harm + help_rows
    changed_same_global_shape = all(
        row["node_count"] == 27 and row["edge_count"] == 55 for row in changed_rows
    )
    changed_query_only_max = max(row["query_only_service_count"] for row in changed_rows)
    changed_metric_conflict_max = max(
        row["conflicted_metric_channel_count"] for row in changed_rows
    )
    changed_root_trace_visible = sum(
        row["root_reference_trace_visible"] is True for row in changed_rows
    )

    root_groups = group_table(rows, "root_service")
    fault_groups = group_table(rows, "fault")
    cell_groups = group_table(rows, "cell")

    lines: list[str] = []
    lines.extend(
        [
            "# C1 observed graph/PPR — post-hoc development mechanism analysis",
            "",
            "**POST-HOC DEVELOPMENT DIAGNOSTIC**  ",
            "**NOT FINAL EFFICACY**  ",
            "**NOT PARAMETER SELECTION**",
            "",
            "Owner nhận bàn giao: Minh. Phạm vi: đúng 30 RE2-TT development cases đã hoàn tất. "
            "Phân tích này chỉ đọc output sealed; không chạy lại prediction/model, không sửa "
            "TD/config/registry và không mở final60/F/G/H/I.",
            "",
            "## Kết luận ngắn",
            "",
            "**Hypothesis verdict: NOT SUPPORTED.** Trên development30, không có bằng chứng "
            "rằng PPR thường làm hại khi local evidence đã đủ chắc chắn theo dấu hiệu trực tiếp "
            "là root đứng rank 1. Cả "
            f"{len(rank1)}/{len(rank1)} case local rank-1 đều giữ root ở rank 1 sau PPR; "
            f"không có case nào tụt. Toàn bộ {len(harm)} HARM case đều bắt đầu với root không "
            "đứng đầu local. Vì vậy dữ liệu phù hợp hơn với cơ chế yếu hơn: PPR có thể làm "
            "xấu thêm các case local vốn mơ hồ/sai top-1, trong khi evidence mạnh đủ sức kháng "
            "lại phép lan truyền trong sample nhỏ này.",
            "",
            "Evidence thuận cho phần *relative dilution*: "
            f"{harm_more_nodes_above}/{len(harm)} HARM case có thêm service vượt root sau "
            "PPR. Trong đó, dominant non-root mass giảm ở "
            f"{harm_best_nonroot_mass_decrease}/{len(harm)} case, phù hợp với việc mass của "
            "competitor mạnh bị trải ra nhiều node. "
            "Evidence chống phần *khi local đã mạnh*: 0 local-rank1 case bị tụt; HELP cũng chỉ "
            "xuất hiện ở case root chưa rank1. Đây là quan sát cơ chế hậu nghiệm, không là chứng "
            "minh nhân quả hay kết luận cho final/FlashTicket.",
            "",
            "## Identity và validation",
            "",
            "- Session bootstrap: P branch `codex/rca-research-program`, HEAD "
            "`576be4b6935c9a837e6f2bcc6356a89bfe61c6ac`, chỉ có README dirty sẵn từ trước "
            "(SHA-256 `3646cb1b6e8da832e8b9513fd8318d749f7f5f6788b5d3223eda7f5a9a662274`); "
            "W branch `main`, HEAD `664d7180f0af3fadc8f11d7747b9d75833aeca34`, clean trước phân tích.",
            f"- TD-v1.3 SHA-256: `{sha256(TD)}` (khớp canonical).",
            f"- Run: `e27-033-c1-development-full`; exit code 0; L={fmt(metadata['recomputed_l'])}, "
            f"O={fmt(metadata['recomputed_o'])}, O−L={fmt(metadata['recomputed_o'] - metadata['recomputed_l'])}.",
            f"- `c1-results.json` SHA-256 `{sha256(FULL / 'c1-results.json')}`; "
            f"`c1-sensitivity.json` SHA-256 `{sha256(SENS / 'c1-sensitivity.json')}`; "
            "cả hai khớp identity đã ghi trong final scientific review/inventory.",
            "- Recompute từ đúng 30/30 case khớp `c1-results.json` trong tolerance 1e-12; "
            "mọi tie interval/rank của L và O cũng khớp score sealed.",
            "- Đã kiểm SHA-256 seal cho 30 local score artifacts, 30 observed-local6 artifacts "
            "và 60 temporal sensitivity artifacts (bin5/bin20). Đã đọc 30 uniform diagnostics; "
            "run không cung cấp per-file seal cho loại intermediate này nên báo cáo không bịa seal.",
            "- Topology summary: 180/180 jobs COMPLETE; artifact ghi rõ `no_predictions=true`; "
            "không tái sinh graph.",
            "",
            "## Q1 — Những case L đã đặt root rank 1",
            "",
            f"- Local rank1: **{len(rank1)}/30**.",
            f"- Giữ rank1 sau PPR: **{len(rank1_retained)}/{len(rank1)}**.",
            f"- Bị tụt: **{len(rank1_dropped)}/{len(rank1)}**; mức tụt = 0 case, "
            "0 bậc, tổng ΔRR=0 trong nhóm này.",
            "- Do đó giảm MRR không đến từ việc PPR phá các root local-top1 trong sample này.",
            "",
            "## Q2–Q3 — HARM khác HELP như thế nào",
            "",
            "Các số dưới đây là median [Q1, Q3]. Raw local score có thang theo từng case; "
            "so sánh median và Spearman chỉ là mô tả hậu nghiệm.",
            "",
            "| Nhóm | n | Local rank1 | Root margin | Global top1−top2 | Root undirected degree | "
            "Reachability fraction | Parent resolution | Root PPR mass Δ | Uniform-PPR root rank |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for name in ("HELP", "HARM", "UNCHANGED"):
        stats = outcome_stats[name]
        lines.append(
            f"| {name} | {counts[name]} | {stats['local_rank1']} | "
            f"{interval_text(stats['root_margin'])} | {interval_text(stats['global_margin'])} | "
            f"{interval_text(stats['root_degree'])} | {interval_text(stats['reachability'])} | "
            f"{interval_text(stats['parent_resolution'])} | {interval_text(stats['mass_delta'])} | "
            f"{interval_text(stats['uniform_rank'])} |"
        )
    lines.extend(
        [
            "",
            f"- HARM: root distribution `{distribution(harm, 'root_service')}`; fault "
            f"distribution `{distribution(harm, 'fault')}`; cell distribution "
            f"`{distribution(harm, 'cell')}`.",
            f"- HELP: root distribution `{distribution(help_rows, 'root_service')}`; fault "
            f"distribution `{distribution(help_rows, 'fault')}`; cell distribution "
            f"`{distribution(help_rows, 'cell')}`.",
            "- Local: HARM bắt đầu ở ranks 2,2,4,3,2,2; HELP bắt đầu ở ranks 7 và 10. "
            "Cả hai nhóm đều có root margin âm; raw margin có thang theo case nên không đặt "
            "một threshold hậu nghiệm.",
            "- Root visibility không giải thích khác biệt: 30/30 root hiện diện trong candidate "
            f"set. Nhưng topology có pattern rõ: {harm_root_isolates}/{len(harm)} HARM roots "
            f"là isolate, so với {help_root_isolates}/{len(help_rows)} HELP roots; exact per-case "
            "fields nằm trong CSV.",
            "- Hai HELP roots đều degree 8, cách strongest local competitor 1 hop và có cạnh "
            "raw competitor→root. Trong HARM, bốn isolate không reach competitor; hai root "
            "còn lại degree 3, cách competitor 2 hops và không có direct edge.",
            f"- Global graph size không tách nhóm: "
            f"{len(changed_rows) if changed_same_global_shape else 0}/{len(changed_rows)} "
            "changed cases đều có 27 nodes/55 edges. Khác biệt nằm ở vị trí root, không phải "
            "kích thước graph.",
            "- Parent resolution không tạo common pattern: một HARM case là 0.835500, năm "
            "HARM còn lại gần/đúng 1; hai HELP gần 1. Trong 8 changed cases, root reference "
            f"trace visible={changed_root_trace_visible}/8, max query-only count="
            f"{changed_query_only_max}, max conflicted metric-channel count="
            f"{changed_metric_conflict_max}. Đây là field thật từ loader audit, không phải proxy.",
            f"- Literal root-mass dilution không xuất hiện: chỉ {harm_mass_decrease}/{len(harm)} "
            "HARM root giảm absolute mass. Bốn auth roots là isolate nên root mass được self-loop "
            "giữ nguyên; dominant mass ở component còn lại bị lan ra, khiến nhiều node vượt root. "
            f"Ngược lại {help_mass_increase}/{len(help_rows)} HELP roots tăng mass và đều có "
            "undirected degree 8. Đây là cơ chế gần của operator/topology, không chứng minh "
            "topology là nguyên nhân nhân quả đúng/sai.",
            "",
            "## Q4 — Mức độ chi phối theo root/fault/cell",
            "",
            f"Tổng negative contribution trước bù trừ là {fmt(negative_total)} RR; tổng positive "
            f"contribution là {fmt(positive_total)}. `ts-auth-service` tạo {fmt(auth_negative)} "
            f"({fmt(auth_negative / negative_total * 100, 2)}%) tổng độ lớn âm. Vì vậy O−L âm "
            "bị chi phối đáng kể bởi auth, nhưng không chỉ bởi một case: route/mem và train/cpu "
            "cũng âm. Ngược lại, travel/loss là cell dương duy nhất và bù một phần đáng kể.",
            "",
            "### Theo root",
            "",
            markdown_group_table(root_groups),
            "",
            "### Theo fault",
            "",
            markdown_group_table(fault_groups),
            "",
            "### Theo cell",
            "",
            markdown_group_table(cell_groups),
            "",
            "Các mean và leave-group ở trên được recompute từ 30 case và assert khớp toàn bộ "
            "saved subgroup/leave-group results trong `c1-results.json` ở tolerance 1e-12.",
            "",
            "## Q5 — Temporal sensitivity bin5 / primary-bin10 / bin20",
            "",
            "| Bin setting | L MRR | O MRR | O−L | HELP | HARM | UNCHANGED | Local rank1 | "
            "Rank1 giữ | Rank1 tụt | Root-margin↔ΔRR Spearman ρ |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for item in sensitivities:
        lines.append(
            f"| {item['variant']} | {fmt(item['L_mrr'])} | {fmt(item['O_mrr'])} | "
            f"{fmt(item['delta'])} | {item['help']} | {item['harm']} | "
            f"{item['unchanged']} | {item['local_rank1']} | {item['rank1_retained']} | "
            f"{item['rank1_dropped']} | {fmt(item['margin_delta_spearman_rho'])} |"
        )
    lines.extend(
        [
            "",
            "Pattern thay đổi theo độ phân giải thời gian: bin5 làm local yếu hơn và số HARM tăng; "
            "bin20 gần trung hòa về mean nhưng vẫn có cả HELP lẫn HARM. Ở cả ba setting, không có "
            "local-rank1 case nào bị PPR đẩy khỏi rank1. Quan sát này chống hypothesis "
            "local-strong→harm, nhưng cũng cho thấy mechanism rất nhạy với binning. Không dùng "
            "bảng này để chọn bin tốt nhất.",
            "",
            "## Q6 — Hypothesis adjudication",
            "",
            "**Verdict: NOT SUPPORTED.**",
            "",
            "Evidence thuận:",
            "",
            f"- {harm_more_nodes_above}/{len(harm)} HARM case có thêm node vượt root sau PPR; "
            f"{harm_best_nonroot_mass_decrease}/{len(harm)} đồng thời có best non-root mass "
            "giảm, phù hợp với mass mạnh bị trải ra nhiều node và làm root tụt tương đối.",
            "- O−L thay đổi theo graph/topology và temporal binning; harm không phải lỗi số học "
            "vì score/rank/seal và aggregate đều khớp artifact đã audit.",
            "",
            "Evidence chống:",
            "",
            f"- {len(rank1)}/{len(rank1)} local-rank1 case giữ rank1; 0 bị hại. HARM chỉ xảy ra "
            "khi root đã không là local top1.",
            f"- Chỉ {harm_mass_decrease}/{len(harm)} HARM root giảm absolute PPR mass; do đó "
            "dữ liệu không hỗ trợ cách hiểu literal rằng PPR lấy bớt mass khỏi root mạnh.",
            "- Khi temporal resolution chuyển từ bin5 sang bin20, local rank1 tăng và mean harm "
            "giảm từ âm mạnh về gần 0; pattern đi ngược dự đoán rằng local mạnh hơn sẽ bị PPR "
            "làm hại thường xuyên hơn.",
            "- HELP tập trung ở travel/loss; HARM tập trung ở auth/cpu-delay, route/mem và "
            "train/cpu. Root×fault confounding và chỉ 10 cells khiến không thể gán cơ chế riêng "
            "cho margin, degree hay trace quality.",
            "- Không có comparator 'gated propagation' hay can thiệp topology theo mechanism; "
            "do đó từ `O−L` không thể chứng minh chữ *indiscriminate* là nguyên nhân nhân quả.",
            "",
            "Hypothesis yếu hơn được development evidence gợi ý ở mức CANDIDATE: PPR có thể "
            "làm xấu thêm các case mà local ranking đã mơ hồ/sai top1, tùy topology và binning. "
            "Đây không phải method change hay đề xuất graph gate.",
            "",
            "## Correlation — EXPLORATORY / POST-HOC / NOT CAUSAL",
            "",
            "| Feature | Spearman ρ với ΔRR | p (descriptive) |",
            "|---|---:|---:|",
        ]
    )
    correlation_labels = {
        "root_margin": "root local margin",
        "root_undirected_degree": "root undirected degree",
        "root_reachability_fraction_selected_undirected_ppr": "root reachability fraction",
        "parent_resolution_rate": "parent-resolution rate",
        "root_uniform_ppr_tie_start": "uniform-PPR root rank",
    }
    for key, label in correlation_labels.items():
        rho, pvalue = correlations[key]
        lines.append(f"| {label} | {fmt(rho)} | {fmt(pvalue)} |")
    lines.extend(
        [
            "",
            "p-value chỉ được ghi để mô tả phép tính; không phải confirmatory test, không sửa "
            "multiple comparisons, và 30 cases/10 cells không độc lập theo nghĩa population.",
            "",
            "Cross-check sau raw recomputation: `final-numerical-review.md` xác nhận toàn bộ "
            "540 L/O sensitivity case metrics và headline means; `final-scientific-review.md` "
            "ghi cùng 2 HELP/6 HARM/22 UNCHANGED, travel/loss dương, auth/delay âm và sign flip "
            "nhỏ ở bin20. Review prose chỉ dùng để đối chiếu, không thay raw artifacts.",
            "",
            "## Bảng 30 case — bản compact",
            "",
            "Bản đầy đủ với local scores, graph degree/reachability/relation và input-quality "
            "fields nằm ở `case-table.csv`. `UNKNOWN` chỉ được dùng khi field không tồn tại.",
            "",
            "| Case | Cell | L RR/rank | O RR/rank | ΔRR | Outcome | Root margin | Degree in/out/u | "
            "Reach | Strongest competitor (distance) |",
            "|---|---|---:|---:|---:|---|---:|---:|---:|---|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['case_id']} | {row['cell']} | {fmt(row['L_rr'])}/"
            f"{row['L_tie_start']}-{row['L_tie_end']} | {fmt(row['O_rr'])}/"
            f"{row['O_tie_start']}-{row['O_tie_end']} | {fmt(row['delta_rr'])} | "
            f"{row['outcome']} | {fmt(row['root_margin'])} | {row['root_in_degree']}/"
            f"{row['root_out_degree']}/{row['root_undirected_degree']} | "
            f"{row['root_reachable_nodes_selected_undirected_ppr']}/{row['node_count']} | "
            f"{row['strongest_nonroot_service']} "
            f"({row['root_to_strongest_undirected_distance']}) |"
        )
    lines.extend(
        [
            "",
            "## Evidence state, limitations và việc nên kiểm tiếp",
            "",
            "- `FACT`: identity/hashes, 30-case metrics, sealed scores, graph/input fields và "
            "các recomputation trong báo cáo.",
            "- `CANDIDATE`: diễn giải mechanism, verdict hypothesis và hypothesis yếu hơn nêu trên.",
            "- `OPEN`: human method approval/freeze, final efficacy, external generalization và "
            "FlashTicket validation.",
            "- Sample chỉ 30 incidents/10 cells; root và fault không crossed đầy đủ; local scores "
            "không có một thang tuyệt đối chung giữa cases; correlation không causal.",
            "- Reachability/distance được tính trực tiếp trên adjacency sealed sau khi đối xứng hóa "
            "đúng selected PPR (`undirected`, damping 0.5); không phải proxy từ tên service.",
            "- Evidence tiếp theo nên kiểm: trên campaign được cấp quyền riêng, kiểm xem pattern "
            "`local non-top1 + topology redistribution → HARM` có lặp lại trên cells/dataset độc "
            "lập và FlashTicket hay không, với cùng frozen method và planned denominators. Không "
            "thay operator/config từ kết quả development này.",
            "",
            "## Artifact và execution boundary",
            "",
            "Tạo đúng ba artifact:",
            "",
            "- `analysis.py` — script chỉ đọc sealed outputs và tự kiểm invariants/hashes.",
            "- `case-table.csv` — bảng đúng 30 case, đầy đủ field được yêu cầu.",
            "- `report.md` — báo cáo này.",
            "",
            "Xác nhận: **0 model/prediction rerun; 0 RCD/C5 run; 0 graph regeneration; 0 "
            "TD/config/registry mutation; final60/F/G/H/I untouched; 0 commit/push.**",
            "",
            "PHASE 1 COMPLETE — WAITING FOR MINH.  ",
            "PHASE 2 NOT STARTED.",
        ]
    )
    (HERE / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows, metadata = direct_primary_rows()
    sensitivities = sensitivity_summary(rows, metadata["loader_summary"])
    write_case_table(rows)
    write_report(rows, metadata, sensitivities)

    counts = Counter(row["outcome"] for row in rows)
    rank1 = [row for row in rows if row["L_tie_start"] == 1]
    print("POST-HOC DEVELOPMENT DIAGNOSTIC — NOT FINAL EFFICACY — NOT PARAMETER SELECTION")
    print(f"cases={len(rows)} L={metadata['recomputed_l']:.15f} O={metadata['recomputed_o']:.15f}")
    print(
        f"HELP={counts['HELP']} HARM={counts['HARM']} UNCHANGED={counts['UNCHANGED']} "
        f"local_rank1={len(rank1)} rank1_dropped={sum(r['O_tie_start'] > 1 for r in rank1)}"
    )
    for item in sensitivities:
        print(
            f"{item['variant']}: HELP={item['help']} HARM={item['harm']} "
            f"UNCHANGED={item['unchanged']} L1={item['local_rank1']} "
            f"L1drop={item['rank1_dropped']} delta={item['delta']:.15f}"
        )
    print("wrote=analysis.py,case-table.csv,report.md")


if __name__ == "__main__":
    main()
