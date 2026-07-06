"""GPU memory management helpers for staged inference."""

import gc
import logging

import torch

logger = logging.getLogger(__name__)


def clear_gpu_memory() -> None:
    """Release cached GPU memory after model inference."""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    gc.collect()
    logger.debug("GPU memory cache cleared")
