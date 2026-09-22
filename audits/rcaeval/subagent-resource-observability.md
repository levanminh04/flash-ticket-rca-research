# Subagent Resource-Observability Audit — RCAEval

**Role:** independent resource-observability reviewer  
**Status:** RAW SAMPLE FINDING — six pinned raw cases only  
**Source revision:** phamquiluan/RCAEval at afeacb11bcc94dadfd1c8f483ee4377b2b8b614e  
**Scope:** inspect raw Parquet fields and literal values only; do not infer deployment architecture from names, operation text, or free-form log messages.

## Evidence rule

An OBSERVABLE ENTITY would require a dedicated structured identity and a dataset-supported relation. A literal metric prefix or container_name value does not meet that rule by itself. It is preserved as raw evidence but is not converted into a runtime resource, a graph node, or a USES edge.

The deterministic evidence is in [subagent-resource-observability-evidence.json](subagent-resource-observability-evidence.json).

## Raw schema evidence

The three selected trace files expose only these flat fields:

    time, traceID, spanID, serviceName, methodName, operationName,
    parentSpanID, startTimeMillis, startTime, duration, statusCode

They contain no nested map/attribute field and no host, pod, container, database, cache, broker, queue, topic, peer, endpoint, or resource field.

The four selected log files each expose exactly timestamp, container_name, and message. container_name is a literal label, not a container ID or pod/host identity. message is a scalar text body, not a structured resource relation.

Metrics are wide tables. Their series prefixes include raw lexical labels such as ts-auth-mongo, ts-voucher-mysql, carts-db, redis, rabbitmq, and queue-master. These strings are evidence of literal telemetry series names only. The schema has no typed resource ID, endpoint, database name, topic name, connection attribute, or service-to-resource relation.

## Decisive resource classification

| Resource type | Classification | Raw evidence | May form a graph node? | May form a USES edge? |
|---|---|---|---|---|
| Host | NOT SUPPORTED | no structured host/node/hostname field in any sampled schema | No | No |
| Pod/container | ATTRIBUTE ONLY | logs.parquet.container_name exists, but no pod UID, container ID, host/node, or lifecycle relation | No resource node; retain only as a log-row attribute | No |
| Database | REQUIRES EXTERNAL MAPPING | lexical labels -mongo, -mysql, and -db occur in metrics/container labels; no db.system, ID, endpoint, connection, or relation | No, from this dataset alone | No |
| Logical database | NOT SUPPORTED | no logical DB/schema/catalog/name field | No | No |
| Cache | REQUIRES EXTERNAL MAPPING | literal redis / cache strings occur in telemetry labels or free text, without cache identity or relation | No, from this dataset alone | No |
| Broker | REQUIRES EXTERNAL MAPPING | literal rabbitmq / broker strings occur in telemetry labels or free text, without broker ID or producer/consumer relation | No, from this dataset alone | No |
| Queue/topic | NOT SUPPORTED | no queue/topic/destination/producer/consumer field; queue-master is only a label | No | No |
| Other | ATTRIBUTE ONLY | opaque metric prefixes and container_name literals are available as attributes, not typed resource identities | No typed resource node | No |

REQUIRES EXTERNAL MAPPING is deliberately not permission to add those nodes in Task B. It says only that an external, separately governed source would be needed to establish the type, identity, and relationship.

## RE2-TT pilot implication

**RAW SAMPLE FINDING.** The selected RE2-TT case, re2tt_ts-auth-service_cpu_1, has metrics.parquet and traces.parquet, but no raw log file. Its metric prefixes include literal -mongo and -mysql strings, while the trace schema has no resource fields. Therefore the first RE2-TT pilot must use **no resource nodes and no USES edges**. It can retain trace-derived service/operation representation and metric-series features only under their own explicit rules; this audit does not treat either as resource topology.

## Verdict

**Task B resource verdict:** a typed resource graph is **NOT SUPPORTED BY THE PINNED RAW DATA**. No host, container, database, logical database, cache, broker, queue/topic, or other resource may be introduced as a graph node or USES edge in the first RE2-TT pilot from RCAEval alone.
