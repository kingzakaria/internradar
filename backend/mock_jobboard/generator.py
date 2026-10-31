"""Generate fake job offers from seed.py and save them in a SQLite database.

The output is deterministic: the same --seed always gives the same offers.
Every offer is SYNTHETIC (is_synthetic=True once converted to an Offer).

Usage, from the backend folder:
    python -m mock_jobboard.generator --count 2000 --seed 42 --db data/mock_jobs.db
"""

from __future__ import annotations

import argparse
import random
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from common.schemas import Offer
from mock_jobboard import seed

BASE_URL = "http://localhost:8000"
# Fixed "today" so the generated dates do not change between runs.
REFERENCE_TIME = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
COMPANY_POOL_SIZE = 300
BOARDS = ("board_a", "board_b", "board_c")
DUPLICATE_RATE = 0.18  # share of offers that are also published on a second board
INTERNSHIP_CONTRACTS = {"stage", "pfe", "alternance"}


@dataclass(frozen=True)
class FakeRecord:
    """Ground truth about one fake offer (what the mock website will show)."""

    id: int
    title: str
    company: str
    city: str
    country: str
    language: str
    family: str
    contract: str
    is_internship: bool
    duration_months: int | None
    skills: tuple[str, ...]
    description: str
    posted_at: datetime
    boards: tuple[str, ...]

    def to_offer(self) -> Offer:
        """Convert to the standard Offer format used by the whole project."""
        return Offer(
            source="synthetic",
            source_id=str(self.id),
            title=self.title,
            company=self.company,
            city=self.city,
            country=self.country,
            url=f"{BASE_URL}/offers/{self.id}",
            description=self.description,
            posted_at=self.posted_at,
            is_synthetic=True,
        )


def build_company_pool(rng: random.Random) -> list[str]:
    """Invent a fixed pool of fictional companies, so companies repeat across offers."""
    names: set[str] = set()
    while len(names) < COMPANY_POOL_SIZE:
        prefix = rng.choice(seed.COMPANY_PREFIXES)
        suffix = rng.choice(seed.COMPANY_SUFFIXES)
        names.add(f"{prefix} {suffix}")
    return sorted(names)  # sorted: a set has no stable order between runs


def _duration(rng: random.Random, contract: str, language: str) -> tuple[int | None, str]:
    if contract in ("stage", "pfe"):
        months = rng.choices(
            [d for d, _ in seed.DURATIONS], weights=[w for _, w in seed.DURATIONS]
        )[0]
    elif contract == "alternance":
        months = rng.choice([12, 24])
    elif contract == "cdd":
        months = rng.choice([6, 9, 12])
    else:  # cdi
        return None, ("durée indéterminée" if language == "fr" else "permanent")
    return months, seed.DURATION_TEXT[language].format(n=months)


def pick_boards(rng: random.Random) -> tuple[str, ...]:
    """Choose the board(s) where an offer is published (sometimes two)."""
    first = rng.choice(BOARDS)
    if rng.random() < DUPLICATE_RATE:
        second = rng.choice([b for b in BOARDS if b != first])
        return tuple(sorted((first, second)))
    return (first,)


def generate_records(count: int, seed_value: int = 42) -> list[FakeRecord]:
    rng = random.Random(seed_value)
    board_rng = random.Random(seed_value + 1)  # separate generator: keeps old data unchanged
    companies = build_company_pool(rng)
    families = list(seed.JOB_FAMILIES.items())
    city_weights = [weight for _, _, weight in seed.CITIES]
    contract_weights = [weight for _, _, weight in seed.CONTRACTS]

    records: list[FakeRecord] = []
    for offer_id in range(1, count + 1):
        city, country, _ = rng.choices(seed.CITIES, weights=city_weights)[0]
        language_weights = seed.LANGUAGE_WEIGHTS[country]
        language = rng.choices(
            list(language_weights), weights=list(language_weights.values())
        )[0]

        family_name, family = rng.choice(families)
        base_title = rng.choice(family["titles_fr" if language == "fr" else "titles_en"])
        contract, is_internship, _ = rng.choices(seed.CONTRACTS, weights=contract_weights)[0]
        title = rng.choice(seed.TITLE_FORMATS[contract][language]).format(title=base_title)

        company = rng.choice(companies)
        skills = tuple(rng.sample(family["skills"], k=min(len(family["skills"]), rng.randint(3, 5))))
        months, duration_text = _duration(rng, contract, language)

        description = rng.choice(seed.DESCRIPTION_TEMPLATES[language]).format(
            company=company,
            city=city,
            title=base_title,
            skills=", ".join(skills),
            main_skill=skills[0],
            education=rng.choice(seed.EDUCATION[language]),
            duration=duration_text,
        )
        posted_at = REFERENCE_TIME - timedelta(
            days=rng.randint(0, 60), hours=rng.randint(0, 23), minutes=rng.randint(0, 59)
        )

        records.append(
            FakeRecord(
                id=offer_id,
                title=title,
                company=company,
                city=city,
                country=country,
                language=language,
                family=family_name,
                contract=contract,
                is_internship=is_internship,
                duration_months=months,
                skills=skills,
                description=description,
                posted_at=posted_at,
                boards=pick_boards(board_rng),
            )
        )
    return records


def save_to_sqlite(records: list[FakeRecord], db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("DROP TABLE IF EXISTS offers")
        conn.execute(
            """
            CREATE TABLE offers (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                city TEXT NOT NULL,
                country TEXT NOT NULL,
                language TEXT NOT NULL,
                family TEXT NOT NULL,
                contract TEXT NOT NULL,
                is_internship INTEGER NOT NULL,
                duration_months INTEGER,
                skills TEXT NOT NULL,
                description TEXT NOT NULL,
                posted_at TEXT NOT NULL,
                boards TEXT NOT NULL
            )
            """
        )
        conn.executemany(
            "INSERT INTO offers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    r.id, r.title, r.company, r.city, r.country, r.language, r.family,
                    r.contract, int(r.is_internship), r.duration_months,
                    ", ".join(r.skills), r.description, r.posted_at.isoformat(),
                    ", ".join(r.boards),
                )
                for r in records
            ],
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate fake job offers (synthetic data).")
    parser.add_argument("--count", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--db", default="data/mock_jobs.db")
    args = parser.parse_args()

    records = generate_records(args.count, args.seed)
    save_to_sqlite(records, args.db)

    internships = sum(r.is_internship for r in records)
    countries = Counter(r.country for r in records)
    duplicated = sum(len(r.boards) > 1 for r in records)
    print(f"Saved {len(records)} synthetic offers to {args.db}")
    print(f"  internships: {internships} ({internships / len(records):.0%})")
    print(f"  by country: {dict(countries)}")
    print(f"  on two boards (duplicates): {duplicated} ({duplicated / len(records):.0%})")


if __name__ == "__main__":
    main()