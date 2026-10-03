"""Low-allocation media chunking generators using memoryview for audio and video."""

import asyncio
import time
from typing import AsyncGenerator, Generator


def chunk_pcm_audio(
    data: bytes, chunk_size: int = 640
) -> Generator[memoryview, None, None]:
    """Chunk raw 16kHz 16-bit mono PCM audio into fixed-size frames.

    A 20ms frame at 16kHz is 640 bytes (16000 samples/sec * 2 bytes/sample * 0.02 sec).

    Args:
        data: Raw PCM audio bytes.
        chunk_size: Size of each chunk in bytes.

    Yields:
        memoryview slices of the original data to avoid memory allocation.
    """
    view = memoryview(data)
    length = len(view)
    for i in range(0, length, chunk_size):
        yield view[i : i + chunk_size]


async def stream_video_frames(
    frames: list[bytes], fps: float = 5.0
) -> AsyncGenerator[bytes, None]:
    """Simulate a rate-limited video frame stream.

    Args:
        frames: List of raw image bytes (e.g., JPEG or WebP).
        fps: Target frames per second.

    Yields:
        Raw image bytes at the specified frame rate.
    """
    delay = 1.0 / fps
    for frame in frames:
        start_time = time.perf_counter()
        yield frame
        elapsed = time.perf_counter() - start_time
        remaining = delay - elapsed
        if remaining > 0:
            await asyncio.sleep(remaining)
