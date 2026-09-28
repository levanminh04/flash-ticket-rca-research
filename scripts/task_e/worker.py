"""Numeric-only Task E child process and strict, non-pickle wire protocol.

This module never imports controller, loader, evaluator, source manifests or
cache code. A dedicated Python entry point avoids spawn importing the campaign
as __main__. Process/API separation is not a hostile-code OS filesystem sandbox.
"""
from __future__ import annotations

import hashlib
import io
import json
import struct
import sys

import numpy as np

from scripts.task_e.detection import fit_detector, score_bin, _config
from scripts.task_e.ranking import local_scores, rank_scores

WIRE_SCHEMA = "TD13-NUMERIC-WIRE-v1"
MAX_WIRE_BYTES = 512 * 1024 * 1024


class ProtocolError(ValueError):
    pass


def _array(value, label, dimensions=None, boolean=False, allow_missing=True):
    if not isinstance(value, np.ndarray) or value.dtype.kind not in "biuf":
        raise ProtocolError(f"{label} requires a numeric ndarray; object/string arrays forbidden")
    if dimensions is not None and value.ndim not in dimensions:
        raise ProtocolError(f"{label} has an invalid number of axes")
    if boolean and value.dtype != np.bool_:
        raise ProtocolError(f"{label} requires a boolean mask")
    if np.isinf(value).any() or (not allow_missing and not np.isfinite(value).all()):
        raise ProtocolError(f"{label} has forbidden nonfinite input")
    return value


def _fields(message, required, optional=()):
    if not isinstance(message, dict) or set(message) - set(required) - set(optional):
        raise ProtocolError("Unknown message field: labels, epochs, names, paths and metadata are forbidden")
    if set(required) - set(message):
        raise ProtocolError("Missing required numeric protocol field")


def _local_config(config):
    allowed = {"floor", "pool", "fusion", "temporal", "cap", "include_logs"}
    if not isinstance(config, dict) or set(config) - allowed:
        raise ProtocolError("Unknown local configuration field")
    if config.get("floor", .01) not in (.0001, .001, .01):
        raise ProtocolError("Unregistered local scale floor")
    if config.get("pool", "max") not in ("max", "q90") or config.get("temporal", "q90") not in ("max", "q90"):
        raise ProtocolError("Unregistered local pooling")
    if config.get("fusion", "max") not in ("max", "availablemean"):
        raise ProtocolError("Unregistered local fusion")
    if config.get("cap") not in (None, 20):
        raise ProtocolError("Unregistered historical cap")
    if "include_logs" in config and not isinstance(config["include_logs"], bool):
        raise ProtocolError("include_logs must be boolean")


def _rank_configs(configs):
    if not isinstance(configs, list) or not configs:
        raise ProtocolError("Ranking configs must be a nonempty list")
    for config in configs:
        if not isinstance(config, dict) or set(config) - {"operator", "direction", "damping"}:
            raise ProtocolError("Unknown ranking configuration field")
        operator = config.get("operator", "ppr")
        direction = config.get("direction", "reverse")
        if operator not in ("ppr", "diffusion") or direction not in ("reverse", "undirected"):
            raise ProtocolError("Unregistered ranking operator/direction")
        if operator == "diffusion" and direction != "undirected":
            raise ProtocolError("Diffusion requires its registered undirected projection")
        if config.get("damping", .85) not in (.2, .5, .85):
            raise ProtocolError("Unregistered ranking parameter")


def validate_request(message):
    """Fail closed on a finite schema before any numeric function is invoked."""
    if not isinstance(message, dict) or not isinstance(message.get("op"), str):
        raise ProtocolError("Request must name one registered operation")
    op = message["op"]
    if op in ("ping", "close"):
        _fields(message, {"op"})
    elif op == "fit_c5":
        _fields(message, {"op", "warmup", "adj", "channel_types", "fit_service_mask", "configs"})
        values = _array(message["warmup"], "warmup", (3,))
        adjacency = _array(message["adj"], "adj", (2,), allow_missing=False)
        types = _array(message["channel_types"], "channel_types", (1,), allow_missing=False)
        services = _array(message["fit_service_mask"], "fit_service_mask", (1,), boolean=True)
        if not isinstance(message["configs"], list) or not message["configs"]:
            raise ProtocolError("Detector configs must be a nonempty list")
        configs = [_config(config) for config in message["configs"]]
        for config in configs:
            if len(values) != config["fit_bins"] + config["cal_bins"]:
                raise ProtocolError("Only the exact registered warmup is admitted, never a future suffix")
        if len({(cfg["bin_seconds"], cfg["fit_bins"], cfg["cal_bins"]) for cfg in configs}) != 1:
            raise ProtocolError("One C5 session needs one common chronological bin/prefix grid")
        if (adjacency.shape != (values.shape[1], values.shape[1]) or
                services.shape != (values.shape[1],) or types.shape != (values.shape[2],)):
            raise ProtocolError("Inconsistent numeric C5 axes")
    elif op == "score_c5":
        _fields(message, {"op", "values", "bin_index"})
        _array(message["values"], "current_bin", (2,))
        if type(message["bin_index"]) is not int or message["bin_index"] < 0:
            raise ProtocolError("bin_index must be a relative nonnegative index")
    elif op == "c1":
        _fields(message, {"op", "ref", "query", "adj", "channel_types", "local_config"}, {"rank_configs"})
        ref = _array(message["ref"], "ref", (3,))
        query = _array(message["query"], "query", (3,))
        _array(message["adj"], "adj", (2,), allow_missing=False)
        _array(message["channel_types"], "channel_types", (1,), allow_missing=False)
        if ref.shape[:2] != query.shape[:2]:
            raise ProtocolError("C1 numeric input axes disagree")
        _local_config(message["local_config"])
        if message.get("rank_configs"):
            _rank_configs(message["rank_configs"])
    elif op == "rank":
        _fields(message, {"op", "local", "adj", "configs"})
        _array(message["local"], "local", (1,), allow_missing=False)
        _array(message["adj"], "adj", (2, 3), allow_missing=False)
        _rank_configs(message["configs"])
    else:
        raise ProtocolError("Unregistered operation")
    return message


