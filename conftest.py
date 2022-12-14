from snakebench import *  # noqa


def pytest_addoption(parser):
    parser.addoption("--local", action="store_true")
    parser.addoption("--reuse", action="store_true")
    parser.addoption("--pyspy", action="store_true")
    parser.addoption("--pyspy-scheduler", action="store_true")
