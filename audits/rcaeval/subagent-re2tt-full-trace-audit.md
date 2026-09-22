# Independent targeted RE2-TT full-trace audit

**Status:** `COMPLETE`  
**Role:** additional independent full-subset Trace Auditor for Task B  
**Scope:** `FULL-SUBSET PROPERTY` — all 90 RE2-TT trace objects at immutable revision `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`. This report does not make a claim about other RCAEval suites or systems.

## Source and transfer boundary

The official source is [`phamquiluan/RCAEval`](https://huggingface.co/datasets/phamquiluan/RCAEval) at `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`. The pinned inventory has 90 metadata cases, 90 declared trace-bearing cases, and 90 matching remote `traces.parquet` objects. The remote objects total 1,624,336,514 bytes; only trace Parquet data were read. One existing local object was checksum-verified and reused. The other 89 objects were read with no persistent telemetry copy; the recorded range responses transferred 1,602,452,536 bytes (1528.22 MiB) in 179 logical range reads.

## Full-subset trace facts

All 90 files were processed. They contain 67,345,051 trace rows in 103 Parquet row groups. There are 1 physical schema variant(s). The common schema is the 11 fields previously observed: `time`, `traceID`, `spanID`, `serviceName`, `methodName`, `operationName`, `parentSpanID`, `startTimeMillis`, `startTime`, `duration`, and `statusCode`.

The audit found 0 duplicate `(traceID, spanID)` rows within cases. Exact composite parent resolution is 65,748,095 / 66,781,374 = 0.984527; 1,033,279 parent references did not resolve within the same trace ID. This aggregate is not uniform: 7 cases are below 90% resolution, and the lowest is `re2tt_ts-route-service_disk_2` at 0.385429. Of resolved/comparable links, 4,543 begin before their parent and 1,754,132 outlive their parent. These are observed data-quality facts, not grounds for repair or causal interpretation.

## Graph decision supported by the full subset

`serviceName` supports a literal service-node representation. `161` literal `(serviceName, operationName)` pairs support a reproducible operation representation across 27 observed services. However, 12 raw operation strings occur under more than one service, so the operation string by itself is not a stable globally unique operation identity. There is no operation-level root-cause target in this trace audit.

Resolved parent-span links yield 55 observed cross-service **parent-to-child trace relation** pairs. They do not establish network `CALLS`, resource `USES`, messaging semantics, or causal propagation. Across every physical schema, there are no dedicated HTTP/RPC/peer/endpoint, resource, messaging, causal, attributes/events/links, or span-kind field names. `operationName` remains a textual field and does not change that conclusion.

## Task-B implication for RE2-TT

The full RE2-TT trace subset supports a trace-derived service/operation representation with observed parent-child relations, subject to the recorded integrity rates. A pilot must retain only resolved parent links and report per-case resolution; it must not impute the missing 1,033,279 parent references. The data do **not** support labeling those edges as protocol calls or causal propagation, and they do **not** supply resource or operation-level ground truth. This is evidence about the dataset only; it selects no algorithm or research question.
