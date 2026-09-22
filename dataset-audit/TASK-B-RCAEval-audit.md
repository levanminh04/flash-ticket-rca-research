# Task B — RCAEval data audit checkpoint

**Status:** `CLOSED · DATASET CAPABILITY DECISION · NOT A METHOD OR DATASET-SELECTION DECISION`  
**Audit date:** 20 September 2026  
**Scope rule:** every conclusion is explicitly labelled as a `DATASET-WIDE METADATA FACT`, `RAW SAMPLE FINDING`, `PRIMARY-DOCUMENTATION FACT`, `INFERENCE`, or `UNKNOWN`.

**Closure note:** Sections 1–11 preserve the original pre-close checkpoint verbatim, including findings later corrected. An exact copy made before this update is [TASK-B-RCAEval-audit.pre-close.md](D:/Project/flash-ticket-rca-research/dataset-audit/TASK-B-RCAEval-audit.pre-close.md:1). Sections 12 onward contain the reconciled final Task-B decision.

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

## 12. Continuation, reconciliation, and closure

### 12.1 Executive Verdict

**Q1 — RE2-TT is suitable as the first pilot dataset: YES.**

It is suitable for a trace-derived service graph, literal service–operation representation, root-cause **service** ranking, and RCA given a known incident window. It supports a bounded automatic incident-window experiment and a multimodal experiment with explicit join rules and an explicit log-availability rule.

It is not suitable for operation-level or resource-level RCA ranking, service/node anomaly labels, node-level anomaly F1, resource graphs, `CALLS`/`USES`/messaging graphs, causal-propagation evaluation, or a request/event-level multimodal correlation claim.

This is a dataset capability verdict only. It does not choose a Research Question, detector, ranker, PageRank, GNN, or final thesis graph.

### 12.2 Exact dataset, revision, audit scope, and integrity

| Item | Final evidence | Status |
|---|---|---|
| Official source | Hugging Face `phamquiluan/RCAEval` | `VERIFIED` |
| Immutable revision | `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e` | `VERIFIED` |
| Official metadata | 735 rows; SHA-256 `c49a288920dbba2e8e724679a14636d5c7eb2b45426bba14007ef79a6c0ab1bb` | `VERIFIED` |
| Original raw sample | six planned cases / 20 files; original manifest order, revision, byte sizes and SHA-256 all match | `VERIFIED` |
| Supplemental B2B sample | one separate log-bearing RE2-TT case / three files / 24,334,988 bytes; each local SHA-256 matches official LFS SHA-256 | `VERIFIED` |
| B2 full-subset audit | all 90 RE2-TT `traces.parquet` objects, trace-only; one local trace reused and 89 official pinned range reads | `VERIFIED` |
| Preservation | original six-case manifest remains separate from B2B manifest; no audit artifact was deleted | `VERIFIED` |

The original six-case evidence remains at `datasets\rcaeval\raw-samples\raw-download-manifest.json`. The B2B addition is deliberately separate at [b2b-re2tt-multimodal-download-manifest.json](D:/Project/flash-ticket-rca-research/audits/rcaeval/b2b-re2tt-multimodal-download-manifest.json:1). B2 read 1,602,452,536 bytes by official HTTP ranges and retained no new trace corpus.

### 12.3 Corrections to the pre-close checkpoint

| Previous finding | New evidence | Final correction |
|---|---|---|
| Logs ↔ metrics were stated as time-window-only. | Independent E inspected four log+metric samples and H independently rechecked B2B `re2tt_ts-auth-service_cpu_2`. | `DIRECT` only at an exact `(UTC second, exact container/entity)` aggregation bin. It is not an event/request or causal join. |
| Trace joins were described only generically. | E verified raw timestamp-unit conversion, exact service string overlap, and zero log trace/span ID matches. | Metrics ↔ traces and logs ↔ traces are `SERVICE + TIME WINDOW`, never direct trace/span joins. |
| Trace parent coverage was based on three samples. | B2 scanned all 90 RE2-TT trace files. | Overall parent resolution is 98.45274372%, but seven cases are below 90% and the lowest is 38.54287289%; only resolved links form the graph. |
| RE2-TT multimodal status rested on its sole no-log raw case. | B2B added one normal log-bearing RE2-TT case with three checksum-verified files. | The precise three pairwise join rules are now verified on an actual log-bearing RE2-TT case; prevalence across the other 88 log-bearing cases is not claimed. |
| E and H were unavailable. | Both produced independent on-disk reports/evidence before their final chat turns hit quota limits. | Their completed artifacts are used in this closure. |

