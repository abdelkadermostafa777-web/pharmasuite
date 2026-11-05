"""Periodic-table helpers: grid positions, element categories, electron shells."""
from rdkit import Chem

PT = Chem.GetPeriodicTable()

NOBLE = {2, 10, 18, 36, 54, 86, 118}
HALOGEN = {9, 17, 35, 53, 85, 117}
NONMETAL = {1, 6, 7, 8, 15, 16, 34}
METALLOID = {5, 14, 32, 33, 51, 52, 84}
ALKALI = {3, 11, 19, 37, 55, 87}
ALKALINE = {4, 12, 20, 38, 56, 88}

CATEGORY_COLORS = {
    "noble": "#8e44ad",
    "halogen": "#d35400",
    "nonmetal": "#16a085",
    "metalloid": "#2980b9",
    "alkali": "#c0392b",
    "alkaline": "#e67e22",
    "lanthanide": "#b7950b",
    "actinide": "#7d6608",
    "transition": "#2c3e50",
    "post": "#5d6d7e",
}


def _cols8(i):
    return i if i <= 2 else i + 10


def position(z):
    """Return (row, col) in the standard 18-column layout. f-block uses rows 9 and 10."""
    if z == 1:
        return 1, 1
    if z == 2:
        return 1, 18
    if z <= 10:
        return 2, _cols8(z - 2)
    if z <= 18:
        return 3, _cols8(z - 10)
    if z <= 36:
        return 4, z - 18
    if z <= 54:
        return 5, z - 36
    if z <= 86:
        if z in (55, 56):
            return 6, z - 54
        if z == 57:
            return 6, 3
        if z <= 71:
            return 9, z - 55
        return 6, z - 68
    if z in (87, 88):
        return 7, z - 86
    if z == 89:
        return 7, 3
    if z <= 103:
        return 10, z - 87
    return 7, z - 100


def category(z):
    if z in NOBLE:
        return "noble"
    if z in HALOGEN:
        return "halogen"
    if z in NONMETAL:
        return "nonmetal"
    if z in METALLOID:
        return "metalloid"
    if z in ALKALI:
        return "alkali"
    if z in ALKALINE:
        return "alkaline"
    if 57 <= z <= 71:
        return "lanthanide"
    if 89 <= z <= 103:
        return "actinide"
    row, col = position(z)
    if 4 <= row <= 7 and 3 <= col <= 12:
        return "transition"
    return "post"


def period_of(z):
    row, _ = position(z)
    return {9: 6, 10: 7}.get(row, row)


# Madelung filling order: (n, l, capacity)
_ORDER = [
    (1, 0, 2), (2, 0, 2), (2, 1, 6), (3, 0, 2), (3, 1, 6), (4, 0, 2), (3, 2, 10),
    (4, 1, 6), (5, 0, 2), (4, 2, 10), (5, 1, 6), (6, 0, 2), (4, 3, 14), (5, 2, 10),
    (6, 1, 6), (7, 0, 2), (5, 3, 14), (6, 2, 10), (7, 1, 6),
]


def shells(z):
    """Electrons per shell (K, L, M, ...) using the Aufbau approximation for teaching."""
    remaining = z
    per_n = {}
    for n, _l, cap in _ORDER:
        if remaining <= 0:
            break
        taken = min(cap, remaining)
        per_n[n] = per_n.get(n, 0) + taken
        remaining -= taken
    return [per_n[n] for n in sorted(per_n)]
