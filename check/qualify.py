#!/usr/bin/env python3
"""Finite local A209933 qualification; never an official campaign.

Owner: Luna for Carlo Corti. Scratch fixtures are temporary. One T101 replay
may be retained. Full mode executes the predeclared finite scale plan once.
"""
import argparse
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('producer', ROOT / 'src/a209933.py')
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
v = s.v
OBS = []


def observation(name, actual, expected):
    if actual != expected:
        raise AssertionError((name, actual, expected))
    OBS.append({'id': name, 'status': 'PASS', 'actual': actual})


def rejects(name, call):
    try:
        call()
    except (OSError, ValueError, UnicodeError, TypeError, KeyError, KeyboardInterrupt):
        OBS.append({'id': name, 'status': 'PASS', 'actual': 'REJECTED'})
    else:
        raise AssertionError(name + ': accepted invalid state')


def execute(args, expected=0, cwd=ROOT, preexec_fn=None):
    result = subprocess.run(args, cwd=cwd, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=600, preexec_fn=preexec_fn)
    if expected is not None and result.returncode != expected:
        raise AssertionError((args, result.returncode, result.stdout, result.stderr))
    return result


def fixture(tmp, raw):
    path = tmp / 'prime.tsv'
    path.write_bytes(raw)
    return path


def synthetic_catalog(raw):
    lines = raw.decode('ascii').splitlines()
    lines[1] = '# mode=SYNTHETIC'
    lines[3] = '# complete_through=' + str(v.MAX_T)
    lines[4] = '# coverage_source=synthetic:capacity-only'
    for i in range(6, len(lines)):
        fields = lines[i].split('\t')
        fields[2] = 'SYNTHETIC'
        fields[4] = 'synthetic:capacity-only'
        lines[i] = '\t'.join(fields)
    return ('\n'.join(lines) + '\n').encode('ascii')


