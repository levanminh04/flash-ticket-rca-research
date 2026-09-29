"""Frozen public-data RCA orchestration from admitted telemetry to packet.

The pipeline owns no selector and imports no evaluator.  Ground truth can only
be joined by a separate controller after the returned packet/prediction seal.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from .comparators import baro_scores, local_max_scores
from .contracts import FrozenReleaseConfig, load_frozen_config
from .detection import create_event_state, event_step, fit_detector, score_bin
from .observation import (
    C1Observation,
    C5Observation,
    admit_c1_bundle,
    admit_c5_bundle,
    public_c1_observation,
)
from .packet import PACKET_SCHEMA, SCORE_SEMANTICS, rank_table, seal_packet
from .ranking import local_scores, perturb_graphs, rank_scores


class PipelineError(RuntimeError):
    """Frozen core orchestration failed without altering method semantics."""


def _plain(value: Any):
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return copy.deepcopy(value)


def _source_evidence(observation) -> tuple[dict[str, Any], dict[str, list[str]]]:
    catalog = _plain(observation.evidence_catalog)
    common: list[str] = []
    for modality, digest in observation.source_hashes.items():
        evidence_id = f"source:{modality}"
        if evidence_id in catalog:
            raise PipelineError("Evidence catalog collides with source evidence ID")
        catalog[evidence_id] = {
            "kind": "public-telemetry-source",
            "modality": modality,
            "sha256_or_status": digest,
        }
        common.append(evidence_id)
    per_node = {node_id: list(common) for node_id in observation.node_ids}
    return catalog, per_node


def _graph_packet(observation, *, processing_direction: str, operator: str):
    adjacency = observation.adjacency
    degree = adjacency | adjacency.T
    return {
        "raw_relation_direction": "observed parent -> observed child",
        "raw_adjacency": adjacency.astype(np.uint8),
        "processing_direction": processing_direction,
        "operator": operator,
        "node_count": len(adjacency),
        "edge_count": int(adjacency.sum()),
        "isolates": [
            observation.node_ids[index]
            for index in np.flatnonzero(~degree.any(axis=0))
        ],
        "provenance": _plain(observation.graph_provenance),
        "causal_claim": "NONE; observed trace dependency is not a causal graph",
    }


class FrozenRcaPipeline:
    """One immutable Task F method/config identity and callable core boundary."""

    def __init__(
        self,
        config: FrozenReleaseConfig,
        *,
        code_identity: Mapping[str, str],
        release_id: str = "TASK-F-TD13-v1",
    ):
        if not isinstance(config, FrozenReleaseConfig):
            raise TypeError("FrozenReleaseConfig required")
        if not isinstance(code_identity, Mapping) or not code_identity or any(
            not isinstance(name, str)
            or not name
            or not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            for name, digest in code_identity.items()
        ):
            raise ValueError("Explicit Task F source SHA256 identity required")
        if not isinstance(release_id, str) or not release_id:
            raise ValueError("Nonempty release ID required")
        self.config = config
        self.code_identity = dict(code_identity)
        self.release_id = release_id

    @classmethod
    def from_manifest(
        cls,
        path: str | Path,
        *,
        code_identity: Mapping[str, str],
        release_id: str = "TASK-F-TD13-v1",
    ):
        return cls(
            load_frozen_config(path),
            code_identity=code_identity,
            release_id=release_id,
        )

    def _method_identity(self, mode: str) -> dict[str, Any]:
        return {
            "release_id": self.release_id,
            "mode": mode,
            "td_sha256": self.config.td_sha256,
            "frozen_config_canonical_sha256": self.config.canonical_sha256,
            "code_sha256": dict(self.code_identity),
        }

    def _base_packet(self, observation, *, mode: str, status: str):
        catalog, _ = _source_evidence(observation)
        return {
            "schema_version": PACKET_SCHEMA,
            "method_identity": self._method_identity(mode),
            "observation": {
                "opaque_handle": observation.handle,
                "source_hashes": dict(observation.source_hashes),
            },
            "status": status,
            "score_semantics": SCORE_SEMANTICS,
            "evidence_catalog": catalog,
            "quality": _plain(observation.quality),
            "uncertainty": {
                "known_limitations": _plain(self.config.manifest["limitations"]),
                "no_causal_claim": True,
                "no_probability_claim": True,
            },
        }

    def _failure_packet(self, observation, *, mode: str, status: str, exc: Exception):
        packet = self._base_packet(observation, mode=mode, status=status)
        packet["failure"] = {
            "error_type": type(exc).__name__,
            "message_redacted": True,
        }
        return seal_packet(packet)

    def run_c1(
        self,
        observation: C1Observation,
        *,
        include_structural_control: bool = True,
    ) -> dict[str, Any]:
        """Run frozen L/O/R plus secondary diffusion on one C1 observation."""
        if not isinstance(observation, C1Observation):
            raise TypeError("C1Observation required")
        try:
            evidence = local_scores(
                observation.ref,
                observation.query,
                observation.channel_types,
                dict(self.config.local),
            )
            local = evidence["local"]
            primary = rank_scores(
                local,
                observation.adjacency,
                operator=self.config.primary_ppr.operator,
                direction=self.config.primary_ppr.direction,
                damping=self.config.primary_ppr.damping,
            )
            secondary = rank_scores(
                local,
                observation.adjacency,
                operator=self.config.secondary_diffusion.operator,
                direction=self.config.secondary_diffusion.direction,
                damping=self.config.secondary_diffusion.damping,
            )
            local_max = local_max_scores(evidence["blocks"], evidence["masks"]["blocks"])
            baro = baro_scores(
                observation.ref,
                observation.query,
                observation.channel_types,
                floor=float(self.config.local["floor"]),
            )
            control = None
            control_scores = None
            if include_structural_control:
                representation = self.config.primary_ppr.direction
                control = perturb_graphs(
                    observation.adjacency,
                    observation.handle,
                    representation,
                    count=self.config.r_chains,
                    budget=self.config.r_proposals_per_edge,
                )
                control_scores = np.stack(
                    [
                        rank_scores(
                            local,
                            graph,
                            operator=self.config.primary_ppr.operator,
                            direction=self.config.primary_ppr.direction,
                            damping=self.config.primary_ppr.damping,
                        )["scores"]
                        for graph in control["graphs"]
                    ]
                )
        except (TypeError, ValueError) as exc:
            return {
                "status": "INPUT_FAILURE",
                "packet": self._failure_packet(
                    observation, mode="C1", status="INPUT_FAILURE", exc=exc
                ),
            }
        except Exception as exc:
            return {
                "status": "METHOD_FAILURE",
                "packet": self._failure_packet(
                    observation, mode="C1", status="METHOD_FAILURE", exc=exc
                ),
            }

        catalog, per_node = _source_evidence(observation)
        packet = self._base_packet(observation, mode="C1", status="SUCCESS")
        packet["evidence_catalog"] = catalog
        packet["ranking"] = rank_table(
            primary["scores"], observation.node_ids, evidence_ids=per_node
        )
        packet["alternatives"] = {
            "L": rank_table(local, observation.node_ids, evidence_ids=per_node),
            "secondary_value_diffusion": rank_table(
                secondary["scores"], observation.node_ids, evidence_ids=per_node
            ),
            "Local-MAX-MT": rank_table(
                local_max["scores"], observation.node_ids, evidence_ids=per_node
            ),
            "BARO-RANK-adapted-TD12": rank_table(
                baro["scores"], observation.node_ids, evidence_ids=per_node
            ),
        }
        packet["local_evidence"] = {
            "scores": local,
            "blocks": evidence["blocks"],
            "masks": evidence["masks"],
            "diagnostics": evidence["diagnostics"],
            "same_input_for_L_O_R": True,
        }
        packet["graph"] = _graph_packet(
            observation,
            processing_direction=self.config.primary_ppr.direction,
            operator=self.config.primary_ppr.operator,
        )
        if control is not None:
            packet["graph"]["structural_control"] = {
                "summary": control["summary"],
                "all_draws_retained_in_numeric_output": True,
                "interpretation": "finite registered perturbation mobility only; not a mixing proof",
            }
        sealed = seal_packet(packet)
        return {
            "status": "SUCCESS",
            "local_evidence": evidence,
            "L_scores": local.copy(),
            "O": primary,
            "secondary": secondary,
            "R": control,
            "R_scores": control_scores,
            "comparators": {"Local-MAX-MT": local_max, "BARO-RANK-adapted-TD12": baro},
            "packet": sealed,
        }

    def _c5_profile(self) -> dict[str, Any]:
        return _plain(self.config.manifest["selections"]["c5"]["profile"])

    def run_c5(self, observation: C5Observation, detector_id: str) -> dict[str, Any]:
        """Fit one frozen detector and replay every consecutive relative bin."""
        if not isinstance(observation, C5Observation):
            raise TypeError("C5Observation required")
        try:
            selected = self.config.detector(detector_id)
            profile = self._c5_profile()
            fit_arm = "G" if selected.arm == "TV" else selected.arm
            detector_config = {
                "arm": fit_arm,
                "modalities": selected.modalities,
                "lambda": self.config.selected_lambda,
                "floor": profile["input_relative_floor"],
                "residual_floor": profile["residual_floor"],
                "lag": profile["lag"],
                "bin_seconds": profile["bin_seconds"],
                "fit_bins": profile["fit_bins"],
                "cal_bins": profile["calibration_bins"],
                "min_fit_rows": profile["min_fit_rows"],
                "min_cal_rows": profile["min_calibration_rows"],
            }
            state = fit_detector(
                observation.warmup_values,
                observation.adjacency,
                observation.channel_types,
                observation.fit_service_mask,
                detector_config,
            )
            event_state = create_event_state(
                selected.threshold,
                bin_seconds=profile["bin_seconds"],
                streak=profile["event_streak"],
                refractory_seconds=profile["refractory_seconds"],
            )
            expected = np.arange(
                len(observation.warmup_values) + 1,
                len(observation.warmup_values) + len(observation.stream_values) + 1,
                dtype=np.int64,
            ) * int(profile["bin_seconds"])
            if not np.array_equal(observation.relative_endpoints, expected):
                raise ValueError("C5 stream endpoints must be every consecutive relative bin")
            outputs: list[dict[str, Any]] = []
            packets: list[dict[str, Any]] = []
            for values, endpoint in zip(
                observation.stream_values, observation.relative_endpoints, strict=True
            ):
                result = score_bin(state, values)
                if result["endpoint"] != int(endpoint):
                    raise PipelineError("Detector endpoint differs from admitted relative grid")
                system_score = result["tv_score"] if selected.arm == "TV" else result["score"]
                event = event_step(event_state, system_score, int(endpoint))
                result["selected_system_score"] = system_score
                result["event"] = event
                outputs.append(result)
                if event["trigger"]:
                    packets.append(
                        self._c5_packet(
                            observation,
                            selected,
                            state,
                            result,
                            profile,
                            status="SUCCESS",
                        )
                    )
            if outputs:
                final_packet = self._c5_packet(
                    observation,
                    selected,
                    state,
                    outputs[-1],
                    profile,
                    status=(
                        "SUCCESS"
                        if np.isfinite(outputs[-1]["selected_system_score"])
                        else "UNAVAILABLE"
                    ),
                )
            else:
                packet = self._base_packet(observation, mode="C5", status="UNAVAILABLE")
                packet["detection"] = {
                    "detector_id": detector_id,
                    "reason": "NO_POST_WARMUP_BINS",
                }
                final_packet = seal_packet(packet)
        except (TypeError, ValueError) as exc:
            return {
                "status": "INPUT_FAILURE",
                "packet": self._failure_packet(
                    observation, mode="C5", status="INPUT_FAILURE", exc=exc
                ),
            }
        except Exception as exc:
            return {
                "status": "METHOD_FAILURE",
                "packet": self._failure_packet(
                    observation, mode="C5", status="METHOD_FAILURE", exc=exc
                ),
            }
        return {
            "status": "SUCCESS",
            "detector_id": detector_id,
            "detector_config": detector_config,
            "state": state,
            "bins": outputs,
            "trigger_packets": packets,
            "packet": final_packet,
        }

    def _c5_packet(
        self,
        observation,
        selected,
        state,
        result,
        profile,
        *,
        status,
        integrated_diagnosis=None,
    ):
        packet = self._base_packet(observation, mode="C5", status=status)
        packet["detection"] = {
            "detector_id": selected.detector_id,
            "arm": selected.arm,
            "modalities": selected.modalities,
            "selected_lambda": self.config.selected_lambda,
            "q": selected.q,
            "threshold": selected.threshold,
            "profile": profile,
            "relative_endpoint": result["endpoint"],
            "selected_system_score": result["selected_system_score"],
            "event": result["event"],
            "scored_channels": result["scored_channels"],
            "model_count": state["diagnostics"]["model_count"],
            "tv_score": result["tv_score"],
            "local_magnitude": result["local_magnitude"],
            "tv_failure": result["tv_failure"],
            "input_scale_absolute_fallback": 1e-12,
            "input_scale_fallback_preserved": True,
        }
        packet["graph"] = _graph_packet(
            observation,
            processing_direction="static fit graph; G uses directed out/in context, TV uses undirected edges",
            operator="conditional ridge context / graph-TV secondary",
        )
        if selected.arm != "TV" and np.isfinite(result["residuals"]).any():
            node_scores = np.zeros(len(observation.node_ids), dtype=np.float64)
            for index, row in enumerate(result["residuals"]):
                finite = row[np.isfinite(row)]
                node_scores[index] = float(np.max(finite)) if len(finite) else 0.0
            catalog, per_node = _source_evidence(observation)
            packet["evidence_catalog"] = catalog
            packet["ranking"] = rank_table(
                node_scores, observation.node_ids, evidence_ids=per_node
            )
            packet["ranking_interpretation"] = (
                "per-node maximum frozen normalized residual at this bin; detector support, not C1 ranking"
            )
        if integrated_diagnosis is not None:
            packet["integrated_diagnosis"] = integrated_diagnosis
        return seal_packet(packet)

    def _integrated_payload(
        self,
        observation: C1Observation,
        *,
        relative_endpoint: int,
    ) -> dict[str, Any]:
        """Run the frozen past-only trigger diagnosis without R/comparators."""
        try:
            local_config = {**dict(self.config.local), "include_logs": True}
            evidence = local_scores(
                observation.ref,
                observation.query,
                observation.channel_types,
                local_config,
            )
            if np.any(evidence["diagnostics"]["numerical_channel_failures"]):
                raise RuntimeError("Invalid integrated local channel")
            primary = rank_scores(
                evidence["local"],
                observation.adjacency,
                operator=self.config.primary_ppr.operator,
                direction=self.config.primary_ppr.direction,
                damping=self.config.primary_ppr.damping,
            )
            catalog, per_node = _source_evidence(observation)
            return {
                "status": "SUCCESS",
                "profile": "TD12-INTEGRATED-MTL",
                "relative_endpoint": int(relative_endpoint),
                "past_windows_relative": [
                    int(relative_endpoint) - 360,
                    int(relative_endpoint) - 60,
                    int(relative_endpoint),
                ],
                "ranking": rank_table(
                    primary["scores"], observation.node_ids, evidence_ids=per_node
                ),
                "local_evidence": {
                    "scores": evidence["local"],
                    "blocks": evidence["blocks"],
                    "masks": evidence["masks"],
                    "diagnostics": evidence["diagnostics"],
                    "include_logs": True,
                },
                "graph": _graph_packet(
                    observation,
                    processing_direction=self.config.primary_ppr.direction,
                    operator=self.config.primary_ppr.operator,
                ),
                "quality": _plain(observation.quality),
                "evidence_catalog": catalog,
                "no_structural_control_or_comparator_per_trigger": True,
            }
        except (TypeError, ValueError) as exc:
            return {
                "status": "INPUT_FAILURE",
                "relative_endpoint": int(relative_endpoint),
                "failure": {"error_type": type(exc).__name__, "message_redacted": True},
            }
        except Exception as exc:
            return {
                "status": "METHOD_FAILURE",
                "relative_endpoint": int(relative_endpoint),
                "failure": {"error_type": type(exc).__name__, "message_redacted": True},
            }

    def run_integrated(
        self,
        observation: C1Observation,
        *,
        relative_endpoint: int,
    ) -> dict[str, Any]:
        """Public numeric boundary for one already-admitted integrated window."""
        if not isinstance(observation, C1Observation):
            raise TypeError("C1Observation required")
        if not isinstance(relative_endpoint, (int, np.integer)) or relative_endpoint < 360:
            raise ValueError("Integrated observation requires at least 360 relative seconds")
        return self._integrated_payload(
            observation,
            relative_endpoint=int(relative_endpoint),
        )

    def run_public_c1(
        self,
        raw_telemetry,
        *,
        qualified_adapter,
        loader_kwargs,
        handle,
        evidence_catalog=None,
        include_structural_control=True,
    ):
        """Public telemetry → admitted C1 observation → structured packet."""
        observation = public_c1_observation(
            raw_telemetry,
            qualified_adapter=qualified_adapter,
            loader_kwargs=loader_kwargs,
            handle=handle,
            evidence_catalog=evidence_catalog,
        )
        return self.run_c1(
            observation, include_structural_control=include_structural_control
        )

    def run_public_c5(
        self,
        raw_telemetry,
        detector_id,
        *,
        qualified_adapter,
        loader_kwargs,
        handle,
        evidence_catalog=None,
    ):
        """Public telemetry → admitted C5 observation → structured packet."""
        profile = self._c5_profile()
        from .adapters import QualifiedTelemetryAdapter

        if not isinstance(qualified_adapter, QualifiedTelemetryAdapter):
            raise TypeError("QualifiedTelemetryAdapter required")
        bundle = qualified_adapter.c5(raw_telemetry, **dict(loader_kwargs))
        origin = bundle.get("s0")
        if not isinstance(origin, (int, np.integer)):
            raise PipelineError("Qualified C5 bundle lacks an integral controller origin")
        source_hashes = qualified_adapter.source_hashes(raw_telemetry)
        observation = admit_c5_bundle(
            bundle,
            handle=handle,
            source_hashes=source_hashes,
            fit_bins=profile["fit_bins"],
            cal_bins=profile["calibration_bins"],
            evidence_catalog=evidence_catalog,
        )
        result = self.run_c5(observation, detector_id)
        if result.get("status") != "SUCCESS":
            return result
        selected = self.config.detector(detector_id)
        trigger_packets: list[dict[str, Any]] = []
        integrated_records: list[dict[str, Any]] = []
        for scored in result["bins"]:
            if not scored["event"]["trigger"]:
                continue
            endpoint = int(scored["endpoint"])
            if endpoint < 360:
                integrated = {
                    "status": "INSUFFICIENT_HISTORY",
                    "profile": "TD12-INTEGRATED-MTL",
                    "relative_endpoint": endpoint,
                    "history_available": False,
                }
            else:
                try:
                    integrated_bundle = qualified_adapter.integrated(
                        raw_telemetry, int(origin) + endpoint
                    )
                    integrated_observation = admit_c1_bundle(
                        integrated_bundle,
                        handle=handle,
                        source_hashes=source_hashes,
                        evidence_catalog=evidence_catalog,
                    )
                    integrated = self.run_integrated(
                        integrated_observation,
                        relative_endpoint=endpoint,
                    )
                except Exception as exc:
                    integrated = {
                        "status": "METHOD_FAILURE",
                        "profile": "TD12-INTEGRATED-MTL",
                        "relative_endpoint": endpoint,
                        "failure": {
                            "error_type": type(exc).__name__,
                            "message_redacted": True,
                        },
                    }
            integrated_records.append(integrated)
            trigger_packets.append(
                self._c5_packet(
                    observation,
                    selected,
                    result["state"],
                    scored,
                    profile,
                    status="SUCCESS",
                    integrated_diagnosis=integrated,
                )
            )
        result["trigger_packets"] = trigger_packets
        result["integrated_diagnoses"] = integrated_records
        return result


__all__ = ["FrozenRcaPipeline", "PipelineError"]
