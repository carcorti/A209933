#!/usr/bin/env python3
"""Local distribution checks and source restoration for Carlo Corti's A209933.

Packaging driver added after the scientific runs. It delegates numerical
work to the unchanged retained programs; it is not a new scientific oracle.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def safe(name):
    p = PurePosixPath(name)
    require(not p.is_absolute() and name == p.as_posix() and
            all(c not in ('', '.', '..') for c in p.parts), 'unsafe path')
    return p


def inventory():
    expected = {}
    for line in (ROOT / 'checks.sha256').read_text('ascii').splitlines():
        h, name = line.split('  ', 1)
        safe(name)
        require(len(h) == 64 and set(h) <= set('0123456789abcdef') and
                name not in expected and name != 'checks.sha256', 'invalid manifest')
        expected[name] = h
    require(bool(expected), 'empty manifest')
    actual = set()
    for p in ROOT.rglob('*'):
        rel = p.relative_to(ROOT)
        # Only root clone metadata is outside the payload contract.
        if rel.parts[0] == '.git':
            continue
        require(not p.is_symlink(), 'payload symlink: ' + str(rel))
        if p.is_file():
            actual.add(rel.as_posix())
        else:
            require(p.is_dir() and any(x.startswith(rel.as_posix() + '/')
                                     for x in expected), 'unexpected directory: ' + str(rel))
    require(actual == set(expected) | {'checks.sha256'}, 'changed inventory')
    for name, h in expected.items():
        require(digest((ROOT / name).read_bytes()) == h, 'changed file: ' + name)
    return len(actual)


def lean_sources():
    rows = json.loads((ROOT / 'formal/map.json').read_text())['members']
    require(len(rows) == 13, 'Lean input count')
    names, paths, data = set(), set(), {}
    with tarfile.open(ROOT / 'formal/lean.tgz', 'r:gz') as archive:
        members = archive.getmembers()
        require(len(members) == len(rows), 'Lean archive member count')
        by_name = {m.name: m for m in members}
        require(len(by_name) == len(members), 'duplicate archive member')
        for row in rows:
            name, path = row['member'], row['path']
            safe(name)
            safe(path)
            require(name not in names and path not in paths, 'duplicate restoration map')
            names.add(name)
            paths.add(path)
            m = by_name[name]
            require(row['mode'] == '0644' and m.isfile() and m.size == row['bytes'] and
                    format(m.mode, '04o') == row['mode'], 'archive type/size/mode')
            raw = archive.extractfile(m).read()
            require(digest(raw) == row['sha256'], 'Lean source identity')
            data[path] = raw
        require(set(by_name) == names, 'unexpected archive member')
    return data


def provenance(lean):
    originals = {}
    for row in json.loads((ROOT / 'outputs/origin.json').read_text())['files']:
        raw = (ROOT / row['public']).read_bytes()
        require(len(raw) == row['bytes'] and digest(raw) == row['sha256'], 'copy identity')
        originals[row['workspace']] = raw
    originals.update({'formal/' + k: v for k, v in lean.items()})
    for receipt in ['formal', 'relate']:
        record = json.loads((ROOT / ('outputs/' + receipt + '.json')).read_text())
        for row in record['sources'] + record['logs']:
            # The old explanatory README is superseded by the public README;
            # it is not a proof input and is not made a dependency just to hash it.
            if row['path'] == 'formal/README.md':
                continue
            raw = originals[row['path']]
            require(len(raw) == row['bytes'] and digest(raw) == row['sha256'],
                    'historical proof source/log identity: ' + row['path'])
    run = json.loads((ROOT / 'outputs/run.json').read_text())
    for key, path in [('source_sha256', 'src/a209933.py'),
                      ('verifier_sha256', 'check/verify.py'),
                      ('catalog_sha256', 'data/prime.tsv')]:
        require(digest((ROOT / path).read_bytes()) == run[key], 'historical input identity')


def execute(args, cwd=ROOT, expected=0):
    r = subprocess.run(args, cwd=cwd, stdin=subprocess.DEVNULL,
                       capture_output=True, timeout=180)
    require(r.returncode == expected,
            'command failed: ' + repr(args) + '\n' + r.stderr.decode(errors='replace'))
    return r.stdout


def python(path, *args, cwd=ROOT, expected=0):
    return execute([sys.executable, '-B', str(path), *map(str, args)], cwd, expected)


def generate(tmp, target):
    out = tmp / 'run'
    python(ROOT / 'src/a209933.py', '--catalog', ROOT / 'data/prime.tsv',
           '--through', target, '--out', out)
    checked = json.loads(python(ROOT / 'check/verify.py', '--catalog',
                               ROOT / 'data/prime.tsv', '--run', out))
    require(checked['rows'] == target, 'generated row count')
    return out


def bounded(tmp):
    audit = json.loads(python(ROOT / 'check/audit.py'))
    old = json.loads((ROOT / 'outputs/check46.json').read_text())
    for key in ['status', 'canonical_sha256', 'local_primality_certificates',
                'finite_exclusion', 'canonical']:
        require(audit[key] == old[key], 'finite audit changed: ' + key)
    language = json.loads(python(ROOT / 'check/language.py'))
    require(language['status'] == 'PASS' and len(language['rows']) == 30, 'language certificate')
    out = generate(tmp, 46)
    require((out / 'b209933.txt').read_bytes() == (ROOT / 'data/b209933.txt').read_bytes(),
            'canonical regeneration mismatch')
    python(ROOT / 'src/a209933.py', '--catalog', ROOT / 'data/prime.tsv',
           '--through', 46, '--out', out, expected=2)
    rejected = tmp / 'blocked'
    python(ROOT / 'src/a209933.py', '--catalog', ROOT / 'data/prime.tsv',
           '--through', 112, '--out', rejected, expected=2)
    require(not rejected.exists(), 'PRP gate mutated output')
    return {'finite_rows': 46, 'gcd_classes': 30,
            'canonical_regeneration': 'byte-identical', 'existing_root_and_PRP_controls': 'PASS'}


def auxiliary(tmp):
    out = generate(tmp, 101)
    receipt = json.loads((ROOT / 'outputs/run.json').read_text())
    raw = (out / 'b209933.txt').read_bytes()
    require(len(raw) == receipt['table']['bytes'] and
            digest(raw) == receipt['table']['sha256'], '101-row historical identity')
    # Historical audit expects the longer table at data/b209933.txt. Restore
    # that layout exclusively in scratch; never replace the adopted public file.
    stage = tmp / 'audit'
    for name in ['data', 'outputs']:
        (stage / name).mkdir(parents=True)
    shutil.copy2(out / 'b209933.txt', stage / 'data/b209933.txt')
    shutil.copy2(ROOT / 'outputs/aud101.py', stage / 'outputs/aud101.py')
    result = json.loads(python(stage / 'outputs/aud101.py', cwd=stage))
    old = json.loads((ROOT / 'outputs/audit.json').read_text())
    for key in ['status', 'canonical_sha256', 'local_primality_certificates',
                'finite_exclusion', 'full_table']:
        require(result[key] == old[key], '101-row audit mismatch: ' + key)
    return {'auxiliary_rows': 101, 'divisor_occurrences': result['full_table']['direct_divisors_checked'],
            'scope': 'Rows beyond 46 retain external primality and catalog premises'}


def restore(destination, data):
    target = destination.absolute()
    require(not target.resolve().is_relative_to(ROOT), 'restore outside the payload')
    require(target.parent.is_dir() and not target.exists() and not target.is_symlink(),
            'restore requires a NEW directory in an existing parent')
    target.mkdir(mode=0o700, exist_ok=False)
    for name, raw in data.items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)
        path.chmod(0o644)
        require(path.read_bytes() == raw, 'restored bytes differ')
    return {'restored_members': len(data), 'destination': str(target), 'build_executed': False}


def main():
    p = argparse.ArgumentParser(__doc__, allow_abbrev=False)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--aux101', action='store_true')
    mode.add_argument('--dev', action='store_true')
    mode.add_argument('--tex', action='store_true')
    mode.add_argument('--lean-source', type=Path)
    args = p.parse_args()
    count = inventory()
    lean = lean_sources()
    provenance(lean)
    if args.lean_source is not None:
        result = restore(args.lean_source, lean)
    else:
        with tempfile.TemporaryDirectory(prefix='a209933-check-') as name:
            tmp = Path(name)
            if args.aux101:
                result = auxiliary(tmp)
            elif args.dev:
                # The unchanged development harness was written before the
                # adopted-prefix consolidation and expects the 24-row baseline.
                # Recreate that historical layout, with current source bytes,
                # exclusively in scratch instead of changing scientific code.
                stage = tmp / 'dev'
                for name in ['src', 'check', 'data']:
                    (stage / name).mkdir(parents=True)
                for name in ['src/a209933.py', 'check/verify.py',
                             'check/qualify.py', 'check/supplement.py', 'data/prime.tsv']:
                    shutil.copy2(ROOT / name, stage / name)
                shutil.copy2(ROOT / 'outputs/b24.txt', stage / 'data/b209933.txt')
                python(stage / 'check/qualify.py', '--result', tmp / 'dev.json', cwd=stage)
                supplement = json.loads(python(stage / 'check/supplement.py', cwd=stage))
                require(supplement['status'] == 'PASS', 'development supplement')
                result = {'qualification': 'PASS', 'transaction_supplement': 'PASS',
                          'maximum_capacity_run': 'not executed'}
            elif args.tex:
                for _ in range(3):
                    execute(['pdflatex', '-interaction=nonstopmode',
                             '-halt-on-error', '-output-directory=' + str(tmp),
                             str(ROOT / 'paper/A209933.tex')], cwd=tmp)
                log = (tmp / 'A209933.log').read_text(errors='replace')
                require(re.search(r'(?im)^(?:!|[^\n]*\bwarning:|pdfTeX warning\b|Overfull\b|Underfull\b|Missing character:)', log) is None,
                        'TeX error, warning or box diagnostic')
                require((tmp / 'A209933.pdf').is_file(), 'missing rebuilt PDF')
                result = {'tex': 'PASS', 'PDF_created': True, 'PDF_output': 'temporary only'}
            else:
                result = bounded(tmp)
    print(json.dumps({'status': 'PASS', 'payload_files': count, **result}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, tarfile.TarError, subprocess.SubprocessError) as error:
        print('ERROR: ' + str(error), file=sys.stderr)
        sys.exit(1)