def _encode(value, arrays):
    if isinstance(value, np.ndarray):
        if value.dtype.kind not in "biuf":
            raise ProtocolError("Wire arrays must be numeric; pickle/object arrays forbidden")
        key = f"a{len(arrays)}"
        arrays[key] = np.ascontiguousarray(value)
        return {"__array__": key}
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return {"__float__": "nan" if np.isnan(value) else "inf" if value > 0 else "-inf"}
    if isinstance(value, dict):
        if any(not isinstance(k, str) for k in value):
            raise ProtocolError("Wire object keys must be strings")
        return {k: _encode(v, arrays) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_encode(v, arrays) for v in value]
    if value is None or type(value) in (str, int, float, bool):
        return value
    raise ProtocolError("Unsupported wire object")


def encode_message(value):
    """NPZ numeric arrays plus JSON structure; no executable deserialization."""
    arrays = {}
    tree = _encode(value, arrays)
    manifest = json.dumps({"schema": WIRE_SCHEMA, "tree": tree}, allow_nan=False,
                          separators=(",", ":")).encode()
    arrays["__manifest__"] = np.frombuffer(manifest, dtype=np.uint8)
    stream = io.BytesIO()
    np.savez(stream, **arrays)
    payload = stream.getvalue()
    if len(payload) > MAX_WIRE_BYTES:
        raise ProtocolError("Wire message exceeds declared resource bound")
    return payload


def decode_message(payload):
    if len(payload) > MAX_WIRE_BYTES:
        raise ProtocolError("Wire message exceeds declared resource bound")
    with np.load(io.BytesIO(payload), allow_pickle=False) as archive:
        meta = archive["__manifest__"]
        if meta.dtype != np.uint8 or meta.ndim != 1:
            raise ProtocolError("Malformed numeric wire manifest")
        manifest = json.loads(meta.tobytes().decode())
        if manifest.get("schema") != WIRE_SCHEMA or set(manifest) != {"schema", "tree"}:
            raise ProtocolError("Unknown numeric wire schema")
        used = set()

        def decode(value):
            if isinstance(value, dict) and set(value) == {"__array__"}:
                key = value["__array__"]
                if not isinstance(key, str) or key == "__manifest__":
                    raise ProtocolError("Malformed numeric array reference")
                array = archive[key]
                if array.dtype.kind not in "biuf":
                    raise ProtocolError("Object/string arrays forbidden")
                used.add(key)
                return array.copy()
            if isinstance(value, dict) and set(value) == {"__float__"}:
                return {"nan": np.nan, "inf": np.inf, "-inf": -np.inf}[value["__float__"]]
            if isinstance(value, dict):
                return {k: decode(v) for k, v in value.items()}
            if isinstance(value, list):
                return [decode(v) for v in value]
            return value

        result = decode(manifest["tree"])
        if set(archive.files) != used | {"__manifest__"}:
            raise ProtocolError("Unreferenced wire objects are forbidden")
        return result


def numeric_content_digest(value):
    """Hash semantic wire content without ZIP timestamps/container metadata."""
    arrays = {}
    tree = _encode(value, arrays)
    manifest = {"tree": tree, "arrays": {
        key: {"dtype": array.dtype.str, "shape": list(array.shape),
              "sha256": hashlib.sha256(array.tobytes()).hexdigest()}
        for key, array in arrays.items()}}
    return hashlib.sha256(json.dumps(manifest, sort_keys=True, allow_nan=False,
                                     separators=(",", ":")).encode()).hexdigest()


