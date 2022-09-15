import time

import dask.array as da
import distributed
import pytest


def test_benchmark_half(auto_benchmark_time):
    time.sleep(0.5)


def test_benchmark_quarter(auto_benchmark_time):
    time.sleep(0.25)


@pytest.mark.parametrize("amt", [0.1, 0.3, 0.5])
def test_benchmark_param(auto_benchmark_time, amt):
    time.sleep(amt)


def test_benchmark_all(benchmark_all):
    with distributed.Client(
        n_workers=2, threads_per_worker=1, processes=False
    ) as client:
        with benchmark_all(client):
            da.random.random((10_000, 10_000), chunks=1000).sum().compute()
