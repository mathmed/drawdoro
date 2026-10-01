import pytest

from app.domain.constants.comments import (
    COMMENT_CONTENT_MAX_LENGTH,
    COMMENT_ELEMENT_ID_MAX_LENGTH,
)
from app.domain.errors.domain_errors import InvalidInputError
from app.domain.services.comment_content import normalize_comment_content, normalize_element_id


def test_should_keep_markup_as_plain_text() -> None:
    text = "<script>alert('x')</script> **bold** & <b>Service</b>"
    assert normalize_comment_content(text) == text


def test_should_trim_surrounding_whitespace() -> None:
    assert normalize_comment_content("  \n Missing the queue \t\n") == "Missing the queue"


def test_should_keep_line_breaks_and_tabs_inside_the_text() -> None:
    assert normalize_comment_content("a\n\tb") == "a\n\tb"


def test_should_unify_line_endings() -> None:
    assert normalize_comment_content("a\r\nb\rc") == "a\nb\nc"


def test_should_drop_control_characters_that_cannot_be_stored_or_shown() -> None:
    assert normalize_comment_content("a\x00b\x07c\x1bd\x7fe") == "abcde"


@pytest.mark.parametrize(
    "control",
    [
        chr(code)
        for code in (0x202A, 0x202B, 0x202C, 0x202D, 0x202E, 0x2066, 0x2067, 0x2068, 0x2069)
    ],
)
def test_should_drop_bidirectional_controls(control: str) -> None:
    assert normalize_comment_content(f"safe{control}txt") == "safetxt"


def test_should_keep_other_unicode_text() -> None:
    assert normalize_comment_content("Falta o serviço 🚀 — ok") == "Falta o serviço 🚀 — ok"


@pytest.mark.parametrize("blank", ["", "   ", "\n\t", "\x00\x01"])
def test_should_reject_comments_without_text(blank: str) -> None:
    with pytest.raises(InvalidInputError, match="^A comment needs some text$"):
        normalize_comment_content(blank)


def test_should_accept_the_longest_allowed_comment() -> None:
    text = "x" * COMMENT_CONTENT_MAX_LENGTH
    assert normalize_comment_content(f"  {text}  ") == text


def test_should_reject_comments_over_the_limit() -> None:
    too_long = COMMENT_CONTENT_MAX_LENGTH + 1
    with pytest.raises(InvalidInputError) as error:
        normalize_comment_content("x" * too_long)
    assert error.value.message == (
        f"A comment can have at most {COMMENT_CONTENT_MAX_LENGTH} characters "
        f"(this one has {too_long})"
    )


def test_should_check_the_limit_after_cleaning_the_text() -> None:
    text = "x" * COMMENT_CONTENT_MAX_LENGTH
    assert normalize_comment_content(text + "\x00" * 10) == text


@pytest.mark.parametrize("missing", [None, "", "   "])
def test_should_anchor_to_the_whole_diagram_without_element(missing: str | None) -> None:
    assert normalize_element_id(missing) is None


def test_should_trim_the_element_id() -> None:
    assert normalize_element_id("  shape:abc ") == "shape:abc"


def test_should_accept_the_longest_element_id() -> None:
    element_id = "s" * COMMENT_ELEMENT_ID_MAX_LENGTH
    assert normalize_element_id(element_id) == element_id


def test_should_reject_element_ids_over_the_limit() -> None:
    with pytest.raises(InvalidInputError) as error:
        normalize_element_id("s" * (COMMENT_ELEMENT_ID_MAX_LENGTH + 1))
    assert error.value.message == (
        f"element_id can have at most {COMMENT_ELEMENT_ID_MAX_LENGTH} characters"
    )
