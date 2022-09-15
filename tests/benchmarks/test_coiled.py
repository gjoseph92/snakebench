from coiled import Cluster


def test_default_cluster_spinup_time(module_id, auto_benchmark_time):

    with Cluster(name=module_id):
        pass