### 12.4 Metadata-wide facts for RE2-TT

**DATASET-WIDE METADATA FACT.** RE2-TT has 90 cases: five root-cause-service labels × six fault labels × three repetitions, with 18 cases per root service and 15 per fault. Metrics and traces are declared in 90/90 cases; logs in 89/90. Every RE2-TT row has `inject_time` inside its published observation window, with 720 normal and 721 faulty timesteps.

The two published injection-window anomalies are both RE1 cases. `re1ob_productcatalogservice_cpu_3` is confirmed by its raw `inject_time.txt` to have all 63 metric rows before injection. For a protocol that relies on the published fault window:

| Case | Classification | Reason |
|---|---|---|
| `re1ob_productcatalogservice_cpu_3` | `INVALID FOR FAULT-WINDOW EVALUATION` | raw injection time is after every metric observation; no faulty window exists |
| `re1ob_currencyservice_loss_1` | `INVALID FOR FAULT-WINDOW EVALUATION` | published injection time is outside its published observation window; the audit does not repair it |
| All RE2-TT cases | `VALID FOR PUBLISHED FAULT-WINDOW EVALUATION` | 90/90 metadata rows have in-window injection time and positive normal/faulty counts |

Thus the known timestamp problem is a documented RE1 defect, not a RE2-TT pilot pattern.

### 12.5 Original raw sample and supplemental RE2-TT evidence

**RAW SAMPLE FINDING.** The original six cases remain a deliberately stratified schema/leakage sample, not a prevalence sample. It proves the sampled `root_cause.txt` contains a log line that exactly matches one raw log, and that paths encode labels.

**RAW SAMPLE FINDING.** The supplemental `re2tt_ts-auth-service_cpu_2` is a normal log-bearing RE2-TT case. It confirms:

| Pair | Final class | Exact deterministic rule | Evidence boundary |
|---|---|---|---|
| Logs ↔ metrics | `DIRECT` | `logs.timestamp == metrics.time` and exact `logs.container_name == metric entity token` after documented wide-to-long suffix parsing | direct service/container-second bin only |
| Metrics ↔ traces | `SERVICE + TIME WINDOW` | `metrics.time == floor(traces.startTimeMillis / 1000)` and exact entity/service string equality | no trace/span key in metrics |
| Logs ↔ traces | `SERVICE + TIME WINDOW` | `logs.timestamp == floor(traces.startTimeMillis / 1000)` and exact container/service string equality | zero exact traceID and spanID matches in raw log body |

For B2B, all 271,919 log rows match a metric timestamp and an exact container/entity key at the aggregation-bin definition. They do not identify an individual request, span, event, or causal relation.

### 12.6 Full RE2-TT trace B2 results

**FULL-SUBSET PROPERTY — all 90 RE2-TT trace objects.** B2 processed 67,345,051 span rows. All 90 files have the same 11 fields: `time`, `traceID`, `spanID`, `serviceName`, `methodName`, `operationName`, `parentSpanID`, `startTimeMillis`, `startTime`, `duration`, and `statusCode`.

| Full-subset result | Value |
|---|---:|
| Files / rows | 90 / 67,345,051 |
| Physical schema variants | 1 |
| Literal service names | 27 |
| Literal `(serviceName, operationName)` pairs | 161 |
| Operation strings reused by more than one service | 12 |
| Duplicate `(traceID, spanID)` pairs | 0 |
| Resolved same-trace parent links | 65,748,095 / 66,781,374 (98.45274372%) |
| Unresolved parent links | 1,033,279 |
| Cases below 90% parent resolution | 7; lowest `re2tt_ts-route-service_disk_2` at 38.54287289% |
| Observed resolved cross-service parent→child relation types | 55 |
| Cross-service relation rows | 12,070,854 |
| Negative or zero durations | 0 |
| Resolved child starts before parent | 4,543 |
| Resolved child outlives parent | 1,754,132 |

Every one of the 90 schemas lacks dedicated HTTP/RPC/peer/endpoint, resource, messaging, causal, attributes/events/links, and `span.kind` fields. This is decisive raw evidence for the unsupported graph semantics below.

