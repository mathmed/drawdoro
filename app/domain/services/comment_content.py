import unicodedata

from app.domain.constants.comments import (
    COMMENT_CONTENT_MAX_LENGTH,
    COMMENT_ELEMENT_ID_MAX_LENGTH,
)
from app.domain.errors.domain_errors import InvalidInputError

KEPT_CONTROL_CHARACTERS = frozenset("\n\t")
# Bidirectional overrides and isolates can make the text shown differ from the text stored.
BIDI_CONTROLS = frozenset(chr(code) for code in (*range(0x202A, 0x202F), *range(0x2066, 0x206A)))


# Comments are plain text: they are never interpreted as HTML or Markdown, so nothing is escaped
# here. What goes is what can't be shown honestly or stored at all (Postgres rejects NUL).
def normalize_comment_content(content: str) -> str:
    unified = content.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = "".join(char for char in unified if _is_displayable(char)).strip()
    if cleaned == "":
        raise InvalidInputError("A comment needs some text")
    if len(cleaned) > COMMENT_CONTENT_MAX_LENGTH:
        raise InvalidInputError(
            f"A comment can have at most {COMMENT_CONTENT_MAX_LENGTH} characters "
            f"(this one has {len(cleaned)})"
        )
    return cleaned


def normalize_element_id(element_id: str | None) -> str | None:
    if element_id is None or element_id.strip() == "":
        return None
    trimmed = element_id.strip()
    if len(trimmed) > COMMENT_ELEMENT_ID_MAX_LENGTH:
        raise InvalidInputError(
            f"element_id can have at most {COMMENT_ELEMENT_ID_MAX_LENGTH} characters"
        )
    return trimmed


def _is_displayable(char: str) -> bool:
    if char in KEPT_CONTROL_CHARACTERS:
        return True
    return unicodedata.category(char) != "Cc" and char not in BIDI_CONTROLS
