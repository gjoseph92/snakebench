from __future__ import annotations

import logging
from contextlib import ExitStack
from os import environ
from typing import Iterator, cast

import dask.config
import pytest
import sneks
from coiled import Cluster as CoiledCluster
from dask_pyspy import pyspy, pyspy_on_scheduler
from distributed.client import Client
from distributed.deploy.cluster import Cluster

from snakebench.schema import TestRun
from snakebench.utils_test import cluster_memory

N_WORKERS = 128


CLUSTER_ENV: dict[str, str] = dict(
    # DASK_DISTRIBUTED__SCHEDULER__WORKER_SATURATION="1.0",
)

CLUSTER_KWARGS = dict(
    account="dask-engineering",
    wait_for_workers=True,
    environ=CLUSTER_ENV,
    backend_options=dict(
        send_prometheus_metrics=True,
    ),
)


# TODO find some way to generalize this pattern
# Have a way to create the base and function-scoped fixtures given n_workers and args.


def _client_coiled(module_id: str, reuse: bool = False) -> Client:
    # So coiled logs can be displayed on test failure
    logging.getLogger("coiled").setLevel(logging.INFO)

    print(f"Creating cluster {module_id}...")
    return sneks.get_client(
        name=module_id,
        n_workers=N_WORKERS,
        worker_vm_types=["t3.large"],  # 2CPU, 8GiB
        scheduler_vm_types=["t3.large"],
        shutdown_on_close=not reuse,
        **CLUSTER_KWARGS,
    )


def _client_local(module_id: str, reuse: bool = False) -> Client:
    print(f"Creating local cluster {module_id}...")
    # TODO mock/monkeypatch and dask config set!!
    environ.update(CLUSTER_ENV)
    dask.config.refresh()
    return Client(name=module_id, scheduler_port=8786, silence_logs=False)


@pytest.fixture(scope="module")
def _small_client_base(
    module_id: str, reuse_cluster: bool, request: pytest.FixtureRequest
) -> Iterator[tuple[Client, int]]:
    "Create a per-module client. Do not use this fixture directly."
    n_workers = None
    if request.config.getoption("--local"):
        backend = _client_local
    else:
        backend = _client_coiled
        n_workers = N_WORKERS

    with backend(module_id, reuse=reuse_cluster) as client:
        if n_workers is None:
            cluster = client.cluster
            assert isinstance(cluster, Cluster)
            n_workers = len(cluster.workers)
        yield client, n_workers


def setup_test_run_from_client(client: Client, test_run_benchmark: TestRun) -> None:
    cluster = client.cluster

    if isinstance(cluster, CoiledCluster):
        coiled_cluster = cast(
            CoiledCluster, cluster
        )  # FIXME pyright type narrowing isn't working
        test_run_benchmark.cluster_id = coiled_cluster.cluster_id

        vms = coiled_cluster.worker_vm_types
        if vms is not None:
            assert isinstance(vms, list) and len(vms) == 1, vms
            test_run_benchmark.worker_vm_type = vms[0]

        vms = coiled_cluster.scheduler_vm_types
        if vms is not None:
            assert isinstance(vms, list) and len(vms) == 1, vms
            test_run_benchmark.scheduler_vm_type = vms[0]

    info = client.scheduler_info()
    test_run_benchmark.n_workers = len(info["workers"])
    test_run_benchmark.n_threads = sum(w["nthreads"] for w in info["workers"].values())

    test_run_benchmark.cluster_memory = cluster_memory(client)


@pytest.fixture
def small_client(
    _small_client_base: tuple[Client, int],
    test_run_benchmark: TestRun,
    test_id: str,
    benchmark_all,
    request: pytest.FixtureRequest,
) -> Iterator[Client]:
    "Per-test fixture to get a client, with automatic benchmarking."
    client, n_workers = _small_client_base
    cluster = client.cluster
    assert isinstance(cluster, Cluster)

    cluster.scale(n_workers)
    print(f"Waiting for {n_workers} workers")
    client.wait_for_workers(n_workers)
    client.restart()
    print(f"Using cluster {cluster.name!r}. Dashboard: {client.dashboard_link}")

    print(client)
    setup_test_run_from_client(client, test_run_benchmark)

    with ExitStack() as ctxs:
        if request.config.getoption("--pyspy") is True:
            ctxs.enter_context(pyspy(f"profiles-{test_id}", native=True))
        if request.config.getoption("--pyspy-scheduler") is True:
            ctxs.enter_context(
                pyspy_on_scheduler(f"profile-{test_id}.json", native=True)
            )
        ctxs.enter_context(benchmark_all(client))

        yield client