### 12.7 Trace semantics, service graph, and operation verdicts

| Layer | Verdict | Node identity / edge derivation | Meaning actually supported |
|---|---|---|---|
| Service node | `SUPPORTED` | exact literal `trace.serviceName` | a trace-recorded service label |
| Service edge | `PARTIALLY SUPPORTED` | resolved `(traceID,parentSpanID) → (traceID,spanID)`, aggregated only when literal parent and child services differ | observed trace-derived parent→child service relation |
| Overall service graph | `PARTIALLY SUPPORTED` | 27 nodes and 55 relation types across RE2-TT | incomplete observed graph; not complete topology |
| Operation representation | `SUPPORTED` | exact literal `(serviceName, operationName)` | 161 reproducible representation keys |
| Semantic operation identity | `NOT SUPPORTED` | names such as `GET` and `POST` are reused across services | no protocol/kind field establishes semantic type |
| Operation-level ground truth | `ABSENT` | no field or artifact records root-cause operation | `NOT EVALUABLE` |

The edge name is **`TRACE-DERIVED SERVICE/OPERATION RELATIONSHIP`**. The data does not justify naming it `CALLS`, `USES`, `PUBLISHES_TO`, `DELIVERS_TO`, or `CAUSAL_PROPAGATION`.

### 12.8 Resource taxonomy verdict

| Resource type | Final classification | Dataset capability consequence |
|---|---|---|
| Host | `NOT SUPPORTED` | no host identity or host relation |
| Pod/container | `ATTRIBUTE ONLY` | `logs.container_name` is a literal observed label; it has no UID, lifecycle, host, or graph edge semantics |
| Database | `REQUIRES EXTERNAL MAPPING` | text labels or operation strings do not establish a typed database entity |
| Logical database | `NOT SUPPORTED` | no structured logical-database identity |
| Cache | `REQUIRES EXTERNAL MAPPING` | literal strings cannot create a cache node or `USES` relation |
| Broker | `REQUIRES EXTERNAL MAPPING` | literal strings cannot create a broker node or edge |
| Queue/topic | `NOT SUPPORTED` | no topic, queue, producer, consumer, or correlation identifier |
| Other resource | `ATTRIBUTE ONLY` | untyped literal attributes do not create a resource graph |

**Final resource decision:** the RE2-TT first pilot has **no resource nodes and no `USES` edges**.

### 12.9 Ground-truth matrix

| Item | Status | Decisive evidence and allowed interpretation |
|---|---|---|
| Incident / failure case | `AVAILABLE` | all 90 cases are fault-injection cases with a valid published window |
| Root-cause service | `AVAILABLE` | five balanced `root_cause_service` labels, 18 each |
| Fault type | `AVAILABLE` | six balanced metadata labels, 15 each |
| Injection target | `PARTIAL` | no independent target field; case/path repeats the service label and cannot validate an observable target |
| Injection time | `AVAILABLE` | valid evaluation boundary for 90/90 RE2-TT rows |
| Root-cause operation | `ABSENT` | no metadata/tree artifact |
| Affected operation | `ABSENT` | no metadata/tree artifact |
| Root-cause resource | `ABSENT` | no metadata/tree artifact |
| Affected-node labels | `ABSENT` | no node/service set or per-node labels |
| Propagation-path labels | `ABSENT` | no path artifact or field |

The full B2 trace result plus [re2tt-target-candidate-coverage.json](D:/Project/flash-ticket-rca-research/audits/rcaeval/re2tt-target-candidate-coverage.json:1) confirms the ground-truth service label is present in the telemetry-derived service set for 90/90 cases. That candidate set contains 20–27 literal trace services per case. It must not be replaced by the five known injected labels.

### 12.10 Locked leakage policy

