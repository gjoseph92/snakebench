import dask


def test_asyncio_comm_config():
    assert dask.config.get("distributed.comm.tcp.backend") == "asyncio"
