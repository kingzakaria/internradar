import json
import re

from mock_jobboard import server


def ids_on(records, board):
    return {record.id for record in records if board in record.boards}


def test_robots_txt_lists_the_boards(client):
    response = client.get("/robots.txt")
    assert response.status_code == 200
    for board in ("board_a", "board_b", "board_c"):
        assert f"Allow: /{board}/" in response.text
    assert "Crawl-delay: 1" in response.text


def test_board_a_list_has_20_offers_and_a_next_link(client):
    page = client.get("/board_a/offers").text
    assert page.count('class="offer"') == 20
    assert 'rel="next"' in page
    assert 'rel="prev"' not in page


def test_board_a_detail_and_404(client, records):
    on_a = ids_on(records, "board_a")
    not_on_a = ids_on(records, "board_b") - on_a
    assert client.get(f"/board_a/offers/{min(on_a)}").status_code == 200
    assert client.get(f"/board_a/offers/{min(not_on_a)}").status_code == 404
    assert client.get("/board_a/offers/999999").status_code == 404


def test_board_b_uses_cards_and_numbered_pages(client):
    page = client.get("/board_b/jobs").text
    assert page.count('class="job-card"') == 12
    assert 'class="current">1<' in page
    assert "/board_b/jobs?p=2" in page


def test_board_c_cursor_pagination_visits_every_offer_once(client, records):
    seen, url = [], "/board_c/emplois"
    while url:
        page = client.get(url).text
        seen += [int(i) for i in re.findall(r'href="/board_c/emplois/(\d+)"', page)]
        match = re.search(r'rel="next" href="([^"]+)"', page)
        url = match.group(1) if match else None
    assert len(seen) == len(set(seen))
    assert set(seen) == ids_on(records, "board_c")


def test_board_c_rejects_a_made_up_cursor(client):
    assert client.get("/board_c/emplois?cursor=not-a-cursor").status_code == 400


def test_board_c_detail_contains_valid_json_ld(client, records):
    offer_id = min(ids_on(records, "board_c"))
    page = client.get(f"/board_c/emplois/{offer_id}").text
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
    assert len(blocks) == 1
    data = json.loads(blocks[0].replace("<\\/", "</"))
    assert data["@type"] == "JobPosting"
    assert data["identifier"]["value"] == str(offer_id)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", data["datePosted"])


def test_json_ld_can_never_close_the_script_tag_early():
    row = {
        "id": 1, "title": "t", "company": "c", "city_display": "", "country": "MA",
        "contract": "stage", "posted_at": "2026-09-01T10:00:00+00:00",
        "expires_at": "2026-10-01T00:00:00+00:00",
        "description_html": "<p>x</p></script><b>evil</b>",
    }
    output = server.job_posting_jsonld(row)
    assert "</script" not in output
    assert json.loads(output.replace("<\\/", "</"))["description"] == row["description_html"]
    assert "jobLocation" not in json.loads(output)  # no city, no location