"""
This file is ignored in CI.

It's just useful for local development while working on new snakebench features.
"""

import time

import dask
import dask.array as da
import distributed
import pytest

pytestmark = pytest.mark.no_ci


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
            da.random.random((1_000, 1_000), chunks=100).sum().compute()


def test_dask_config():
    # Config comes from `dask.yaml` in the root directory.
    # `DASK_CONFIG` env var is set to point to this in `pyproject.toml` via `pytest-env`.
    assert dask.config.get("foo") == "bar"
    assert dask.config.get("distributed.scheduler")
