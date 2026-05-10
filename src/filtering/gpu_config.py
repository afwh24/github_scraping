from dask_cuda import LocalCUDACluster
from dask.distributed import Client, get_worker

from nemo_curator.utils.distributed_utils import get_client
import os

# Good defaults for a single GPU; tweak for multi-GPU later
def start_gpu_cluster(n_workers=1, rmm_pool="4GB", gpu="0"):
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu)  # e.g. "1" or "0,2"

    cluster = LocalCUDACluster(
        n_workers=n_workers,            # one worker (uses GPU 0 by default)
        rmm_pool_size=rmm_pool,    # pre-allocate GPU memory to reduce fragmentation
        rmm_async = True,
        device_memory_limit="8GB",
        jit_unspill=False,
        threads_per_worker=1
    )
    client = Client(cluster)
    
    return client

    # Set up GPU-enabled Dask client
    # client = get_client(cluster_type="gpu")
    # return client


# # after you do:
# if __name__ == "__main__":
#     start_gpu_cluster(gpu="7")
#     print(os.environ.get("CUDA_VISIBLE_DEVICES"))