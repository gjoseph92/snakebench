# snakebench

A framework for benchmarking [dask](https://www.dask.org/) on the [Coiled](https://coiled.io/) platform.

Snakebench is _commit-based_: each case to benchmark is a separate commit. If you want to compare six cases, you make six different commits defining each case. This may sound inconvenient at first, but it's very powerful, and easy to build convenience tooling on top of.

When you push a commit, the benchmarks run, and the results are written to storage (currently [S3](https://s3.console.aws.amazon.com/s3/buckets/snakebench-public?region=us-east-2&tab=objects)). If you run benchmarks for the same commit multiple times, they are _appended_ (not overwritten).

Then you can compare results between arbitrary commits in the browser: https://gjoseph92.github.io/snakebench, https://observablehq.com/@gjoseph92/snakebench. The browser fetches per-commit results from S3 as needed and visualizes them.

Dependencies are managed using the [PDM package manager](https://pdm.fming.dev/latest/). This ensures deterministic, reproducible environments everywhere (dev machines, GitHub actions, the dask clusters themselves). (We use PDM because it [supports overrides](https://pdm.fming.dev/latest/usage/dependency/#solve-the-locking-failure), [unlike Poetry](https://github.com/python-poetry/poetry/issues/697), which are necessary to install dask forks. Plus, it locks faster.)

To compare across different packages being installed, you simply push commits with different `pyproject.toml` and `pdm.lock` files, and compare them like you would any other change.

Packages are currently synced using [sneks](https://github.com/gjoseph92/sneks), but this will change once Coiled's package sync [supports it](https://github.com/coiled/platform/issues/94#issuecomment-1252567131).

## Design and motivation

There are two primary design decisions in snakebench:

1. Using separate git commits to define each case (versus, say, using a YAML file defining a set of parameters to compare)
2. Separating results visualization from generation (all visualization in the browser, instead of rendering static HTML files)

The purpose of both of these is flexibility.

It's hard to predict what kinds of changes we'll need to benchmark in the future, or how we'll want to compare them. Snakebench aims to be highly flexible, so it can be pragmatically adapted to future benchmarking needs.

A commit is perhaps the simplest and most adaptable unit by which to track performance.

This also separates the concept of a "case" from the idea of a "comparison", further increasing flexibility. _Without re-running any workloads_, you are free to:
* Change the visualization (or write a new one) for existing results
* Fix something in just one case, push the change, and compare without re-running the others
* Compare before and after your fix
* Realize your fix was bad, and go back to comparing before your fix, instantly
* Remove a case from comparison, instantly
* Change the baseline or order of comparison, instantly
* Compare a few cases, realize you need to add another, and add it without re-running any of the others
* Compare existing cases somebody already ran

Examples of things you could compare via the snakebench framework:
* Different ways of implementing a test
* Different cluster sizes, with or without different data sizes
* Nightly benchmarks: make a GitHub actions cron job that pushes commits updating the SHAs `dask/dask` and `dask/distributed` are installed from. Make a timeseries visualization comparing those commits.

# Usage

## Setup

1. [Install PDM](https://pdm.fming.dev/latest/#installation) if you don't have it already.
1. `git clone git@github.com:gjoseph92/snakebench.git`
1. `cd snakebench`
1. `pdm install --dev`
1. `eval $(pdm venv activate)` to activate the virtual environment. If using an IDE, set `.venv/bin/python` as your Python interpreter.
1. `pre-commit install` (pre-commit is installed automatically in the virtual environment as a dev dependency)

## Creating cases to compare

1. Make a branch for the case you want to run, named `bench/<comparison>/<title>`.
1. Make the change you want to try, commit, push.
1. Repeat for each case.
1. When the [actions](https://github.com/gjoseph92/snakebench/actions/workflows/test.yaml) are done, enter those commit hashes into the visualization tools.
    * Currently https://observablehq.com/@gjoseph92/snakebench is a prototype. A more formal version may be consolidated and refined soon.
    * Having to enter commit hashes by hand is temporary. We'll eventually use the GitHub API to list branches and their commits for you.
1. Push new commits to those branches as necessary, make new branches, and so on. You can always compare between any commit hashes.

### Comparing different dependencies

There's nothing special about dependencies. Whatever is listed in `pyproject.toml` and `pdm.lock` is what will get installed, and those are tracked in version control like everything else.

For convenience, you can just push changes `pyproject.toml` without locking. Snakebench will re-lock for you in GitHub actions, push a commit with the new lockfile, then run benchmarks off that new commit.

So a typical workflow might look like:

```bash
$ git checkout -b bench/pyarrow-versions/pyarrow-old main
$ pdm add pyarrow@8.0.0  # or, much faster, manually edit `pyproject.toml` and change the `pyarrow` version there, to skip locking
$ git add .
$ git commit -m "pyarrow 8"  # if you manually edited `pyproject.toml`, add `--no-verify`: pre-commit will complain the lockfile is out of date
$ git push

$ git checkout -b bench/pyarrow-versions/pyarrow-new main
$ pdm add pyarrow@9.0.0  # again, editing `pyproject.toml` is faster
$ git add .
$ git commit -m "pyarrow 9"  # again, add `--no-verify`
$ git push
```

Once the benchmarks have run, compare your commits. Note that if you manually edited `pyproject.toml`, use the SHA of the new commits that snakebench pushed to your branches (you'll have to `git pull` to get these locally, or just find them on the GitHub UI).

To install dask or distributed from GitHub, you'll usually need to specify a [PDM override](https://pdm.fming.dev/latest/usage/dependency/#solve-the-locking-failure). Because `dask/dask` and `dask/distributed` each depend on each other (and `coiled` depends on both), trying to install a fork will usually make the environment un-solveable.

An override might look like:

```toml
[tool.pdm.overrides]
dask = "git+https://github.com/dask/dask.git@<commit-sha>"
distributed = "git+https://github.com/<your-username>/distributed.git@<your-fork-sha>"
```

## Applying changes to multiple branches

With many similar branches around, applying changes one-by-one can be tedious. The [`for-each-branch.sh`](/blob/main/for-each-branch.sh) utility makes this easier:

```bash
$ ./for-each-branch.sh bench/pyarrow-versions git push
$ ./for-each-branch.sh bench/pyarrow-versions 'git cherry-pick abcd1234 || git cherry-pick --abort'  # || abort handles case when commit is already there
$ ./for-each-branch.sh bench/pyarrow-versions git checkout -b '$branch-v2'  # `$branch` is substituted with current branch. Use single quotes!
```

See the script for the variables you can substitute.

Eventually, this will be expanded to make it easy to substitute variables into patches, so you can map over an array of options to easily set up many test cases.

## Dependencies

Refer to the [PDM docs](https://pdm.fming.dev/latest/usage/dependency/) for specific usage. In general, `pyproject.toml` defines the packages we _want_ installed. `pdm.lock` defines everything that _will_ be installed (including transitive deps). You can edit `pyproject.toml`, then run `pdm lock`. You should never edit (and probably never look at) `pdm.lock`.

The easiest way to add dependencies is `pdm add`.

_Only dependencies that actually need to be installed on the cluster should go in the main `dependencies` section._ Packages just needed for testing (like `pytest`) or convenience (like `jupyterlab`) should be added as [dev dependencies](https://pdm.fming.dev/latest/usage/dependency/#add-development-only-dependencies). Use `pdm add -dG <group name>`, or add them to `pyproject.toml` in the `[tool.pdm.dev-dependencies]` section.

The `test` group, along will all prod dependencies, will be installed on GitHub actions in order to run tests. Only the prod dependencies will actually be installed on clusters (significantly speeding up cluster startup time).

Pre-commit will verify that the lockfile is up to date before each commit. If you've changed `pyproject.toml`, run `pdm sync --dev` to update it. (The one exception is below.)

If you pull down commits that change dependencies, or check out a different branch, run `pdm sync --dev --clean` to install the new dependencies (and remove any old ones).

## Local development

### Driving tests locally

You can easily drive tests from your machine, without needing GitHub actions to run them for you.

For most tests, you don't need to do anything special (assuming you're already [logged into Coiled](https://docs.coiled.io/user_guide/getting_started.html#log-in) locally and a member of the `dask-engineering` team):
```bash
pytest benchmarks/test_array.py::test_double_diff
pytest -k dataframe
```

Tests that need access to AWS (to read/write data) will use your local AWS credentials automatically. You may need to set the `AWS_PROFILE` variable to whatever profile you have set up to use the `coiled-oss` role. For me, that's:

```bash
AWS_PROFILE=oss pytest benchmarks/test_parquet.py
```

The test results will be written locally to `results-<commit>.json` files. (Note these are [newline-delimited JSON](http://ndjson.org/), not proper JSON.)

Currently, to visualize them, you'll need to manually update the `sha_to_url` function in the visualizations, and run [`http-server --cors`](https://www.npmjs.com/package/http-server) locally to serve the results files.

### Driving actions locally

[`act`](https://github.com/nektos/act) is very useful for testing and running GitHub actions locally. For this sort of thing, usually you don't need to run tests that actually create clusters, so you can change the `pytest` line `test.yaml` to `pdm run pytest tests/test_test.py` or something.

To test steps involving uploading or downloading GitHub artifacts, use `--artifact-server-url=artifacts`.

To test steps involving AWS access (uploading profile results), use `-s AWS_ACCESS_KEY_ID=<key> -s AWS_SECRET_ACCESS_KEY=<secret>`.

To test steps involving Coiled, use `-s COILED_BENCHMARK_BOT_TOKEN=<token>`.

## Mapping between Coiled clusters and the tests running them

Snakebench names Coiled clusters deterministically, so you can easily tell which GitHub Actions job created each one, and visa versa.

See the `module_id` fixture in [`snakebench/core.py`](blob/main/snakebench/core.py) for the specific pattern. Generally, it includes the commit hash, GitHub Actions run ID and retry number, any matrix parameters, and the module name of the test (clusters are generally shared per module).

Each test _should_ also print out the cluster name and dashboard link before it starts, which will be visible in pytest output if it fails.
