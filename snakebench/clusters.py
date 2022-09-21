import logging
from typing import Iterator, cast

import pytest
import sneks
from coiled import Cluster
from distributed.client import Client

from snakebench.schema import TestRun
from snakebench.utils_test import cluster_memory

N_WORKERS = 10


CLUSTER_KWARGS = dict(
    account="dask-engineering",
    wait_for_workers=True,
    shutdown_on_close=True,
    environ=dict(
        DASK_DISTRIBUTED__SCHEDULER__WORKER_SATURATION="1.0",
    ),
)


# TODO find some way to generalize this pattern
# Have a way to create the base and function-scoped fixtures given n_workers and args.


@pytest.fixture(scope="module")
def _small_client_base(module_id) -> Iterator[Client]:
    "Create a per-module client. Do not use this fixture directly."
    # So coiled logs can be displayed on test failure
    logging.getLogger("coiled").setLevel(logging.INFO)

    print(f"Creating cluster {module_id}...")
    with sneks.get_client(
        name=module_id,
        n_workers=N_WORKERS,
        worker_vm_types=["t3.large"],  # 2CPU, 8GiB
        scheduler_vm_types=["t3.large"],
        **CLUSTER_KWARGS,
    ) as client:
        yield client


def setup_test_run_from_client(client: Client, test_run_benchmark: TestRun) -> None:
    cluster = cast(Cluster, client.cluster)
    assert isinstance(cluster, Cluster)

    test_run_benchmark.cluster_id = cluster.cluster_id

    vms = cluster.worker_vm_types
    if vms is not None:
        assert isinstance(vms, list) and len(vms) == 1, vms
        test_run_benchmark.worker_vm_type = vms[0]

    vms = cluster.scheduler_vm_types
    if vms is not None:
        assert isinstance(vms, list) and len(vms) == 1, vms
        test_run_benchmark.scheduler_vm_type = vms[0]

    info = client.scheduler_info()
    test_run_benchmark.n_workers = len(info["workers"])
    test_run_benchmark.n_threads = sum(w["nthreads"] for w in info["workers"].values())

    test_run_benchmark.cluster_memory = cluster_memory(client)


@pytest.fixture
def small_client(
    _small_client_base: Client, test_run_benchmark: TestRun, benchmark_all
) -> Iterator[Client]:
    "Per-test fixture to get a client, with automatic benchmarking."
    cluster = cast(Cluster, _small_client_base.cluster)
    assert isinstance(cluster, Cluster)

    cluster.scale(N_WORKERS)
    print(f"Waiting for {N_WORKERS} workers")
    _small_client_base.wait_for_workers(N_WORKERS)
    _small_client_base.restart()
    print(
        f"Using cluster {cluster.name!r}. Dashboard: {_small_client_base.dashboard_link}"
    )

    print(_small_client_base)
    setup_test_run_from_client(_small_client_base, test_run_benchmark)
    with benchmark_all(_small_client_base):
        yield _small_client_base
