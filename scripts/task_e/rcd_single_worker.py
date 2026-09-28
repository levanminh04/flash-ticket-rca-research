"""One registered RCD configuration per process, same qualified numeric engine."""
import json
import hashlib
import sys
from pathlib import Path
from .rcd_numeric_worker import bootstrap, parse_request, run_request, REGISTERED, _object_without_duplicates, _reject_json_constant


def main():
    runtime = bootstrap(Path(sys.argv[1]).resolve())
    request = json.loads(sys.stdin.read(), object_pairs_hook=_object_without_duplicates, parse_constant=_reject_json_constant)
    if set(request) != {'values', 'config'}:
        raise ValueError('Only values and one registered config admitted')
    cfg = request['config']
    if (type(cfg) is not dict or set(cfg) != {'seed', 'bins'}
            or type(cfg['seed']) is not int or type(cfg['bins']) is not int
            or (cfg['seed'], cfg['bins']) not in REGISTERED):
        raise ValueError('Unregistered single configuration')
    # Reuse the unchanged independently qualified numeric value validator.
    all_configs = [{'seed': s, 'bins': b} for s, b in sorted(REGISTERED)]
    values, _ = parse_request(json.dumps({'values': request['values'], 'configs': all_configs}, allow_nan=False))
    response = run_request(values, [(cfg['seed'], cfg['bins'])], runtime)
    response['chunk_schema'] = 'TD13-RCD-SINGLE-CHUNK-v1'
    response['single_worker_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    response['fidelity']['execution'] = 'one registered configuration; unchanged qualified RCD engine'
    sys.stdout.write(json.dumps(response, allow_nan=False) + '\n')
    sys.stdout.flush()


if __name__ == '__main__':
    main()
