import pytest

from app import chem_tools as ct


def test_balance_water():
    coeffs, text = ct.balance_equation("H2 + O2 -> H2O")
    assert coeffs == [2, 1, 2]
    assert text == "2H2 + O2 -> 2H2O"


def test_balance_glucose_combustion():
    coeffs, text = ct.balance_equation("C6H12O6 + O2 -> CO2 + H2O")
    assert coeffs == [1, 6, 6, 6]


def test_balance_permanganate():
    coeffs, _ = ct.balance_equation("KMnO4 + HCl -> KCl + MnCl2 + H2O + Cl2")
    assert coeffs == [2, 16, 2, 2, 8, 5]


def test_cannot_balance_impossible_equation():
    with pytest.raises(ValueError):
        ct.balance_equation("H2 -> O2")


def test_parentheses_formula():
    assert ct.parse_formula("Ca(OH)2") == {"Ca": 1, "O": 2, "H": 2}


def test_half_lives():
    assert abs(ct.half_life(0, 10, 2) - 2.5) < 1e-9
    assert abs(ct.half_life(1, 10, 0.693147) - 1.0) < 1e-4
    assert abs(ct.half_life(2, 2, 0.5) - 1.0) < 1e-9


def test_rate_constant_roundtrip():
    c = ct.concentration(1, 10, 0.2, 3)
    assert abs(ct.rate_constant(1, 10, c, 3) - 0.2) < 1e-9


def test_arrhenius_increases_with_temperature():
    k25 = 0.01
    k40 = ct.arrhenius_k(k25, 25, 50, 40)
    assert 2.4 < k40 / k25 < 2.8


def test_shelf_life_first_order():
    result = ct.shelf_life(0.01, 25, 50, 25)
    assert abs(result["k_storage"] - 0.01) < 1e-12
    assert abs(result["t90"] - (-__import__("math").log(0.9) / 0.01)) < 1e-9
