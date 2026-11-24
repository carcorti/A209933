#!/usr/bin/env python3
"""Focused transaction and verifier evidence supplement for Carlo Corti."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('q', Path(__file__).with_name('qualify.py'))
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)
s, v = q.s, q.v


def main():
    with tempfile.TemporaryDirectory(prefix='a209933-delta-') as name:
        tmp = Path(name)
        cat = q.fixture(tmp, (q.ROOT / 'data/prime.tsv').read_bytes())
        real_open = Path.open
        class CloseFailure:
            def __init__(self, stream):
                self.stream = stream
            def __enter__(self):
                return self.stream.__enter__()
            def __exit__(self, *args):
                self.stream.__exit__(*args)
                raise OSError('deterministic close failure')
        with contextlib.redirect_stdout(io.StringIO()):
            for basename in ('b209933.txt', '.pending'):
                def failing_open(path, mode='r', *args, **kwargs):
                    stream = real_open(path, mode, *args, **kwargs)
                    return CloseFailure(stream) if path.name == basename and 'x' in mode else stream
                out = tmp / ('tableclose' if basename == 'b209933.txt' else 'jsonclose')
                with patch.object(Path, 'open', failing_open):
                    q.rejects('close-failure-' + basename, lambda: s.materialize(cat, 25, out))
                q.observation('close-no-receipt-' + basename, (out / 'run.json').exists(), False)
            out = tmp / 'changed'
            original = cat.read_bytes()
            real_rows = s.rows
            def changing_rows(c, target):
                for row in real_rows(c, target):
                    yield row
                cat.write_bytes(original.replace(b'2026-11-23', b'2026-11-24'))
            with patch.object(s, 'rows', changing_rows):
                q.rejects('input-change-before-commit', lambda: s.materialize(cat, 25, out))
            q.observation('changed-no-receipt', (out / 'run.json').exists(), False)
            cat.write_bytes(original)
            q.rejects('missing-parent', lambda: s.materialize(cat, 25, tmp / 'absent' / 'out'))
            good = tmp / 'good'
            s.materialize(cat, 25, good)
            table_path = good / 'b209933.txt'
            original_table = table_path.read_bytes()
            table_path.write_bytes(b'1 ' + b'1' * (v.MAX_LINE + 1) + b'\n\n')
            q.rejects('oversized-result-line', lambda: v.verify_run(good, cat))
            table_path.write_bytes(original_table)
            (good / '.pending').write_text('incomplete publication')
            q.rejects('pending-publication-rejected', lambda: v.verify_run(good, cat))
            (good / '.pending').unlink()
            receipt_path = good / 'run.json'
            raw = receipt_path.read_bytes()
            data = json.loads(raw)
            data['table']['bytes'] = True
            receipt_path.write_text(json.dumps(data))
            q.rejects('boolean-table-metadata', lambda: v.verify_run(good, cat))
            receipt_path.write_bytes(raw)
            table_path.unlink()
            table_path.symlink_to(q.ROOT / 'data/b209933.txt')
            q.rejects('symlink-run-file', lambda: v.verify_run(good, cat))
        # Syntax analysis creates no bytecode or cache files.
        for path in (q.ROOT / 'src/a209933.py', q.ROOT / 'check/verify.py'):
            compile(path.read_bytes(), str(path), 'exec')
            q.OBS.append({'id': 'compile-' + path.name, 'status': 'PASS'})
    print(json.dumps({'status': 'PASS', 'observations': q.OBS,
                      'source_sha256': v.file_hash(q.ROOT / 'src/a209933.py'),
                      'verifier_sha256': v.file_hash(q.ROOT / 'check/verify.py'),
                      'supplement_sha256': v.file_hash(__file__),
                      'scratch_removed': True}, indent=2))


if __name__ == '__main__':
    main()
