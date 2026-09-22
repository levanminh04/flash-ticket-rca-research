# Task B2 — targeted full-RE2-TT trace audit scope

**Status:** `COMPLETE`  
**Purpose:** resolve the full-subset trace questions that determine whether RE2-TT can be the first Task-C pilot. This is a bounded extension of Task B, not a method decision.

## Pre-download inventory

**DATASET-WIDE METADATA FACT.** The pinned official metadata contains 90 `RE2-TT` cases. All 90 declare `has_traces=true` and a positive `n_traces` value. The official Hugging Face file inventory at revision `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e` exposes exactly 90 matching objects, one at `<case>/traces.parquet` for every metadata case; none is missing and none is extra.

The 90 remote trace objects total **1,624,336,514 bytes** (1,549.09 MiB; 1.513 GiB). The individual object inventory, including immutable LFS SHA-256 values and byte sizes, will be recorded in machine-readable evidence before row inspection. This inventory operation reads repository metadata only; it does not retrieve trace telemetry.

## QUESTION

Does the complete RE2-TT trace subset support a reproducible first-pilot **trace-derived service/operation representation**, and exactly which stronger graph claims are unsupported by its raw fields?

## WHY IT AFFECTS THE TASK-B VERDICT

The initial three-file trace review could only establish sample findings. A first-pilot verdict for RE2-TT requires full-subset evidence that trace availability, schema, identity fields, parent-link integrity, and observed cross-service relationships do not depend on the selected cases. The audit also checks whether any unexamined field could overturn the preliminary conclusion that network `CALLS`, resources, messaging, and causal propagation are not directly observable.

## EXACT SUBSET

All and only the 90 `RE2-TT` case directories defined by the pinned official `cases.parquet` metadata and the corresponding 90 official `<case>/traces.parquet` objects.

## EXACT FILE TYPES REQUIRED

`traces.parquet` only. The audit will not request `metrics.parquet`, `logs.parquet`, `inject_time.txt`, `root_cause.txt`, or any other object. Fault labels and root-cause labels are not read as trace-model features.

## TRANSFER AND STORAGE BOUNDARY

The existing local file `re2tt_ts-auth-service_cpu_1/traces.parquet` is reused after its recorded checksum is matched; it is not downloaded again. All other objects are read one at a time through official pinned Hugging Face HTTP range requests, selecting only columns needed for the specified checks. No new trace corpus is retained under `datasets`; the script records actual request count and response bytes. The possible upper bound is the 1.513-GiB remote trace corpus, while actual range transfer is expected to be lower because unneeded `time`, `methodName`, and `statusCode` data columns are not scanned.

## DECISIVE CHECKS AND STOP CONDITION

For every object: physical schema; null/identity coverage for trace, span, service, operation, and parent fields; duplicate `(traceID, spanID)` pairs; parent resolution; parent/child temporal containment; and cross-service parent-child edge coverage. The audit also scans every schema for HTTP/RPC/DB/messaging/peer/resource/attribute/event/link fields.

Stop when all 90 objects have a recorded immutable source identity and a completed per-file result, or if the official source makes a specific object inaccessible after deterministic retries. In the latter case, the report must name that object and its failed request rather than generalizing.

## Completion record

All 90 objects completed at the pinned revision. One previously retained raw trace file was checksum-verified and reused; the other 89 were read through official Hugging Face byte ranges. No metrics, logs, injection files, root-cause files, or new persistent trace files were retrieved. The range reader recorded 179 successful logical reads, 1,602,452,536 received bytes, and zero retries.

The resulting full-subset evidence is [re2tt-trace-full-subset-audit.json](D:/Project/flash-ticket-rca-research/audits/rcaeval/re2tt-trace-full-subset-audit.json:1), with an independent reviewer report at [subagent-re2tt-full-trace-audit.md](D:/Project/flash-ticket-rca-research/audits/rcaeval/subagent-re2tt-full-trace-audit.md:1). It resolves the B2 question: RE2-TT supports only a trace-derived literal service/operation representation and observed parent-to-child trace relations; it does not support semantic `CALLS`, resource, messaging, causal, or operation-ground-truth claims.

### Shared-workspace provenance note

The immutable inventory recorded before this audit listed only `re2tt_ts-auth-service_cpu_1/traces.parquet` as locally present and reused it. A later post-completion filesystem check found a separate `re2tt_ts-auth-service_cpu_2` directory containing metrics, logs, and traces, created after this audit had already range-read its trace object. It is therefore not an input to this B2 result and was not created by this trace-only script; its retrieval must be accounted for by the concurrent audit that requested it.
