import contextlib

import pytest


@pytest.fixture(scope="function")
def benchmark_all(benchmark_memory, benchmark_time, benchmark_transfers):
    """Return a function that creates a context manager for benchmarking.

    Example:
    >>> def test_example(benchmark_all):
    >>>    ...
    >>>    with benchmark_all(client):
    >>>       client.compute(my_computation)
    """

    @contextlib.contextmanager
    def _benchmark_all(client):
        with benchmark_transfers(client), benchmark_memory(client), benchmark_time:
            yield

    return _benchmark_all
