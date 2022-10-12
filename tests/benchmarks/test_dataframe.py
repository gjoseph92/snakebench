from dask.sizeof import sizeof
from dask.utils import format_bytes

from snakebench.utils_test import cluster_memory, slowdown, timeseries_of_size, wait


def print_dataframe_info(df):
    p = df.partitions[0].compute(scheduler="threads")
    partition_size = sizeof(p)
    total_size = partition_size * df.npartitions
    print(
        f"~{len(p) * df.npartitions:,} rows x {len(df.columns)} columns, "
        f"{format_bytes(total_size)} total, "
        f"{df.npartitions:,} {format_bytes(partition_size)} partitions"
    )


def test_basic_df_mean(small_client):
    memory = cluster_memory(small_client)  # 76.66 GiB

    df = slowdown(
        timeseries_of_size(
            memory * 2,
            start="2020-01-01",
            freq="1200ms",
            partition_freq="24h",
            dtypes={i: float for i in range(1_000)},
        )
    )
    print_dataframe_info(df)
    # ~20,592,000 rows x 1000 columns, 153.58 GiB total, 286 549.87 MiB partitions

    result = df.sum(split_every=None)  # see https://github.com/dask/dask/issues/9450
    wait(result.persist(), small_client, 5 * 60)


def test_dataframe_align(small_client):
    memory = cluster_memory(small_client)  # 76.66 GiB

    df = slowdown(
        timeseries_of_size(
            memory // 2,
            start="2020-01-01",
            freq="600ms",
            partition_freq="12h",
            dtypes={i: float for i in range(100)},
        )
    )
    print_dataframe_info(df)
    # ~50,904,000 rows x 100 columns, 38.31 GiB total, 707 55.48 MiB partitions

    df2 = slowdown(
        timeseries_of_size(
            memory // 4,
            start="2010-01-01",
            freq="600ms",
            partition_freq="12h",
            dtypes={i: float for i in range(100)},
        )
    )
    print_dataframe_info(df2)
    # ~25,488,000 rows x 100 columns, 19.18 GiB total, 354 55.48 MiB partitions

    final = (df2 - df).mean()  # will be all NaN, just forcing alignment
    wait(final.persist(), small_client, 10 * 60)


def test_shuffle(small_client):
    memory = cluster_memory(small_client)  # 76.66 GiB

    df = slowdown(
        timeseries_of_size(
            memory // 4,
            start="2020-01-01",
            freq="1200ms",
            partition_freq="24h",
            dtypes={i: float for i in range(100)},
        )
    )
    print_dataframe_info(df)
    # ~25,488,000 rows x 100 columns, 19.18 GiB total, 354 55.48 MiB partitions

    shuf = df.shuffle(0, shuffle="tasks")
    result = shuf.size
    wait(result.persist(), small_client, 20 * 60)


def test_larger_shuffle(small_client):
    memory = cluster_memory(small_client)  # 76.66 GiB

    df = slowdown(
        timeseries_of_size(
            int(memory * 0.75),
            start="2020-01-01",
            freq="1200ms",
            partition_freq="24h",
            dtypes={str(i): float for i in range(100)},
        )
    )
    print_dataframe_info(df)
    # ~71,856,000 rows x 100 columns, 54.07 GiB total, 998 55.48 MiB partitions

    shuf = df.shuffle("0", shuffle="tasks")
    result = shuf.size
    wait(result.persist(), small_client, 20 * 60)
