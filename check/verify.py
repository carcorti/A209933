#!/usr/bin/env python3
"""Independent decimal verification for A209933. Author: Carlo Corti.

Arithmetic independence: grade-school multiplication, not producer templates.
Shared premises: structural theorem and externally admitted complete prime catalog.
No large integer conversion, primality proof or runtime network operation.
"""
import argparse
import datetime
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import sys

MAX_T = 8177207
MAX_ROWS = 134
MAX_BYTES = 159374652
MAX_LINE = MAX_T + 8
MAX_META = 65536
COEFFICIENTS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 24)
SMALL = (1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 15, 24, 48)
HEADER = 'rank\texponent\tstatus\tattribution\tsource'
META_KEYS = {'schema', 'mode', 'audited', 'complete_through', 'coverage_source'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def natural(text, maximum):
    require(isinstance(text, str) and len(text) <= len(str(maximum)) and
            re.fullmatch(r'[1-9][0-9]*', text) is not None,
            'expected canonical positive decimal')
    value = int(text)
    require(value <= maximum, 'numeric bound exceeded')
    return value


def bounded_bytes(path, maximum=MAX_META):
    with Path(path).open('rb') as stream:
        raw = stream.read(maximum + 1)
    require(len(raw) <= maximum, 'input exceeds byte limit')
    return raw


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def runtime():
    """Runtime identity metadata, not a bundled runtime or certificate."""
    executable = Path(sys.executable).resolve()
    return {'implementation': platform.python_implementation(),
            'version': sys.version, 'executable_sha256': file_hash(executable),
            'platform': platform.platform(), 'byteorder': sys.byteorder,
            'stdlib': 'installed standard library; not independently hashed'}


def catalog(path, synthetic=False):
    raw = bounded_bytes(path)
    text = raw.decode('ascii')
    require(text.endswith('\n') and '\r' not in text, 'catalog requires ASCII LF')
    require(all(c in '\t\n' or 32 <= ord(c) < 127 for c in text),
            'catalog requires printable ASCII, tabs and LF')
    lines = text[:-1].split('\n')
    require(len(lines) >= 7 and lines[5] == HEADER, 'catalog header/schema mismatch')
    meta = {}
    for line in lines[:5]:
        require(line.startswith('# ') and '=' in line, 'catalog metadata grammar')
        key, value = line[2:].split('=', 1)
        require(key not in meta and value != '', 'duplicate/empty catalog metadata')
        require(all(32 <= ord(c) < 127 for c in value), 'catalog metadata must be printable ASCII')
        meta[key] = value
    require(set(meta) == META_KEYS and meta['schema'] == 'a209933-primes-1',
            'unknown catalog schema/keys')
    require(meta['mode'] == ('SYNTHETIC' if synthetic else 'PUBLISHED'),
            'catalog mode does not match explicit synthetic flag')
    require(re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', meta['audited']) is not None,
            'invalid audit date')
    datetime.date.fromisoformat(meta['audited'])
    coverage = natural(meta['complete_through'], MAX_T)
    require(meta['coverage_source'].startswith(('https://', 'synthetic:')),
            'coverage provenance required')
    if not synthetic:
        require(meta['coverage_source'].startswith('https://'), 'published coverage source required')
    rows = []
    last = 0
    require(1 <= len(lines[6:]) <= 11, 'catalog entry count exceeds envelope')
    for rank, line in enumerate(lines[6:], 1):
        parts = line.split('\t')
        require(len(parts) == 5 and all(parts), 'catalog row grammar')
        number = natural(parts[0], 11)
        t = natural(parts[1], MAX_T)
        status, attribution, source = parts[2:]
        require(number == rank, 'catalog ranks must be contiguous')
        require((rank == 1 and t == 2) or
                (rank > 1 and t >= last + 2 and t % 2 == 1 and t != 3),
                'catalog exponent order/parity invalid')
        require(status in ({'SYNTHETIC'} if synthetic else {'PROVEN', 'PRP'}),
                'inadmissible catalog status')
        require(source.startswith(('synthetic:',) if synthetic else ('https://',)),
                'catalog source required')
        require(all(32 <= ord(c) < 127 for c in attribution + source),
                'catalog fields must be printable ASCII')
        rows.append((t, status))
        last = t
    require(coverage >= 2, 'catalog must cover baseline R2')
    return {'meta': meta, 'rows': rows, 'coverage': coverage,
            'sha256': hashlib.sha256(raw).hexdigest()}


def admitted(cat, target):
    require(type(target) is int and 1 <= target <= MAX_ROWS, 'target outside row envelope')
    # 13 small numbers followed by eleven elements per admitted repunit block.
    needed = max(1, (max(0, target - 13) + 10) // 11)
    require(needed <= len(cat['rows']), 'target exceeds catalog')
    selected = cat['rows'][:needed]
    require(all(status in ('PROVEN', 'SYNTHETIC') for _, status in selected),
            'first unresolved PRP blocks indexed continuation')
    require(selected[-1][0] <= cat['coverage'], 'catalog completeness gap before target')
    require(output_size(selected, target) <= MAX_BYTES, 'aggregate output exceeds byte envelope')
    return selected


def output_size(exponents, target):
    """Exact ASCII row-size arithmetic, including the final empty record."""
    initial = sorted(set(SMALL) | {11 * m for m in COEFFICIENTS})
    size = 1  # Terminal empty record.
    for index, n in enumerate(initial[:target], 1):
        size += len(str(index)) + len(str(n)) + 2
    index = 24
    for t, _ in exponents[1:]:
        for coefficient in COEFFICIENTS:
            index += 1
            if index > target:
                return size
            size += len(str(index)) + t + (coefficient > 9) + 2
    return size


def multiply_repunit(t, coefficient):
    """Right-to-left multiplication by a small integer, O(t) bytes and work."""
    require(type(t) is int and 2 <= t <= MAX_T and coefficient in COEFFICIENTS,
            'multiplication outside envelope')
    digits = bytearray(t + 1)
    carry = 0
    for pos in range(t, 0, -1):
        value = coefficient + carry  # repunit source digit is exactly 1
        digits[pos] = 48 + value % 10
        carry = value // 10
    if carry:
        digits[0] = 48 + carry
        return digits
    del digits[0]
    return digits


def expected_rows(cat, target):
    exponents = admitted(cat, target)
    # Deliberately reconstruct the exceptional first block using small integers.
    initial = sorted(set(SMALL) | {11 * m for m in COEFFICIENTS})
    for index, n in enumerate(initial[:target], 1):
        yield index, str(n).encode('ascii')
    index = 24
    for t, _ in exponents[1:]:
        for coefficient in COEFFICIENTS:
            index += 1
            if index > target:
                return
            yield index, multiply_repunit(t, coefficient)


def verify_table(path, cat, target):
    """Bounded line reads, independent arithmetic, index/order/framing and hash."""
    h = hashlib.sha256()
    total = 0
    previous = b''
    with Path(path).open('rb') as stream:
        for index, expected in expected_rows(cat, target):
            line = stream.readline(MAX_LINE + 1)
            require(len(line) <= MAX_LINE and line.endswith(b'\n'), 'oversized/truncated row')
            h.update(line)
            total += len(line)
            prefix = str(index).encode('ascii') + b' '
            require(line.startswith(prefix), 'wrong/missing/duplicate index')
            value = line[len(prefix):-1]
            require(value == expected, 'decimal multiplication mismatch at index ' + str(index))
            require((len(value), value) > (len(previous), previous), 'table not increasing')
            previous = value
            del expected, line
        require(stream.read(2) == b'\n', 'exact terminal empty record required; no trailing bytes')
    h.update(b'\n')
    return {'rows': target, 'bytes': total + 1, 'sha256': h.hexdigest()}


def unique(pairs):
    obj = {}
    for k, v in pairs:
        require(k not in obj, 'duplicate JSON key')
        obj[k] = v
    return obj


def nonfinite(value):
    raise ValueError('nonfinite JSON number: ' + value)


def verify_run(root, cat_path, synthetic=False):
    root = Path(root)
    require(not root.is_symlink() and root.is_dir(), 'regular run directory required')
    require({p.name for p in root.iterdir()} == {'b209933.txt', 'run.json'},
            'run must contain exactly table and completed receipt')
    for name in ('b209933.txt', 'run.json'):
        require(not (root / name).is_symlink() and (root / name).is_file(), 'regular run files required')
    receipt = json.loads(bounded_bytes(root / 'run.json'), object_pairs_hook=unique,
                         parse_constant=nonfinite)
    keys = {'schema', 'status', 'mode', 'target', 'catalog_sha256', 'source_sha256',
            'verifier_sha256', 'runtime', 'table', 'elapsed_seconds', 'completed_utc'}
    require(type(receipt) is dict and set(receipt) == keys and
            receipt['schema'] == 'a209933-run-1' and receipt['status'] == 'COMPLETE',
            'invalid/incomplete receipt')
    require(type(receipt['elapsed_seconds']) in (int, float) and
            math.isfinite(receipt['elapsed_seconds']) and receipt['elapsed_seconds'] >= 0,
            'invalid elapsed time')
    require(isinstance(receipt['completed_utc'], str), 'completion timestamp required')
    stamp = datetime.datetime.fromisoformat(receipt['completed_utc'])
    require(stamp.utcoffset() == datetime.timedelta(0), 'UTC completion timestamp required')
    require(type(receipt['table']) is dict and
            set(receipt['table']) == {'rows', 'bytes', 'sha256'} and
            all(type(receipt['table'][k]) is int for k in ('rows', 'bytes')),
            'invalid table metadata')
    require(receipt['mode'] == ('SYNTHETIC_CAPACITY_ONLY' if synthetic else 'ATTRIBUTED_DERIVATION'),
            'run mode mismatch')
    cat = catalog(cat_path, synthetic)
    require(receipt['catalog_sha256'] == cat['sha256'], 'catalog identity mismatch')
    require(receipt['verifier_sha256'] == file_hash(__file__), 'verifier identity mismatch')
    source = Path(__file__).resolve().parents[1] / 'src' / 'a209933.py'
    require(receipt['source_sha256'] == file_hash(source), 'source identity mismatch')
    require(receipt['runtime'] == runtime(), 'runtime differs from producing runtime')
    result = verify_table(root / 'b209933.txt', cat, receipt['target'])
    require(receipt['table'] == result, 'table receipt mismatch')
    return result


def parser(description):
    return argparse.ArgumentParser(description=description, allow_abbrev=False)


def reject_duplicate_flags(argv):
    flags = [arg.split('=', 1)[0] for arg in argv if arg.startswith('--')]
    require(len(flags) == len(set(flags)), 'duplicate CLI option')


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    p = parser(__doc__)
    p.add_argument('--catalog', required=True, type=Path)
    p.add_argument('--run', required=True, type=Path)
    p.add_argument('--synthetic', action='store_true', help='accept synthetic capacity fixtures only')
    try:
        reject_duplicate_flags(argv)
        args = p.parse_args(argv)
        result = verify_run(args.run, args.catalog, args.synthetic)
        print(json.dumps({'status': 'PASS', 'mode': 'SYNTHETIC' if args.synthetic else 'DERIVATION', **result}))
        return 0
    except (OSError, ValueError, UnicodeError, TypeError, KeyError, OverflowError, RecursionError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
