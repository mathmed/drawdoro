import pytest

from app.domain.errors.domain_errors import InvalidInputError
from app.domain.services.gallery_item_labels import (
    normalize_gallery_item_description,
    normalize_gallery_item_tags,
)


def test_should_lower_case_trim_and_collapse_spaces_in_tags() -> None:
    assert normalize_gallery_item_tags(["  Cloud \t  Native ", "K8S"]) == ["cloud native", "k8s"]


def test_should_drop_empty_and_repeated_tags_keeping_the_first() -> None:
    assert normalize_gallery_item_tags(["aws", " ", "AWS", "", "gcp", "aws "]) == ["aws", "gcp"]


def test_should_accept_technology_names() -> None:
    tags = ["c++", "c#", "ci/cd", "node.js", "event-driven", "snake_case", "café"]
    assert normalize_gallery_item_tags(tags) == tags


@pytest.mark.parametrize("tag", ["<script>", "a;b", "a&b", "back\\slash", 'quote"', "emoji 🚀"])
def test_should_reject_tags_with_unsupported_characters(tag: str) -> None:
    with pytest.raises(InvalidInputError, match="unsupported characters"):
        normalize_gallery_item_tags([tag])


def test_should_accept_tags_up_to_the_length_limit() -> None:
    assert normalize_gallery_item_tags(["a" * 32]) == ["a" * 32]


def test_should_reject_tags_over_the_length_limit() -> None:
    with pytest.raises(InvalidInputError, match="at most 32 characters"):
        normalize_gallery_item_tags(["a" * 33])


def test_should_accept_up_to_ten_tags() -> None:
    tags = [f"tag{index}" for index in range(10)]
    assert normalize_gallery_item_tags(tags) == tags


def test_should_reject_more_than_ten_distinct_tags() -> None:
    with pytest.raises(InvalidInputError, match="at most 10 tags"):
        normalize_gallery_item_tags([f"tag{index}" for index in range(11)])


def test_should_count_tags_after_removing_repeats() -> None:
    tags = [f"tag{index}" for index in range(10)] + ["TAG0", "tag1"]
    assert len(normalize_gallery_item_tags(tags)) == 10


def test_should_trim_the_description() -> None:
    assert normalize_gallery_item_description("  Logo of the queue  ") == "Logo of the queue"


@pytest.mark.parametrize("raw", [None, "", "   "])
def test_should_turn_a_missing_or_blank_description_into_none(raw: str | None) -> None:
    assert normalize_gallery_item_description(raw) is None


def test_should_accept_a_description_up_to_the_limit() -> None:
    assert normalize_gallery_item_description("a" * 500) == "a" * 500


def test_should_reject_a_description_over_the_limit() -> None:
    with pytest.raises(InvalidInputError, match="at most 500 characters"):
        normalize_gallery_item_description("a" * 501)
