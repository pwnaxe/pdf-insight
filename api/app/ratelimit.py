import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable


class SlidingWindowLimiter:
    # Per-process only: with several workers or containers each one keeps its own counters.

    def __init__(
        self, limit: int, window_s: float, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._limit = limit
        self._window = window_s
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    # None when allowed, otherwise seconds until a slot frees up
    def check(self, key: str) -> float | None:
        now = self._clock()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] >= self._window:
                hits.popleft()
            if len(hits) >= self._limit:
                return self._window - (now - hits[0])
            hits.append(now)
            if len(self._hits) > 10_000:
                self._evict(now)
            return None

    def _evict(self, now: float) -> None:
        for key in [k for k, h in self._hits.items() if not h or now - h[-1] >= self._window]:
            del self._hits[key]
