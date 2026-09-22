# Task B — RCAEval data audit checkpoint

**Status:** `DRAFT · FORMATION · NOT A METHOD OR DATASET-SELECTION DECISION`  
**Audit date:** 20 September 2026  
**Scope rule:** every conclusion is explicitly labelled as a `DATASET-WIDE METADATA FACT`, `RAW SAMPLE FINDING`, `PRIMARY-DOCUMENTATION FACT`, `INFERENCE`, or `UNKNOWN`.

## 1. Read this first

This checkpoint preserves the evidence gathered before the execution quota was exhausted. It does **not** finalize Task B's required independent-review gate: Subagent E stopped before producing an independent report, and the required final Subagent H red-team could not be started because the agent quota/thread limit was reached. The main agent ran deterministic, labelled fallbacks for the missing raw checks; those fallbacks are evidence, but they are not independent reviewer consensus.

No dataset material was stored in `D:\Project\flash-ticket-platform`. All artifacts are under `D:\Project\flash-ticket-rca-research`.

### Current evidence verdict

**RAW SAMPLE FINDING.** The three sampled trace files support a reproducible *trace-derived* graph with exact service labels, `(serviceName, operationName)` keys, and resolved parent-span links. They do **not** support calling the edges confirmed network `CALLS`, resource `USES`, messaging relations, or causal-propagation paths.

**RAW SAMPLE FINDING.** The sampled modalities do not expose a direct cross-modal identity key. Metrics, logs, and traces can only be aligned by time window where both are present; that is not an exact log–trace or metric–trace correlation.

**DATASET-WIDE METADATA FACT plus RAW SAMPLE FINDING.** Case names/paths encode the root-cause service and fault for all 735 metadata rows. `root_cause.txt` contains a root-cause log line in a sampled case and matches one raw log exactly. These sources must be excluded from all blind detection/RCA model inputs.

## 2. Environment, source and preservation verification

