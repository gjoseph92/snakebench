import contextlib
import uuid

import pandas as pd
import pytest
from distributed.diagnostics.memory_sampler import MemorySampler

from .schema import TestRun


@pytest.fixture(scope="function")
def benchmark_memory(test_run_benchmark: TestRun):
    @contextlib.contextmanager
    def _benchmark_memory(client):
        sampler = MemorySampler()
        label = uuid.uuid4().hex[:8]
        measure = "process"
        with sampler.sample(label, client=client, measure=measure):
            yield

        series = sampler.to_pandas(align=True)[label]

        test_run_benchmark.measure = measure
        test_run_benchmark.average_memory = series.mean()
        test_run_benchmark.peak_memory = series.max()
        test_run_benchmark.samples = series.to_list()

        idx = series.index
        assert isinstance(idx, pd.TimedeltaIndex)
        test_run_benchmark.times = idx.total_seconds().to_list()

    return _benchmark_memory
