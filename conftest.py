from snakebench import *  # noqa


def pytest_addoption(parser):
    parser.addoption("--local", action="store_true")
