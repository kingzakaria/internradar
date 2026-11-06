"""Evaluate the pipeline: compare cleaned offers with the generator's ground truth.

The generator keeps the true city, date and description of every fake offer in SQLite.
This script checks how many of them the spider + normalizer recovered correctly.

Usage, from the backend folder:
    python -m pipeline.evaluate --offers data/board_a_offers.jsonl --truth data/mock_jobs.db
    python -m pipeline.evaluate --offers ... --truth ... --fail-under 0.95   # exit code 1 if lower
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from contextlib import closing
from datetime import datetime

# Order of the report. Names not listed here are printed after these.
REPORT_ORDER = [
    "title",
    "company",
    "city (when the page shows one)",
    "country (when the page shows a city)",
    "city left empty (when the page shows none)",
    "date (exact day, absolute formats)",
    "date (within 1 day, relative formats)",
    "description keeps the original text",
    "description exactly equal (no extra text)",
    "date (exact day, relative formats)",
]
# Reported but never counted against --fail-under: the page itself does not hold this
# information ("il y a 3 jours" cannot tell which hour of the day it was).
INFORMATIONAL = {"date (exact day, relative formats)"}
SENTENCE_END = re.compile(r"(?<=[.?!])\s+")


def load_truth(db_path: str) -> dict[str, sqlite3.Row]:
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM offers").fetchall()
    return {str(row["id"]): row for row in rows}


def load_offers(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def _day(value: str | None):
    return datetime.fromisoformat(value).date() if value else None


def evaluate(offers: list[dict], truth: dict[str, sqlite3.Row]) -> tuple[dict[str, list[int]], int]:
    """Return ({metric: [correct, total]}, number of offers with no ground truth)."""
    scores: dict[str, list[int]] = {}
    unmatched = 0

    def score(name: str, correct: bool) -> None:
        entry = scores.setdefault(name, [0, 0])
        entry[0] += bool(correct)
        entry[1] += 1

    for offer in offers:
        real = truth.get(str(offer.get("source_id")))
        if real is None:
            unmatched += 1
            continue

        score("title", offer["title"] == real["title"])
        score("company", offer["company"] == real["company"])

        if real["city_display"]:  # the page showed a city (maybe misspelled)
            score("city (when the page shows one)", offer["city"] == real["city"])
            score("country (when the page shows a city)", offer["country"] == real["country"])
        else:  # nothing on the page: the right answer is "no city", not a guess
            score("city left empty (when the page shows none)", offer["city"] is None)

        got, expected = _day(offer["posted_at"]), _day(real["posted_at"])
        if real["date_style"] == "relative":
            score("date (within 1 day, relative formats)",
                  got is not None and abs((got - expected).days) <= 1)
            score("date (exact day, relative formats)", got == expected)
        else:
            score("date (exact day, absolute formats)", got == expected)

        text = offer["description"]
        sentences = [s for s in SENTENCE_END.split(real["description"]) if s]
        score("description keeps the original text", all(s in text for s in sentences))
        if real["description_style"] != "bullets":  # bullets add the skills list on purpose
            score("description exactly equal (no extra text)", text == real["description"])

    return scores, unmatched


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare cleaned offers with the ground truth.")
    parser.add_argument("--offers", required=True, help=".jsonl written by pipeline.normalize")
    parser.add_argument("--truth", required=True, help="SQLite database made by the generator")
    parser.add_argument("--fail-under", type=float, help="exit with code 1 if a metric is lower")
    args = parser.parse_args()

    offers = load_offers(args.offers)
    scores, unmatched = evaluate(offers, load_truth(args.truth))

    print(f"Compared {len(offers) - unmatched} offers with the ground truth", end="")
    print(f" ({unmatched} without ground truth, ignored)" if unmatched else "")
    print()
    names = [n for n in REPORT_ORDER if n in scores] + [n for n in scores if n not in REPORT_ORDER]
    width = max((len(n) for n in names), default=0)
    failed = []
    for name in names:
        correct, total = scores[name]
        rate = correct / total
        note = "  (informational)" if name in INFORMATIONAL else ""
        print(f"{name:<{width}}  {correct:>4}/{total:<4}  {rate:6.1%}{note}")
        if args.fail_under is not None and name not in INFORMATIONAL and rate < args.fail_under:
            failed.append(name)

    if failed:
        print(f"\nBelow {args.fail_under:.0%}: {', '.join(failed)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()