import time

import dask
import dask.array as da
import numpy as np
import pytest
from dask.core import istask
from dask.datasets import timeseries
from dask.sizeof import sizeof
from dask.utils import parse_bytes

from snakebench.utils_test import scaled_array_shape, slowdown, timeseries_of_size


def test_scaled_array_shape():
    assert scaled_array_shape(1024, (2, "x"), dtype=bool) == (2, 512)
    assert scaled_array_shape(1024, (2, "x"), dtype=float) == (2, 64)
    assert scaled_array_shape(1024, (2, "x"), dtype=np.float64) == (2, 64)
    assert scaled_array_shape(1024, (2, "x")) == (2, 64)

    assert scaled_array_shape(16, ("x", "x"), dtype=bool) == (4, 4)
    assert scaled_array_shape(256, ("4x", "x"), dtype=bool) == (32, 8)
    assert scaled_array_shape(64, ("x", "x", "x"), dtype=float) == (2, 2, 2)

    assert scaled_array_shape("10kb", ("x", "1kb"), dtype=bool) == (10, 1000)


def sizeof_df(df):
    # Measure the size of each partition separately (each one has overhead of being a separate DataFrame)
    # TODO more efficient method than `df.partitions`? Use `dask.get` directly?
    parts = dask.compute(
        [df.partitions[i] for i in range(df.npartitions)], scheduler="threads"
    )
    return sum(map(sizeof, parts))


def test_timeseries_of_size():
    small_parts = timeseries_of_size(
        "1mb", freq="1s", partition_freq="100s", dtypes={"x": float}
    )
    big_parts = timeseries_of_size(
        "1mb", freq="1s", partition_freq="100s", dtypes={i: float for i in range(10)}
    )
    assert sizeof_df(small_parts) == pytest.approx(parse_bytes("1mb"), rel=0.1)
    assert sizeof_df(big_parts) == pytest.approx(parse_bytes("1mb"), rel=0.1)
    assert big_parts.npartitions < small_parts.npartitions


@pytest.mark.parametrize(
    "obj",
    [
        da.random.random(5, chunks=1),
        timeseries("2000-01-01", "2000-01-06", freq="12h", partition_freq="1d"),
    ],
)
def test_slowdown_arr(obj):
    slow = slowdown(obj, delay=0.2, jitter_factor=0.0)

    # Ensure the slow task gets fused into data generation
    [opt] = dask.optimize(slow)
    dsk = opt.__dask_graph__().to_dict()
    tasks = [k for k, v in dsk.items() if istask(v)]
    assert len(tasks) == opt.npartitions

    with dask.config.set({"scheduler": "sync"}):
        start = time.perf_counter()
        obj.compute()
        baseline = time.perf_counter() - start

        start = time.perf_counter()
        slow.compute()
        elapsed = time.perf_counter() - start

        assert baseline + 1 <= elapsed <= baseline + 1.5
