from decimal import Decimal

from gallica_le_temps.extract import first_number, parse_french_number


def test_comma_decimal():
    assert parse_french_number("84,25") == Decimal("84.25")


def test_thousands_dot_and_comma():
    assert parse_french_number("1.234,50") == Decimal("1234.50")


def test_thousands_space():
    assert parse_french_number("1 234") == Decimal("1234")


def test_dotted_thousands_no_decimal():
    assert parse_french_number("1.234") == Decimal("1234")


def test_mixed_fraction_eighths():
    assert parse_french_number("83 1/2") == Decimal("83.5")
    assert parse_french_number("83 3/8") == Decimal("83.375")


def test_bare_percent_mark_is_not_a_value():
    assert parse_french_number("0/0") is None


def test_zero_denominator():
    assert parse_french_number("5 1/0") is None


def test_empty_and_none():
    assert parse_french_number("") is None
    assert parse_french_number(None) is None
    assert parse_french_number("abc") is None


def test_plain_integer():
    assert parse_french_number("83") == Decimal("83")


def test_first_number_in_noisy_text():
    assert first_number("cote: 84,25 fr.") == Decimal("84.25")
    assert first_number("Banque de France 4.100") == Decimal("4100")


def test_first_number_none():
    assert first_number("no digits here") is None