def _freeze_summary(state):
    keys = ("config", "E", "centers", "scales", "adj", "channel_types", "fit_service_mask",
            "degrees", "coefficients", "intercepts", "fit_model_mask", "model_mask",
            "residual_centers", "residual_scales", "calibration_errors",
            "calibration_predictions", "fit_target_mask", "calibration_target_mask")
    summary = {key: state[key] for key in keys}
    diagnostics = {key: value for key, value in state["diagnostics"].items()
                   if key != "applicability_reasons"}
    reasons = state["diagnostics"]["applicability_reasons"]
    legend = sorted(set(reasons.ravel().tolist()))
    codes = np.zeros(reasons.shape, dtype=np.int64)
    for index, reason in enumerate(legend):
        codes[reasons == reason] = index
    diagnostics.update(applicability_reason_codes=codes, applicability_reason_legend=legend)
    summary["diagnostics"] = diagnostics
    summary["frozen_numeric_sha256"] = numeric_content_digest(summary)
    return summary


def _rank(local, adjacency, configs):
    if adjacency.ndim == 2:
        return [rank_scores(local, adjacency, **config) for config in configs]
    return [[rank_scores(local, graph, **config) for config in configs]
            for graph in adjacency]


class NumericSession:
    """One child session; C5 states are inaccessible to controller mutation."""

    def __init__(self):
        self.states = []
        self.poisoned = False
        self.next_bin = None

    def dispatch(self, message):
        validate_request(message)
        op = message["op"]
        if op == "ping":
            return {"schema": WIRE_SCHEMA,
                    "project_modules": sorted(name for name in sys.modules
                                              if name.startswith("scripts.task_e.")),
                    "isolation": "NUMERIC_API_AND_PROCESS_NOT_HOSTILE_OS_SANDBOX"}
        if op == "close":
            return {"closed": True}
        if op == "fit_c5":
            self.states, self.poisoned, self.next_bin = [], False, None
            new_states = [fit_detector(message["warmup"], message["adj"],
                                       message["channel_types"], message["fit_service_mask"], cfg)
                          for cfg in message["configs"]]
            self.states = new_states
            self.next_bin = len(message["warmup"])
            return {"next_bin_index": self.next_bin,
                    "models": [_freeze_summary(state) for state in new_states]}
        if op == "score_c5":
            if not self.states or self.poisoned:
                raise ProtocolError("No usable fitted C5 session")
            if message["bin_index"] != self.next_bin:
                raise ProtocolError("Only the next chronological bin is admitted; no skips/replays/epochs")
            if message["values"].shape != self.states[0]["E"].shape:
                raise ProtocolError("Current bin axes differ from frozen model")
            try:
                full = [score_bin(state, message["values"]) for state in self.states]
            except Exception:
                # Some earlier states may already have advanced. Never retry a
                # partial transaction and silently diverge config chronology.
                self.poisoned = True
                raise
            self.next_bin += 1
            retained = {"score", "residuals", "errors", "predictions", "target_mask",
                        "z", "endpoint", "start", "scored_channels", "tv_score",
                        "tv_channels", "tv_edge_counts", "local_magnitude", "tv_failure"}
            return {"bin_index": message["bin_index"], "results": [
                {k: v for k, v in output.items() if k in retained} for output in full]}
        if op == "c1":
            evidence = local_scores(message["ref"], message["query"],
                                    message["channel_types"], message["local_config"])
            ranks = _rank(evidence["local"], message["adj"], message["rank_configs"]) if message.get("rank_configs") else []
            return {"evidence": evidence, "rankings": ranks}
        if op == "rank":
            return {"rankings": _rank(message["local"], message["adj"], message["configs"])}
        raise ProtocolError("Unreachable operation")


def _read_exact(stream, size):
    pieces = []
    remaining = size
    while remaining:
        piece = stream.read(remaining)
        if not piece:
            raise EOFError("Incomplete numeric pipe frame")
        pieces.append(piece)
        remaining -= len(piece)
    return b"".join(pieces)


def serve():
    session = NumericSession()
    while True:
        header = sys.stdin.buffer.read(8)
        if not header:
            return
        try:
            if len(header) != 8:
                raise ProtocolError("Incomplete numeric frame header")
            size = struct.unpack("!Q", header)[0]
            if size > MAX_WIRE_BYTES:
                raise ProtocolError("Numeric frame exceeds resource bound")
            request = decode_message(_read_exact(sys.stdin.buffer, size))
            result = session.dispatch(request)
            response = {"ok": True, "result": result}
        except Exception as exc:
            response = {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}
            request = None
        encoded = encode_message(response)
        sys.stdout.buffer.write(struct.pack("!Q", len(encoded)))
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()
        if request and request.get("op") == "close":
            return


if __name__ == "__main__":
    serve()
