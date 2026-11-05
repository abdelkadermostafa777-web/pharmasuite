"""Pure-Python chemistry and pharmaceutical calculations (no GUI, no RDKit needed)."""
import math
import re
from fractions import Fraction
from math import gcd

R_GAS = 8.314  # J/(mol*K)
_TOKEN_RE = re.compile(r"[A-Z][a-z]?|\(|\)|\d+")


def parse_formula(formula):
    """Parse a formula such as 'Ca(OH)2' into element counts: {'Ca': 1, 'O': 2, 'H': 2}."""
    formula = formula.replace(" ", "")
    if not formula:
        raise ValueError("Empty formula")
    tokens = _TOKEN_RE.findall(formula)
    if "".join(tokens) != formula:
        raise ValueError(f"Invalid formula: {formula}")

    stack = [{}]
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "(":
            stack.append({})
        elif tok == ")":
            if len(stack) == 1:
                raise ValueError("Unbalanced parentheses")
            group = stack.pop()
            mult = 1
            if i + 1 < len(tokens) and tokens[i + 1].isdigit():
                mult = int(tokens[i + 1])
                i += 1
            for el, cnt in group.items():
                stack[-1][el] = stack[-1].get(el, 0) + cnt * mult
        elif tok.isdigit():
            raise ValueError(f"Unexpected number in formula: {formula}")
        else:
            cnt = 1
            if i + 1 < len(tokens) and tokens[i + 1].isdigit():
                cnt = int(tokens[i + 1])
                i += 1
            stack[-1][tok] = stack[-1].get(tok, 0) + cnt
        i += 1
    if len(stack) != 1:
        raise ValueError("Unbalanced parentheses")
    return stack[0]


def _nullspace(matrix, n):
    """Basis of the null space of a matrix of Fractions (Gauss-Jordan elimination)."""
    m = [row[:] for row in matrix]
    pivots = []
    r = 0
    for c in range(n):
        p = next((i for i in range(r, len(m)) if m[i][c] != 0), None)
        if p is None:
            continue
        m[r], m[p] = m[p], m[r]
        pv = m[r][c]
        m[r] = [x / pv for x in m[r]]
        for i in range(len(m)):
            if i != r and m[i][c] != 0:
                f = m[i][c]
                m[i] = [a - f * b for a, b in zip(m[i], m[r])]
        pivots.append(c)
        r += 1
        if r == len(m):
            break
    free = [c for c in range(n) if c not in pivots]
    basis = []
    for fc in free:
        v = [Fraction(0)] * n
        v[fc] = Fraction(1)
        for i, pc in enumerate(pivots):
            v[pc] = -m[i][fc]
        basis.append(v)
    return basis


def _split_species(side):
    parts = [p.replace(" ", "") for p in side.split("+")]
    return [re.sub(r"^\d+", "", p) for p in parts if p]


def _format(species, coeffs, n_reactants):
    def side(items):
        return " + ".join(f"{c if c != 1 else ''}{s}" for s, c in items)
    left = list(zip(species[:n_reactants], coeffs[:n_reactants]))
    right = list(zip(species[n_reactants:], coeffs[n_reactants:]))
    return f"{side(left)} -> {side(right)}"


def balance_equation(equation):
    """Balance a chemical equation. Returns (coefficients, balanced_text)."""
    eq = equation.replace("→", "->").replace("=", "->")
    if eq.count("->") != 1:
        raise ValueError("Use exactly one arrow: reactants -> products")
    left, right = eq.split("->")
    reactants, products = _split_species(left), _split_species(right)
    if not reactants or not products:
        raise ValueError("Both sides need at least one species")

    species = reactants + products
    parsed = [parse_formula(s) for s in species]
    elements = sorted({e for p in parsed for e in p})
    n = len(species)
    matrix = []
    for el in elements:
        row = []
        for i, p in enumerate(parsed):
            sign = 1 if i < len(reactants) else -1
            row.append(Fraction(p.get(el, 0) * sign))
        matrix.append(row)

    basis = _nullspace(matrix, n)
    if not basis:
        raise ValueError("This equation cannot be balanced")
    if len(basis) > 1:
        raise ValueError("More than one solution exists; check the species")

    vec = basis[0]
    lcm = 1
    for x in vec:
        lcm = lcm * x.denominator // gcd(lcm, x.denominator)
    ints = [int(x * lcm) for x in vec]
    if all(c <= 0 for c in ints):
        ints = [-c for c in ints]
    if any(c <= 0 for c in ints):
        raise ValueError("Equation cannot be balanced with positive coefficients")
    g = 0
    for c in ints:
        g = gcd(g, c)
    ints = [c // g for c in ints]
    return ints, _format(species, ints, len(reactants))


def _check_pos(**values):
    for name, v in values.items():
        if v <= 0:
            raise ValueError(f"{name} must be greater than zero")


def half_life(order, a0, k):
    """Half-life for reaction order 0, 1 or 2."""
    _check_pos(a0=a0, k=k)
    if order == 0:
        return a0 / (2 * k)
    if order == 1:
        return math.log(2) / k
    if order == 2:
        return 1 / (k * a0)
    raise ValueError("order must be 0, 1 or 2")


def concentration(order, a0, k, t):
    """Concentration remaining at time t."""
    _check_pos(a0=a0, k=k)
    if t < 0:
        raise ValueError("t must be zero or greater")
    if order == 0:
        return max(a0 - k * t, 0.0)
    if order == 1:
        return a0 * math.exp(-k * t)
    if order == 2:
        return 1 / (1 / a0 + k * t)
    raise ValueError("order must be 0, 1 or 2")


def rate_constant(order, a0, at, t):
    """Estimate k from one measurement: concentration at (a0) and at time t (at)."""
    _check_pos(a0=a0, at=at, t=t)
    if at > a0:
        raise ValueError("Concentration at time t cannot exceed the initial concentration")
    if order == 0:
        return (a0 - at) / t
    if order == 1:
        return math.log(a0 / at) / t
    if order == 2:
        return (1 / at - 1 / a0) / t
    raise ValueError("order must be 0, 1 or 2")


def arrhenius_k(k_ref, t_ref_c, ea_kj, t_c):
    """Rate constant at temperature t_c given k at t_ref_c (Arrhenius equation)."""
    _check_pos(k_ref=k_ref)
    t1, t2 = t_ref_c + 273.15, t_c + 273.15
    if t1 <= 0 or t2 <= 0:
        raise ValueError("Temperature cannot be below absolute zero")
    return k_ref * math.exp(-(ea_kj * 1000) / R_GAS * (1 / t2 - 1 / t1))


def shelf_life(k_ref, t_ref_c, ea_kj, t_storage_c):
    """Predict degradation at storage temperature, assuming first-order kinetics.

    t90 is the time until 90% of the drug remains. Units follow k_ref (e.g. per day -> days).
    """
    k = arrhenius_k(k_ref, t_ref_c, ea_kj, t_storage_c)
    return {
        "k_storage": k,
        "t90": -math.log(0.9) / k,
        "t_half": math.log(2) / k,
    }
