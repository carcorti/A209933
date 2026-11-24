#!/usr/bin/env python3
"""A209933 decimal materialization from an externally admitted catalog.

Author: Carlo Corti. Standard-library Python; no runtime primality assertion.
The theorem and complete published catalog are premises, not locally recomputed.
An output root is exclusively created. Only a final completed receipt admits it.
Interruptions require regeneration in a NEW root; no intra-row resume is claimed.
"""
import datetime
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time

_CHECKER = Path(__file__).resolve().parents[1] / 'check' / 'verify.py'
_spec = importlib.util.spec_from_file_location('a209933_verifier', _CHECKER)
v = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v)


def term(t, coefficient):
    """Closed ASCII templates; independently checked by decimal multiplication."""
    v.require(type(t) is int and 2 <= t <= v.MAX_T and coefficient in v.COEFFICIENTS,
              'template outside envelope')
    if coefficient <= 9:
        return bytes((48 + coefficient,)) * t
    if coefficient == 12:
        return b'1' + b'3' * (t - 1) + b'2'
    return b'2' + b'6' * (t - 1) + b'4'


def rows(cat, target):
    exponents = v.admitted(cat, target)
    # Independent literal baseline: not the verifier's set/sort construction.
    baseline = (1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 15, 22, 24, 33, 44,
                48, 55, 66, 77, 88, 99, 132, 264)
    for index, n in enumerate(baseline[:target], 1):
        yield index, str(n).encode('ascii')
    index = 24
    for t, _ in exponents[1:]:
        for coefficient in v.COEFFICIENTS:
            index += 1
            if index > target:
                return
            yield index, term(t, coefficient)


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def interrupted(signum, frame):
    raise InterruptedError('interrupted by signal ' + str(signum))


def materialize(cat_path, target, out, synthetic=False):
    started = time.monotonic()
    cat = v.catalog(cat_path, synthetic)
    v.admitted(cat, target)  # All admission checks precede directory mutation.
    source_hash = v.file_hash(__file__)
    verifier_hash = v.file_hash(_CHECKER)
    runtime = v.runtime()
    out = Path(out)
    out.mkdir(mode=0o700, parents=False, exist_ok=False)
    sync_directory(out.parent)
    receipt_path = out / 'run.json'
    pending = out / '.pending'
    try:
        table_path = out / 'b209933.txt'
        print(json.dumps({'event': 'START', 'target': target, 'synthetic': synthetic}), flush=True)
        with table_path.open('xb') as stream:
            for index, value in rows(cat, target):
                stream.write(str(index).encode('ascii') + b' ')
                stream.write(value)
                stream.write(b'\n')
            stream.write(b'\n')
            stream.flush()
            os.fsync(stream.fileno())
        # Drop the last generated value before independent verification overlaps.
        del value
        result = v.verify_table(table_path, cat, target)
        v.require(source_hash == v.file_hash(__file__) and verifier_hash == v.file_hash(_CHECKER),
                  'candidate changed during materialization')
        v.require(cat['sha256'] == v.file_hash(cat_path), 'catalog changed during materialization')
        receipt = {'schema': 'a209933-run-1', 'status': 'COMPLETE',
                   'mode': 'SYNTHETIC_CAPACITY_ONLY' if synthetic else 'ATTRIBUTED_DERIVATION',
                   'target': target, 'catalog_sha256': cat['sha256'],
                   'source_sha256': source_hash, 'verifier_sha256': verifier_hash,
                   'runtime': runtime, 'table': result,
                   'elapsed_seconds': time.monotonic() - started,
                   'completed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
        # Fsync before publishing the completion name. A hard link publishes
        # without replacement; this Linux/private-directory contract is explicit.
        with pending.open('x', encoding='ascii', newline='\n') as stream:
            json.dump(receipt, stream, indent=2, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.link(pending, receipt_path)
        pending.unlink()
        sync_directory(out)
        print(json.dumps({'event': 'COMPLETE', **result}), flush=True)
        return result
    except BaseException:
        # Handled errors/signals invalidate even a fully written receipt.
        # SIGKILL/power loss before commit: absent/torn receipt or a fully valid
        # table+receipt; verification is always required before admission.
        try:
            receipt_path.unlink(missing_ok=True)
            sync_directory(out)
        except OSError:
            pass  # Primary failure remains visible; verification still mandatory.
        raise


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    p = v.parser(__doc__)
    p.add_argument('--catalog', required=True, type=Path)
    p.add_argument('--through', required=True, help='last index, 1..134; first gap fails closed')
    p.add_argument('--out', required=True, type=Path, help='NEW directory in an existing parent')
    p.add_argument('--synthetic', action='store_true', help='capacity fixtures; never exact sequence evidence')
    try:
        v.reject_duplicate_flags(argv)
        args = p.parse_args(argv)
        target = v.natural(args.through, v.MAX_ROWS)
        signal.signal(signal.SIGTERM, interrupted)
        materialize(args.catalog, target, args.out, args.synthetic)
        return 0
    except (OSError, ValueError, UnicodeError, TypeError, KeyError, KeyboardInterrupt) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
