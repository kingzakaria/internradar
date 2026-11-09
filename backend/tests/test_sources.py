"""The source registry is a safety rule, so the rule itself is tested."""

from __future__ import annotations

from pathlib import Path

import pytest

from common.sources import (
    SOURCES,
    SourceNotApproved,
    approved_sources,
    get_source,
    require_approved,
    to_markdown,
)
from connectors.board_a_spider import BoardASpider
from connectors.board_b_spider import BoardBSpider
from connectors.board_c_spider import BoardCSpider

CONNECTORS = Path(__file__).resolve().parent.parent / "connectors"


def test_approved_source_is_returned():
    assert require_approved("board_a").status == "approved"


def test_unknown_source_is_refused():
    with pytest.raises(SourceNotApproved):
        require_approved("some_site_nobody_listed")


@pytest.mark.parametrize("source_id", ["linkedin", "indeed", "glassdoor"])
def test_blocked_sources_are_refused(source_id):
    assert get_source(source_id).status == "blocked"
    with pytest.raises(SourceNotApproved):
        require_approved(source_id)


def test_pending_sources_are_refused():
    pending = [s for s in SOURCES if s.status == "pending"]
    assert pending  # real sources are planned
    for source in pending:
        with pytest.raises(SourceNotApproved):
            require_approved(source.id)


def test_only_our_own_mock_boards_are_approved_for_now():
    assert {s.kind for s in approved_sources()} == {"mock_board"}


def test_a_real_source_cannot_be_approved_without_a_terms_link_and_a_check_date():
    for source in SOURCES:
        if source.status == "approved" and source.kind != "mock_board":
            assert source.terms_url
            assert source.checked_on


def test_no_code_exists_for_blocked_sources():
    blocked = [s.id for s in SOURCES if s.status == "blocked"]
    for path in CONNECTORS.glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for source_id in blocked:
            assert source_id not in path.name.lower(), path.name
            assert f"{source_id}.com" not in text, path.name


def test_every_spider_is_registered_and_approved():
    for spider_class in (BoardASpider, BoardBSpider, BoardCSpider):
        assert get_source(spider_class.name).status == "approved"
        spider_class()  # would raise if refused


def test_spider_refuses_to_start_when_its_source_is_not_approved(monkeypatch):
    monkeypatch.setattr("connectors.board_a_spider.require_approved", _deny)
    with pytest.raises(SourceNotApproved):
        BoardASpider()


def _deny(source_id):
    raise SourceNotApproved(source_id)


def test_markdown_lists_every_source():
    text = to_markdown()
    for source in SOURCES:
        assert source.name in text