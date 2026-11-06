"""City normalization: many ways to write a city in, one (city, country) out."""

from __future__ import annotations

import re

from common.schemas import normalize_text

# The cities we know, by country. A city not listed here is kept as written, with no country.
CITIES_BY_COUNTRY = {
    "MA": [
        "Casablanca", "Rabat", "Tanger", "Marrakech", "Fès", "Agadir", "Kénitra",
        "Tétouan", "Oujda", "Meknès", "Mohammedia", "Salé", "El Jadida", "Nador",
        "Béni Mellal", "Safi", "Témara", "Laâyoune",
    ],
    "FR": [
        "Paris", "Lyon", "Toulouse", "Marseille", "Lille", "Bordeaux", "Nantes", "Nice",
        "Strasbourg", "Rennes", "Montpellier", "Grenoble", "Toulon", "Dijon", "Angers",
        "Nîmes", "Reims", "Le Havre", "Saint-Étienne", "Clermont-Ferrand", "Aix-en-Provence",
    ],
}

# Other names for the same city. Keys are already normalized (lowercase, no accents).
ALIASES = {
    "casa": "Casablanca",
    "rabat sale": "Rabat",
    "tangier": "Tanger",
    "marrakesh": "Marrakech",
    "fez": "Fès",
}

# Some sites write only the country where a city should be.
COUNTRY_NAMES = {"maroc": "MA", "morocco": "MA", "france": "FR"}

_LOOKUP = {
    normalize_text(city): (city, country)
    for country, cities in CITIES_BY_COUNTRY.items()
    for city in cities
}


def normalize_city(raw: str | None) -> tuple[str | None, str | None]:
    """Return (city, country). Unknown or empty input gives (None, None) or the raw text."""
    if not raw:
        return None, None
    text = re.sub(r"\([^)]*\)", " ", raw)  # "Casablanca (Maroc)", "Lyon (69)" -> drop the (...)
    text = re.sub(r"\b\d+(?:er|e|ème|eme)?\b", " ", text)  # "Paris 8e" -> "Paris"
    key = normalize_text(text)
    if not key:
        return None, None
    if key in COUNTRY_NAMES:
        return None, COUNTRY_NAMES[key]
    if key in ALIASES:
        key = normalize_text(ALIASES[key])
    if key in _LOOKUP:
        return _LOOKUP[key]
    return re.sub(r"\s+", " ", text).strip(), None  # unknown city: keep it as written