from typing import Annotated

from pydantic import BeforeValidator

NUL = "\x00"


def _drop_nul(value: object) -> object:
    return value.replace(NUL, "") if isinstance(value, str) else value


# Text that Postgres stores or looks up. It can't hold NUL characters, so they are dropped on the way
# in, before length limits apply, instead of failing the request with a 500. Values that are not
# strings go on to the usual str validation, which rejects them.
NulFreeStr = Annotated[str, BeforeValidator(_drop_nul)]
