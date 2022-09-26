"""
Parquet-related benchmarks.
"""

from typing import Iterator

import dask.dataframe as dd
import dask.datasets
import fsspec
import pandas
import pytest
import sneks
from distributed.client import Client

from snakebench.clusters import CLUSTER_KWARGS, setup_test_run_from_client
from snakebench.utils_test import wait

N_WORKERS = 15


@pytest.fixture(scope="module")
def _parquet_client_base(module_id) -> Iterator[Client]:
    with sneks.get_client(
        name=module_id,
        n_workers=N_WORKERS,
        worker_vm_types=["m5.xlarge"],
        scheduler_vm_types=["m5.xlarge"],
        **CLUSTER_KWARGS,
    ) as client:
        yield client


@pytest.fixture
def parquet_client(
    _parquet_client_base: Client, test_run_benchmark, benchmark_all
) -> Iterator[Client]:
    cluster = _parquet_client_base.cluster
    assert cluster

    cluster.scale(N_WORKERS)
    print(f"Waiting for {N_WORKERS} workers")
    _parquet_client_base.wait_for_workers(N_WORKERS)
    _parquet_client_base.restart()
    print(
        f"Using cluster {cluster.name!r}. Dashboard: {_parquet_client_base.dashboard_link}"
    )

    print(_parquet_client_base)
    setup_test_run_from_client(_parquet_client_base, test_run_benchmark)
    with benchmark_all(_parquet_client_base):
        yield _parquet_client_base


def test_read_spark_generated_data(parquet_client):
    """
    Read a ~15 GB subset of a ~800 GB spark-generated
    open dataset on AWS.

    The dataset was copied from AWS open data on 2022-05-25
    https://registry.opendata.aws/1000-genomes-data-lakehouse-ready/
    Citation: https://www.nature.com/articles/s41467-018-08148-z
    """
    ddf = dd.read_parquet(
        "s3://coiled-runtime-ci/thousandgenomes_dagen/NA21**.parquet",
        engine="pyarrow",
        index="sample_id",
    )
    ddf.groupby(ddf.index).first().compute()


def test_read_hive_partitioned_data(parquet_client):
    """
    Read a dataset partitioned by year and quarter.

    The dataset was copied from AWS open data on 2022-05-25
    https://registry.opendata.aws/speedtest-global-performance/
    """
    ddf = dd.read_parquet(
        "s3://coiled-runtime-ci/ookla-open-data/type=fixed/**.parquet",
        engine="pyarrow",
    )

    ddf.groupby(["year", "quarter"]).first().compute()


def test_write_wide_data(parquet_client, s3_url):
    # Write a ~700 partition, ~200 GB dataset with a lot of columns
    ddf = dask.datasets.timeseries(
        dtypes={
            **{f"name-{i}": str for i in range(25)},
            **{f"price-{i}": float for i in range(25)},
            **{f"id-{i}": int for i in range(25)},
            **{f"cat-{i}": "category" for i in range(25)},
        },
        start="2021-01-01",
        end="2021-02-01",
        freq="10ms",
        partition_freq="1H",
    )
    ddf.to_parquet(s3_url + "/wide-data/")


def test_download_throughput_s3fs(parquet_client):
    # Test throughput for downloading and parsing a ~500 MB file
    path = (
        "s3://coiled-runtime-ci/ookla-open-data/"
        "type=fixed/year=2022/quarter=1/2022-01-01_performance_fixed_tiles.parquet"
    )

    def load(path):
        with fsspec.open(path) as f:
            f.read()

    wait(parquet_client.submit(load, path), parquet_client, 5 * 60)


def test_download_throughput_pandas(parquet_client):
    # Test throughput for downloading and parsing a ~500 MB file
    path = (
        "s3://coiled-runtime-ci/ookla-open-data/"
        "type=fixed/year=2022/quarter=1/2022-01-01_performance_fixed_tiles.parquet"
    )
    wait(
        parquet_client.submit(pandas.read_parquet, path, engine="pyarrow"),
        parquet_client,
        5 * 60,
    )


def test_download_throughput_dask(parquet_client):
    # Test throughput for downloading and parsing a ~500 MB file
    path = (
        "s3://coiled-runtime-ci/ookla-open-data/"
        "type=fixed/year=2022/quarter=1/2022-01-01_performance_fixed_tiles.parquet"
    )
    wait(dd.read_parquet(path, engine="pyarrow").persist(), parquet_client, 5 * 60)
