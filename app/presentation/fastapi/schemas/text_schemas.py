from collections.abc import Callable
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator
from pydantic_core import PydanticKnownError

from app.domain.constants.names import NAME_MAX_LENGTH

NUL = "\x00"


def _drop_nul(value: object) -> object:
    return value.replace(NUL, "") if isinstance(value, str) else value


def _at_most(max_length: int) -> Callable[[str], str]:
    def check(value: str) -> str:
        if len(value) > max_length:
            raise PydanticKnownError("string_too_long", {"max_length": max_length})
        return value

    return check


# Text that Postgres stores or looks up. It can't hold NUL characters, so they are dropped on the way
# in, before length limits apply, instead of failing the request with a 500. Values that are not
# strings go on to the usual str validation, which rejects them.
NulFreeStr = Annotated[str, BeforeValidator(_drop_nul)]

# Names and slugs, stored in columns of NAME_MAX_LENGTH characters. Longer ones get the same 422 as a
# max_length, but the limit stays out of the published schema: oasdiff reports a maxLength added to a
# request property as a breaking change.
NameStr = Annotated[NulFreeStr, AfterValidator(_at_most(NAME_MAX_LENGTH))]
