# Each message spends a token and tokens refill at a steady rate, so short bursts pass while a
# sustained flood is cut down to the refill rate. Times come from a monotonic clock, in seconds.
class TokenBucket:
    def __init__(self, capacity: float, refill_per_second: float, now: float) -> None:
        self._capacity = capacity
        self._refill_per_second = refill_per_second
        self._tokens = capacity
        self._updated_at = now

    def try_take(self, now: float) -> bool:
        elapsed = now - self._updated_at
        self._tokens = min(self._capacity, self._tokens + elapsed * self._refill_per_second)
        self._updated_at = now
        if self._tokens < 1:
            return False
        self._tokens -= 1
        return True
