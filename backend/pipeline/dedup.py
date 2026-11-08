"""Deduplication: the same internship published on several boards becomes ONE offer.

Input : clean offers (one .jsonl per board, written by pipeline.normalize).
Output: merged offers, each remembering every board and link where it was seen.

Rule: same title + company + city (after normalization) = same offer.
(We tested a second pass for listings without a city: it found no extra duplicate and added
wrong merges, so it was removed. Simple and strict wins.)

Usage, from the backend folder:
    python -m pipeline.dedup --offers data/board_a_offers.jsonl data/board_b_offers.jsonl \
        data/board_c_offers.jsonl --out data/offers.jsonl
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from common.schemas import Offer


class Listing(BaseModel):
    """One place where an offer was seen."""

    source: str
    source_id: str | None = None
    url: str
    posted_at: datetime | None = None


class MergedOffer(Offer):
    """An offer plus every listing it was found in. Fields come from the most complete listing."""

    key: str
    listings: list[Listing]


def _merge(key: str, offers: list[Offer]) -> MergedOffer:
    ordered = sorted(offers, key=lambda o: (o.source, o.source_id or "", o.url))  # stable ties
    best = max(ordered, key=lambda o: (o.city is not None, o.posted_at is not None, len(o.description)))
    data = best.model_dump()

    for field in ("company", "city", "country"):  # fill gaps from the other listings
        if data[field] is None:
            data[field] = next((getattr(o, field) for o in ordered if getattr(o, field)), None)
    dates = [o.posted_at for o in ordered if o.posted_at]
    data["posted_at"] = min(dates) if dates else None
    data["fetched_at"] = max(o.fetched_at for o in ordered)
    data["is_synthetic"] = any(o.is_synthetic for o in ordered)  # one fake listing makes it fake

    listings = [
        Listing(source=o.source, source_id=o.source_id, url=o.url, posted_at=o.posted_at)
        for o in ordered
    ]
    return MergedOffer(**data, key=key, listings=listings)


def deduplicate(offers: list[Offer]) -> list[MergedOffer]:
    groups: dict[str, list[Offer]] = defaultdict(list)
    for offer in offers:
        groups[offer.dedup_key].append(offer)
    return sorted((_merge(key, members) for key, members in groups.items()), key=lambda m: m.key)


def _pairs(count: int) -> int:
    return count * (count - 1) // 2


def evaluate_grouping(merged: list[MergedOffer]) -> dict:
    """Score the grouping. Only valid for the fake boards, where source_id is the SAME number
    on every board for the same offer, so it tells us the truth."""
    all_ids = Counter(item.source_id for m in merged for item in m.listings)
    truth_pairs = sum(_pairs(count) for count in all_ids.values())
    predicted_pairs = sum(_pairs(len(m.listings)) for m in merged)
    correct_pairs = sum(
        _pairs(count)
        for m in merged
        for count in Counter(item.source_id for item in m.listings).values()
    )
    ids_per_group = [len({item.source_id for item in m.listings}) for m in merged]
    groups_of_each_id = Counter(i for m in merged for i in {item.source_id for item in m.listings})
    return {
        "listings": sum(all_ids.values()),
        "distinct_offers": len(all_ids),
        "after_dedup": len(merged),
        "true_duplicate_pairs": truth_pairs,
        "found_duplicate_pairs": correct_pairs,
        "wrong_pairs": predicted_pairs - correct_pairs,
        "wrong_merges": sum(count > 1 for count in ids_per_group),  # groups mixing different offers
        "split_offers": sum(count > 1 for count in groups_of_each_id.values()),  # one offer, many groups
        "precision": correct_pairs / predicted_pairs if predicted_pairs else 1.0,
        "recall": correct_pairs / truth_pairs if truth_pairs else 1.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge offers published on several boards.")
    parser.add_argument("--offers", nargs="+", required=True, help="clean .jsonl files, one per board")
    parser.add_argument("--out", required=True, help="output .jsonl of merged offers")
    args = parser.parse_args()

    offers = []
    for path in args.offers:
        with open(path, encoding="utf-8") as file:
            offers += [Offer.model_validate_json(line) for line in file if line.strip()]

    merged = deduplicate(offers)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as file:
        for item in merged:
            file.write(item.model_dump_json() + "\n")

    on_several = sum(len(m.listings) > 1 for m in merged)
    print(f"{len(offers)} listings -> {len(merged)} offers ({on_several} seen on several boards)")
    print(f"  saved to {args.out}")

    if all(o.is_synthetic for o in offers):  # fake data: the source_id gives us the truth
        r = evaluate_grouping(merged)
        print(f"\nCompared with the truth ({r['distinct_offers']} distinct offers really exist):")
        print(f"  duplicates found : {r['found_duplicate_pairs']} of {r['true_duplicate_pairs']}"
              f"  (recall {r['recall']:.1%})")
        print(f"  wrong merges     : {r['wrong_pairs']} pairs in {r['wrong_merges']} groups"
              f"  (precision {r['precision']:.1%})")
        print(f"  offers split in several groups: {r['split_offers']}")


if __name__ == "__main__":
    main()