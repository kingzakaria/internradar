"""Mock job board websites (board_a, board_b), served from the fake offers in SQLite.

Everything shown here is SYNTHETIC. The sites exist only so we can practise
scraping on our own machine, with no legal risk.

Run from the backend folder:
    python -m uvicorn mock_jobboard.server:app --port 8000
Then open http://localhost:8000/board_a/offers or http://localhost:8000/board_b/jobs
"""

from __future__ import annotations

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
TEMPLATES_DIR = Path(__file__).parent / "templates"

# Rules for crawlers. Our spider must read this file and obey it.
ROBOTS_TXT = """User-agent: *
Allow: /board_a/
Allow: /board_b/
Disallow: /admin/
Crawl-delay: 1
"""

app = FastAPI(title="Mock job boards")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# "boards" is stored like "board_a, board_c": this matches one board name in it.
ON_BOARD = "(', ' || boards || ', ') LIKE ?"


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


LIST_COLUMNS = "id, title, company, city_display, date_display, is_expired"


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