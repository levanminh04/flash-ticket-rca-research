"""Task D compatibility evidence: bounded Parquet footers/tree/README only.

No remote telemetry rows, model execution, baseline installation or training.
HTTP200/full-object responses are rejected, not accepted as range reads.
Official LFS hashes identify objects; they are not recomputed full-file hashes.
"""
import hashlib
import json
import struct
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pyarrow as pa
import pyarrow.parquet as pq
from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[1]
REV = 'afeacb11bcc94dadfd1c8f483ee4377b2b8b614e'
META = ROOT / 'datasets/rcaeval/metadata/cases.parquet'
OUT = ROOT / 'task-d/td-v1.2-public-metadata.json'
LEMMA = {
    'Product_Review_Preprocessed': 'df25484004e50483de6f6756c3a4d7ab03174b83',
    'Cloud_Computing_Preprocessed': '03f82a2c4b16afe09e9315def9f5d6990427000a',
    'Product_Review_Original': '63aa4abe7dd7217d9b0b108894c7d893e2b29aef',
    'Cloud_Computing_Original': '9e5ad23fa390f6b596f41be014233fe446679bcd',
}
api = HfApi()
info = api.dataset_info('phamquiluan/RCAEval', revision=REV, files_metadata=True)
assert info.sha == REV
meta = pq.read_table(META).to_pandas().set_index('case')
files = [f for f in info.siblings
         if f.rfilename.startswith('re3tt_') and f.rfilename.endswith('.parquet')]


def check_footer(f):
    url = f'https://huggingface.co/datasets/phamquiluan/RCAEval/resolve/{REV}/{f.rfilename}'
    with httpx.Client(follow_redirects=True, timeout=40) as client:
        def read_range(a, b):
            with client.stream('GET', url + f'?footer_review_range={a}-{b}',
                               headers={'Range': f'bytes={a}-{b}',
                                        'Accept-Encoding': 'identity'}) as response:
                if response.status_code != 206:
                    raise RuntimeError(f'Reject HTTP{response.status_code}, no full download')
                expected = b - a + 1
                data = bytearray()
                for chunk in response.iter_raw():
                    data.extend(chunk)
                    if len(data) > expected:
                        raise RuntimeError('Oversized range response rejected')
                if len(data) != expected:
                    raise RuntimeError('Range length mismatch')
                return bytes(data)

        tail = read_range(f.size - 8, f.size - 1)
        assert tail[4:] == b'PAR1', 'Not a Parquet footer'
        n = struct.unpack('<I', tail[:4])[0]
        assert n <= 500000, 'Footer exceeds fixed500k bound'
        footer = read_range(f.size - 8 - n, f.size - 1)
    pf = pq.ParquetFile(pa.BufferReader(b'PAR1' + footer))
    schema = str(pf.schema_arrow.remove_metadata())
    case, filename = f.rfilename.split('/')
    modality = filename.split('.')[0]
    expected_rows = int(meta.loc[case, {'metrics': 'n_timesteps', 'logs': 'n_logs',
                                      'traces': 'n_traces'}[modality]])
    timecol = {'metrics': 'time', 'logs': 'timestamp', 'traces': 'startTimeMillis'}[modality]
    idx = pf.schema_arrow.names.index(timecol)
    stats = [pf.metadata.row_group(j).column(idx).statistics
             for j in range(pf.metadata.num_row_groups)]
    finite_stats = [s for s in stats if s and s.has_min_max]
    return {
        'file': f.rfilename, 'file_bytes': f.size,
        'official_lfs_sha256': f.lfs.sha256, 'http_range_status': 206,
        'footer_bytes_transferred': n + 16,
        'footer_sha256': hashlib.sha256(footer).hexdigest(),
        'rows': pf.metadata.num_rows, 'groups': pf.metadata.num_row_groups,
        'match_metadata_rows': pf.metadata.num_rows == expected_rows,
        'schema': schema, 'schema_sha256': hashlib.sha256(schema.encode()).hexdigest(),
        'time_min': min(s.min for s in finite_stats) if finite_stats else None,
        'time_max': max(s.max for s in finite_stats) if finite_stats else None,
        'timestamp_unit_evidence': ('milliseconds: field naming+existing sample arithmetic'
                                    if modality == 'traces'
                                    else 'epoch seconds: documentation+existing sample alignment'),
    }


