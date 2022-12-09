from __future__ import annotations

import contextlib

import pytest
from distributed.worker import Worker

from .schema import TestRun


@pytest.fixture(scope="function")
def benchmark_transfers(test_run_benchmark: TestRun):
    @contextlib.contextmanager
    def _benchmark_transfers(client):
        def total_transfer(dask_worker: Worker) -> int:
            return dask_worker.transfer_outgoing_bytes_total

        initial: dict[str, int] = client.run(total_transfer)
        yield
        final: dict[str, int] = client.run(total_transfer)

        assert initial.keys() == final.keys(), (
            f"Workers changed during test: {initial.keys() - final.keys()} left, "
            f"{final.keys() - initial.keys()} joined"
        )

        test_run_benchmark.total_transfer_per_worker = [
            f - initial[addr] for addr, f in final.items()
        ]

    return _benchmark_transfers