| Field / artifact | Final classification | Rule |
|---|---|---|
| Case ID | `FORBIDDEN MODEL INPUT` | encodes root service, fault, and repetition |
| Directory name / path | `FORBIDDEN MODEL INPUT` | carries the same answer tokens |
| `root_cause_service` | `EVALUATION ONLY` | service-ranking target only |
| `fault`, `fault_description` | `EVALUATION ONLY` | report/stratification target only |
| `inject_time` | `EVALUATION ONLY — ONLY FOR RCA-GIVEN-KNOWN-INCIDENT-WINDOW` | `FORBIDDEN FOR END-TO-END DETECTION INPUT` |
| `normal_timesteps`, `faulty_timesteps`, full-case end/duration/counts | `FORBIDDEN MODEL INPUT` | oracle or look-ahead aggregate |
| `root_cause.txt` and presence flag | `FORBIDDEN MODEL INPUT` | sampled artifact contains the answer log line |
| `repetition`, `suite`, `system`, `dataset` | `PROVENANCE ONLY` | not runtime telemetry |
| Raw telemetry read without label-bearing path/features | `MODEL INPUT ALLOWED` | subject to the documented graph and join boundaries |

### 12.11 Parent resolution and missingness analysis

The seven low-resolution cases remain **usable as incomplete observed graphs**. They are not removed, repaired, or filled from architecture or ground truth. For each case, graph construction uses only resolved parent links and records that case's observed resolution rate.

This means:

- complete-topology assumptions are `NOT SUPPORTED`;
- a service-ranking or known-window RCA evaluation can include every case, because all 90 ground-truth targets are present in its visible trace candidate set;
- any graph-dependent result must report parent-resolution coverage per case or stratum;
- a robustness experiment based on observed low vs high parent-resolution coverage is evaluable without using labels to repair topology.

### 12.12 Detection, RCA-ranking, ablation, and robustness readiness

| Task | Verdict | Required input / available ground truth | Binding limitation |
|---|---|---|---|
| RCA given known incident window | `YES` | trace/metric telemetry; `inject_time` as external published boundary; root-cause service label | injection time is not a model feature |
| End-to-end anomaly detection | `PARTIAL` | telemetry and injected normal/fault windows | no independently labelled anomaly onset or affected-entity ground truth |
| Service-level root-cause ranking | `YES` | telemetry-derived 20–27 service candidates; root-cause service label | candidate universe must not use five injected labels or paths |
| Operation-level root-cause ranking | `NO` | operation representation exists | root-cause operation label is absent; `NOT EVALUABLE` |
| Service-level binary anomaly detection | `NO` | no affected/anomalous service set | root cause is not an anomaly-node label |
| Node-level anomaly precision/recall/F1 | `NO` | no node universe or per-node label | `NOT EVALUABLE` |
| Graph-based anomaly detection | `PARTIAL` | trace-derived service graph, metrics, and published fault windows | no node-level anomaly labels, causal graph, or resource graph |
| Graph-ablation experiment | `YES` | resolved trace-derived graph versus an explicitly graph-free comparator; service-ranking label | graph semantics remain trace-derived only |
| Multimodal experiment | `PARTIAL` | deterministic joins are sample-verified, including one normal RE2-TT log-bearing case | one RE2-TT case has no logs; full-89 log-schema prevalence is not claimed |
| Missing/incomplete-trace robustness experiment | `YES` | observed per-case parent-resolution rates and service-ranking label | do not drop, impute, or repair low-resolution graphs with labels |

### 12.13 Cross-review disagreement and resolution matrix

| Question | Evidence source 1 | Evidence source 2 | Disagreement | Deterministic evidence | Final resolution |
|---|---|---|---|---|---|
| Is the trace relation a complete `CALLS` graph? | B/C sample trace review: trace-derived parent relation only | B2 full trace review: same 11-field schema in 90/90 files | no substantive disagreement; B2 strengthens scope | schema field inventory and 90-file scan | `NOT SUPPORTED` for `CALLS`; `PARTIALLY VERIFIED` trace-derived service relation |
| Does a literal operation pair equal operation ground truth? | Trace/graph reviewers: pair is derivable | I ground-truth review: no operation target artifact | representation and target are distinct | 161 pairs; no operation label in metadata/tree | `VERIFIED` representation; `NOT EVALUABLE` operation RCA |
| Is log ↔ metric only an approximate time join? | Original fallback said time-only | Independent E and H found exact second + exact entity/container keys | contradiction resolved against fallback | raw L–M bin joins, including 271,919/271,919 B2B log rows | `CONTRADICTED` old wording; `VERIFIED` direct bin join |
| Do trace joins have direct IDs? | E: zero direct IDs in logs | D: no trace/span key in metric rows | aligned | raw log ID scan and raw schemas | `VERIFIED` `SERVICE + TIME WINDOW` only |
| Can resource text create graph resources? | Resource reviewer: only attributes/mapping requirements | C/B2 trace review: no resource fields | aligned | raw schema and literal-string checks | `NOT SUPPORTED` for resource graph / `USES` |
| Does metadata prove an RE2-TT-valid trace candidate target? | I: root service label available but candidate universe not in metadata | B2: exact trace services available per case | resolved by telemetry check | 90/90 targets present among 20–27 trace services | `VERIFIED` telemetry-derived candidate universe |
| Do low-resolution cases invalidate the first pilot? | B2: seven cases below 90% | H: no repair/exclusion; preserve coverage | no disagreement after raw profile | lowest 38.54287289%, labels still present in candidate set | `PARTIALLY VERIFIED` graph coverage; pilot remains valid |
| Are RE1 timing defects a RE2-TT pattern? | Metadata A: two global out-of-window cases | I: 0/90 RE2-TT invalid windows | resolved by full metadata subset query | 90/90 in-window RE2-TT rows | `VERIFIED` RE2-TT does not have this pattern |

