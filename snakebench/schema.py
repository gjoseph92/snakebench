from __future__ import annotations

from datetime import datetime
from typing import Literal

import msgspec

Outcome = Literal["passed", "failed", "skipped"]


class TestRun(msgspec.Struct):
    name: str
    commit: str
    commit_subject: str
    commit_body: str
    # path: str

    setup_outcome: Outcome | None = None
    call_outcome: Outcome | None = None
    teardown_outcome: Outcome | None = None

    ci_run_url: str | None = None
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
