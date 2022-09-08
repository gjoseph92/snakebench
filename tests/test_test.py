import time

import pytest


def test_benchmark_half(auto_benchmark_time):
    time.sleep(0.5)


def test_benchmark_quarter(auto_benchmark_time):
    # time.sleep(0.25)
    time.sleep(0.1)


@pytest.mark.parametrize("amt", [0.3, 0.5, 0.7])
# @pytest.mark.parametrize("amt", [0.1, 0.3, 0.5])
def test_benchmark_param(auto_benchmark_time, amt):
    time.sleep(amt)
