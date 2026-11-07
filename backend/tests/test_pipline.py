"""End to end, offline: fake site -> spider parsing -> normalizer -> compared with the truth."""

from __future__ import annotations

from scrapy.http import HtmlResponse

from connectors.board_a_spider import BoardASpider
from mock_jobboard.generator import REFERENCE_TIME
from pipeline.evaluate import INFORMATIONAL, evaluate
from pipeline.normalize import normalize_offer


def to_response(client, path: str) -> HtmlResponse:
    """Fetch a page from the in-process fake site and wrap it like Scrapy would."""
    reply = client.get(path)
    assert reply.status_code == 200
    return HtmlResponse(url=f"http://localhost:8000{path}", body=reply.content, encoding="utf-8")


def test_list_page_gives_offer_links_and_the_next_page(client):
    requests = list(BoardASpider().parse(to_response(client, "/board_a/offers")))
    urls = [request.url for request in requests]
    assert sum("/board_a/offers/" in url for url in urls) == 20
    assert any(url.endswith("/board_a/offers?page=2") for url in urls)


def test_spider_skips_a_page_without_a_title(client):
    page = HtmlResponse(url="http://localhost:8000/board_a/offers/1", body=b"<html></html>")
    assert list(BoardASpider().parse_offer(page)) == []


def test_spider_then_normalizer_recover_the_ground_truth(client, records, truth):
    spider = BoardASpider()
    on_board_a = [record for record in records if "board_a" in record.boards][:80]

    raw_items = []
    for record in on_board_a:
        raw_items += list(spider.parse_offer(to_response(client, f"/board_a/offers/{record.id}")))
    assert len(raw_items) == len(on_board_a)

    offers = [normalize_offer(raw, REFERENCE_TIME).model_dump(mode="json") for raw in raw_items]
    scores, unmatched = evaluate(offers, truth)

    assert unmatched == 0
    for name, (correct, total) in scores.items():
        if name not in INFORMATIONAL:
            assert correct == total, f"{name}: {correct}/{total}"