| Item | Evidence | Status |
|---|---|---|
| Research workspace | `D:\Project\flash-ticket-rca-research` exists with the required layout | `VERIFIED` |
| Operating system | Windows 11 Home Single Language, version `10.0.22631` | `VERIFIED` |
| Python used | `C:\Users\84583\AppData\Local\Programs\Python\Python312\python.exe`, Python `3.12.10` | `VERIFIED` |
| Isolated environment | `D:\Project\flash-ticket-rca-research\.venv` | `VERIFIED` |
| Installed audit packages | pandas `3.0.6`, pyarrow `25.0.1`, huggingface_hub `1.32.0`, fsspec `2026.9.0` | `VERIFIED` |
| Official source | Hugging Face dataset [`phamquiluan/RCAEval`](https://huggingface.co/datasets/phamquiluan/RCAEval) at revision `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e` | `VERIFIED` |
| Official companion repository | [`phamquiluan/RCAEval`](https://github.com/phamquiluan/RCAEval) | `PRIMARY-DOCUMENTATION FACT` |
| Metadata snapshot | `cases.parquet`, 29,500 bytes, SHA-256 `c49a288920dbba2e8e724679a14636d5c7eb2b45426bba14007ef79a6c0ab1bb` | `VERIFIED` |
| Selective raw retrieval | six planned cases, 20 allowed files, same pinned revision | `VERIFIED` |
| Data preservation check | all 20 files exist, are allowed types, and match recorded byte size and SHA-256 | `VERIFIED` |

The preservation check is machine-readable in [raw-manifest-verification.json](D:/Project/flash-ticket-rca-research/audits/rcaeval/raw-manifest-verification.json:1). It answers the practical question raised during the run: the quota interruption did **not** remove metadata, raw samples, manifests, scripts, or completed audit outputs.

## 3. Dataset-wide metadata audit

**DATASET-WIDE METADATA FACT.** The official `cases.parquet` has 735 unique, non-null rows and 22 columns.

| Dimension | Result |
|---|---:|
| Suites | RE1: 375; RE2: 270; RE3: 90 |
| Systems | Online Boutique: 245; Sock Shop: 245; Train Ticket: 245 |
| Metadata root-cause-service values | 18 |
| Fault labels | 11 |
| Cases declaring metrics | 735 |
| Cases declaring logs | 359 |
| Cases declaring traces | 240 |
| Cases declaring a root-cause file | 8 |

The metadata describes strongly structured modality availability: RE1 is metric-only (375 cases); RE2-OB and RE3-OB/TT are declared tri-modal; RE2-SS and RE3-SS are metrics plus logs without traces; and one RE2-TT case has metrics plus traces without logs. This is a declaration in metadata, not proof that every unselected raw file has the same schema.

Two metadata records have injection times outside their stated windows:

| Case | Machine observation | Current treatment |
|---|---|---|
| `re1ob_currencyservice_loss_1` | `inject_time=16933142`, before `[1693313863, 1693314583]`; 0 normal timesteps | `UNKNOWN` until its raw `inject_time.txt` is audited; never infer a repair |
| `re1ob_productcatalogservice_cpu_3` | `inject_time=1685373255`, after `[1685371737, 1685371799]`; 0 faulty timesteps | Confirmed by selected raw file; exclude from fault-window detection/RCA evaluation |

The checks are recorded in [metadata-invariants.json](D:/Project/flash-ticket-rca-research/audits/rcaeval/metadata-invariants.json:1) and [subagent-a-metadata.md](D:/Project/flash-ticket-rca-research/audits/rcaeval/subagent-a-metadata.md:1).

## 4. Selective raw sample plan and what it can prove

Only the six cases below were retrieved. This was a schema/leakage/provenance audit, not a representative performance benchmark.

| Case | Suite / system | Fault metadata | Root target metadata | Reason and uncertainty tested |
|---|---|---|---|---|
| `re1ob_productcatalogservice_cpu_3` | RE1 / Online Boutique | cpu | `productcatalogservice` | Verify the stated injection-time contradiction with raw files |
| `re2ob_productcatalogservice_loss_1` | RE2 / Online Boutique | loss | `productcatalogservice` | Inspect tri-modal schemas and trace relationships |
| `re2ss_orders_loss_2` | RE2 / Sock Shop | loss | `orders` | Inspect logs + metrics when traces are absent |
| `re2tt_ts-auth-service_cpu_1` | RE2 / Train Ticket | cpu | `ts-auth-service` | Inspect traces + metrics when logs are absent |
| `re3ss_carts_f1_1` | RE3 / Sock Shop | f1 | `carts` | Inspect root-cause-file leakage and logs-only layout |
| `re3tt_ts-route-service_f2_1` | RE3 / Train Ticket | f2 | `ts-route-service` | Compare tri-modal schemas across systems |

The independent A and F proposals and the main-agent reconciliation are retained in [raw-sample-plan.md](D:/Project/flash-ticket-rca-research/audits/rcaeval/raw-sample-plan.md:1). No suite or full dataset was downloaded.

### Raw time check

**RAW SAMPLE FINDING.** The selected problematic RE1 case has 63 metric rows before its raw injection time and zero at or after it. The other five selected cases have their raw injection time within their metric range, with 720/721 or 900/901 rows before/at-or-after injection respectively. This validates the exclusion of `re1ob_productcatalogservice_cpu_3` from any evaluation that relies on a faulty window; it does not resolve the unselected currency-service case.

See [raw-time-alignment.json](D:/Project/flash-ticket-rca-research/audits/rcaeval/raw-time-alignment.json:1).

## 5. Raw telemetry evidence

### 5.1 Traces and graph constructability

**RAW SAMPLE FINDING.** The three trace-bearing samples contain the same 11 flat fields:

```text
time, traceID, spanID, serviceName, methodName, operationName,
parentSpanID, startTimeMillis, startTime, duration, statusCode
```

The raw schema has no `span.kind`, HTTP/RPC/DB/messaging attributes, peer endpoint, structured resource identity, deployment identity, events, or links.

| Graph element | Evidence and exact rule | Classification |
|---|---|---|
| Span-level service label | `serviceName` is present and non-null in all three selected trace files | `DIRECTLY_OBSERVED` |
| Service node | One node per non-empty literal `serviceName`; no aliasing or normalisation | `DERIVABLE_BY_EXPLICIT_RULE` |
| Operation node | One node per literal `(serviceName, operationName)` pair | `DERIVABLE_BY_EXPLICIT_RULE` |
| Parent-span relation | Join `(traceID, parentSpanID)` to `(traceID, spanID)` only when the parent exists in the same file | `DERIVABLE_BY_EXPLICIT_RULE` |
| Candidate cross-service trace dependency | Aggregate resolved parent/child links when their literal service labels differ | `DERIVABLE_BY_EXPLICIT_RULE` |
| Confirmed network HTTP/RPC `CALLS` | No protocol, kind, peer, or endpoint fields | `NOT_SUPPORTED` |
| Resource node or `USES` edge | No structured resource identifier or join key | `REQUIRES_EXTERNAL_INFORMATION` |
| Messaging relation | No topic, queue, producer, consumer, or messaging kind | `NOT_SUPPORTED` |
| Causal-propagation edge | Parent–child trace relations are not causal labels | `NOT_SUPPORTED` |

The parent reference resolves for 99.8785%, 99.9843%, and 100.0000% of parent-bearing rows in the three raw files. However, 18,122 resolved links in the Train Ticket CPU sample and 8,398 in the Train Ticket F2 sample fail simple parent/child interval containment. They must be retained as observed values; no silent filtering or repair is justified.

An operation string alone is not a stable operation identity: examples such as `GET`, `POST`, `TripRepository.findByTripId`, and `hipstershop.ProductCatalogService/GetProduct` occur under multiple service labels. A pair key is therefore a reproducible graph representation, not operation-level ground truth.

Evidence: [subagent-b-trace-schema.md](D:/Project/flash-ticket-rca-research/audits/rcaeval/subagent-b-trace-schema.md:1), [subagent-c-graph-constructability.md](D:/Project/flash-ticket-rca-research/audits/rcaeval/subagent-c-graph-constructability.md:1), and [subagent-c-graph-constructability-evidence.json](D:/Project/flash-ticket-rca-research/audits/rcaeval/subagent-c-graph-constructability-evidence.json:1).

### 5.2 Metrics

**RAW SAMPLE FINDING.** All six raw metrics files are wide tables: one `time` column (`int64`) and floating-point metric columns. Across samples there are 58–369 metric columns and 63–1,801 rows. There is no raw per-row root-cause label, fault label, trace ID, span ID, log ID, resource ID, or anomaly label.

Metric column tokens can support only a conditional **service-level** association by an explicit naming rule. They do not contain a shared identity for an exact graph or cross-modal join. Missingness ranges from 0% to 3.7767% in the sampled files; there are no all-null metric columns, but some constant-zero series exist. Neither condition should be silently imputed or discarded without a future documented rule.

Evidence: [subagent-d-metrics.md](D:/Project/flash-ticket-rca-research/audits/rcaeval/subagent-d-metrics.md:1) and [subagent-d-metrics-data.json](D:/Project/flash-ticket-rca-research/audits/rcaeval/subagent-d-metrics-data.json:1).

### 5.3 Logs and cross-modal relationships

**RAW SAMPLE FINDING — main-agent deterministic fallback for the unavailable independent Subagent E.** Each sampled logs file has exactly `timestamp`, `container_name`, and `message`. No sampled log file has a dedicated trace ID, span ID, or exception field.

The two selected tri-modal cases (`re2ob_productcatalogservice_loss_1` and `re3tt_ts-route-service_f2_1`) have overlapping time ranges across modalities. Their log messages contain no detected 16- or 32-hex token matching any trace or span ID. Therefore:

| Join | Classification | Reason |
|---|---|---|
| Logs ↔ traces | `TIME-WINDOW APPROXIMATION` | no direct trace/span field and no matched ID token |
| Metrics ↔ logs | `TIME-WINDOW APPROXIMATION` | timestamps overlap, but metric columns have no log identity |
| Metrics ↔ traces | `TIME-WINDOW APPROXIMATION` | timestamps overlap, but metric columns have no trace/span identity |
| Metric token ↔ telemetry entity | `SERVICE-LEVEL ONLY` | metric names are wide-column tokens, not shared entity keys |

In the sampled `re3ss_carts_f1_1`, `root_cause.txt` has six fields, identifies `carts`, contains a full log message, and that message occurs exactly once in `logs.parquet`. It is direct leakage if included in a log corpus.

Evidence: [main-log-multimodal-evidence.json](D:/Project/flash-ticket-rca-research/audits/rcaeval/main-log-multimodal-evidence.json:1). This evidence is valid raw inspection but must be independently reproduced once the quota permits.

## 6. Ground truth and leakage controls

| Field or artifact | Permitted role | Evidence |
|---|---|---|
| `case` and case directory/path | `FORBIDDEN MODEL INPUT` | the name regex recovers service, fault, and repetition for 735/735 metadata rows |
| `root_cause_service` | `EVALUATION ONLY` | official service-level ground-truth target, not a runtime feature |
| `fault`, `fault_description` | `EVALUATION ONLY` | injection labels, not observables |
| `inject_time`, `normal_timesteps`, `faulty_timesteps` | `FORBIDDEN MODEL INPUT` | fault-campaign oracle and two window inconsistencies |
| Whole-case counts and end/duration fields | `FORBIDDEN MODEL INPUT` | look-ahead aggregate shortcuts |
| `root_cause.txt` and its presence flag | `FORBIDDEN MODEL INPUT` | contains the sampled root-cause log line exactly |
| `has_logs`, `has_traces` | conditional `MODEL INPUT CANDIDATE` only | must be recomputed at an observable cutoff and tested against suite/system proxy leakage |
| Runtime telemetry fields | future `MODEL INPUT CANDIDATE` | only after a frozen, leakage-safe loader and protocol are specified |

**DATASET-WIDE METADATA FACT.** The metadata has no operation label, resource label, affected-node label, propagation-path label, or separately recorded injection target. Consequently, operation-level, resource-level, and propagation-path evaluation targets remain `UNKNOWN` for this audit.

Evidence: [subagent-f-ground-truth-leakage.md](D:/Project/flash-ticket-rca-research/audits/rcaeval/subagent-f-ground-truth-leakage.md:1).

## 7. Subagent execution summary

| Role | Work and raw artifacts inspected | Script/check | Important finding | Disagreement or limitation |
|---|---|---|---|---|
| A — Official metadata | official `cases.parquet`, all 735 rows; no raw telemetry | `audit_rcaeval_metadata.py` | exact counts, modality layout, two injection-window anomalies | completed independently |
| B — Trace schema | three selected `traces.parquet` files | `subagent_b_trace_schema.py` | 11 flat fields; parent-ID structure; no semantic protocol/resource fields | report and evidence completed; final agent response was interrupted by quota |
| C — Graph constructability | the same three raw trace files, independently of B | `subagent_c_graph_constructability.py` | limited trace-derived graph is constructable; `CALLS`/resource/messaging/causal claims are unsupported | completed independently |
| D — Metrics | all six selected `metrics.parquet` files | `audit_subagent_d_metrics.py` | wide metrics, no direct multimodal or label join key | completed independently; deterministic output was rerun twice by D |
| E — Logs / multimodal | required independent review did not complete | — | no independent conclusion available | quota stopped this role; main fallback inspected four log files and two tri-modal pairs |
| F — Ground truth / leakage | all 735 metadata rows; no telemetry at its pre-sample stage | `audit_ground_truth.py`, `crosscheck_ground_truth_pyarrow.py` | 735/735 path leakage; labels/oracles barred from inputs | completed independently at metadata stage; raw root-cause-file check is main fallback |
| G — Reproducibility / quality | official metadata, provenance, runtime, checks | `audit_reproducibility.py` | pinned metadata is reproducible; timestamp anomalies and missing dependency lock flagged | completed independently before raw retrieval; raw manifest verification was added afterward by main script |
| H — Methodology red team | required last, but could not start | — | no independent red-team conclusion | agent quota/thread limit blocked this mandatory role |

## 8. Cross-review results

The table resolves differences by raw evidence, never by reviewer count. “E fallback” is intentionally not presented as an independent reviewer.

| Question | Reviewer 1 conclusion | Reviewer 2 conclusion | Raw evidence used to adjudicate | Final status |
|---|---|---|---|---|
| Can an operation node be constructed? | B: `(serviceName, operationName)` is usable as an explicit key, but not stable semantic ground truth. | C: the literal pair is derivable as a graph node. | both fields are non-null in three trace files; standalone names repeat across services. | `PARTIALLY VERIFIED` — a reproducible key, not operation ground truth |
| Does a resolved parent link prove `CALLS` or causal propagation? | B: no protocol/kind/peer evidence and some timing inconsistencies. | C: parent links support only technical trace relationships. | the 11-field schema lacks protocol/resource attributes; 18,122 and 8,398 resolved links fail interval containment. | `VERIFIED` — stronger semantic claims are unsupported |
| Are metrics, logs and traces directly joinable? | D: metrics lack trace/span/log identity fields. | E fallback: logs lack dedicated trace/span fields; no matched ID token in two tri-modal cases. | raw schemas and zero matching candidate ID tokens. | `VERIFIED` — only time-window approximation in the observed cases |
| May a graph loader use case metadata or paths? | C: graph elements must arise from raw trace fields and explicit rules. | F: case/path strings encode the answer in all rows. | 735/735 regex recovery of service/fault/repetition from case name. | `VERIFIED` — metadata and paths are forbidden model inputs |
| Is the metadata snapshot reproducible? | A: 735-row metadata audit with exact schema/counts. | G: byte/hash/revision/API cross-check. | pinned revision and metadata SHA-256 recorded above. | `VERIFIED` |
| Is the RE1 product-catalog timestamp issue merely index transcription? | A: metadata is inconsistent but cannot settle raw truth. | G: required raw follow-up. | selected `inject_time.txt` is also after all 63 raw metric rows. | `PARTIALLY VERIFIED` — this case’s raw input is inconsistent; the currency-service case is still `UNKNOWN` |

## 9. Red-team findings — main-agent fallback, not an independent H review

The following adversarial review covers the required H questions using the available raw evidence. Its status is deliberately lower than an independent red-team result.

| Challenge | Finding | Severity | Disposition |
|---|---|---|---|
| 1. Selection bias in six downloaded cases | cases were intentionally stratified for schema uncertainty, not sampled for prevalence | `MAJOR` | do not generalize raw findings dataset-wide |
| 2. Dataset-wide claim from samples | three trace files and six metrics files cannot establish all-suite schema rates | `CRITICAL` | scope every raw conclusion to the selected cases |
| 3. Operation representation mistaken for ground truth | pair key is a construction rule; raw operation text repeats and has mixed semantics | `MAJOR` | do not evaluate operation RCA as ground truth |
| 4. Root-cause labels mistaken for anomaly labels | service-level metadata target has no per-timestamp anomaly label | `CRITICAL` | use only for service-level evaluation after protocol is fixed |
| 5. Injection target mistaken for observable RCA entity | no independent raw evidence links injection target to a trace/metric/resource entity | `CRITICAL` | keep mapping `UNKNOWN` |
| 6. Trace relationships mistaken for causal propagation | parent span links lack causal labels and include timing inconsistencies | `CRITICAL` | call them trace-derived relationships only |
| 7. High-cardinality span names treated as stable operations | names include generic verbs and cross-service repetitions | `MAJOR` | retain literal pair representation only |
| 8. Approximate time join treated as exact multimodal correlation | no shared ID; timestamp overlap is not identity | `CRITICAL` | label every cross-modal join as time-window approximation |
| 9. Root-cause/fault information leaks into inputs | paths encode labels; sampled root-cause file contains an exact log line | `CRITICAL` | freeze loader exclusions before modeling |
| 10. Graph edges invented from architecture | raw trace has no protocol/resource/messaging attributes | `CRITICAL` | prohibit inferred `CALLS`, `USES`, or messaging edges |
| 11. Missing telemetry silently repaired | modality absence is structured and observed in selected cases | `MAJOR` | expose availability; do not impute absent modality |
| 12. Injection time used as model information | it is a campaign oracle and can be inconsistent with raw windows | `CRITICAL` | forbid from input, feature engineering, and cutoff selection |

## 10. Unresolved questions and safe next step

1. **Independent completion remains open.** Rerun Subagent E and the required independent Subagent H once quota is available. The two main-agent fallback outputs should be independently challenged, not rubber-stamped.
2. **Unselected timestamp anomaly.** Do not retrieve `re1ob_currencyservice_loss_1` unless the team needs to decide whether any RE1 injection-time-based evaluation is admissible. If needed, create a targeted expansion request specifying only that case’s `metrics.parquet` and `inject_time.txt`; do not download an entire suite.
3. **Operation/resource/causal evaluation.** No safe claim or metric exists yet for operation-level root cause, resource-level root cause, or propagation path. Do not design an evaluation around these targets without new evidence.
4. **Multimodal model design.** A future design may use time-window aggregation with an explicit uncertainty label, but it must not call that an exact cross-modal join. A trace-only graph can be explored as a limited candidate representation on trace-bearing cases.
5. **Loader protocol.** Before any baseline or model experiment, create a reviewed loader contract that excludes case IDs, paths, metadata labels/oracles, `root_cause.txt`, and whole-case aggregates from model inputs. It should write a provenance-safe sample identifier unrelated to the label-bearing directory name.
6. **Reproducibility.** Record a dependency lock before baseline reproduction. No extra package is required for this audit checkpoint.

No Task B2 full-suite audit is triggered by the current checkpoint. A B2 request is necessary only if a later decision requires a dataset-wide telemetry-schema statistic, cross-suite operation stability, or an answer about the unselected RE1 timestamp anomaly.

## 11. Reproducibility artifacts

| Purpose | Artifact |
|---|---|
| Pinned metadata retrieval | `scripts/audit/fetch_metadata.py` |
| Complete metadata counts/invariants | `scripts/audit/audit_rcaeval_metadata.py`, `scripts/audit/check_metadata_invariants.py` |
| Selective raw retrieval | `scripts/audit/fetch_raw_samples.py` |
| File-preservation and hash verification | `scripts/audit/verify_raw_manifest.py` |
| Raw timestamp check | `scripts/audit/check_raw_time_alignment.py` |
| Trace and graph checks | `scripts/audit/subagent_b_trace_schema.py`, `scripts/audit/subagent_c_graph_constructability.py` |
| Metric check | `scripts/audit/audit_subagent_d_metrics.py` |
| Log/multimodal fallback | `scripts/audit/audit_logs_multimodal_main.py` |
| Ground-truth/leakage checks | `scripts/audit/audit_ground_truth.py`, `scripts/audit/crosscheck_ground_truth_pyarrow.py` |
| Reproducibility check | `scripts/audit/audit_reproducibility.py` |

All raw files and audit outputs referenced here remain under `D:\Project\flash-ticket-rca-research`.