def local_matrix(tmp, original):
    cat_path = fixture(tmp, original)
    cat = v.catalog(cat_path)
    # Arithmetic oracle uses actual small integers, not either string algorithm.
    pairs = 0
    for t in range(2, 129):
        for m in v.COEFFICIENTS:
            expected = str(m * ((10 ** t - 1) // 9)).encode('ascii')
            if s.term(t, m) != expected or v.multiply_repunit(t, m) != expected:
                raise AssertionError(('small arithmetic', t, m))
            pairs += 1
    observation('decimal-oracle-distinct-pairs', pairs, 1397)
    for n in (1, 2, 13, 14, 23, 24, 25, 34, 35, 36, 46, 47, 57, 58, 68, 69, 79, 80, 90, 91, 100, 101):
        out = tmp / 'small'
        result = s.materialize(cat_path, n, out)
        observation('normal-prefix-' + str(n), v.verify_run(out, cat_path), result)
        observation('exact-byte-model-' + str(n), v.output_size(v.admitted(cat, n), n), result['bytes'])
        if n == 24:
            observation('canonical-byte-identity', (out / 'b209933.txt').read_bytes(),
                        (ROOT / 'data/b209933.txt').read_bytes())
            OBS[-1]['actual'] = '129 bytes, exact LF LF and SHA256 match'
        shutil.rmtree(out)
    for text in ('0', '-1', '+1', ' 1', '01', '135', '1.0', '1e2', '١', '9' * 1000):
        rejects('numeric-' + repr(text[:12]), lambda text=text: v.natural(text, v.MAX_ROWS))
    observation('numeric-max-minus-one', v.natural('133', 134), 133)
    observation('numeric-max', v.natural('134', 134), 134)
    for n in (0, 135, True, 1.5):
        rejects('target-type-' + repr(n), lambda n=n: v.admitted(cat, n))
    for n in (102, 112, 123, 134):
        rejects('PRP-barrier-' + str(n), lambda n=n: v.admitted(cat, n))
    mutants = {
        'empty': b'', 'oversize': b'x' * 65537,
        'CRLF': original.replace(b'\n', b'\r\n'), 'truncated': original[:-1],
        'nonascii': original + b'\xff',
        'unknown-key': original.replace(b'# mode=', b'# bogus='),
        'duplicate-key': original.replace(b'# mode=PUBLISHED', b'# schema=PUBLISHED'),
        'bad-date': original.replace(b'2026-11-23', b'2026-02-30'),
        'extra-line': original + b'\n',
        'duplicate-rank': original.replace(b'2\t19\t', b'1\t19\t'),
        'unsorted': original.replace(b'3\t23\t', b'3\t17\t'),
        'even-exponent': original.replace(b'3\t23\t', b'3\t24\t'),
        'exponent-three': original.replace(b'2\t19\t', b'2\t3\t'),
        'zero-exponent': original.replace(b'2\t19\t', b'2\t0\t'),
        'max-exceeded': original.replace(b'8177207', b'8177208'),
        'empty-attribution': original.replace(b'Historical_repunit_prime_catalog', b''),
        'bad-source': original.replace(b'https://', b'file://'),
        'positive-substring': original.replace(b'PROVEN', b'not-PROVEN'),
        'unknown-status': original.replace(b'PROVEN', b'CERTIFIED'),
        'too-many-rows': original + original.splitlines()[-1] + b'\n',
        'mode-conflict': synthetic_catalog(original)}
    for name, raw in mutants.items():
        fixture(tmp, raw)
        rejects('catalog-' + name, lambda: v.catalog(cat_path))
    fixture(tmp, original)
    synthetic = synthetic_catalog(original)
    synth_path = tmp / 'cap.tsv'
    synth_path.write_bytes(synthetic)
    synth = v.catalog(synth_path, True)
    observation('full-byte-bound-exact', v.output_size(v.admitted(synth, 134), 134), 159374652)
    alt = synthetic.decode().splitlines()
    for i, t in enumerate([2] + [v.MAX_T - 2 * j for j in range(9, -1, -1)], 6):
        fields = alt[i].split('\t')
        fields[1] = str(t)
        alt[i] = '\t'.join(fields)
    synth_path.write_text('\n'.join(alt) + '\n')
    alternate = v.catalog(synth_path, True)
    observation('hostile-volume-counterexample-size', v.output_size(alternate['rows'], 134), 899492404)
    rejects('aggregate-byte-envelope', lambda: v.admitted(alternate, 134))
    outsize = tmp / 'oversized'
    rejects('volume-before-output-mutation', lambda: s.materialize(synth_path, 134, outsize, True))
    observation('oversized-root-not-created', outsize.exists(), False)
    with patch.object(v, 'MAX_BYTES', v.MAX_BYTES - 1):
        rejects('one-byte-beyond-effective-quota', lambda: v.admitted(synth, 134))
    missing = tmp / 'absent'
    rejects('missing-catalog', lambda: v.catalog(missing))
    gap = copy.deepcopy(cat)
    gap['coverage'] = 23
    rejects('completeness-gap', lambda: v.admitted(gap, 57))
    changed = copy.deepcopy(cat)
    changed['rows'][8] = (270343, 'PROVEN')
    changed['coverage'] = 270343
    observation('future-input-evolution-no-source-change', len(v.admitted(changed, 112)), 9)
    changed['rows'][8] = (270343, 'PRP')
    changed['rows'][9] = (5794777, 'PROVEN')
    changed['coverage'] = 5794777
    rejects('later-proven-cannot-skip-PRP', lambda: v.admitted(changed, 123))
    # Completed tiny run for parser and failure controls.
    good = tmp / 'good'
    s.materialize(cat_path, 25, good)
    before = {p.name: v.file_hash(p) for p in good.iterdir()}
    rejects('existing-root', lambda: s.materialize(cat_path, 25, good))
    link = tmp / 'link'
    link.symlink_to(good, target_is_directory=True)
    rejects('symlink-root-producer', lambda: s.materialize(cat_path, 25, link))
    rejects('symlink-root-checker', lambda: v.verify_run(link, cat_path))
    link.unlink()
    table = (good / 'b209933.txt').read_bytes()
    receipt = (good / 'run.json').read_bytes()
    for name, raw in {'missing-row': table.replace(b'2 2\n', b''),
                      'wrong-index': table.replace(b'2 2\n', b'1 2\n'),
                      'wrong-value': table.replace(b'2 2\n', b'2 3\n'),
                      'one-LF': table[:-1], 'third-LF': table + b'\n',
                      'extra-data': table + b'26 1\n',
                      'leading-zero': table.replace(b'2 2\n', b'2 02\n')}.items():
        (good / 'b209933.txt').write_bytes(raw)
        rejects('table-' + name, lambda: v.verify_run(good, cat_path))
    (good / 'b209933.txt').write_bytes(table)
    parsed = json.loads(receipt)
    for field, value in (('target', True), ('status', 'INCOMPLETE'), ('schema', 'x'),
                         ('catalog_sha256', '0' * 64), ('source_sha256', '0' * 64),
                         ('verifier_sha256', '0' * 64), ('runtime', {}),
                         ('elapsed_seconds', -1), ('elapsed_seconds', float('nan')),
                         ('completed_utc', '2026-11-23T10:00:00')):
        mutant = {**parsed, field: value}
        (good / 'run.json').write_text(json.dumps(mutant))
        rejects('receipt-' + field + '-' + repr(value)[:20], lambda: v.verify_run(good, cat_path))
    for name, raw in {'duplicate-key': receipt.replace(b'"status":', b'"target":1,"status":'),
                      'truncated': receipt[:32], 'wrong-root': b'[]'}.items():
        (good / 'run.json').write_bytes(raw)
        rejects('receipt-' + name, lambda: v.verify_run(good, cat_path))
    (good / 'run.json').write_bytes(receipt)
    (good / 'extra').write_text('unexpected')
    rejects('extra-run-file', lambda: v.verify_run(good, cat_path))
    (good / 'extra').unlink()
    (good / 'run.json').unlink()
    rejects('missing-receipt', lambda: v.verify_run(good, cat_path))
    (good / 'run.json').write_bytes(receipt)
    observation('complete-output-preserved', {p.name: v.file_hash(p) for p in good.iterdir()}, before)
    base_flags = ['--catalog', str(cat_path), '--through', '25', '--out', str(tmp / 'cli')]
    cases = [[], ['--unknown'], ['--catalog'], base_flags + ['--through', '24'],
             base_flags + ['--synthetic'], ['--cat', str(cat_path)]]
    for i, flags in enumerate(cases):
        r = execute([sys.executable, '-B', str(ROOT / 'src/a209933.py'), *flags], expected=None)
        observation('CLI-invalid-' + str(i), r.returncode, 2)
    # Failures at row boundaries leave no admissible receipt, preserving other runs.
    original_rows = s.rows
    for stop in (0, 1, 3):
        def interrupted_rows(c, target, stop=stop):
            for pos, row in enumerate(original_rows(c, target)):
                if pos == stop:
                    raise InterruptedError('deterministic row-boundary interruption')
                yield row
        out = tmp / ('stop' + str(stop))
        with patch.object(s, 'rows', interrupted_rows):
            rejects('interruption-' + str(stop), lambda: s.materialize(cat_path, 25, out))
        observation('no-receipt-' + str(stop), (out / 'run.json').exists(), False)
        rejects('incomplete-rejected-' + str(stop), lambda: v.verify_run(out, cat_path))
    # fsync, close, write and atomic publication failures at distinct stages.
    for fail_at in (1, 2, 3, 4):
        real_fsync = os.fsync
        calls = [0]
        def failing_fsync(fd):
            calls[0] += 1
            if calls[0] == fail_at:
                raise OSError('injected fsync failure')
            return real_fsync(fd)
        out = tmp / ('fsync' + str(fail_at))
        with patch.object(s.os, 'fsync', failing_fsync):
            rejects('fsync-failure-' + str(fail_at), lambda: s.materialize(cat_path, 25, out))
        observation('fsync-no-receipt-' + str(fail_at), (out / 'run.json').exists(), False)
    out = tmp / 'linkfail'
    with patch.object(s.os, 'link', side_effect=OSError('injected publication failure')):
        rejects('receipt-publication-failure', lambda: s.materialize(cat_path, 25, out))
    observation('publish-no-receipt', (out / 'run.json').exists(), False)
    # Actual OS failure during buffered write/flush, not a fake numerical path.
    out = tmp / 'fsize'
    def small_fsize():
        signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
        resource.setrlimit(resource.RLIMIT_FSIZE, (128, 128))
    r = execute([sys.executable, '-B', str(ROOT / 'src/a209933.py'), '--catalog', str(cat_path),
                 '--through', '25', '--out', str(out)], expected=None, preexec_fn=small_fsize)
    observation('OS-write-limit-exit', r.returncode, 2)
    observation('OS-write-limit-no-receipt', (out / 'run.json').exists(), False)
    # Actual SIGTERM while the real maximum-generation path is active.
    syn = tmp / 'syn.tsv'
    syn.write_bytes(synthetic_catalog(original))
    out = tmp / 'signal'
    proc = subprocess.Popen([sys.executable, '-B', str(ROOT / 'src/a209933.py'),
                             '--catalog', str(syn), '--through', '134', '--synthetic', '--out', str(out)],
                            cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    started = proc.stdout.readline()
    if b'START' not in started:
        proc.kill(); proc.communicate()
        raise AssertionError('no START before signal')
    proc.terminate()
    stdout, stderr = proc.communicate(timeout=10)
    observation('SIGTERM-exit', proc.returncode, 2)
    observation('SIGTERM-no-receipt', (out / 'run.json').exists(), False)
    observation('prior-run-still-preserved', {p.name: v.file_hash(p) for p in good.iterdir()}, before)
    # Isolated source dependency closure: no workspace lookup outside copied tree.
    isolated = tmp / 'arbitrary-root'
    (isolated / 'src').mkdir(parents=True)
    (isolated / 'check').mkdir()
    shutil.copy2(ROOT / 'src/a209933.py', isolated / 'src/a209933.py')
    shutil.copy2(ROOT / 'check/verify.py', isolated / 'check/verify.py')
    shutil.copy2(cat_path, isolated / 'prime.tsv')
    r = execute([sys.executable, '-B', 'src/a209933.py', '--catalog', 'prime.tsv', '--through', '25', '--out', 'result'], cwd=isolated)
    r = execute([sys.executable, '-B', 'check/verify.py', '--catalog', 'prime.tsv', '--run', 'result'], cwd=isolated)
    observation('isolated-source-route', json.loads(r.stdout)['rows'], 25)


def measured(tmp, cat, target, synthetic, out):
    log = tmp / 'time.log'
    args = [sys.executable, '-B', str(ROOT / 'src/a209933.py'), '--catalog', str(cat),
            '--through', str(target), '--out', str(out)] + (['--synthetic'] if synthetic else [])
    start = time.monotonic()
    result = execute(['/usr/bin/time', '-v', '-o', str(log), *args])
    producer_wall = time.monotonic() - start
    raw = log.read_text()
    peak = int(re.search(r'Maximum resident set size \(kbytes\): (\d+)', raw)[1]) * 1024
    user = float(re.search(r'User time \(seconds\): ([0-9.]+)', raw)[1])
    system = float(re.search(r'System time \(seconds\): ([0-9.]+)', raw)[1])
    start = time.monotonic()
    standalone = execute(['/usr/bin/time', '-v', '-o', str(log), sys.executable, '-B',
                          str(ROOT / 'check/verify.py'), '--catalog', str(cat), '--run', str(out)] +
                         (['--synthetic'] if synthetic else []))
    verifier_wall = time.monotonic() - start
    check_raw = log.read_text()
    check_peak = int(re.search(r'Maximum resident set size \(kbytes\): (\d+)', check_raw)[1]) * 1024
    table = json.loads(standalone.stdout)
    if max(peak, check_peak) > 128 * 1024 ** 2:
        raise AssertionError('RSS exceeds agreed envelope')
    return {'target': target, 'synthetic': synthetic, 'producer_wall_seconds': producer_wall,
            'standalone_verifier_wall_seconds': verifier_wall,
            'combined_wall_seconds': producer_wall + verifier_wall,
            'producer_cpu_seconds': user + system, 'producer_peak_rss_bytes': peak,
            'verifier_peak_rss_bytes': check_peak, 'table': table,
            'producer_stdout': result.stdout.decode(), 'producer_time_v': raw,
            'verifier_time_v': check_raw,
            'command': args, 'timeout_seconds': 600}


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument('--full', action='store_true')
    p.add_argument('--scale-only', action='store_true', help='inherit successful unchanged local matrix')
    p.add_argument('--result', type=Path, required=True)
    p.add_argument('--retain', type=Path)
    args = p.parse_args()
    v.require(not args.scale_only or args.full, 'scale-only requires full scale plan')
    v.require(not args.result.exists(), 'qualification receipt exists')
    if args.retain:
        v.require(not args.retain.exists(), 'replay root exists')
    started = time.monotonic()
    original = (ROOT / 'data/prime.tsv').read_bytes()
    canonical = v.file_hash(ROOT / 'data/b209933.txt')
    metrics = []
    with tempfile.TemporaryDirectory(prefix='a209933-qual-') as name:
        tmp = Path(name)
        if not args.scale_only:
            with contextlib.redirect_stdout(io.StringIO()):
                local_matrix(tmp, original)
        if args.full:
            cat = fixture(tmp, original)
            for i in range(3):
                out = (args.retain if args.retain and i == 0 else tmp / 'timed')
                row = measured(tmp, cat, 101, False, out)
                observation('T101-bytes-' + str(i), row['table']['bytes'], 2708884)
                metrics.append(row)
                if out != args.retain:
                    shutil.rmtree(out)
            cat.write_bytes(synthetic_catalog(original))
            out = tmp / 'maximum'
            row = measured(tmp, cat, 134, True, out)
            observation('H134-bytes', row['table']['bytes'], 159374652)
            metrics.append(row)
            # Max and max-1 rows exercised in all11 multiplier paths in H134.
            observation('maximum-row-length', len(s.term(v.MAX_T, 24)), 8177208)
            observation('maximum-minus-one-row-length', len(s.term(v.MAX_T - 1, 24)), 8177207)
            rejects('first-rejected-exponent', lambda: s.term(v.MAX_T + 1, 24))
    observation('canonical-protected', v.file_hash(ROOT / 'data/b209933.txt'), canonical)
    report = {'status': 'PASS', 'scope': 'Finite local qualification; no official run or admitted new canonical term',
              'source_sha256': v.file_hash(ROOT / 'src/a209933.py'),
              'verifier_sha256': v.file_hash(ROOT / 'check/verify.py'),
              'harness_sha256': v.file_hash(__file__), 'catalog_sha256': hashlib.sha256(original).hexdigest(),
              'runtime': v.runtime(), 'observations': OBS, 'actual_observation_count': len(OBS),
              'metrics': metrics, 'wall_seconds': time.monotonic() - started,
              'scratch_removed': True, 'retained_replay': str(args.retain) if args.retain else None}
    with args.result.open('x', encoding='utf-8') as f:
        json.dump(report, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({'status': 'PASS', 'observations': len(OBS), 'wall_seconds': report['wall_seconds']}))


if __name__ == '__main__':
    main()
