# A209933: decimal divisor digits and prime repunits

Carlo Corti, November 2026. Sources prepared 23 November 2026;
published on the repository's default branch on 24 November 2026.
Software version: `v1.0`, released 24 November 2026;
provisional manuscript: `paper/A209933_v4.tex`.
Repository: <https://github.com/carcorti/A209933>.
Release: <https://github.com/carcorti/A209933/releases/tag/v1.0>.
The DOI `10.5281/zenodo.xxxxxxxx` remains a literal placeholder until separate
post-publication finalization with the verified designated Zenodo locator.
The supplied MIT license is preserved.

A209933 consists of positive integers divisible by every digit of every positive
divisor. A zero digit fails the condition. Write `R_t = (10^t - 1)/9` and
`B = {1,2,3,4,5,6,7,8,9,12,24}`. The all-natural classification is
`B union {15,48} union {m*R_t : m in B, R_t prime}`. The Lean project also proves
that every divisor satisfies this predicate exactly when the number satisfies it
and differs from 48: the set for A182183 is the set for A209933 with 48 removed.
Neither theorem asserts infinitude or proves a particular large repunit prime.

The adopted canonical result is **indices 1 through 46**, ending at
`a(46) = 266666666666666666666664 = 24*R_23`. An independent finite enumeration
finds exactly these 46 solutions below `10^24`; it proves primality of R19 and
R23 by local full-order Lucas certificates. The original 24-term prefix ends at
264. The manuscript explains the historical attribution and the 22 added rows.

An auxiliary derivation reaches index 101 under the published primality and
catalog-coverage premises in `data/prime.tsv`. It is separate from the adopted
46-term b-file. The last three catalog entries are PRPs and block further exact
indexed continuation in the supplied materializer. The catalog reader validates
syntax and declared status, not the truth of those external scientific premises.

## Files and evidence

| Path | Role |
| --- | --- |
| `paper/A209933_v4.tex` | Current monolithic English manuscript, inline bibliography, no external scientific assets. Version 4 changes only data availability from version 3. |
| `src/a209933.py` | Original reviewed decimal materializer; standard-library Python. |
| `check/verify.py` | Original digit-by-digit multiplication verifier. Arithmetic differs from producer templates; catalog and block ordering are shared premises. |
| `check/audit.py` | Original independent finite enumeration below `10^24`, local Lucas proofs and exact adopted-prefix comparison. Imports neither materializer, verifier nor catalog. |
| `check/language.py` | Original finite initialization/transition diagnostic for all 30 gcd classes; complements the Lean proof. |
| `check/qualify.py`, `check/supplement.py` | Original bounded implementation and transaction checks; maximum capacity is a separate optional mode, not part of the commands below. |
| `check/check.py` | New packaging driver: exact inventory, archive identities, safe restoration and delegation to unchanged scientific programs. |
| `data/b209933.txt` | Byte-identical adopted b-file: consecutive decimal `index value` pairs, ASCII LF, exactly one final blank record. |
| `data/prime.tsv` | Original attributed external catalog input. Five `# key=value` metadata lines, then rank, exponent, status, attribution and source columns separated by tabs. |
| `formal/lean.tgz`, `formal/map.json` | All 10 original Lean source files and 3 original build/pin inputs. Short archive aliases restore the exact original project without changing module names or proof bytes. |
| `outputs/b24.txt` | Historical 24-term baseline required by the finite audit, with the same b-file framing. |
| `outputs/check46.json` | Original complete finite audit result, including Lucas certificates and exclusion witnesses. |
| `outputs/aud101.py`, `outputs/audit.json` | Original exact-integer audit of the auxiliary 101-row table and its result: 643 divisor occurrences. Larger prime premises remain external. |
| `outputs/run.json`, `outputs/time.json` | Original completed 101-row receipt and measured final-parser qualification record. Timing scope and raw resource telemetry are retained, including historical paths. |
| `outputs/formal.json`, `outputs/relate.json` | Original formal statements, source hashes, successful builds, axiom audits and replay scope. |
| `outputs/*.log` | Essential original formal build, axiom and replay logs, including the failed incompatible Lean4Lean attempt. |
| `outputs/origin.json` | Exact original-to-public copy map, byte sizes and SHA-256 identities. Historical paths in immutable records are interpreted through this map. |
| `checks.sha256`, `CITATION.cff`, `LICENSE` | Frozen inventory, provisional citation metadata and existing author license. |

