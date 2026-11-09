"""Scrapy spider for the mock job board C (French site, table, cursor pagination, JSON-LD).

Two differences from boards A and B:
- Pagination: the "Voir plus" link carries an opaque cursor. The spider cannot guess page 5,
  it must follow the link found on the previous page.
- Data: each detail page holds the offer as schema.org JobPosting JSON-LD, a structured block
  made for machines. That is cleaner and more stable than reading the visible HTML.
  The "expired" status exists only in the list table, so it is passed along to the detail page.

Run from the backend folder:
    python -m scrapy runspider connectors/board_c_spider.py -a max_pages=2 -O data/board_c_raw.jsonl
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime

import scrapy
from scrapy.http import Response

from common.config import settings
from common.sources import require_approved
from common.text import clean


def find_job_posting(blocks: list[str]) -> dict | None:
    """Return the schema.org JobPosting among the contents of JSON-LD <script> tags, or None."""
    for text in blocks:
        try:
            data = json.loads(text)
        except ValueError:  # broken JSON in one block: look at the others
            continue
        if isinstance(data, dict):
            candidates = data.get("@graph", [data])  # some sites wrap everything in a @graph
        elif isinstance(data, list):
            candidates = data
        else:
            continue
        for item in candidates:
            if isinstance(item, dict) and item.get("@type") == "JobPosting":
                return item
    return None


class BoardCSpider(scrapy.Spider):
    name = "board_c"
    allowed_domains = ["localhost"]
    custom_settings = {
        "USER_AGENT": settings.user_agent,  # honest: names the project
        "ROBOTSTXT_OBEY": True,  # read /robots.txt and follow it
        "DOWNLOAD_DELAY": 1.0,  # robots.txt says Crawl-delay: 1 (Scrapy does not apply it alone)
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,  # one request at a time: polite
        "RETRY_TIMES": 2,
        "LOG_LEVEL": "INFO",
    }

    def __init__(self, base_url: str = "http://localhost:8000", max_pages: str | None = None, **kwargs):
        super().__init__(**kwargs)
        require_approved(self.name)  # refuses to run if the source is not approved
        self.base_url = base_url.rstrip("/")
        self.max_pages = int(max_pages) if max_pages else None  # None = all pages
        self.pages_seen = 0
        self.start_urls = [f"{self.base_url}/board_c/emplois"]

    # ---- list page: read each table row, then follow "Voir plus" -----------
    def parse(self, response: Response) -> Iterator[scrapy.Request]:
        self.pages_seen += 1
        for row in response.css("tr.annonce"):
            href = row.css("td.col-titre a::attr(href)").get()
            if href:
                expired = bool(row.css("td.col-statut .tag-expire"))
                yield response.follow(href, callback=self.parse_offer, cb_kwargs={"expired": expired})

        next_href = response.css("a.load-more[rel=next]::attr(href)").get()
        if next_href and (self.max_pages is None or self.pages_seen < self.max_pages):
            yield response.follow(next_href, callback=self.parse)

    # ---- detail page: read the JSON-LD block --------------------------------
    def parse_offer(self, response: Response, expired: bool = False) -> Iterator[dict]:
        posting = find_job_posting(response.css('script[type="application/ld+json"]::text').getall())
        title = clean(posting.get("title")) if posting else None
        if not title:  # no usable structured data: say it loudly instead of saving garbage
            self.logger.warning("no JobPosting found, skipped: %s", response.url)
            return

        address = (posting.get("jobLocation") or {}).get("address") or {}
        organization = posting.get("hiringOrganization") or {}

        yield {
            "board": self.name,
            "source_id": response.url.rstrip("/").rsplit("/", 1)[-1],
            "url": response.url,
            "title": title,
            "company": clean(organization.get("name")),
            "city_raw": clean(address.get("addressLocality")),
            "country_raw": clean(address.get("addressCountry")),
            "date_raw": clean(posting.get("datePosted")),
            "deadline_raw": clean(posting.get("validThrough")),
            "is_expired": expired,
            "contract_raw": clean(posting.get("employmentType")),
            "description_html": posting.get("description"),
            "scraped_at": datetime.now(UTC).isoformat(),
        }