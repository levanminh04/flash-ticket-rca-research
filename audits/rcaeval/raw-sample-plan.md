# RAW SAMPLE PLAN — RCAEval Task B

**Status:** `EXECUTION PLAN`, not a research-method or dataset-selection decision.  
**Evidence scope:** metadata-wide facts for the selection criteria; future results from these six cases are `RAW SAMPLE FINDING` only.  
**Pinned source:** Hugging Face `phamquiluan/RCAEval`, revision `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`.

## Independent proposals and reconciliation

| Reviewer | Independent proposal (not final) | Contribution retained in final plan |
|---|---|---|
| A — Metadata | `re1ob_adservice_cpu_1`, `re2ob_productcatalogservice_loss_1`, `re2tt_ts-order-service_disk_2`, `re2tt_ts-auth-service_cpu_1`, `re3ss_carts_f1_1`, `re3ob_adservice_f5_1` | Tri-modal network case, trace-without-log case, root-cause-file case |
| F — Ground truth/leakage | `re1ob_productcatalogservice_cpu_3`, `re2ob_checkoutservice_socket_1`, `re2ss_orders_loss_2`, `re2tt_ts-auth-service_cpu_1`, `re3ss_carts_f1_1`, `re3tt_ts-route-service_f2_1` | Timestamp-quality check, logs-without-trace case, trace-without-log case, root-cause-file case, code-level TT case |
| Main agent | `re1tt_ts-order-service_disk_1`, `re2ob_checkoutservice_cpu_1`, `re2ss_carts_loss_1`, `re2tt_ts-auth-service_cpu_1`, `re3ob_adservice_f3_1`, `re3ss_front-end_f2_1` | Cross-system comparison and explicit missing-modality coverage criteria |

`re1ob_productcatalogservice_cpu_3` is retained despite the reproducibility review's default-exclusion recommendation. It is **not** a representative benchmark case: it resolves an explicit metadata contradiction through raw evidence. This is a deterministic adjudication need, not a vote between reviewers.

## Six cases approved for selective retrieval

| Case | Suite | System | Fault metadata | Root target metadata | Reason | Uncertainty tested |
|---|---|---|---|---|---|---|
| `re1ob_productcatalogservice_cpu_3` | RE1 | Online Boutique | `cpu` | `productcatalogservice` | Metric-only data-quality case | Is metadata `inject_time` inconsistent with raw injection/timestamps? |
| `re2ob_productcatalogservice_loss_1` | RE2 | Online Boutique | `loss` | `productcatalogservice` | Tri-modal network-labeled case | Trace/log/metric schemas and observed relationships |
| `re2ss_orders_loss_2` | RE2 | Sock Shop | `loss` | `orders` | Logs + metrics with no declared trace | Is trace absence actual and how does it constrain graph construction? |
| `re2tt_ts-auth-service_cpu_1` | RE2 | Train Ticket | `cpu` | `ts-auth-service` | Traces + metrics with no declared log | Is log absence actual and what trace schema exists? |
| `re3ss_carts_f1_1` | RE3 | Sock Shop | `f1` | `carts` | Root-cause file present; no declared trace | Exact leakage contents and safe exclusion path |
| `re3tt_ts-route-service_f2_1` | RE3 | Train Ticket | `f2` | `ts-route-service` | Tri-modal code-level case | Observed service/operation/resource fields and cross-system schema comparison |

The six cases cover the three systems, RE1/RE2/RE3, resource/network/code-level fault labels, metric-only/logs-without-trace/traces-without-log/tri-modal layouts, an explicit root-cause-file leakage case, and at least one raw data-quality contradiction. They do **not** support dataset-wide schema or prevalence claims.
