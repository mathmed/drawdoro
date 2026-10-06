import pytest

from app.domain.services.token_bucket import TokenBucket


@pytest.fixture
def sut() -> TokenBucket:
    return TokenBucket(capacity=3, refill_per_second=2, now=100.0)


def take_all(bucket: TokenBucket, now: float, attempts: int) -> list[bool]:
    return [bucket.try_take(now) for _ in range(attempts)]


def test_should_let_a_full_burst_through_and_refuse_the_next(sut: TokenBucket) -> None:
    assert take_all(sut, 100.0, 4) == [True, True, True, False]


def test_should_refill_at_the_given_rate(sut: TokenBucket) -> None:
    take_all(sut, 100.0, 3)

    assert take_all(sut, 100.5, 2) == [True, False]
    assert take_all(sut, 101.5, 3) == [True, True, False]


def test_should_refuse_until_a_whole_token_has_refilled(sut: TokenBucket) -> None:
    take_all(sut, 100.0, 3)

    assert sut.try_take(100.4) is False
    assert sut.try_take(100.5) is True


def test_should_not_save_up_more_than_its_capacity(sut: TokenBucket) -> None:
    assert take_all(sut, 1000.0, 4) == [True, True, True, False]


def test_should_not_count_refused_attempts_against_the_refill(sut: TokenBucket) -> None:
    take_all(sut, 100.0, 3)
    take_all(sut, 100.25, 5)

    assert sut.try_take(100.5) is True
