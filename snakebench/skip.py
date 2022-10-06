import os

import pytest

BENCHMARKING = os.environ.get("BENCHMARKING", "false").lower() == "true"


def skip_bench(reason: str) -> pytest.MarkDecorator:
    return pytest.mark.skipif(BENCHMARKING, reason=reason)
