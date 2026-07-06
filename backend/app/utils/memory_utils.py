import gc
import logging
import torch

logger = logging.getLogger("omnivision")

def clear_gpu_memory():
    """
    Aggressively clears GPU VRAM and runs python garbage collection.
    Essential for running multiple large models sequentially on 4GB VRAM.
    """
    logger.debug("Running memory cleanup...")
    # Force python garbage collection
    gc.collect()
    
    # If CUDA is available, clear the cache and IPC memory
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
        
        # Log VRAM usage for debugging
        allocated = torch.cuda.memory_allocated() / (1024 ** 2)
        reserved = torch.cuda.memory_reserved() / (1024 ** 2)
        logger.debug(f"GPU Memory post-cleanup: {allocated:.2f}MB allocated / {reserved:.2f}MB reserved")
    else:
        logger.debug("CUDA not available. CPU GC complete.")
