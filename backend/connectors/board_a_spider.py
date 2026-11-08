"""Scrapy spider for the mock job board A (French site, list + detail pages).

It only EXTRACTS: every field is kept as the site shows it ("Casa", "il y a 3 jours",
HTML description...). Cleaning those values is the job of the normalizer, a later step.
Knowledge that belongs to THIS site only (for example the text "Lieu non précisé"
meaning "no city") is handled here.

Run from the backend folder:
    python -m scrapy runspider connectors/board_a_spider.py -a max_pages=2 -O data/board_a_raw.jsonl
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import UTC, datetime

import scrapy
from scrapy.http import Response

from common.config import settings
from common.text import clean

NO_CITY_TEXT = "Lieu non précisé"  # what board A prints when an offer has no city


class BoardASpider(scrapy.Spider):
    name = "board_a"
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
        self.base_url = base_url.rstrip("/")
        self.max_pages = int(max_pages) if max_pages else None  # None = all pages
        self.pages_seen = 0
        self.start_urls = [f"{self.base_url}/board_a/offers"]

    # ---- list page: find the offers and the "Suivant" link -----------------
    def parse(self, response: Response) -> Iterator[scrapy.Request]:
        self.pages_seen += 1
        for href in response.css("a.offer-title::attr(href)").getall():
            yield response.follow(href, callback=self.parse_offer)

        next_href = response.css("nav.pagination a[rel=next]::attr(href)").get()
        if next_href and (self.max_pages is None or self.pages_seen < self.max_pages):
            yield response.follow(next_href, callback=self.parse)

    # ---- detail page: extract one raw offer --------------------------------
    def parse_offer(self, response: Response) -> Iterator[dict]:
        title = clean(response.css("article.offer-detail h1::text").get())
        if not title:  # the page layout changed: say it loudly instead of saving garbage
            self.logger.warning("no title found, skipped: %s", response.url)
            return

        city = clean(response.css("p.meta span.city::text").get())
        if city == NO_CITY_TEXT:
            city = None

        expired = bool(response.css("span.badge.expired"))
        deadline = None
        if not expired:
            match = re.search(r":\s*(\S+)", " ".join(response.css("p.deadline::text").getall()))
            deadline = match.group(1) if match else None

        yield {
            "board": self.name,
            "source_id": response.url.rstrip("/").rsplit("/", 1)[-1],
            "url": response.url,
            "title": title,
            "company": clean(response.css("p.meta span.company::text").get()),
            "city_raw": city,
            "date_raw": clean(response.css("p.meta span.date::text").get()),
            "deadline_raw": deadline,
            "is_expired": expired,
            "description_html": response.css("div.description").get(),
            "scraped_at": datetime.now(UTC).isoformat(),
        }
        