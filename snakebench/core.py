from __future__ import annotations

import os
from types import ModuleType

import pytest
from filelock import FileLock

from snakebench.commit_info import CommitInfo
from snakebench.schema import TestRun, encoder

RESULTS_FILE_BASE = os.environ.get("RESULTS_FILE_BASE", "results")

if os.environ.get("GITHUB_SERVER_URL"):
    WORKFLOW_URL = "/".join(
        [
            os.environ.get("GITHUB_SERVER_URL", ""),
            os.environ.get("GITHUB_REPOSITORY", ""),
            "actions",
            "runs",
            os.environ.get("GITHUB_RUN_ID", ""),
        ]
    )
else:
    WORKFLOW_URL = None

# Set in test.yml
RUN_ID = os.environ.get("GITHUB_RUN_ID", "0")
RUN_ATTEMPT = os.environ.get("GITHUB_RUN_ATTEMPT", "0")


@pytest.fixture(scope="session")
def results_filename(commit_info: CommitInfo):
    return f"{RESULTS_FILE_BASE}-{commit_info.sha}.json"


@pytest.fixture(scope="session")
def result_file_lock(results_filename, tmp_path_factory):
    # get the temp directory shared by all workers
    root_tmp_dir = tmp_path_factory.getbasetemp().parent
    lock_path = root_tmp_dir / (results_filename + ".lock")

    return FileLock(lock_path)


# this code was taken from pytest docs
# https://docs.pytest.org/en/latest/example/simple.html#making-test-result-information-available-in-fixtures
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # set a report attribute for each phase of a call, which can
    # be "setup", "call", "teardown"

    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(scope="module")
def module_id(commit_info: CommitInfo, request: pytest.FixtureRequest) -> str:
    "Module-level unique identifier (commit + run ID + run attempt + module name)"
    mod: ModuleType = request.module
    parts = [commit_info.sha, RUN_ID, RUN_ATTEMPT, mod.__name__.replace(".", "_")]
    return "-".join(parts)


@pytest.fixture
def test_id(request: pytest.FixtureRequest, module_id) -> str:
    "Test-level unique identifier (commit + run ID + run attempt + module name + test name)"
    return f"{module_id}-{request.node.name}"


@pytest.fixture(scope="function")
def test_run_benchmark(
    result_file_lock,
    results_filename,
    commit_info: CommitInfo,
    request: pytest.FixtureRequest,
):
    node = request.node
    run = TestRun(
        name=node.name,
        commit=commit_info.sha,
        commit_subject=commit_info.subject,
        commit_body=commit_info.body,
        ci_run_url=WORKFLOW_URL,
        ci_run_id=RUN_ID,
        ci_run_attempt=RUN_ATTEMPT,
        # session_id=testrun_uid,
        # originalname=node.originalname,
        # path=str(node.path.relative_to(TEST_DIR)),
        # dask_version=dask.__version__,
        # distributed_version=distributed.__version__,
        # python_version=".".join(map(str, sys.version_info)),
        # platform=sys.platform,
    )
    yield run

    if rep := getattr(request.node, "rep_setup", None):
        run.setup_outcome = rep.outcome
    if rep := getattr(request.node, "rep_call", None):
        run.call_outcome = rep.outcome
    if rep := getattr(request.node, "rep_teardown", None):
        run.teardown_outcome = rep.outcome

    with result_file_lock:
        # Write newline-delimited JSON
        with open(results_filename, "ab") as f:
            f.write(encoder.encode(run))
            f.write(b"\n")
