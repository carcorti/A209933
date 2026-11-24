"""Finite independent audit requested by Carlo after canonical consolidation.

Read-only; imports neither production program, checker nor catalog. No search
campaign or large primality proof. Certificates below prove R19/R23 locally.
Other large-prime statuses remain explicit external premises.
"""
import hashlib
import json
import math
from pathlib import Path
import time


def require(condition, message):
    if not condition:
        raise ValueError(message)


def small_prime(n):
    require(2 <= n <= 1000000, 'small-prime trial range')
    return all(n % d for d in range(2, math.isqrt(n) + 1))


def lucas(t, factors, base):
    p = (10 ** t - 1) // 9
    require(math.prod(q ** e for q, e in factors.items()) == p - 1,
            'incomplete p-1 factorization')
    require(all(small_prime(q) for q in factors), 'factor not prime')
    require(pow(base, p - 1, p) == 1, 'Fermat equality failed')
    gcds = {q: math.gcd(pow(base, (p - 1) // q, p) - 1, p) for q in factors}
    require(all(g == 1 for g in gcds.values()), 'Lucas order test failed')
    return p, {'exponent': t, 'prime': str(p), 'factors_of_p_minus_one': factors,
               'base': base, 'gcds': gcds, 'status': 'PROVED_PRIME_LUCAS_FULL_ORDER'}


def bad_digit(n, divisor):
    return any(c == '0' or n % int(c) != 0 for c in str(divisor))


def finite_scan(local_primes, started):
    """Complete necessary-prefix enumeration; actual divisor witnesses finish it.

    L=gcd(n,2520). Each nonzero digit divides L. For d|L, n/d is a
    divisor, so all its digits divide L. If P is any decimal prefix of n,
    floor(P/d) is the corresponding prefix of n/d, possibly empty/zero.
    Thus every true solution survives every prefix test used here.
    """
    classes = [g for g in range(1, 2521) if 2520 % g == 0 and g % 10 != 0]
    solutions, candidates, rejected = set(), set(), {}
    nodes, peak = 0, 0
    for g in classes:
        allowed = {str(d) for d in range(1, 10) if g % d == 0}
        divisors = [d for d in range(1, g + 1) if g % d == 0]
        frontier = [0]
        for length in range(1, 25):
            following = []
            for prefix in frontier:
                for digit in sorted(allowed):
                    n = 10 * prefix + int(digit)
                    nodes += 1
                    if all(n // d == 0 or set(str(n // d)) <= allowed for d in divisors):
                        following.append(n)
            frontier = following
            peak = max(peak, len(frontier))
            require(len(frontier) <= 100000, 'finite audit frontier ceiling')
            for n in frontier:
                if math.gcd(n, 2520) != g:
                    continue
                candidates.add(n)
                witness = None
                # These are merely trial divisor witnesses. Their primality is
                # irrelevant; each divisibility and offending digit is checked.
                for d in (21649, 2071723):
                    if n % d == 0 and bad_digit(n, d):
                        witness = d
                        break
                if witness is None:
                    for d in range(1, min(math.isqrt(n), 10000) + 1):
                        if n % d == 0:
                            if bad_digit(n, d):
                                witness = d
                                break
                            if bad_digit(n, n // d):
                                witness = n // d
                                break
                if witness is not None:
                    rejected[n] = witness
                    continue
                if math.isqrt(n) <= 10000:
                    # All divisor pairs have just been checked exhaustively.
                    solutions.add(n)
                    continue
                p = next((p for p in local_primes if n % p == 0 and n // p <= 2520), None)
                require(p is not None, 'unresolved finite candidate: ' + str(n))
                m = n // p
                require(math.gcd(m, p) == 1, 'prime valuation boundary')
                ds = [d for d in range(1, m + 1) if m % d == 0]
                ds += [p * d for d in ds]
                require(all(n % d == 0 and not bad_digit(n, d) for d in ds),
                        'finite candidate fails its complete divisor set')
                solutions.add(n)
            require(time.monotonic() - started < 60, 'finite audit wall ceiling')
    return sorted(solutions), {
        'bound_exclusive': str(10 ** 24), 'gcd_classes': len(classes),
        'prefix_digit_trials': nodes, 'peak_frontier': peak,
        'distinct_terminal_candidates': len(candidates),
        'actual_divisor_exclusions': len(rejected),
        'exclusion_witnesses': [{'n': str(n), 'divisor': str(d)} for n, d in sorted(rejected.items())],
        'solutions': [str(n) for n in sorted(solutions)],
        'independence': 'No production imports, no global structural classification, no external prime catalog. Only necessary quotient-prefix lemma, explicit invalid divisors, exhaustive small-divisor checks and local Lucas primes R19/R23.'}


def parse_decimal(raw):
    # Independent full integer arithmetic, without changing Python's decimal
    # conversion limit. Each int conversion has at most nine decimal digits.
    value = 0
    for offset in range(0, len(raw), 9):
        chunk = raw[offset:offset + 9]
        require(all(48 <= c <= 57 for c in chunk), 'nondecimal input')
        value = value * 10 ** len(chunk) + int(chunk)
    return value


def main():
    started = time.monotonic()
    p19, c19 = lucas(19, {2: 1, 3: 2, 5: 1, 7: 1, 11: 1, 13: 1,
                          19: 1, 37: 1, 52579: 1, 333667: 1}, 3)
    p23, c23 = lucas(23, {2: 1, 5: 1, 11: 2, 23: 1, 4093: 1,
                          8779: 1, 21649: 1, 513239: 1}, 11)
    finite, scan = finite_scan([p19, p23], started)
    root = Path(__file__).resolve().parents[1]
    path = root / 'data/b209933.txt'
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() ==
            '2768468ad0f9a808e0e82bf43f6ecd16009e72c37e50d5dfcae038d39aa72fbc', 'canonical identity')
    require(raw.endswith(b'\n\n') and not raw.endswith(b'\n\n\n'), 'terminal framing')
    rows, by_number = [], {}
    for index, line in enumerate(raw[:-1].splitlines(), 1):
        prefix = str(index).encode() + b' '
        require(line.startswith(prefix), 'index mismatch')
        digits = line[len(prefix):]
        require(digits and digits[0] != 48, 'decimal framing')
        n = parse_decimal(digits)
        require(n > (rows[-1][0] if rows else 0), 'order mismatch')
        rows.append((n, digits))
        by_number[n] = digits
        require(time.monotonic() - started < 60, 'finite audit wall ceiling')
    require(len(rows) == 101, 'row count')
    require(finite == [n for n, digits in rows if n < 10 ** 24], 'independent finite prefix mismatch')
    # These five larger prime premises are externally sourced, not Lucas-proved
    # by this audit. Explicit constants make the residual shared premise visible.
    prime_statuses = {19: 'LOCAL_LUCAS', 23: 'LOCAL_LUCAS', 317: 'EXTERNAL_PROVEN',
                      1031: 'EXTERNAL_PROVEN', 49081: 'EXTERNAL_PROVEN',
                      86453: 'EXTERNAL_PROVEN', 109297: 'EXTERNAL_PROVEN'}
    repunits = {(10 ** t - 1) // 9: t for t in prime_statuses}
    counts, checked_divisors, small_rows = {}, 0, 0
    for index, (n, digits) in enumerate(rows, 1):
        if n <= 264:
            ds = set()
            for d in range(1, math.isqrt(n) + 1):
                if n % d == 0:
                    ds.update((d, n // d))
            small_rows += 1
        else:
            m = math.gcd(n, 2520)
            p = n // m
            require(p in repunits and m <= 24 and math.gcd(m, p) == 1,
                    'row not an admitted prime times its small gcd')
            t = repunits[p]
            require(9 * n == m * (10 ** t - 1), 'full integer closed-form mismatch')
            ds = {d for d in range(1, m + 1) if m % d == 0}
            ds |= {p * d for d in ds}
            counts[t] = counts.get(t, 0) + 1
        allowed = {48 + d for d in range(1, 10) if n % d == 0}
        for divisor in ds:
            divisor_digits = (str(divisor).encode('ascii') if divisor <= 264
                              else by_number.get(divisor))
            require(divisor_digits is not None and n % divisor == 0, 'missing divisor bytes')
            require(set(divisor_digits) <= allowed, 'original divisor-digit predicate failed')
            checked_divisors += 1
        require(time.monotonic() - started < 60, 'finite audit wall ceiling')
    require(small_rows == 24 and counts == {t: 11 for t in prime_statuses}, 'block coverage')
    print(json.dumps({
        'status': 'PASS_INDEPENDENT_FINITE_PREFIX_AND_DIRECT_DIVISOR_AUDIT',
        'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'canonical_sha256': hashlib.sha256(raw).hexdigest(),
        'local_primality_certificates': [c19, c23], 'finite_exclusion': scan,
        'full_table': {'rows': len(rows), 'direct_divisors_checked': checked_divisors,
                       'closed_form_check': 'Full exact Python integer arithmetic parsed in nine-digit chunks; neither decimal production algorithm reused.',
                       'block_counts': counts, 'prime_statuses': prime_statuses},
        'conclusion': 'Exact sequence prefix1..46 below10^24 independently verified without structural theorem or external prime catalog. All101 values pass original divisor-digit predicate conditional only on external primality of five larger repunits. Exact ranks beyond46 still reuse the formal classification and externally admitted complete catalog.',
        'new_large_primality_proofs': False, 'canonical_modified': False,
        'audit_development_note': 'First audit implementation incorrectly expected even small divisor16 of48 to occur in the sequence table. Corrected only this auxiliary lookup: small divisor bytes now come directly from the integer. No production code or b-file changed; no hereditary-predicate assumption used.',
        'wall_seconds': time.monotonic() - started}, indent=2))


if __name__ == '__main__':
    main()