### 12.14 Independent Red-Team findings

| Challenge | Classification | Closure |
|---|---|---|
| Sample-selection bias | `MAJOR` | original six-case findings remain sample-scoped; B2 trace facts are explicitly full-subset |
| Overgeneralizing log/metric joins | `CRITICAL` | direct/log trace claims are limited to inspected raw cases |
| Operation representation mistaken for ground truth | `MAJOR` | representation supported; operation-ranking evaluation not evaluable |
| Root-cause service mistaken for anomaly-node label | `CRITICAL` | service anomaly and node F1 are not evaluable |
| Injection target mistaken for an observed entity | `MAJOR` | only partial label provenance; no observable-target assertion |
| Span relation mistaken for RPC/causality | `CRITICAL` | edge label stays trace-derived parent→child relation |
| Operation strings treated as semantic IDs | `MAJOR` | literal pair only |
| Time co-occurrence called event correlation | `RESOLVED` | direct L–M applies only to a service/container-second bin; trace joins stay service+time |
| Root-cause text leakage | `CRITICAL` | forbidden model input |
| Path/fault-name leakage | `CRITICAL` | paths forbidden; labels evaluation-only |
| `inject_time` used as model input | `CRITICAL` | evaluation-only for known-window RCA; forbidden for end-to-end input |
| Architecture-invented edges | `CRITICAL` | no static/resource/protocol/causal completion |
| Silent missing-modality imputation | `MAJOR` | logs optional with explicit availability; no imputation |
| Resource over-inference | `MAJOR` | no resource nodes or `USES` edges |
| Five-label candidate universe | `CRITICAL` | derive 20–27 candidates from visible telemetry |
| Top-5 under five candidates | `CRITICAL` | label-restricted Top-5 is invalid and forbidden |
| Aggregate parent rate hiding hard cases | `MAJOR` | report and retain per-case resolution rates |

The independent H report finds no external blocker to closure. Its final chat delivery hit quota after the complete report/evidence were written; this does not invalidate those persisted artifacts.

### 12.15 Minimal data-supported graph for RE2-TT

```text
NODE TYPES
  ServiceNode(serviceName)                         # exact trace.serviceName
  OperationNode(serviceName, operationName)        # exact literal pair
  SpanNode(traceID, spanID)                         # exact within-case composite key

EDGE TYPES
  SPAN_PARENT_OF(parentSpan, childSpan)             # only resolved same-trace parent reference
  SPAN_HAS_SERVICE(span, service)
  SPAN_HAS_OPERATION(span, operation)
  TRACE_DERIVED_SERVICE_RELATION(parentService, childService)
                                                    # only resolved cross-service parent-child spans

TIME-BIN OBSERVATIONS, NOT REQUEST/CAUSAL EDGES
  MetricLogBin(serviceOrContainer, epochSecond)     # exact matching L–M bins where present
  MetricTraceBin(service, epochSecond)              # service + time
  LogTraceBin(service, epochSecond)                 # service + time
```

Known missingness: 1/90 RE2-TT cases has no logs; parent references are unresolved at a case-dependent rate; the lowest observed parent resolution is 38.54287289%. Unsupported semantics: network `CALLS`, `USES`, resources, messaging, causal propagation, request/event correlation, operation root cause, and propagation paths.

### 12.16 Final RE2-TT first-pilot verdict

