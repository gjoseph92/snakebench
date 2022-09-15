import logging
from typing import Iterator

import pytest
import sneks
from distributed.client import Client

from snakebench.commit_info import CommitInfo

N_WORKERS = 10


@pytest.fixture(scope="module")
def cluster_name(commit_info: CommitInfo, current_module: str) -> str:
    return f"{commit_info.sha}-{current_module.replace('.', '_')}"


# TODO find some way to generalize this pattern
# Have a way to create the base and function-scoped fixtures given n_workers and args.


@pytest.fixture(scope="module")
def _small_client_base(cluster_name) -> Iterator[Client]:
    "Create a per-module client. Do not use this fixture directly."
    # So coiled logs can be displayed on test failure
    logging.getLogger("coiled").setLevel(logging.INFO)

    print(f"Creating cluster {cluster_name}...")
    with sneks.get_client(
        name=cluster_name,
        n_workers=N_WORKERS,
        worker_vm_types=["t3.large"],  # 2CPU, 8GiB
        scheduler_vm_types=["t3.large"],
        shutdown_on_close=True,
        # environ=dict(DASK_DISTRIBUTED__SCHEDULER__WORKER_SATURATION=1.0),
    ) as client:
        yield client


@pytest.fixture
def small_client(_small_client_base: Client, benchmark_all) -> Iterator[Client]:
    "Per-test fixture to get a client, with automatic benchmarking."
    assert _small_client_base.cluster
    _small_client_base.cluster.scale(N_WORKERS)
    print(f"Waiting for {N_WORKERS} workers")
    _small_client_base.wait_for_workers(N_WORKERS)
    _small_client_base.restart()

    print(_small_client_base)
    with benchmark_all(_small_client_base):
        yield _small_client_base
