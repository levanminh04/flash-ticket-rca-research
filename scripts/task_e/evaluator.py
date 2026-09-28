"""Evaluator-side utilities; never imported by ranking/detection workers."""
from __future__ import annotations

import math
import numpy as np


def tie_metrics(scores, root_index, *, failed=False):
    values = np.asarray(scores, dtype=np.float64)
    zero = {'rr': 0.0, 'hit1': 0.0, 'hit3': 0.0, 'hit5': 0.0, 'ndcg5': 0.0}
    if failed:
        return {**zero, 'status': 'METHOD_FAILURE', 'tie_start': None, 'tie_end': None}
    if root_index is None or root_index < 0 or root_index >= len(values):
        return {**zero, 'status': 'ROOT_ABSENT', 'tie_start': None, 'tie_end': None}
    if values.ndim != 1 or not np.isfinite(values).all():
        raise ValueError('Invalid ranking output must be recorded as explicit method failure')
    # NumPy decimal scaling can overflow for finite uncapped comparator scores.
    # Python's float round preserves finite large magnitudes at positive ndigits.
    rounded = np.array([round(float(value), 12) for value in values])
    root = rounded[root_index]
    start = 1 + int(np.sum(rounded > root))
    end = start + int(np.sum(rounded == root)) - 1
    count = end - start + 1
    result = {'rr': sum(1 / r for r in range(start, end + 1)) / count,
              'ndcg5': sum(1 / math.log2(r + 1)
                           for r in range(start, min(end, 5) + 1)) / count,
              'status': 'VALID_TIE' if count > 1 else 'VALID_RANK',
              'tie_start': start, 'tie_end': end}
    for k in (1, 3, 5):
        result[f'hit{k}'] = max(0, min(end, k) - start + 1) / count
    return result


def planned_mean(outcomes, planned_ids, metric='rr'):
    if len(set(planned_ids)) != len(planned_ids) or not planned_ids:
        raise ValueError('Planned denominator must be unique and nonempty')
    if set(outcomes) != set(planned_ids):
        raise ValueError('Every planned ID must have an explicit outcome, including failures')
    return sum(float(outcomes[i][metric]) for i in planned_ids) / len(planned_ids)


def service_scores_from_metric_ranks(ranks, metric_owners, n_services):
    """RCD-only partial padding: success [] yields one complete worst tie."""
    if not isinstance(ranks, list) or any(not isinstance(k, str) for k in ranks):
        raise ValueError('Unparseable metric ranking')
    if len(ranks) != len(set(ranks)):
        raise ValueError('Duplicate metric keys in RCD output')
    selected, unknown = [], []
    for key in ranks:
        if key not in metric_owners:
            unknown.append(key)
        elif metric_owners[key] not in selected:
            selected.append(metric_owners[key])
    scores = np.zeros(n_services)
    for position, owner in enumerate(selected):
        if not isinstance(owner, int) or not 0 <= owner < n_services:
            raise ValueError('Invalid metric owner index')
        scores[owner] = len(selected) - position
    return scores, {'unknown_metric_keys': unknown, 'ranked_services': len(selected)}
