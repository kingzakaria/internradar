"""Deduplication: unit tests on tiny offers, then end to end on the three fake boards."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from common.schemas import Offer
from mock_jobboard.generator import REFERENCE_TIME
from pipeline.dedup import deduplicate, evaluate_grouping
from pipeline.normalize import normalize_offer
from tests.test_pipeline import BOARDS, crawl

NOW = datetime(2026, 10, 1, tzinfo=UTC)


def make(source="board_a", source_id="1", title="Data Intern", company="Acme", city="Rabat", **extra):
    values = {
        "source": source, "source_id": source_id, "title": title, "company": company,
        "city": city, "country": "MA", "url": f"http://x/{source}/{source_id}",
        "description": "", "posted_at": None, "fetched_at": NOW, "is_synthetic": True,
    }
    values.update(extra)
    return Offer(**values)


def test_same_offer_on_two_boards_becomes_one():
    merged = deduplicate([make("board_a"), make("board_b")])
    assert len(merged) == 1
    assert {item.source for item in merged[0].listings} == {"board_a", "board_b"}


def test_spelling_accents_and_case_do_not_matter():
    merged = deduplicate(
        [make(title="Stagiaire Développeur"), make("board_b", title="STAGIAIRE DEVELOPPEUR")]
    )
    assert len(merged) == 1


def test_different_city_means_different_offer():
    assert len(deduplicate([make(city="Rabat"), make("board_b", city="Casablanca")])) == 2


def test_merged_offer_keeps_the_most_complete_listing_and_earliest_date():
    short = make("board_a", description="short", posted_at=datetime(2026, 9, 20, tzinfo=UTC))
    full = make(
        "board_b", description="a much longer description", posted_at=datetime(2026, 9, 10, tzinfo=UTC)
    )
    merged = deduplicate([short, full])[0]
    assert merged.description == "a much longer description"
    assert merged.posted_at == datetime(2026, 9, 10, tzinfo=UTC)


def test_one_synthetic_listing_makes_the_offer_synthetic():
    merged = deduplicate([make("board_a", is_synthetic=False), make("board_b", is_synthetic=True)])
    assert merged[0].is_synthetic is True


def test_result_does_not_depend_on_input_order():
    offers = [make("board_a"), make("board_b"), make("board_c", city="Fès")]
    forward = [m.model_dump_json() for m in deduplicate(offers)]
    backward = [m.model_dump_json() for m in deduplicate(offers[::-1])]
    assert forward == backward


def test_empty_input():
    assert deduplicate([]) == []


@pytest.fixture(scope="module")
def merged_all_boards(client):
    offers = []
    for param in BOARDS:
        spider_class, _board, start = param.values
        for item in crawl(client, spider_class(), start):
            offers.append(normalize_offer(item, REFERENCE_TIME))
    return deduplicate(offers)


def test_end_to_end_finds_every_planted_duplicate(merged_all_boards):
    result = evaluate_grouping(merged_all_boards)
    assert result["recall"] == 1.0
    assert result["split_offers"] == 0
    assert result["precision"] >= 0.98  # two different offers can share title+company+city