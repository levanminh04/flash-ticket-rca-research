"""Trusted pre-execution receipt and subprocess launcher; never a numeric worker."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from .contract import W, P, begin_run, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run_id')
    parser.add_argument('script')
    parser.add_argument('--stage', default='synthetic qualification')
    parser.add_argument('--exposure', default='SYNTHETIC ONLY')
    parser.add_argument('--input', action='append', default=[])
    parser.add_argument('--config')
    args, extra = parser.parse_known_args()
    script = (W / args.script).resolve()
    script.relative_to(W)
    sources = sorted((W / 'scripts/task_e').glob('*.py'))
    sources += sorted((W / 'tests/task_e').glob('*.py'))
    sources += [W / 'task-d/td-v1.3-c5-clarification-rationale.md',
                P / 'docs/research-rca/task-d-method-and-experiment-specification.md']
    run = W / 'results/task-e' / args.run_id
    command = [sys.executable, str(script), str(run), *extra]
    begin_run(args.run_id, command, sources, stage=args.stage,
              input_files=[Path(p) for p in args.input], exposure=args.exposure,
              config=json.loads(Path(args.config).read_text(encoding='utf-8')) if args.config else None,
              output_schema='Stage-specific JSON receipts, lossless numeric NPZ intermediates, stdout/stderr')
    start = time.perf_counter()
    with (run / 'stdout.log').open('x', encoding='utf-8') as out, \
            (run / 'stderr.log').open('x', encoding='utf-8') as err:
        process = subprocess.run(command, cwd=W, stdout=out, stderr=err)
    write_json(run / 'execution.json', {'exit_code': process.returncode,
               'wall_seconds': time.perf_counter() - start}, exclusive=True)
    print(run)
    print((run / 'stdout.log').read_text(encoding='utf-8'))
    print((run / 'stderr.log').read_text(encoding='utf-8'))
    raise SystemExit(process.returncode)


if __name__ == '__main__':
    main()
