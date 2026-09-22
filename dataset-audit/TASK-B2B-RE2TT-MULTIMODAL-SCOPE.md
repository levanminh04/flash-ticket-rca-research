# Task B2B — targeted RE2-TT multimodal join audit scope

**Status:** `APPROVED BY CURRENT TASK INSTRUCTION · EXECUTING`  
**Bounded purpose:** resolve the Red Team's concrete challenge that the original RE2-TT raw sample is the one declared no-log case and therefore cannot establish whether a log-bearing RE2-TT case supports the same deterministic joins observed in other systems.

## QUESTION

For a normal log-bearing RE2-TT case, what exact raw join class applies to Metrics ↔ Logs, Metrics ↔ Traces, and Logs ↔ Traces?

## WHY THIS AFFECTS THE TASK-B VERDICT

The final RE2-TT pilot verdict may say that 89 log-bearing cases are usable with a precise service/time alignment only if that claim is supported by raw RE2-TT evidence. Metadata declares log presence but cannot prove raw schema or join fields. This bounded retrieval resolves the claim without downloading a suite or changing the original six-case sample plan.

## EXACT SUBSET

One metadata-valid, log-bearing RE2-TT case:

`re2tt_ts-auth-service_cpu_2`

It is the same root-cause service and fault family as the exceptional no-log `cpu_1` sample, but is a distinct official repeat and has all three telemetry modalities according to pinned metadata.

## EXACT FILE TYPES AND EXPECTED SCOPE

Only these three official objects at revision `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e` will be requested. The official path inventory was read before telemetry transfer.

| Object | Official size | Immutable LFS SHA-256 |
|---|---:|---|
| `re2tt_ts-auth-service_cpu_2/logs.parquet` | 3,351,283 bytes | `0cc2ed5ff13a20cf776a42d9d4c3914981afe025fbaa69109ac652d9c7502537` |
| `re2tt_ts-auth-service_cpu_2/metrics.parquet` | 933,362 bytes | `16597725c18258ce0a3bdedc1833fb52ad6638fdc5068e944dce23c1bbde6d93` |
| `re2tt_ts-auth-service_cpu_2/traces.parquet` | 20,050,343 bytes | `3d704979b684c5450a3ddcd48bb91a71d07c485edc878a2969b04ff152b5857c` |
| **Total maximum raw transfer** | **24,334,988 bytes (23.21 MiB)** | — |

No `inject_time.txt`, `root_cause.txt`, metadata snapshot, other case, or full suite will be retrieved. The original six-case manifest remains immutable. A separate B2B manifest records this addition and checks its local SHA-256 against the official LFS object hash.

## STOP CONDITION

Stop after the three listed objects are either locally checksum-verified or a named official object fails deterministic retrieval. Then run Subagent E's deterministic join audit on the added case and record its result as a `RAW SAMPLE FINDING` for one log-bearing RE2-TT case; it does not establish a 89-case full-suite join prevalence.
