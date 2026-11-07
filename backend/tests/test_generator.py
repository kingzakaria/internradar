import re

from mock_jobboard import generator

INTERNSHIP_WORDS = re.compile(r"stage|stagiaire|intern|pfe|alternance")


def test_same_seed_gives_the_same_offers():
    assert generator.generate_records(50, seed_value=1) == generator.generate_records(50, seed_value=1)


def test_different_seeds_give_different_offers():
    assert generator.generate_records(50, seed_value=1) != generator.generate_records(50, seed_value=2)


def test_ids_are_unique_and_sequential(records):
    assert [r.id for r in records] == list(range(1, len(records) + 1))


def test_only_internships_have_internship_words_in_the_title(records):
    for record in records:
        assert bool(INTERNSHIP_WORDS.search(record.title.lower())) == record.is_internship, record.title


def test_every_offer_is_synthetic(records):
    assert all(record.to_offer().is_synthetic for record in records)


def test_some_offers_are_published_on_two_boards(records):
    duplicated = sum(len(record.boards) > 1 for record in records)
    assert 0.10 <= duplicated / len(records) <= 0.26


def test_expiry_flag_matches_the_deadline(records):
    for record in records:
        assert record.is_expired == (record.expires_at < generator.REFERENCE_TIME)


def test_relative_dates_are_only_used_for_recent_offers(records):
    for record in records:
        if record.date_style == "relative":
            assert (generator.REFERENCE_TIME - record.posted_at).days <= generator.MAX_RELATIVE_DAYS


def test_messy_city_is_missing_or_a_known_spelling(records):
    from mock_jobboard import seed

    for record in records:
        allowed = {"", record.city, *seed.CITY_ALIASES.get(record.city, [])}
        assert record.city_display in allowed