from itertools import islice

from app.domain.services.fractional_index import indexes_above


def test_should_generate_increasing_keys_above_the_top_one() -> None:
    keys = list(islice(indexes_above("a5"), 70))
    assert keys[:3] == ["a501", "a502", "a503"]
    assert keys == sorted(keys)
    assert all(key > "a5" for key in keys)
    assert len(set(keys)) == len(keys)


def test_should_never_end_a_key_with_zero() -> None:
    assert not any(key.endswith("0") for key in indexes_above("a1"))


def test_should_offer_every_pair_of_digits() -> None:
    assert len(list(indexes_above("a1"))) == 62 * 61
