"""Mock job board website (board_a), served from the fake offers in SQLite.

Everything shown here is SYNTHETIC. The site exists only so we can practise
scraping on our own machine, with no legal risk.

Run from the backend folder:
    python -m uvicorn mock_jobboard.server:app --port 8000
Then open http://localhost:8000/board_a/offers
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
PAGE_SIZE = 20
TEMPLATES_DIR = Path(__file__).parent / "templates"

# Rules for crawlers. Our spider must read this file and obey it.
ROBOTS_TXT = """User-agent: *
Allow: /board_a/
Disallow: /admin/
Crawl-delay: 1
"""

app = FastAPI(title="Mock job board")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# "boards" is stored like "board_a, board_c": this matches one board name in it.
ON_BOARD = "(', ' || boards || ', ') LIKE ?"


def board_pattern(board: str) -> str:
    return f"%, {board}, %"


def query(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(sql, params).fetchall()


@app.get("/")
def home() -> RedirectResponse:
    return RedirectResponse("/board_a/offers")


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots() -> str:
    return ROBOTS_TXT


@app.get("/board_a/offers")
def board_a_list(request: Request, page: int = 1):
    page = max(page, 1)
    pattern = board_pattern("board_a")
    total = query(f"SELECT COUNT(*) FROM offers WHERE {ON_BOARD}", (pattern,))[0][0]
    pages = max(1, -(-total // PAGE_SIZE))  # ceiling division
    offers = query(
        "SELECT id, title, company, city_display, date_display, is_expired "
        f"FROM offers WHERE {ON_BOARD} ORDER BY id LIMIT ? OFFSET ?",
        (pattern, PAGE_SIZE, (page - 1) * PAGE_SIZE),
    )
    return templates.TemplateResponse(
        request,
        "board_a/list.html",
        {"offers": offers, "page": page, "pages": pages, "total": total},
    )


@app.get("/board_a/offers/{offer_id}")
def board_a_detail(request: Request, offer_id: int):
    rows = query(
        f"SELECT * FROM offers WHERE id = ? AND {ON_BOARD}",
        (offer_id, board_pattern("board_a")),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Offre introuvable")
    return templates.TemplateResponse(request, "board_a/detail.html", {"offer": rows[0]})