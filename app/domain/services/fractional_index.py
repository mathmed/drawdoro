from collections.abc import Iterator
from itertools import product

# Digits of tldraw's fractional indexes (the stacking order of shapes), in sort order.
BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


# Any key that extends `top` sorts after it and after every existing key, because `top` is the
# largest one. A fractional index may not end in "0", so the last digit never is.
def indexes_above(top: str) -> Iterator[str]:
    for first, last in product(BASE62, BASE62[1:]):
        yield f"{top}{first}{last}"
