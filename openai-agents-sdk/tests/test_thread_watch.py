import threading

from runbooks.watch import ThreadWatch


def test_runs_once_after_the_thread_goes_quiet():
    watch = ThreadWatch()
    settled = threading.Event()
    calls = []

    def first():
        calls.append("first")

    def second():
        calls.append("second")
        settled.set()

    watch.observe("C123", "1700000000.000100", delay=0.05, on_settled=first)
    watch.observe("C123", "1700000000.000100", delay=0.05, on_settled=second)

    assert settled.wait(timeout=1)
    assert calls == ["second"]


def test_threads_settle_independently():
    watch = ThreadWatch()
    done = threading.Barrier(3, timeout=1)
    calls = []

    def settle(name):
        calls.append(name)
        done.wait()

    watch.observe(
        "C123", "1700000000.000100", delay=0.01, on_settled=lambda: settle("a")
    )
    watch.observe(
        "C123", "1700000000.000200", delay=0.01, on_settled=lambda: settle("b")
    )

    done.wait()
    assert sorted(calls) == ["a", "b"]
