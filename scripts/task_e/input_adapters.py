"""Trusted raw-window adapters. Names and epoch clocks never enter workers."""
from __future__ import annotations
import numpy as np
from .loader import (_c1_window_frame, _metric_mapping, _metric_bins, _trace_slice,
                     _deduplicate_trace, _counts, _graph, CHANNEL_TYPES, LoaderError)


def rcd_bundle(raw, tau, service_names):
    """TD §6 raw1s 300/300, >=240 seconds each side, positive reference IQR."""
    frame = _c1_window_frame(raw.get('metrics'), 'time', tau - 300, tau + 300)
    if frame is None:
        raise LoaderError('RCD missing metrics')
    mapping, unmatched = _metric_mapping(frame, service_names)
    accepted, owners, reports = [], {}, {}
    for column, (owner, _) in mapping.items():
        group = frame.groupby('time')[column]
        conflicts = group.nunique(dropna=False)
        record = {'conflicting_seconds': int((conflicts > 1).sum())}
        reports[column] = record
        if record['conflicting_seconds']:
            record['reason'] = 'CONFLICTING_ENTITY_SECOND'
            continue
        clean = frame[['time', column]].drop_duplicates('time').set_index('time')[column]
        values = clean.reindex(np.arange(tau - 300, tau + 300)).to_numpy(dtype=float, copy=True)
        values[~np.isfinite(values)] = np.nan
        a, b = values[:300], values[300:]
        nref, nquery = int(np.isfinite(a).sum()), int(np.isfinite(b).sum())
        record.update(reference_seconds=nref, query_seconds=nquery)
        if nref < 240 or nquery < 240:
            record['reason'] = 'INSUFFICIENT_DISTINCT_SECONDS'
            continue
        finite = a[np.isfinite(a)]
        q25, median, q75 = np.quantile(finite, [.25, .5, .75], method='linear')
        iqr = q75 - q25
        record.update(reference_iqr=float(iqr), reference_median=float(median))
        if not np.isfinite(iqr) or iqr <= 0:
            record['reason'] = 'REFERENCE_IQR_NOT_POSITIVE'
            continue
        record['imputed_reference'] = int(np.isnan(a).sum())
        record['imputed_query'] = int(np.isnan(b).sum())
        values[np.isnan(values)] = median
        key = f'm{len(accepted)}'
        owners[key] = int(owner)
        record.update(reason='ELIGIBLE', opaque_key=key)
        accepted.append(values)
    values = np.column_stack(accepted) if accepted else np.empty((600, 0))
    return {'values': values, 'owners': owners,
            'audit': {'channels': reports, 'unmatched': unmatched,
                      'eligible_columns': len(accepted), 'rows': 600,
                      'imputation': 'reference median only; no interpolated seconds'}}


def integrated_bundle(raw, trigger_epoch):
    """Past-only TD §7.1 reference300s/query60s with independent candidate V."""
    t = int(trigger_epoch)
    if raw.get('metrics') is None or t - int(raw['metrics'].time.min()) < 360:
        raise LoaderError('INSUFFICIENT_HISTORY')
    lo, middle = t - 360, t - 60
    traces = _trace_slice(_c1_window_frame(raw.get('traces'), 'startTimeMillis', lo*1000, t*1000), lo, t)
    traces, duplicates = _deduplicate_trace(traces)
    names = sorted(set(traces.serviceName))
    reference, query = traces[traces.startTimeMillis < middle*1000], traces[traces.startTimeMillis >= middle*1000]
    metrics = _c1_window_frame(raw.get('metrics'), 'time', lo, t)
    ref_m, ref_a = _metric_bins(metrics, names, lo, middle, 10, 5, invalidate_channel=True)
    query_m, query_a = _metric_bins(metrics, names, middle, t, 10, 5, invalidate_channel=True)
    mapping, _ = _metric_mapping(metrics, names)
    conflicts = {c for report in (ref_a, query_a) for c, times in report['conflicting_seconds'].items() if times}
    for c in conflicts:
        node, channel = mapping[c]
        ref_m[node, channel] = np.nan
        query_m[node, channel] = np.nan
    rt, rta = _counts(reference, names, lo, middle, 10, 'traces')
    qt, qta = _counts(query, names, middle, t, 10, 'traces')
    try:
        logs = _c1_window_frame(raw.get('logs'), 'timestamp', lo, t)
        rl, rla = _counts(logs, names, lo, middle, 10, 'logs')
        ql, qla = _counts(logs, names, middle, t, 10, 'logs')
    except LoaderError as exc:
        rl, rla = _counts(None, names, lo, middle, 10, 'logs')
        ql, qla = _counts(None, names, middle, t, 10, 'logs')
        rla['error'] = qla['error'] = str(exc)
    adj, ga = _graph(reference, names)
    return {'ref': np.concatenate((ref_m, rt[:, None], rl[:, None]), axis=1),
            'query': np.concatenate((query_m, qt[:, None], ql[:, None]), axis=1),
            'adj': adj, 'channel_types': CHANNEL_TYPES.copy(), 'service_names': names,
            'audit': {'profile': 'TD12-INTEGRATED-MTL', 'graph': ga, 'duplicates': duplicates,
                      'metric_ref': ref_a, 'metric_query': query_a,
                      'trace_ref': rta, 'trace_query': qta, 'log_ref': rla, 'log_query': qla}}
