"""Generate fake job offers from seed.py and save them in a SQLite database.

The output is deterministic: the same --seed always gives the same offers.
Every offer is SYNTHETIC (is_synthetic=True once converted to an Offer).

Usage, from the backend folder:
    python -m mock_jobboard.generator --count 2000 --seed 42 --db data/mock_jobs.db
"""

from __future__ import annotations

import argparse
import html
import random
import re
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
MISSING_CITY_RATE = 0.05  # share of offers shown without any city
CITY_VARIANT_RATE = 0.10  # share of offers where the city is spelled differently
INTERNSHIP_CONTRACTS = {"stage", "pfe", "alternance"}

# Date styles a board can use, with weights.
DATE_STYLES = [("iso", 25), ("slash", 30), ("long", 25), ("relative", 20)]
MAX_RELATIVE_DAYS = 30  # older offers never use "3 days ago" style
FR_MONTHS = [
    "janvier", "février", "mars", "avril", "mai", "juin", "juillet",
    "août", "septembre", "octobre", "novembre", "décembre",
]
EN_MONTHS = [
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
]

# How a board formats the description, with weights.
DESCRIPTION_STYLES = [("plain", 25), ("paragraphs", 30), ("bullets", 25), ("noisy", 20)]


@dataclass(frozen=True)
class FakeRecord:
    """Ground truth about one fake offer (what the mock website will show)."""

    id: int
    title: str
    company: str
    city: str  # clean city = ground truth
    country: str
    language: str
    family: str
    contract: str
    is_internship: bool
    duration_months: int | None
    skills: tuple[str, ...]
    description: str  # clean text = ground truth
    posted_at: datetime  # real date = ground truth
    boards: tuple[str, ...]
    city_display: str  # messy city shown on the website ("" = missing)
    date_style: str  # iso, slash, long or relative
    date_display: str  # date text shown on the website
    description_style: str  # plain, paragraphs, bullets or noisy
    description_html: str  # description as the website shows it

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


def messy_city(rng: random.Random, city: str) -> str:
    """City as a real board might write it: sometimes missing, sometimes misspelled."""
    roll = rng.random()
    if roll < MISSING_CITY_RATE:
        return ""
    aliases = seed.CITY_ALIASES.get(city)
    if aliases and roll < MISSING_CITY_RATE + CITY_VARIANT_RATE:
        return rng.choice(aliases)
    return city


def messy_date(rng: random.Random, posted_at: datetime, language: str) -> tuple[str, str]:
    """Return (style, text): the date as a board might display it."""
    days_ago = (REFERENCE_TIME - posted_at).days
    style = rng.choices(
        [s for s, _ in DATE_STYLES], weights=[w for _, w in DATE_STYLES]
    )[0]
    if style == "relative" and days_ago > MAX_RELATIVE_DAYS:
        style = "slash"  # "il y a 52 jours" looks unnatural

    if style == "iso":
        text = posted_at.strftime("%Y-%m-%d")
    elif style == "slash":
        text = posted_at.strftime("%d/%m/%Y")
    elif style == "long":
        if language == "fr":
            text = f"{posted_at.day} {FR_MONTHS[posted_at.month - 1]} {posted_at.year}"
        else:
            text = f"{EN_MONTHS[posted_at.month - 1]} {posted_at.day}, {posted_at.year}"
    else:  # relative
        if days_ago == 0:
            text = "aujourd'hui" if language == "fr" else "today"
        elif days_ago == 1:
            text = "hier" if language == "fr" else "yesterday"
        elif language == "fr":
            text = f"il y a {days_ago} jours"
        else:
            text = f"{days_ago} days ago"
    return style, text


def messy_description(
    rng: random.Random, description: str, skills: tuple[str, ...], company: str
) -> tuple[str, str]:
    """Return (style, html): the description as a board might display it."""
    style = rng.choices(
        [s for s, _ in DESCRIPTION_STYLES], weights=[w for _, w in DESCRIPTION_STYLES]
    )[0]
    # html.escape turns ' into &#x27; like many real pages do.
    sentences = [html.escape(s) for s in re.split(r"(?<=[.?!])\s+", description) if s]

    if style == "plain":
        body = "\n   " + "   ".join(sentences) + "\n  "
    elif style == "paragraphs":
        body = "".join(f"<p>{s}</p>" for s in sentences)
    elif style == "bullets":
        items = "".join(f"<li>{html.escape(skill)}</li>" for skill in skills)
        rest = " ".join(sentences[1:])
        body = f"<p>{sentences[0]}</p><ul>{items}</ul><p>{rest}</p>"
    else:  # noisy
        joined = "<br>&nbsp;".join(sentences)
        joined = joined.replace(company, f"<strong>{company}</strong>")
        body = f'<div class="desc">{joined}</div>'
    return style, body


def generate_records(count: int, seed_value: int = 42) -> list[FakeRecord]:
    rng = random.Random(seed_value)
    # Separate generators for the "mess": they keep the clean data unchanged.
    board_rng = random.Random(seed_value + 1)
    mess_rng = random.Random(seed_value + 2)
    date_rng = random.Random(seed_value + 3)
    html_rng = random.Random(seed_value + 4)
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
        date_style, date_display = messy_date(date_rng, posted_at, language)
        description_style, description_html = messy_description(
            html_rng, description, skills, company
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
                city_display=messy_city(mess_rng, city),
                date_style=date_style,
                date_display=date_display,
                description_style=description_style,
                description_html=description_html,
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
                boards TEXT NOT NULL,
                city_display TEXT NOT NULL,
                date_style TEXT NOT NULL,
                date_display TEXT NOT NULL,
                description_style TEXT NOT NULL,
                description_html TEXT NOT NULL
            )
            """
        )
        conn.executemany(
            "INSERT INTO offers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    r.id, r.title, r.company, r.city, r.country, r.language, r.family,
                    r.contract, int(r.is_internship), r.duration_months,
                    ", ".join(r.skills), r.description, r.posted_at.isoformat(),
                    ", ".join(r.boards), r.city_display, r.date_style, r.date_display,
                    r.description_style, r.description_html,
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

    total = len(records)
    internships = sum(r.is_internship for r in records)
    countries = Counter(r.country for r in records)
    duplicated = sum(len(r.boards) > 1 for r in records)
    missing = sum(r.city_display == "" for r in records)
    variants = sum(r.city_display not in ("", r.city) for r in records)
    date_styles = Counter(r.date_style for r in records)
    desc_styles = Counter(r.description_style for r in records)
    print(f"Saved {total} synthetic offers to {args.db}")
    print(f"  internships: {internships} ({internships / total:.0%})")
    print(f"  by country: {dict(countries)}")
    print(f"  on two boards (duplicates): {duplicated} ({duplicated / total:.0%})")
    print(f"  city missing: {missing} | city spelled differently: {variants}")
    print(f"  date styles: {dict(date_styles)}")
    print(f"  description styles: {dict(desc_styles)}")
    sample = next(r for r in records if r.description_style == "noisy")
    print(f"  example (noisy): {sample.description_html[:110]!r}")


if __name__ == "__main__":
    main()