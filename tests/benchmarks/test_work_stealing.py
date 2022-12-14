import time

import dask.array as da
import distributed
import numpy as np
import pytest
import sneks
from dask import delayed, utils
from tornado.ioloop import PeriodicCallback

from snakebench.clusters import CLUSTER_KWARGS, setup_test_run_from_client
from snakebench.skip import skip_bench
from snakebench.utils_test import slowdown

# Not a useful benchmarking signal here currently
pytestmark = skip_bench("Not a useful benchmarking signal here currently")


def test_trivial_workload_should_not_cause_work_stealing(small_client):
    root = delayed(lambda n: "x" * n)(utils.parse_bytes("1MiB"), dask_key_name="root")
    results = [delayed(lambda *args: None)(root, i) for i in range(10000)]
    futs = small_client.compute(results)
    small_client.gather(futs)


@pytest.mark.skip("find a way to make this faster so we don't have to wait for scaling")
@pytest.mark.xfail(
    distributed.__version__ == "2022.6.0",
    reason="https://github.com/dask/distributed/issues/6624",
)
def test_work_stealing_on_scaling_up(test_id, test_run_benchmark, benchmark_all):
    with sneks.get_client(
        name=test_id, n_workers=1, worker_vm_types=["t3.medium"], **CLUSTER_KWARGS
    ) as client:
        setup_test_run_from_client(client, test_run_benchmark)
        with benchmark_all(client):
            # Slow task.
            def func1(chunk):
                if sum(chunk.shape) != 0:  # Make initialization fast
                    time.sleep(5)
                return chunk

            def func2(chunk):
                return chunk

            data = slowdown(da.zeros((30, 30, 30), chunks=5))
            result = data.map_overlap(func1, depth=1, dtype=data.dtype)
            result = result.map_overlap(func2, depth=1, dtype=data.dtype)
            future = client.compute(result)

            print("started computation")

            time.sleep(11)
            # print('scaling to 4 workers')
            # client.cluster.scale(4)

            time.sleep(5)
            print("scaling to 20 workers")
            client.cluster.scale(20)

            _ = future.result()


def test_work_stealing_on_inhomogeneous_workload(small_client):
    np.random.seed(42)
    delays = np.random.lognormal(1, 1.3, 500)

    @delayed
    def clog(n):
        time.sleep(min(n, 60))
        return n

    results = [clog(i) for i in delays]
    futs = small_client.compute(results)
    small_client.gather(futs)


def test_work_stealing_on_straggling_worker(test_id, test_run_benchmark, benchmark_all):
    with sneks.get_client(
        name=test_id, n_workers=10, worker_vm_types=["t3.medium"], **CLUSTER_KWARGS
    ) as client:
        setup_test_run_from_client(client, test_run_benchmark)
        with benchmark_all(client):

            def clog():
                time.sleep(1)

            @delayed
            def slowinc(i, delay):
                time.sleep(delay)
                return i + 1

            def install_clogging_callback(dask_worker):
                pc = PeriodicCallback(clog, 1500)
                dask_worker.periodic_callbacks["clog"] = pc
                pc.start()

            straggler = list(client.scheduler_info()["workers"].keys())[0]
            client.run(install_clogging_callback, workers=[straggler])
            results = [slowinc(i, delay=1) for i in range(1000)]
            futs = client.compute(results)
            client.gather(futs)
