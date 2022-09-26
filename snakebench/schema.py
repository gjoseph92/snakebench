from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

import msgspec
import numpy as np

Outcome = Literal["passed", "failed", "skipped"]


class TestRun(msgspec.Struct):
    name: str
    commit: str
    commit_subject: str
    commit_body: str
    branch: str
    # path: str

    setup_outcome: Outcome | None = None
    call_outcome: Outcome | None = None
    teardown_outcome: Outcome | None = None

    ci_run_url: str | None = None
    ci_run_id: str | None = None
    ci_run_attempt: str | None = None
    # dask_version: str | None = None
    # distributed_version: str | None = None
    # python_version: str | None = None
    # platform: str | None = None

    # Wall clock data
    start: datetime | None = None
    end: datetime | None = None
    duration: float | None = None

    # Memory data
    average_memory: float | None = None
    peak_memory: float | None = None

    # Cluster data
    cluster_id: int | None = None
    worker_vm_type: str | None = None
    scheduler_vm_type: str | None = None
    n_workers: int | None = None
    n_threads: int | None = None
    cluster_memory: int | None = None


def enc_hook(obj: Any) -> Any:
    # For convenience, support encoding NumPy scalars
    if type(obj) in np.ScalarType:
        return obj.item()
    raise TypeError(f"Encoding objects of type {type(obj)} is unsupported")


encoder = msgspec.json.Encoder(enc_hook=enc_hook)
