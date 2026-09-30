from app.domain.constants.gallery import GALLERY_MAX_NAME_LENGTH
from app.domain.errors.domain_errors import InvalidInputError


def normalize_gallery_item_name(raw: str) -> str:
    name = raw.strip()
    if name == "" or len(name) > GALLERY_MAX_NAME_LENGTH:
        raise InvalidInputError(f"Name must have 1 to {GALLERY_MAX_NAME_LENGTH} characters")
    return name
