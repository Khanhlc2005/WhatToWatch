import logging

logger = logging.getLogger(__name__)


def cuda_available() -> bool:
    try:
        import torch
        return bool(torch.cuda.is_available())
    except (ImportError, OSError, RuntimeError, AssertionError):
        # Missing torch or an unusable CUDA runtime means CPU is the safe choice.
        return False


def resolve_device(requested: str) -> str:
    """Resolve a configured device: "auto" picks CUDA when usable, otherwise CPU.

    An explicit "cuda*" request without a usable GPU falls back to CPU instead of crashing.
    """
    value = (requested or "auto").strip().lower()
    if value == "auto":
        return "cuda" if cuda_available() else "cpu"
    if value.startswith("cuda") and not cuda_available():
        logger.warning("Device %r requested but CUDA is unavailable; falling back to cpu", requested)
        return "cpu"
    return value
