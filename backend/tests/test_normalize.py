from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from pipeline.normalize import normalize_offer, parse_date

REFERENCE = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)

RAW = {
    "board": "board_a",
    "source_id": "42",
    "url": "http://localhost:8000/board_a/offers/42",
    "title": "Stage Data Analyst",
    "company": "Atlas Data Labs",
    "city_raw": "Casa",
    "date_raw": "il y a 3 jours",
    "description_html": "<p>L&#x27;équipe cherche un(e) stagiaire.</p>",
    "scraped_at": "2026-11-06T10:00:00+00:00",
}


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2026-09-14", date(2026, 9, 14)),
        ("14/09/2026", date(2026, 9, 14)),  # day first
        ("31 août 2026", date(2026, 8, 31)),  # French month with accent
        ("14 septembre 2026", date(2026, 9, 14)),
        ("September 14, 2026", date(2026, 9, 14)),
        ("il y a 3 jours", date(2026, 9, 28)),  # counted from the reference time
        ("3 days ago", date(2026, 9, 28)),
        ("hier", date(2026, 9, 30)),
        ("aujourd'hui", date(2026, 10, 1)),
        ("31/02/2026", None),  # impossible date
        ("bientôt", None),  # not a date
        ("", None),
        (None, None),
    ],
)
def test_parse_date(raw, expected):
    result = parse_date(raw, REFERENCE)
    assert (result.date() if result else None) == expected


def test_relative_dates_depend_on_the_reference_time():
    later = datetime(2026, 11, 6, tzinfo=UTC)
    assert parse_date("il y a 3 jours", REFERENCE).date() == date(2026, 9, 28)
    assert parse_date("il y a 3 jours", later).date() == date(2026, 11, 3)


def test_normalize_offer_cleans_every_field():
    offer = normalize_offer(RAW, REFERENCE)
    assert (offer.city, offer.country) == ("Casablanca", "MA")
    assert offer.posted_at == datetime(2026, 9, 28, tzinfo=UTC)
    assert offer.description == "L'équipe cherche un(e) stagiaire."
    assert offer.source == "board_a"
    assert offer.fetched_at == datetime(2026, 11, 6, 10, 0, tzinfo=UTC)


def test_without_reference_time_the_scraping_time_is_used():
    offer = normalize_offer(RAW)  # "il y a 3 jours" counted from scraped_at (6 November)
    assert offer.posted_at == datetime(2026, 11, 3, tzinfo=UTC)


def test_unknown_data_is_treated_as_synthetic():
    assert normalize_offer(RAW, REFERENCE).is_synthetic is True
    assert normalize_offer({**RAW, "is_synthetic": False}, REFERENCE).is_synthetic is False


def test_offer_without_city_or_date_is_still_valid():
    offer = normalize_offer({**RAW, "city_raw": None, "date_raw": None}, REFERENCE)
    assert offer.city is None
    assert offer.country is None
    assert offer.posted_at is None


@pytest.mark.parametrize("title", [None, "", "   "])
def test_offer_without_a_real_title_is_rejected(title):
    with pytest.raises(ValueError, match="no title"):
        normalize_offer({**RAW, "title": title}, REFERENCE)


def test_offer_with_no_title_key_is_rejected():
    raw = {key: value for key, value in RAW.items() if key != "title"}
    with pytest.raises(ValueError, match="no title"):
        normalize_offer(raw, REFERENCE)


def test_offer_without_url_is_rejected():
    raw = {key: value for key, value in RAW.items() if key != "url"}
    with pytest.raises(KeyError):
        normalize_offer(raw, REFERENCE)


def test_same_offer_on_two_boards_gets_the_same_dedup_key():
    on_a = normalize_offer(RAW, REFERENCE)
    on_b = normalize_offer(
        {**RAW, "board": "board_b", "title": "  Stage  Data Analyst ", "city_raw": "Casablanca (Maroc)"},
        REFERENCE,
    )
    assert on_a.dedup_key == on_b.dedup_key  # same offer...
    assert on_a.offer_id != on_b.offer_id  # ...but two distinct records


def test_offer_with_an_empty_url_value_is_rejected():
    with pytest.raises(ValidationError):
        normalize_offer({**RAW, "url": None}, REFERENCE)