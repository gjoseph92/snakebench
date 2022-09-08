from __future__ import annotations

import contextlib
import time
from datetime import datetime

import pytest

from .schema import TestRun


@pytest.fixture(scope="function")
def benchmark_time(test_run_benchmark: TestRun):
    @contextlib.contextmanager
    def _benchmark_time():
        start = time.time()
        try:
            yield
        finally:
            end = time.time()
            test_run_benchmark.duration = end - start
            test_run_benchmark.start = datetime.fromtimestamp(start).astimezone()
            test_run_benchmark.end = datetime.fromtimestamp(end).astimezone()

    return _benchmark_time()


@pytest.fixture(scope="function")
def auto_benchmark_time(benchmark_time):
    with benchmark_time:
        yield
