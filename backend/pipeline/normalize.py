"""Normalizer: turn raw scraped offers into clean, standard `Offer` objects.

Input : one JSON object per line, as written by a spider (city_raw, date_raw, description_html...).
Output: one `Offer` per line (JSON lines).

Usage, from the backend folder:
    python -m pipeline.normalize --raw data/board_a_raw.jsonl --out data/board_a_offers.jsonl \
        --reference 2026-10-01T12:00:00+00:00

--reference is the "today" that relative dates ("il y a 3 jours") are counted from.
For the fake boards it is the fixed date used by the generator. For real sources, leave it
out: each offer's own scraping time is used.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from pydantic import ValidationError

from common.geo import normalize_city
from common.schemas import Offer, normalize_text
from common.text import html_to_text

_MONTH_NAMES = {
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"],
    "en": ["january", "february", "march", "april", "may", "june", "july",
           "august", "september", "october", "november", "december"],
}
# "aout", "fevrier"... (accents removed) -> month number, for both languages
MONTHS = {
    normalize_text(name): number
    for names in _MONTH_NAMES.values()
    for number, name in enumerate(names, start=1)
}


def _parse_absolute(text: str) -> date | None:
    """Dates that name the day: 2026-09-14, 14/09/2026, 31 août 2026, August 31, 2026."""
    try:
        if m := re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})(?:[T ].*)?", text):
            return date(int(m[1]), int(m[2]), int(m[3]))
        if m := re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", text):
            return date(int(m[3]), int(m[2]), int(m[1]))  # day first: French and Moroccan sites
        if m := re.fullmatch(r"(\d{1,2})\s+([^\W\d_]+)\.?\s+(\d{4})", text):
            if month := MONTHS.get(normalize_text(m[2])):
                return date(int(m[3]), month, int(m[1]))
        if m := re.fullmatch(r"([^\W\d_]+)\.?\s+(\d{1,2}),?\s+(\d{4})", text):
            if month := MONTHS.get(normalize_text(m[1])):
                return date(int(m[3]), month, int(m[2]))
    except ValueError:  # impossible date such as 31/02/2026
        return None
    return None


def _parse_relative(text: str, today: date) -> date | None:
    """Dates counted back from today: "il y a 3 jours", "hier", "3 days ago", "today"."""
    key = normalize_text(text)  # lowercase, no accents, no punctuation
    if key in ("aujourd hui", "today"):
        return today
    if key in ("hier", "yesterday"):
        return today - timedelta(days=1)
    if m := re.fullmatch(r"(?:il y a (\d+) jours?|(\d+) days? ago)", key):
        return today - timedelta(days=int(m[1] or m[2]))
    return None


def parse_date(raw: str | None, reference_time: datetime) -> datetime | None:
    """Return the date at midnight UTC, or None if the text is not a date we understand."""
    if not raw:
        return None
    text = raw.strip()
    day = _parse_absolute(text) or _parse_relative(text, reference_time.astimezone(UTC).date())
    return datetime(day.year, day.month, day.day, tzinfo=UTC) if day else None


def normalize_offer(raw: dict, reference_time: datetime | None = None) -> Offer:
    """Build one clean Offer from one raw record. Raises KeyError/ValidationError if unusable."""
    fetched_at = (
        datetime.fromisoformat(raw["scraped_at"]) if raw.get("scraped_at") else datetime.now(UTC)
    )
    city, country = normalize_city(raw.get("city_raw"))
    return Offer(
        source=raw["board"],
        source_id=raw.get("source_id"),
        title=raw["title"].strip(),
        company=raw.get("company"),
        city=city,
        country=country,
        url=raw["url"],
        description=html_to_text(raw.get("description_html")),
        posted_at=parse_date(raw.get("date_raw"), reference_time or fetched_at),
        fetched_at=fetched_at,
        # Unknown = treated as synthetic: never show data as real by accident.
        # A connector for a real source must say is_synthetic = False explicitly.
        is_synthetic=bool(raw.get("is_synthetic", True)),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize raw scraped offers into Offer objects.")
    parser.add_argument("--raw", required=True, help="input .jsonl written by a spider")
    parser.add_argument("--out", required=True, help="output .jsonl of clean offers")
    parser.add_argument("--reference", help="ISO datetime used as 'today' for relative dates")
    args = parser.parse_args()
    reference = datetime.fromisoformat(args.reference) if args.reference else None

    written = skipped = with_city = with_country = with_date = 0
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(args.raw, encoding="utf-8") as src, open(out_path, "w", encoding="utf-8") as dst:
        for line_number, line in enumerate(src, start=1):
            if not line.strip():
                continue
            try:
                offer = normalize_offer(json.loads(line), reference)
            except (KeyError, ValueError, ValidationError) as exc:
                skipped += 1
                print(f"line {line_number} skipped: {exc}", file=sys.stderr)
                continue
            dst.write(offer.model_dump_json() + "\n")
            written += 1
            with_city += offer.city is not None
            with_country += offer.country is not None
            with_date += offer.posted_at is not None

    print(f"Normalized {written} offers to {args.out} ({skipped} skipped)")
    print(f"  with city: {with_city} | with country: {with_country} | with date: {with_date}")


if __name__ == "__main__":
    main()