Execution records describe their original dates. In particular, `formal.json`
predates the later deletion-identity proof and cache removal: its then-current
exclusions and cache-retention note are historical. The current proof scope and
cache state are described here. Absolute workstation and scratch paths, old
framework references and old harness paths in immutable records are provenance,
not required public inputs or commands to execute. The original formal-project
README is superseded by this README and is not a mathematical proof input.

Ordinary filenames have short stems. TeX and Python retain their established
descriptive filenames. The unavoidable original Lake filenames and longer Lean
module filenames are restored only into a new scratch directory from the archive.
`formal/map.json` gives every member's alias, restored path, size, mode and hash.
The archive is 9,628 bytes and restores 40,498 bytes in 13 regular files.
No third-party library source is bundled.

The 2,708,884-byte auxiliary table is regenerated rather than duplicated. Caches,
compiled executables, proof exports, old manuscripts, private review conversations,
triage planning and superseded diagnostics are excluded. External literature and
large external primality certificates are located in the manuscript bibliography
and catalog, not redistributed. The original auxiliary table remains local; this
public route does not depend on it. No separate a-file adds unique evidence beyond
the catalog, executable certificates and full audit records supplied here; no
sparse extension beyond an unresolved adopted index is asserted.

## Bounded checks from a fresh root

Run from this directory, with **CPython 3.12.3** (the recorded version) or a
compatible Python **3.10 or later**, on Linux. No third-party Python packages or
network access are needed for these checks. Alternative versions are source-based
reproductions; they are not the historical runtime. The implementation uses Linux
directory fsync and hard-link publication. Historical runtime hashes are evidence;
new runs create their own receipts and are verified with that same runtime.

```sh
python3 -B check/check.py
```

This fails on changed, missing or unexpected payload files (only root `.git`
metadata is exempt), checks every Lean archive member and original proof identity,
repeats the independent finite audit and the quotient-language diagnostic,
regenerates all 46 adopted rows byte for byte, and checks rejection of an existing
output root and continuation across the first PRP. Expected result: `status: PASS`,
`finite_rows: 46`, `gcd_classes: 30`. Temporary outputs are removed automatically.
The finite audit enforces its original 60-second limit. A failure exits nonzero;
it neither edits canonical inputs nor retries or advances a campaign.

To regenerate the complete historical auxiliary scope and repeat its original
exact-integer audit:

```sh
python3 -B check/check.py --aux101
```

Expected result: 101 rows, 2,708,884 regenerated bytes with SHA-256
`2768468ad0f9a808e0e82bf43f6ecd16009e72c37e50d5dfcae038d39aa72fbc`, and
643 divisor occurrences. The historical audit is staged with its original input
layout in scratch. The public 46-row file remains the canonical result.
Expect seconds to tens of seconds depending on hardware; scratch usage is a few
MB. This is a reproduction of already recorded results, not new primality work.

To repeat the retained bounded implementation checks on Linux:

```sh
python3 -B check/check.py --dev
```

This repeats `qualify.py` without `--full`, plus `supplement.py`. It includes
temporary smaller prefixes of the recorded 101-row derivation and injected failure
controls. The original development harness expects the then-current 24-term
baseline: the driver restores that baseline and the unchanged programs in scratch,
without changing the adopted public file. It does not run the 159,374,652-byte
synthetic maximum-capacity test.
That maximum is an implementation envelope, not an exact prime-repunit claim.
The historical lexical-parser delta in `outputs/time.json` is a retained record;
its old-versus-new remediation harness is not advertised as a public replay.

For direct generation into a **new** directory in an existing parent:

