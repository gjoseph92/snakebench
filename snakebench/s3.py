import pytest
import s3fs

S3_REGION = "us-east-2"
S3_BUCKET = "s3://coiled-runtime-ci"


s3 = s3fs.S3FileSystem()


@pytest.fixture(scope="function")
def s3_url(test_id):
    # NOTE: S3 is a prefix-based object store, not an actual filesystem,
    # so creating directories is unnecessary.
    # We assume, however, that the bucket does exist already.
    url = f"{S3_BUCKET}/test-scratch/{test_id}"
    try:
        yield url
    finally:
        s3.rm(url, recursive=True)
