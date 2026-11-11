from app.ratelimit import SlidingWindowLimiter


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_blocks_after_limit_and_recovers() -> None:
    clock = Clock()
    limiter = SlidingWindowLimiter(2, 60, clock)
    assert limiter.check("a") is None
    assert limiter.check("a") is None
    retry = limiter.check("a")
    assert retry is not None and 0 < retry <= 60
    clock.now = 61
    assert limiter.check("a") is None


def test_keys_are_independent() -> None:
    limiter = SlidingWindowLimiter(1, 60, Clock())
    assert limiter.check("a") is None
    assert limiter.check("b") is None
    assert limiter.check("a") is not None