```sh
python3 -B src/a209933.py --catalog data/prime.tsv --through 46 --out /tmp/a209933-run
python3 -B check/verify.py --catalog data/prime.tsv --run /tmp/a209933-run
cmp data/b209933.txt /tmp/a209933-run/b209933.txt
```

An interrupted output requires a new directory, with no automatic resume. Never
replace historical receipts or attach them to a fresh run. The original receipt
is checked by input/table identities; its old executable/platform is not required
for the public reproduction route.

## Lean source restoration and full proof reproduction

```sh
python3 -B check/check.py --lean-source /tmp/a209933-lean
cd /tmp/a209933-lean
sha256sum lake-manifest.json > /tmp/a209933-pins
lake exe cache get
sha256sum -c /tmp/a209933-pins
lake build A209933 A209933.Relations
```

The destination must not exist and must be outside the public payload. Restoration
validates every file and refuses overwriting. Install Elan/Lake for
`leanprover/lean4:v4.36.0`. Mathlib is pinned to
`fc4f59e577feb1a4956671bc04ac18aaaf8cd842`; all nine dependency revisions are in
the restored `lake-manifest.json`. Do not run `lake update` or float the pins.
Network acquisition and substantial regenerated disk space are needed; the earlier
expanded cache occupied about 1.4 GB. Allow ample RAM: a reviewer reported failure
under a roughly 3 GB container limit. Full builds and export replay have separate
resource costs and are not included in the bounded Python check.

After building, a same-kernel replay can be run with new temporary exports:

```sh
set -eu
proof_export=$(mktemp /tmp/a209933-proof.XXXXXX)
lake env leanexport A209933 -- A209933.classification A209933.repunit_closed > "$proof_export"
lake env leanchecker --from-export "$proof_export"
rm -- "$proof_export"
relation_export=$(mktemp /tmp/a209933-rel.XXXXXX)
lake env leanexport A209933.Relations -- A209933.divisor_closed_iff A209933.not_divisor_closed_fortyeight > "$relation_export"
lake env leanchecker --from-export "$relation_export"
rm -- "$relation_export"
```

The retained successful builds/replays used Lean's own kernel in an empty
environment. Axioms are `propext`, `Classical.choice`, `Quot.sound` (the repunit
formula uses a subset). No `sorryAx`, custom axiom or native-decision shortcut is
accepted. Lean4Lean failed because of an incompatible compiled format; no second
independent kernel success is claimed. Packaging verifies original source/log
identities and restoration, **not a new cache-free Lean build**. Such a full build
was not rerun during packaging. The disposable cache and exports were removed
after the original successful checks and are not public dependencies.

## Manuscript build

The TeX is monolithic with inline `thebibliography`: no `.bib`, BibTeX, Biber,
scientific `input`/`include`, figures or private assets are needed. Use pdfTeX
1.40.25 / TeX Live 2023 or a compatible LaTeX installation with `lmodern`,
`geometry`, `amsmath`, `amssymb`, `amsthm`, `booktabs`, `microtype`, `xurl` and
`hyperref` (plus standard font/input encoding packages). The bounded build checks
references in draft mode without producing a PDF:

```sh
python3 -B check/check.py --tex
```

To typeset separately when desired, run `pdflatex` three times on
`paper/A209933_v4.tex`, with an existing output directory outside this payload.
No PDF is included in this local draft. All scientific statements, bibliography
and author identity match version 3; only the availability paragraph was updated.

Package checksums describe this release payload. The local pre-upload audit exercises
the bounded commands above in fresh clone-like and extracted-archive roots,
including missing, changed and unexpected-file controls. This establishes only
the local bytes; actual GitHub/Zenodo distribution verification is a separate
post-publication step. Before each later GitHub release, the author must confirm
the repository/tag-specific Zenodo account connection and enabled repository
synchronization. On 24 November 2026 the author confirmed the linked account and
enabled synchronization for `carcorti/A209933`, tag `v1.0`, and authorized this
release. The resulting Zenodo deposit and actual distributed archives require
their own verification; the account confirmation alone does not certify them.
