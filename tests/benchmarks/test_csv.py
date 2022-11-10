import dask.dataframe as dd
import pandas as pd

from snakebench.skip import skip_bench

# Not a useful benchmarking signal here currently
pytestmark = skip_bench("Not a useful benchmarking signal here currently")


def test_quickstart_csv(small_client):
    ddf = dd.read_csv(
        "s3://coiled-runtime-ci/nyc-tlc/yellow_tripdata_2019_csv/yellow_tripdata_2019-*.csv",
        dtype={
            "payment_type": "UInt8",
            "VendorID": "UInt8",
            "passenger_count": "UInt8",
            "RatecodeID": "UInt8",
        },
        blocksize="16 MiB",
    )

    result = ddf.groupby("passenger_count").tip_amount.mean().compute()

    assert isinstance(result, pd.Series)
    assert not result.empty
