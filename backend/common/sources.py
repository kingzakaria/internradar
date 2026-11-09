"""Source registry: the list of every place InternRadar may (or may not) get offers from.

Default-deny: a source that is not listed, or not marked "approved", cannot run.
Every spider and connector calls require_approved(<its id>) before it does anything.

Statuses:
  approved : we may use it (our own fake boards, or an official API whose terms we verified)
  pending  : planned, terms NOT verified yet -> cannot run until someone checks and approves it
  blocked  : we decided never to use it (terms forbid automated access, or too risky)

Generate the public list for the README:
    python -m common.sources > SOURCES.md
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel


class SourceNotApproved(Exception):
    """Raised when code tries to use a source that is unknown, pending or blocked."""


class Source(BaseModel):
    id: str
    name: str
    kind: Literal["mock_board", "official_api", "public_ats", "website"]
    status: Literal["approved", "pending", "blocked"]
    terms_url: str | None = None  # where the rules of the source are written
    checked_on: date | None = None  # when a human last read those rules (None = never)
    notes: str = ""


SOURCES: list[Source] = [
    # --- our own fake boards: we own them, scraping them is the safe practice ground -----------
    Source(id="board_a", name="Mock board A", kind="mock_board", status="approved",
           notes="Our own fake site (French, list + pages). Synthetic data."),
    Source(id="board_b", name="Mock board B", kind="mock_board", status="approved",
           notes="Our own fake site (English, cards). Synthetic data."),
    Source(id="board_c", name="Mock board C", kind="mock_board", status="approved",
           notes="Our own fake site (table + JSON-LD + cursor). Synthetic data."),
    # --- real sources, official/public interfaces only: NOT usable until a human verifies -------
    Source(id="france_travail", name="France Travail (Offres d'emploi API)", kind="official_api",
           status="pending", notes="Official API with a free key. Verify terms and Morocco coverage."),
    Source(id="la_bonne_alternance", name="La Bonne Alternance API", kind="official_api",
           status="pending", notes="Official API for internships and work-study in France."),
    Source(id="jooble", name="Jooble API", kind="official_api", status="pending",
           notes="Partner API with a key. Verify terms and Morocco coverage."),
    Source(id="careerjet", name="Careerjet API", kind="official_api", status="pending",
           notes="Partner API with a key. Verify terms and Morocco coverage."),
    Source(id="greenhouse", name="Greenhouse public job boards", kind="public_ats", status="pending",
           notes="Public JSON endpoint per company. Verify terms before use."),
    Source(id="lever", name="Lever public postings", kind="public_ats", status="pending",
           notes="Public JSON endpoint per company. Verify terms before use."),
    # --- decided never: no code for them exists in this project ---------------------------------
    Source(id="linkedin", name="LinkedIn", kind="website", status="blocked",
           notes="Not scraped. Policy decision: automated access is against the site rules."),
    Source(id="indeed", name="Indeed", kind="website", status="blocked",
           notes="Not scraped. Policy decision: automated access is against the site rules."),
    Source(id="glassdoor", name="Glassdoor", kind="website", status="blocked",
           notes="Not scraped. Policy decision: automated access is against the site rules."),
]

_BY_ID = {source.id: source for source in SOURCES}
assert len(_BY_ID) == len(SOURCES), "duplicate source id in the registry"


def get_source(source_id: str) -> Source | None:
    return _BY_ID.get(source_id)


def approved_sources() -> list[Source]:
    return [source for source in SOURCES if source.status == "approved"]


def require_approved(source_id: str) -> Source:
    """Return the source if it may run, otherwise raise. Unknown means NO."""
    source = get_source(source_id)
    if source is None:
        raise SourceNotApproved(f"'{source_id}' is not in the source registry")
    if source.status != "approved":
        raise SourceNotApproved(f"'{source_id}' is {source.status}, only approved sources can run")
    return source


def to_markdown() -> str:
    lines = [
        "# Sources",
        "",
        "InternRadar is default-deny: only `approved` sources can run (see `backend/common/sources.py`).",
        "",
        "| Source | Type | Status | Last checked | Notes |",
        "|---|---|---|---|---|",
    ]
    for s in SOURCES:
        checked = s.checked_on.isoformat() if s.checked_on else "-"
        lines.append(f"| {s.name} | {s.kind} | {s.status} | {checked} | {s.notes} |")
    lines += ["", "`pending` = planned, terms not verified yet, cannot run.",
              "`blocked` = never used, and no code for it exists in this project.", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    print(to_markdown())