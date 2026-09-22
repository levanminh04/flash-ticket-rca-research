# Independent RE2-TT Ground-Truth and Leakage Audit

**Scope:** `DATASET-WIDE METADATA FACT` for all 90 RE2-TT cases at the immutable source revision below. This audit did not download or inspect additional telemetry and did not use a prior ground-truth audit.

## Provenance

- Official dataset: [`phamquiluan/RCAEval`](https://huggingface.co/datasets/phamquiluan/RCAEval)
- Pinned revision: `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`
- `cases.parquet`: 29500 bytes; SHA-256 `c49a288920dbba2e8e724679a14636d5c7eb2b45426bba14007ef79a6c0ab1bb`
- Official documentation consulted: [RCAEval README](https://github.com/phamquiluan/RCAEval/blob/main/README.md) and [benchmark evaluator source](https://github.com/phamquiluan/RCAEval/blob/main/main.py).

## Executive verdict

**RE2-TT has complete case-level root-cause-service, fault-type, and injection-window labels for 90 balanced injected-fault cases. It supports service-root-cause ranking given a telemetry-derived candidate universe and RCA given a known incident window. It does not support operation/resource root-cause ranking, affected-node evaluation, propagation-path evaluation, service-level anomaly labels, or node-level anomaly F1.**

The case ID and directory name leak both the answer service and fault in **90/90** cases. Passing a path, case ID, `root_cause_service`, or `fault` into model construction is invalid. There is no separate injection-target record: the service label must not be relabelled as independently verified injection provenance.

## Full RE2-TT metadata facts

- Cases: **90**; each has 1441 timesteps, with [720] normal and [721] faulty timesteps.
- Root-cause labels: `ts-auth-service` (18), `ts-order-service` (18), `ts-route-service` (18), `ts-train-service` (18), `ts-travel-service` (18).
- Fault labels: `cpu` (15), `delay` (15), `disk` (15), `loss` (15), `mem` (15), `socket` (15).
- Full factorial coverage: True — five services × six fault types × three repetitions, with 0 missing and 0 duplicate combinations.
- Modalities declared by metadata: metrics in 90/90, traces in 90/90, logs in 89/90. The no-log case is `re2tt_ts-auth-service_cpu_1`.
- Injection timestamps: 90/90 are within their metadata window; all are exactly [720] seconds after `time_start`.

## Official repository-tree check

At the pinned revision, the repository contains 90 RE2-TT directories and 359 RE2-TT files: `inject_time.txt` × 90, `logs.parquet` × 89, `metrics.parquet` × 90, `traces.parquet` × 90. There are no unexpected RE2-TT files and no `root_cause.txt` files.

## Ground-truth availability

| Item | Status | Decisive evidence |
|---|---|---|
| Incident label | **AVAILABLE** | All 90 cases are indexed as fault-injection cases and every row has an in-range inject_time with nonzero normal and faulty windows. |
| Root-cause service | **AVAILABLE** | root_cause_service is non-null in all 90 metadata rows; five services are balanced at 18 cases each. |
| Fault type | **AVAILABLE** | fault is non-null in all 90 metadata rows; six values occur 15 times each. |
| Injection target | **PARTIAL** | The service label is present and exactly matches the service token in every case identifier. |
| Injection timestamp | **AVAILABLE** | inject_time is non-null and within [time_start, time_end] for all 90 cases; every row has 720 normal and 721 faulty timesteps. |
| Operation-level root cause | **ABSENT** | No operation-root-cause field exists in cases.parquet, and the complete RE2-TT repository tree has no separate ground-truth artifact beyond the four telemetry/inject-time file types. |
| Resource-level root cause | **ABSENT** | No resource target/type/root-cause metadata field or separate RE2-TT ground-truth artifact is present. |
| Affected-node label | **ABSENT** | No affected-service/node set is in the metadata and no corresponding RE2-TT label artifact exists in the pinned tree. |
| Propagation-path label | **ABSENT** | No propagation-path field or RE2-TT artifact is present in the metadata/tree inventory. |
| Machine-readable root-cause indicator | **ABSENT** | The pinned RE2-TT metadata has no indicator field and its complete repository tree contains no root_cause.txt or indicator artifact. |

## Candidate universe and leakage

The metadata label alphabet contains **5** services, but it is **not** a model candidate universe. `cases.parquet` has no per-case candidate-service field and no authoritative split field. Per-case and per-split candidate universes are therefore **NOT AVAILABLE FROM METADATA**.

A deterministic parser recovered `root_cause_service`, `fault`, and `repetition` from **90/90** case IDs. Treating that service token as the candidate universe makes the candidate count exactly one in all cases; this is direct answer leakage. Restricting candidates to the five known injected services also makes Top-5 service accuracy structurally trivial. A valid future evaluator must enumerate candidate services only from telemetry visible in the evaluated case, before reading labels.

| Field | Classification | Reason |
|---|---|---|
| case ID | **FORBIDDEN MODEL INPUT** | Every RE2-TT case ID deterministically encodes the root-cause service, fault type, and repetition. |
| directory name/path | **FORBIDDEN MODEL INPUT** | The official directory convention carries the same root-cause-service and fault tokens as the case ID. |
| root_cause_service | **EVALUATION ONLY** | It is the service-ranking answer label; using it in a case-specific candidate set collapses that universe to one. |
| fault type | **EVALUATION ONLY** | It is the service-fault answer label and is encoded in the case ID/path. |
| inject_time | **EVALUATION ONLY — ONLY FOR RCA-GIVEN-INCIDENT-WINDOW** | It defines the injected-fault boundary. FORBIDDEN FOR END-TO-END DETECTION INPUT. |
| root_cause.txt | **FORBIDDEN MODEL INPUT** | A direct root-cause artifact would be leakage. It is absent from all 90 RE2-TT cases in the pinned repository tree. |
| repetition | **PROVENANCE ONLY** | It identifies a repetition, not a runtime observable; it must not be a model feature. |

## Evaluation readiness

| Evaluation task | Verdict | Why |
|---|---|---|
| RCA given a known incident window | **YES** | All 90 cases have a valid injection boundary and a root-cause-service evaluation label. Use inject_time only to define the evaluation window or to supply an externally known incident time; never expose it as an end-to-end detector feature. |
| End-to-end anomaly detection | **PARTIAL** | Each case has normal/faulty injection windows and metrics/traces; 89/90 also have logs. It can score automatic incident-window detection against the injected-fault boundary, but not a fully labelled anomaly-object/task because observed anomaly onset and affected-node labels are absent. |
| Service-level anomaly evaluation | **NO** | There is only one root-cause-service label per case and no affected/anomalous service set. Do not treat root_cause_service as a label for every anomalous service. |
| Node-level anomaly F1 | **NO** | No authoritative node universe or per-node anomaly labels are available. NOT EVALUABLE WITH CURRENT GROUND TRUTH. |
| Root-cause service ranking | **YES** | All 90 cases have a non-null root_cause_service label across five balanced services. Build each candidate universe from telemetry observable in that case, never from case paths, metadata labels, or known injected-service sets. |
| Operation-level root-cause ranking | **NO** | No operation-level root-cause label exists. NOT EVALUABLE WITH CURRENT GROUND TRUTH. |

## Direct conclusions for Task B

1. **Service-level RCA ranking: YES.** The ground truth is complete and balanced; the evaluator must use a candidate universe derived from pre-label telemetry only.
2. **RCA given a known incident window: YES.** `inject_time` is a permissible protocol boundary only in this setting.
3. **End-to-end anomaly detection: PARTIAL.** It can be scored against injected windows, but has no independently labelled anomaly onset or affected-node ground truth.
4. **Operation/resource/affected-node/propagation evaluation: NOT EVALUABLE WITH CURRENT GROUND TRUTH.** No such labels are available in the pinned RE2-TT artifacts.
5. **RE2-TT’s injection-window metadata is internally valid.** The known out-of-window RE1 case does not form a pattern in this RE2-TT population: 0/90 RE2-TT rows have an out-of-range `inject_time`.

## Reproducibility

Run `D:/Project/flash-ticket-rca-research/.venv/Scripts/python.exe D:/Project/flash-ticket-rca-research/scripts/audit/subagent_i_re2tt_groundtruth.py`. The corresponding machine result is `D:\Project\flash-ticket-rca-research\audits\rcaeval\subagent-i-re2tt-groundtruth.json`.
