import re

from app.domain.constants.gallery import (
    GALLERY_MAX_DESCRIPTION_LENGTH,
    GALLERY_MAX_TAG_LENGTH,
    GALLERY_MAX_TAGS,
)
from app.domain.errors.domain_errors import InvalidInputError

# Letters and digits of any language plus a few separators found in technology names
# ("c++", "c#", "ci/cd", "node.js", "event-driven").
_TAG_PATTERN = re.compile(r"^[\w .+#/-]+$")
_SPACES = re.compile(r"\s+")


# Tags are compared in lower case with single spaces; repeats are dropped, first one wins.
def normalize_gallery_item_tags(raw: list[str]) -> list[str]:
    tags: list[str] = []
    for value in raw:
        tag = _SPACES.sub(" ", value).strip().lower()
        if tag == "" or tag in tags:
            continue
        _validate_tag(tag)
        tags.append(tag)
    if len(tags) > GALLERY_MAX_TAGS:
        raise InvalidInputError(f"An item can have at most {GALLERY_MAX_TAGS} tags")
    return tags


def normalize_gallery_item_description(raw: str | None) -> str | None:
    if raw is None:
        return None
    description = raw.strip()
    if len(description) > GALLERY_MAX_DESCRIPTION_LENGTH:
        raise InvalidInputError(
            f"The description can have at most {GALLERY_MAX_DESCRIPTION_LENGTH} characters"
        )
    return description or None


def _validate_tag(tag: str) -> None:
    if len(tag) > GALLERY_MAX_TAG_LENGTH:
        raise InvalidInputError(f"Tags can have at most {GALLERY_MAX_TAG_LENGTH} characters")
    if not _TAG_PATTERN.match(tag):
        raise InvalidInputError(
            f"Tag {tag!r} has unsupported characters: use letters, digits, spaces and . + # / - _"
        )
