import pytest

from app.domain.constants.gallery import GALLERY_MAX_NAME_LENGTH
from app.domain.errors.domain_errors import InvalidInputError
from app.domain.services.gallery_item_name import normalize_gallery_item_name

TOO_LONG = f"^Name must have 1 to {GALLERY_MAX_NAME_LENGTH} characters$"


def test_should_trim_the_name() -> None:
    assert normalize_gallery_item_name("  AWS logo ") == "AWS logo"


def test_should_accept_a_name_of_the_maximum_length() -> None:
    name = "a" * GALLERY_MAX_NAME_LENGTH
    assert normalize_gallery_item_name(f" {name} ") == name


@pytest.mark.parametrize("raw", ["", "   ", "a" * (GALLERY_MAX_NAME_LENGTH + 1)])
def test_should_reject_an_empty_or_too_long_name(raw: str) -> None:
    with pytest.raises(InvalidInputError, match=TOO_LONG):
        normalize_gallery_item_name(raw)
