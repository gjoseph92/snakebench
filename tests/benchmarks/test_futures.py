import random
import time
from functools import partial
from operator import add
from time import sleep
from typing import Any

import numpy as np
from dask import delayed
from dask.distributed import as_completed
from dask.utils import parse_bytes

from snakebench import skip_bench
from snakebench.utils_test import wait

# NOTE: we can't import helpers like `inc`, `slowinc` from `distributed.utils_test` because
# `utils_test` requires importing all sorts of junk like pytest, which we intentionally don't install
# on the cluster.
# And we can't define them top-level in this file, since then they'd be pickled by reference,
# and this local file isn't available on the cluster.
# Would be nice to have a better solution for this.

inc = partial(add, 1)


@skip_bench("duration too short to measure effectively")
def test_single_future(small_client):
    """How quickly can we run a simple computation?"""
    small_client.submit(inc, 1).result()


def test_large_map(small_client):
    """What's the overhead of map these days?"""
    futures = small_client.map(inc, range(100_000))
    wait(futures, small_client, 10 * 60)


@skip_bench("too much variation to be useful")
def test_large_map_first_work(small_client):
    """
    Large maps are fine, but it's pleasant to see work start immediately.
    We have a batch_size keyword that should work here but it's not on by default.
    Maybe it should be.
    """
    futures = small_client.map(inc, range(100_000))
    for _ in as_completed(futures):
        return


@skip_bench("too short to be useful")
def test_memory_efficient(small_client):
    """
    We hope that we pipeline xs->ys->zs without keeping all of the xs in memory
    to start.  This may not actually happen today.
    """

    def slowinc(x, delay=0.02):
        sleep(delay)
        return x + 1

    def slowdec(x, delay=0.02):
        sleep(delay)
        return x - 1

    xs = small_client.map(np.random.random, [1_000_000] * 100, pure=False)
    ys = small_client.map(slowinc, xs, delay=0.1)
    zs = small_client.map(slowdec, ys, delay=0.1)

    futures = as_completed(zs)
    del xs, ys, zs  # Don't keep references to intermediate results

    future: Any
    for future in futures:  # pass through all futures, forget them immediately
        if future.status in ("error", "cancelled"):
            raise future.exception()


def test_jobqueue(small_client):
    # Just using dask to run lots of embarrassingly-parallel CPU-bound tasks as fast as possible
    nthreads = sum(
        w["nthreads"] for w in small_client.scheduler_info()["workers"].values()
    )
    max_runtime = 120
    max_sleep = 3
    n_tasks = round(max_runtime / max_sleep * nthreads)

    @delayed(pure=True)
    def task(i: int) -> int:
        stuff = "x" * parse_bytes("400MiB")
        time.sleep(random.uniform(0, max_sleep))
        del stuff
        return i

    tasks = [task(i) for i in range(n_tasks)]
    result = delayed(sum)(tasks)  # just so we have a single object

    wait(
        result.persist(),
        small_client,
        max_runtime * 1.15,
    )
