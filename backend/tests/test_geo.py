import pytest

from common.geo import normalize_city


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Casablanca", ("Casablanca", "MA")),
        ("Casa", ("Casablanca", "MA")),  # nickname
        ("CASABLANCA", ("Casablanca", "MA")),  # capitals
        ("Casablanca (Maroc)", ("Casablanca", "MA")),  # country in brackets
        ("Rabat-Salé", ("Rabat", "MA")),  # double name
        ("Salé", ("Salé", "MA")),  # but Salé alone stays Salé
        ("Fes", ("Fès", "MA")),  # missing accent
        ("Kenitra", ("Kénitra", "MA")),
        ("Paris 8e", ("Paris", "FR")),  # arrondissement
        ("Paris (75)", ("Paris", "FR")),  # department number
        ("LYON", ("Lyon", "FR")),
        ("Maroc", (None, "MA")),  # only a country
        ("France", (None, "FR")),
        ("Bruxelles", ("Bruxelles", None)),  # unknown city: kept as written, no country
        ("", (None, None)),
        (None, (None, None)),
    ],
)
def test_normalize_city(raw, expected):
    assert normalize_city(raw) == expected