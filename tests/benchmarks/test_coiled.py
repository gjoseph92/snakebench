from coiled import Cluster


def test_default_cluster_spinup_time(cluster_name, auto_benchmark_time):

    with Cluster(name=cluster_name):
        pass