rows, errors = [], []
with ThreadPoolExecutor(max_workers=6) as pool:
    futures = {pool.submit(check_footer, f): f.rfilename for f in files}
    for future in as_completed(futures):
        try:
            rows.append(future.result())
        except Exception as error:
            errors.append({'file': futures[future], 'error': str(error)})

cohorts = []
for dataset, g in meta.reset_index().groupby('dataset'):
    cohorts.append({
        'dataset': dataset, 'cases': len(g),
        'roots': g.root_cause_service.value_counts().to_dict(),
        'faults': g.fault.value_counts().to_dict(),
        'scenario_cells': [{'root': root, 'fault': fault, 'cases': int(n)}
                           for (root, fault), n in g.groupby(['root_cause_service', 'fault']).size().items()],
        'logs': int(g.has_logs.sum()), 'traces': int(g.has_traces.sum()),
        'root_answer_files': int(g.has_root_cause_file.sum()),
        'normal_timesteps': list(map(int, g.normal_timesteps.unique())),
        'faulty_timesteps': list(map(int, g.faulty_timesteps.unique())),
        'injection_seconds_after_metric_start': sorted(set(map(int, g.inject_time - g.time_start))),
    })

lemma = []
for name, revision in LEMMA.items():
    source = api.dataset_info('Lemma-RCA-NEC/' + name, revision=revision, files_metadata=True)
    assert source.sha == revision
    url = f'https://huggingface.co/datasets/Lemma-RCA-NEC/{name}/resolve/{revision}/README.md'
    response = httpx.get(url, follow_redirects=True, timeout=30)
    response.raise_for_status()
    assert len(response.content) < 100000, 'README size bound'
    lemma.append({'repo': source.id, 'revision': revision, 'readme': response.text,
                  'readme_sha256': hashlib.sha256(response.content).hexdigest(),
                  'card_metadata': source.card_data.to_dict() if source.card_data else None,
                  'files': [{'file': f.rfilename, 'bytes': f.size,
                             'official_lfs_sha256': f.lfs.sha256 if f.lfs else None}
                            for f in source.siblings]})

result = {
    'created_utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'PINNED RE3-TT FOOTERS + EXISTING LOCAL METADATA + LEMMA TREE/README ONLY; NO REMOTE TELEMETRY ROWS; NO MODEL RUN',
    'limits': ['Footer facts do not certify joins/parent resolution/candidate visibility/arrival availability',
               'Official LFS SHA is not independently recomputed full-file checksum',
               'No Task E, model scoring, training or new raw corpus materialization'],
    'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'revision': REV, 'metadata_sha256': hashlib.sha256(META.read_bytes()).hexdigest(),
    'checked': len(rows), 'errors': errors,
    'bytes_transferred': sum(r['footer_bytes_transferred'] for r in rows),
    'modality_summary': {mod: {
        'files': len([r for r in rows if r['file'].endswith(mod + '.parquet')]),
        'rows': sum(r['rows'] for r in rows if r['file'].endswith(mod + '.parquet')),
        'distinct_schema_hashes': len({r['schema_sha256'] for r in rows if r['file'].endswith(mod + '.parquet')}),
        'all_row_metadata_match': all(r['match_metadata_rows'] for r in rows if r['file'].endswith(mod + '.parquet')),
    } for mod in ['metrics', 'logs', 'traces']},
    'per_file_receipt': sorted(rows, key=lambda r: r['file']),
    'metadata_cohorts': cohorts, 'lemma_source_pins': lemma,
}
OUT.write_text(json.dumps(result, indent=2, default=str), encoding='utf-8')
print(json.dumps({'checked': len(rows), 'errors': errors,
                  'bytes_transferred': result['bytes_transferred'],
                  'modality_summary': result['modality_summary']}))
raise SystemExit(0 if len(rows) == 90 and not errors else 1)
