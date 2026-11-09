"""Scrapy spider for the mock job board B (English site, cards, numbered pages).

Same job as the board A spider (it only EXTRACTS, values stay raw) but a different site:
other URLs (/board_b/jobs?p=2), other HTML (cards and a definition list), other wording.

Run from the backend folder:
    python -m scrapy runspider connectors/board_b_spider.py -a max_pages=2 -O data/board_b_raw.jsonl
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import UTC, datetime

import scrapy
from scrapy.http import Response

from common.config import settings
from common.sources import require_approved
from common.text import clean

NO_CITY_TEXT = "Not specified"  # what board B prints on a detail page when there is no city


class BoardBSpider(scrapy.Spider):
    name = "board_b"
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
        self.start_urls = [f"{self.base_url}/board_b/jobs"]

    # ---- list page: find the cards and the "Next" link ---------------------
    def parse(self, response: Response) -> Iterator[scrapy.Request]:
        self.pages_seen += 1
        for href in response.css("article.job-card h2.job-card__title a::attr(href)").getall():
            yield response.follow(href, callback=self.parse_offer)

        next_href = response.css("nav.pager a[rel=next]::attr(href)").get()
        if next_href and (self.max_pages is None or self.pages_seen < self.max_pages):
            yield response.follow(next_href, callback=self.parse)

    # ---- detail page: extract one raw offer --------------------------------
    def parse_offer(self, response: Response) -> Iterator[dict]:
        title = clean(response.css("h1.job-title::text").get())
        if not title:  # the page layout changed: say it loudly instead of saving garbage
            self.logger.warning("no title found, skipped: %s", response.url)
            return

        city = clean(response.css("dl.job-facts dd.location::text").get())
        if city == NO_CITY_TEXT:
            city = None

        expired = bool(response.css("span.status--expired"))
        deadline = None
        if not expired:
            status = " ".join(
                response.xpath('//dt[normalize-space()="Status"]/following-sibling::dd[1]//text()').getall()
            )
            match = re.search(r"Apply before\s+(\S+)", status)
            deadline = match.group(1) if match else None

        yield {
            "board": self.name,
            "source_id": response.url.rstrip("/").rsplit("/", 1)[-1],
            "url": response.url,
            "title": title,
            "company": clean(response.css("dl.job-facts dd.company::text").get()),
            "city_raw": city,
            "date_raw": clean(response.css("dl.job-facts dd.posted::text").get()),
            "deadline_raw": deadline,
            "is_expired": expired,
            "description_html": response.css("section#job-description").get(),
            "scraped_at": datetime.now(UTC).isoformat(),
        }