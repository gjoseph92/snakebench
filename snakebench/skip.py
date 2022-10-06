import os

import pytest

# Ideally we'd use our `commit_info` fixture, but you can't easily use a fixture as input to `skipif`.
BENCHMARKING = os.environ.get("GITHUB_REF_NAME", "").startswith("bench/")


def skip_bench(reason: str) -> pytest.MarkDecorator:
    return pytest.mark.skipif(BENCHMARKING, reason=reason)
