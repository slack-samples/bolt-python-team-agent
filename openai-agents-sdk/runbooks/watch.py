import threading
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class _Thread:
    timer: threading.Timer | None = None
    user_id: str | None = None
    user_token: str | None = None
    running: bool = False


class ThreadWatch:
    """Wait for a thread to go quiet before acting on it.

    Each new reply restarts the wait. Once the thread is quiet, ``on_settled``
    runs once with the last connected person to reply, and never twice at the
    same time for one thread.
    """

    def __init__(self):
        self._threads: dict[tuple[str, str], _Thread] = {}
        self._lock = threading.Lock()

    def observe(
        self,
        channel_id: str,
        thread_ts: str,
        delay: float,
        user_id: str,
        user_token: str | None,
        on_settled: Callable[[str, str], None],
    ) -> None:
        """Restart the wait for a thread after a new reply."""
        key = (channel_id, thread_ts)
        with self._lock:
            thread = self._threads.setdefault(key, _Thread())
            if user_token:
                thread.user_id = user_id
                thread.user_token = user_token
            self._restart(key, thread, delay, on_settled)

    def _restart(self, key, thread, delay, on_settled) -> None:
        if thread.timer is not None:
            thread.timer.cancel()
        thread.timer = threading.Timer(
            delay, self._settle, args=(key, delay, on_settled)
        )
        thread.timer.daemon = True
        thread.timer.start()

    def _settle(self, key, delay, on_settled) -> None:
        with self._lock:
            thread = self._threads.get(key)
            if thread is None or thread.timer is not threading.current_thread():
                return
            if thread.running:
                self._restart(key, thread, delay, on_settled)
                return
            thread.timer = None
            if thread.user_token is None:
                del self._threads[key]
                return
            thread.running = True
            user_id, user_token = thread.user_id, thread.user_token
        try:
            on_settled(user_id, user_token)
        finally:
            with self._lock:
                thread.running = False
                if thread.timer is None:
                    del self._threads[key]