**YES.**

| Suitable for | Not suitable for |
|---|---|
| Trace-derived service/operation representation | `CALLS`, `USES`, messaging, or causal graph claims |
| Service-root-cause ranking over telemetry-derived candidates | Operation-level or resource-level RCA ranking |
| RCA given a known incident window | Service/node anomaly labels or node-level F1 |
| Graph-ablation and incomplete-trace robustness experiments | Complete-topology assumptions or graph repair from labels |
| Bounded multimodal analysis with the explicit pairwise rules | Request/event-level log–trace correlation |
| Injection-window detection experiment with stated limits | Fully labelled end-to-end anomaly-object evaluation |

### 12.17 Explicitly unsupported or not evaluable claims

- `CALLS`, `USES`, messaging, and causal-propagation edge semantics: **NOT SUPPORTED BY DATASET**.
- Resource-node graph and resource `USES` edge: **NOT SUPPORTED BY DATASET**.
- Root-cause operation, affected operation, root-cause resource, affected-node, and propagation-path evaluation: **NOT EVALUABLE WITH CURRENT GROUND TRUTH**.
- Service-level binary anomaly evaluation and node-level anomaly F1: **NOT EVALUABLE WITH CURRENT GROUND TRUTH**.
- A five-injected-service candidate universe and Top-5 computed over it: **INVALID DUE TO LABEL LEAKAGE / STRUCTURAL TRIVIALITY**.
- Direct log–trace or metric–trace request/span correlation: **NOT SUPPORTED BY DATASET**.

### 12.18 Task-C input pack — facts only

Task C may rely on these facts and constraints:

- RE2-TT has 90 valid published fault windows, 90 trace files, 89 log files, and metrics in all 90 cases.
- The supported graph granularity is exact trace `serviceName`, literal `(serviceName, operationName)`, and resolved parent-span relations.
- Use only resolved parent relations; retain and report per-case resolution coverage.
- Service-level root-cause labels are available and balanced. Every label is present in its case's telemetry-derived 20–27 service candidate set.
- Metrics ↔ logs use direct exact service/container-second bins where verified. Metrics ↔ traces and logs ↔ traces use exact service plus time-window alignment only.
- Case/path, label, fault, root-cause-text, and injection-oracle leakage rules in Section 12.10 are mandatory.
- Valid evaluation outputs: root-cause service rank; known-window RCA; partial injected-window detection; graph ablation; incomplete-trace robustness.
- Invalid outputs: operation/resource/affected-node/propagation ranking and node/service anomaly classification metrics.

### 12.19 Subagent execution summary

**SUBAGENT CAPACITY USED: 11 independent reviewer executions.**

| Reviewer | Artifacts inspected | Independent conclusion | Material disagreement and resolution |
|---|---|---|---|
| A — metadata | all 735 metadata rows | counts, modality layout, anomalies | matched G; raw later resolved one selected anomaly |
| B — trace schema | three raw traces | schema/ID/timing limits | confirmed and extended by B2 |
| C — graph constructability | three raw traces | only trace-derived graph semantics | confirmed by B2 and H |
| D — metrics | six raw metrics files | wide metrics/no trace identity/no labels | E corrected only the log–metric bin-join wording |
| E — logs/multimodal | six original samples | direct L–M bins; trace joins service+time | H independently checked B2B added case |
| F — ground truth/leakage | all metadata rows | paths/oracles leak; labels are not features | confirmed by I and H |
| G — reproducibility | provenance/metadata/runtime | pinned snapshot and timestamp risks | original manifest recheck matched |
| I — RE2-TT ground truth | all 90 RE2-TT metadata rows and official tree | service-ranking/known-window readiness and label limits | B2 supplied telemetry candidate coverage |
| J — B2 full trace | all 90 RE2-TT traces | full-subset graph/schema/parent evidence | corrected sample-only scope |
| Resource taxonomy | selected raw modalities | typed resources unsupported | aligned with C/J; no inferred resources |
| H — methodology red team | all current evidence plus B2B raw files | adversarial constraints and corrections | no hard closure blocker |

### 12.20 TASK B STATUS: CLOSED

**TASK B STATUS: CLOSED.** The evidence supports a bounded RE2-TT first pilot and defines its hard data, graph, ground-truth, multimodal, missingness, and leakage limits. No Task-C method decision has been made in this report.
