import pytest
from coiled import Cluster

from snakebench.clusters import CLUSTER_KWARGS

pytestmark = pytest.mark.skip


def test_default_cluster_spinup_time(module_id, auto_benchmark_time):

    with Cluster(name=module_id, **CLUSTER_KWARGS):
        pass
