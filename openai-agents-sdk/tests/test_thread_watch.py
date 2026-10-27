import threading

from runbooks.watch import ThreadWatch

THREAD = ("C123", "1700000000.000100")


def test_runs_once_after_the_thread_goes_quiet():
    watch = ThreadWatch()
    settled = threading.Event()
    calls = []

    def on_settled(user_id, user_token):
        calls.append((user_id, user_token))
        settled.set()

    watch.observe(
        *THREAD, delay=0.05, user_id="U1", user_token="xoxp-1", on_settled=on_settled
    )
    watch.observe(
        *THREAD, delay=0.05, user_id="U2", user_token="xoxp-2", on_settled=on_settled
    )

    assert settled.wait(timeout=1)
    assert calls == [("U2", "xoxp-2")]


def test_keeps_the_last_connected_person_to_reply():
    watch = ThreadWatch()
    settled = threading.Event()
    calls = []

    def on_settled(user_id, user_token):
        calls.append((user_id, user_token))
        settled.set()

    watch.observe(
        *THREAD, delay=0.05, user_id="U1", user_token="xoxp-1", on_settled=on_settled
    )
    watch.observe(
        *THREAD, delay=0.05, user_id="U2", user_token=None, on_settled=on_settled
    )

    assert settled.wait(timeout=1)
    assert calls == [("U1", "xoxp-1")]


def test_skips_threads_without_a_connected_reply():
    watch = ThreadWatch()
    calls = []

    watch.observe(
        *THREAD,
        delay=0.01,
        user_id="U1",
        user_token=None,
        on_settled=lambda user_id, user_token: calls.append(user_id),
    )

    threading.Event().wait(0.1)
    assert calls == []


def test_never_runs_twice_at_once_for_one_thread():
    watch = ThreadWatch()
    release = threading.Event()
    done = threading.Event()
    running = []
    overlaps = []

    def on_settled(user_id, user_token):
        overlaps.append(len(running))
        running.append(user_id)
        if user_id == "U1":
            release.wait(timeout=1)
        running.remove(user_id)
        if user_id == "U2":
            done.set()

    watch.observe(
        *THREAD, delay=0.01, user_id="U1", user_token="xoxp-1", on_settled=on_settled
    )
    threading.Event().wait(0.05)
    watch.observe(
        *THREAD, delay=0.01, user_id="U2", user_token="xoxp-2", on_settled=on_settled
    )
    threading.Event().wait(0.05)
    release.set()

    assert done.wait(timeout=1)
    assert overlaps == [0, 0]
