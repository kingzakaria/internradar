"""End to end, offline: fake site -> spider -> normalizer -> compared with the ground truth."""

from __future__ import annotations

import pytest
import scrapy
from scrapy.http import HtmlResponse

from connectors.board_a_spider import BoardASpider
from connectors.board_b_spider import BoardBSpider
from connectors.board_c_spider import BoardCSpider, find_job_posting
from mock_jobboard.generator import REFERENCE_TIME
from pipeline.evaluate import INFORMATIONAL, evaluate
from pipeline.normalize import normalize_offer

SITE = "http://localhost:8000"

BOARDS = [
    pytest.param(BoardASpider, "board_a", "/board_a/offers", id="board_a"),
    pytest.param(BoardBSpider, "board_b", "/board_b/jobs", id="board_b"),
    pytest.param(BoardCSpider, "board_c", "/board_c/emplois", id="board_c"),
]


def to_response(client, path: str) -> HtmlResponse:
    """Fetch a page from the in-process fake site and wrap it like Scrapy would."""
    reply = client.get(path)
    assert reply.status_code == 200, path
    return HtmlResponse(url=f"{SITE}{path}", body=reply.content, encoding="utf-8")


def crawl(client, spider, start_path: str) -> list[dict]:
    """Run a spider against the in-process site like Scrapy would: no network, no delay."""
    items, queue = [], [(start_path, spider.parse, {})]
    while queue:
        path, callback, kwargs = queue.pop(0)
        for result in callback(to_response(client, path), **kwargs):
            if isinstance(result, scrapy.Request):
                queue.append((result.url.removeprefix(SITE), result.callback, result.cb_kwargs))
            else:
                items.append(result)
    return items


@pytest.mark.parametrize(("spider_class", "board", "start"), BOARDS)
def test_spider_finds_every_offer_of_its_board_once(client, records, spider_class, board, start):
    items = crawl(client, spider_class(), start)
    expected = {str(record.id) for record in records if board in record.boards}
    assert len(items) == len(expected)  # no offer twice
    assert {item["source_id"] for item in items} == expected  # none missing


@pytest.mark.parametrize(("spider_class", "board", "start"), BOARDS)
def test_spider_then_normalizer_recover_the_ground_truth(client, truth, spider_class, board, start):
    items = crawl(client, spider_class(), start)
    offers = [normalize_offer(item, REFERENCE_TIME).model_dump(mode="json") for item in items]
    scores, unmatched = evaluate(offers, truth)

    assert unmatched == 0
    for name, (correct, total) in scores.items():
        if name not in INFORMATIONAL:
            assert correct == total, f"{board}: {name}: {correct}/{total}"


def test_max_pages_limits_the_crawl(client):
    assert len(crawl(client, BoardASpider(max_pages="1"), "/board_a/offers")) == 20
    assert len(crawl(client, BoardBSpider(max_pages="1"), "/board_b/jobs")) == 12
    assert len(crawl(client, BoardCSpider(max_pages="1"), "/board_c/emplois")) == 15


@pytest.mark.parametrize("spider_class", [BoardASpider, BoardBSpider, BoardCSpider])
def test_spider_skips_a_page_without_usable_data(spider_class):
    page = HtmlResponse(url=f"{SITE}/x/1", body=b"<html></html>")
    assert list(spider_class().parse_offer(page)) == []


def test_board_c_expired_status_comes_from_the_list_page(client, records):
    items = {item["source_id"]: item for item in crawl(client, BoardCSpider(), "/board_c/emplois")}
    for record in records:
        if "board_c" in record.boards:
            assert items[str(record.id)]["is_expired"] == record.is_expired


def test_board_c_reads_the_country_from_json_ld(client, records):
    items = {item["source_id"]: item for item in crawl(client, BoardCSpider(), "/board_c/emplois")}
    with_city = [r for r in records if "board_c" in r.boards and r.city_display]
    assert with_city
    for record in with_city:
        assert items[str(record.id)]["country_raw"] == record.country


@pytest.mark.parametrize(
    ("blocks", "expected_title"),
    [
        (['{"@type": "JobPosting", "title": "A"}'], "A"),
        (["not json", '{"@type": "JobPosting", "title": "B"}'], "B"),  # a broken block is ignored
        (['{"@graph": [{"@type": "WebSite"}, {"@type": "JobPosting", "title": "C"}]}'], "C"),
        (['[{"@type": "Organization"}, {"@type": "JobPosting", "title": "D"}]'], "D"),
        (['{"@type": "Organization"}'], None),  # no job posting at all
        ([], None),
    ],
)
def test_find_job_posting(blocks, expected_title):
    posting = find_job_posting(blocks)
    assert (posting["title"] if posting else None) == expected_title