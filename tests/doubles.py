from unittest.mock import NonCallableMagicMock, create_autospec


# A stand-in for an implementation of `contract`: its async methods are AsyncMocks that check the
# contract's signatures, and attributes the contract does not have raise AttributeError. Typed as
# the mock it is, so tests configure it (return_value, side_effect, assert_awaited_*) type-safely.
def double(contract: type[object]) -> NonCallableMagicMock:
    mock: NonCallableMagicMock = create_autospec(contract, instance=True)
    return mock
