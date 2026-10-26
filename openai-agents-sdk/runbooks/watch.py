import threading
from collections.abc import Callable


class ThreadWatch:
    """Wait for a thread to go quiet before acting on it.

    Each new reply restarts the wait, so ``on_settled`` runs once per quiet
    period instead of once per message.
    """

    def __init__(self):
        self._timers: dict[tuple[str, str], threading.Timer] = {}
        self._lock = threading.Lock()

    def observe(
        self,
        channel_id: str,
        thread_ts: str,
        delay: float,
        on_settled: Callable[[], None],
    ) -> None:
        """Restart the wait for a thread after a new reply."""
        key = (channel_id, thread_ts)
        with self._lock:
            pending = self._timers.get(key)
            if pending is not None:
                pending.cancel()
            timer = threading.Timer(delay, self._settle, args=(key, on_settled))
            timer.daemon = True
            self._timers[key] = timer
            timer.start()

    def _settle(self, key: tuple[str, str], on_settled: Callable[[], None]) -> None:
        with self._lock:
            if self._timers.get(key) is not threading.current_thread():
                return
            del self._timers[key]
        on_settled()
