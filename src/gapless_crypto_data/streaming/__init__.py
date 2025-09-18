"""
Streaming processing package for unlimited dataset handling.

Provides SOTA memory-streaming architecture using Polars for constant memory usage
regardless of dataset size.
"""

from .memory_streaming import StreamingDataProcessor, StreamingGapFiller

__all__ = [
    "StreamingDataProcessor",
    "StreamingGapFiller",
]
