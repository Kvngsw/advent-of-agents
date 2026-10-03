"""End-to-end stream latency and chunking benchmarks."""

import asyncio
import time
import pytest
from src.streaming.media_chunker import chunk_pcm_audio, stream_video_frames
from src.streaming.response_parser import GeminiResponseParser


def test_pcm_audio_chunking() -> None:
    """Verify that PCM audio is chunked correctly with zero-copy memoryviews."""
    raw_data = b"\x00" * 32000  # 1 second of audio
    chunks = list(chunk_pcm_audio(raw_data, chunk_size=640))
    
    assert len(chunks) == 50  # 50 chunks of 20ms
    assert all(isinstance(chunk, memoryview) for chunk in chunks)
    assert all(len(chunk) == 640 for chunk in chunks)


@pytest.mark.asyncio
async def test_video_frame_streaming() -> None:
    """Verify that video frames are streamed at the correct rate."""
    frames = [b"frame1", b"frame2", b"frame3"]
    start_time = time.perf_counter()
    
    streamed = []
    async for frame in stream_video_frames(frames, fps=10.0):
        streamed.append(frame)
        
    duration = time.perf_counter() - start_time
    assert len(streamed) == 3
    assert duration >= 0.15  # 3 frames at 10 FPS should take at least 0.15 seconds (with some buffer)


def test_response_parser_text() -> None:
    """Verify that text chunks are parsed correctly."""
    parser = GeminiResponseParser()
    msg = {
        "serverContent": {
            "modelTurn": {
                "parts": [
                    {"text": "Hello, world!"}
                ]
            }
        }
    }
    text, audio, func = parser.parse_message(msg)
    assert text == "Hello, world!"
    assert audio is None
    assert func is None


def test_response_parser_audio() -> None:
    """Verify that audio chunks are parsed and decoded correctly."""
    parser = GeminiResponseParser()
    import base64
    raw_audio = b"fake-audio-bytes"
    b64_audio = base64.b64encode(raw_audio).decode("utf-8")
    
    msg = {
        "serverContent": {
            "modelTurn": {
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": "audio/pcm;rate=24000",
                            "data": b64_audio
                        }
                    }
                ]
            }
        }
    }
    text, audio, func = parser.parse_message(msg)
    assert text is None
    assert audio == raw_audio
    assert func is None
