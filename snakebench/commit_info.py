from __future__ import annotations

import subprocess
from typing import NamedTuple

import pytest


class CommitInfo(NamedTuple):
    sha: str
    subject: str
    body: str
    branch: str


@pytest.fixture(scope="session")
def commit_info() -> CommitInfo:
    # TODO combine into one subprocess call. Just don't want to deal
    # with parsing delimiters.
    sha = subprocess.run(
        ["git", "log", "--format=%h", "-n", "1", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    subject = subprocess.run(
        ["git", "log", "--format=%s", "-n", "1", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    body = subprocess.run(
        ["git", "log", "--format=%b", "-n", "1", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    return CommitInfo(sha, subject, body, branch)
