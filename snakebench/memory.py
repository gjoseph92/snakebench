import contextlib
import uuid

import pytest
from distributed.diagnostics.memory_sampler import MemorySampler

from .schema import TestRun


@pytest.fixture(scope="function")
def benchmark_memory(test_run_benchmark: TestRun):
    @contextlib.contextmanager
    def _benchmark_memory(client):
        sampler = MemorySampler()
        label = uuid.uuid4().hex[:8]
        with sampler.sample(label, client=client, measure="process"):
            yield

        df = sampler.to_pandas()
        if test_run_benchmark:
            test_run_benchmark.average_memory = df[label].mean()
            test_run_benchmark.peak_memory = df[label].max()

    yield _benchmark_memory
