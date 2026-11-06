"""Mock job board websites (board_a, board_b, board_c), served from fake offers in SQLite.

Everything shown here is SYNTHETIC. The sites exist only so we can practise
scraping on our own machine, with no legal risk.

Run from the backend folder:
    python -m uvicorn mock_jobboard.server:app --port 8000
Then open:
    http://localhost:8000/board_a/offers
    http://localhost:8000/board_b/jobs
    http://localhost:8000/board_c/emplois
"""

from __future__ import annotations

import base64
import binascii
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

DB_PATH = os.getenv("MOCK_DB", "data/mock_jobs.db")
PAGE_SIZE_A = 20
PAGE_SIZE_B = 12
PAGE_SIZE_C = 15
TEMPLATES_DIR = Path(__file__).parent / "templates"

# Rules for crawlers. Our spider must read this file and obey it.
ROBOTS_TXT = """User-agent: *
Allow: /board_a/
Allow: /board_b/
Allow: /board_c/
Disallow: /admin/
Crawl-delay: 1
"""

# schema.org employmentType for each contract code.
EMPLOYMENT_TYPES = {
    "stage": "INTERN",
    "pfe": "INTERN",
    "alternance": "INTERN",
    "cdi": "FULL_TIME",
    "cdd": "TEMPORARY",
}

app = FastAPI(title="Mock job boards")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# "boards" is stored like "board_a, board_c": this matches one board name in it.
ON_BOARD = "(', ' || boards || ', ') LIKE ?"
LIST_COLUMNS = "id, title, company, city_display, date_display, is_expired"


def board_pattern(board: str) -> str:
    return f"%, {board}, %"


def query(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(sql, params).fetchall()


def list_page(board: str, page: int, page_size: int, columns: str):
    """Return (rows, total, pages) for one page of the offers shown on a board."""
    pattern = board_pattern(board)
    total = query(f"SELECT COUNT(*) FROM offers WHERE {ON_BOARD}", (pattern,))[0][0]
    pages = max(1, -(-total // page_size))  # ceiling division
    rows = query(
        f"SELECT {columns} FROM offers WHERE {ON_BOARD} ORDER BY id LIMIT ? OFFSET ?",
        (pattern, page_size, (page - 1) * page_size),
    )
    return rows, total, pages


def get_offer(board: str, offer_id: int) -> sqlite3.Row:
    rows = query(
        f"SELECT * FROM offers WHERE id = ? AND {ON_BOARD}", (offer_id, board_pattern(board))
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Offer not found")
    return rows[0]


@app.get("/")
def home() -> RedirectResponse:
    return RedirectResponse("/board_a/offers")


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots() -> str:
    return ROBOTS_TXT


# ---------------------------------------------------------------- board_a
# French site, simple list, "Suivant" link: /board_a/offers?page=2


@app.get("/board_a/offers")
def board_a_list(request: Request, page: int = 1):
    page = max(page, 1)
    offers, total, pages = list_page("board_a", page, PAGE_SIZE_A, LIST_COLUMNS)
    return templates.TemplateResponse(
        request,
        "board_a/list.html",
        {"offers": offers, "page": page, "pages": pages, "total": total},
    )


@app.get("/board_a/offers/{offer_id}")
def board_a_detail(request: Request, offer_id: int):
    return templates.TemplateResponse(
        request, "board_a/detail.html", {"offer": get_offer("board_a", offer_id)}
    )


# ---------------------------------------------------------------- board_b
# English site, cards in a grid, numbered pages: /board_b/jobs?p=2


@app.get("/board_b/jobs")
def board_b_list(request: Request, p: int = 1):
    p = max(p, 1)
    jobs, total, pages = list_page("board_b", p, PAGE_SIZE_B, LIST_COLUMNS)
    # Show a window of up to 5 page numbers around the current page.
    start = max(1, min(p - 2, pages - 4))
    page_numbers = list(range(start, min(pages, start + 4) + 1))
    return templates.TemplateResponse(
        request,
        "board_b/list.html",
        {"jobs": jobs, "p": p, "pages": pages, "total": total, "page_numbers": page_numbers},
    )


@app.get("/board_b/jobs/{offer_id}")
def board_b_detail(request: Request, offer_id: int):
    return templates.TemplateResponse(
        request, "board_b/detail.html", {"job": get_offer("board_b", offer_id)}
    )


# ---------------------------------------------------------------- board_c
# French site, table, "Voir plus" link with an opaque cursor, data in JSON-LD.


def encode_cursor(last_id: int) -> str:
    return base64.urlsafe_b64encode(f"id:{last_id}".encode()).decode().rstrip("=")


def decode_cursor(cursor: str) -> int:
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode()
        prefix, _, value = raw.partition(":")
        if prefix != "id":
            raise ValueError(raw)
        return int(value)
    except (binascii.Error, UnicodeDecodeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid cursor") from None


def job_posting_jsonld(offer: sqlite3.Row) -> str:
    """The offer as schema.org JobPosting JSON-LD, like real job sites publish."""
    data = {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "identifier": {"@type": "PropertyValue", "name": "board_c", "value": str(offer["id"])},
        "title": offer["title"],
        "description": offer["description_html"],
        "datePosted": offer["posted_at"][:10],
        "validThrough": offer["expires_at"],
        "employmentType": EMPLOYMENT_TYPES.get(offer["contract"], "OTHER"),
        "hiringOrganization": {"@type": "Organization", "name": offer["company"]},
    }
    if offer["city_display"]:  # some offers have no location at all
        data["jobLocation"] = {
            "@type": "Place",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": offer["city_display"],
                "addressCountry": offer["country"],
            },
        }
    # "</" is escaped so a description can never close the <script> tag early.
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


@app.get("/board_c/emplois")
def board_c_list(request: Request, cursor: str | None = None):
    after_id = decode_cursor(cursor) if cursor else 0
    rows = query(
        f"SELECT {LIST_COLUMNS} FROM offers WHERE {ON_BOARD} AND id > ? ORDER BY id LIMIT ?",
        (board_pattern("board_c"), after_id, PAGE_SIZE_C + 1),
    )
    has_more = len(rows) > PAGE_SIZE_C
    rows = rows[:PAGE_SIZE_C]
    next_cursor = encode_cursor(rows[-1]["id"]) if has_more else None
    return templates.TemplateResponse(
        request,
        "board_c/list.html",
        {"offers": rows, "next_cursor": next_cursor},
    )


@app.get("/board_c/emplois/{offer_id}")
def board_c_detail(request: Request, offer_id: int):
    offer = get_offer("board_c", offer_id)
    return templates.TemplateResponse(
        request,
        "board_c/detail.html",
        {"offer": offer, "jsonld": job_posting_jsonld(offer)},
    )