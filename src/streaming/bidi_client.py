"""Async duplex WebSocket client for Gemini Live Bidirectional Streaming."""

import asyncio
import base64
import json
import logging
import os
from typing import Any, AsyncGenerator, Dict, Optional

import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class GeminiLiveClient:
    """Asynchronous duplex WebSocket client for the Gemini Live Multimodal API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "models/gemini-2.0-flash-exp",
        host: str = "generativelanguage.googleapis.com",
    ) -> None:
        """Initialize the Gemini Live Client.

        Args:
            api_key: Gemini API key. Defaults to GEMINI_API_KEY environment variable.
            model: Gemini model name.
            host: API host address.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = model
        self.host = host
        self.uri = f"wss://{self.host}/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={self.api_key}"
        self._websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._receive_task: Optional[asyncio.Task[None]] = None
        self._ping_task: Optional[asyncio.Task[None]] = None
        self._incoming_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self._is_running = False

    async def __aenter__(self) -> "GeminiLiveClient":
        """Enter the async context manager and connect to the WebSocket."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the async context manager and close the connection."""
        await self.disconnect()

    async def connect(self) -> None:
        """Establish the WebSocket connection and start background tasks."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is missing or empty.")

        logger.info(f"Connecting to Gemini Live API at {self.host}...")
        try:
            self._websocket = await websockets.connect(self.uri)
            self._is_running = True
            self._receive_task = asyncio.create_task(self._receive_loop())
            self._ping_task = asyncio.create_task(self._ping_loop())
            await self._send_setup()
            logger.info("Connected and initialized Gemini Live session.")
        except Exception as exc:
            logger.exception("Failed to connect to Gemini Live API.")
            await self.disconnect()
            raise exc

    async def disconnect(self) -> None:
        """Clean up background tasks and close the WebSocket connection."""
        self._is_running = False

        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass
            self._ping_task = None

        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None

        if self._websocket:
            await self._websocket.close()
            self._websocket = None

    async def _send_setup(self) -> None:
        """Send the initial setup configuration to the Gemini Live session."""
        if not self._websocket:
            raise RuntimeError("WebSocket is not connected.")
        
        setup_msg = {
            "setup": {
                "model": self.model,
                "generationConfig": {
                    "responseModalities": ["AUDIO", "TEXT"]
                }
            }
        }
        await self._websocket.send(json.dumps(setup_msg))

    async def _receive_loop(self) -> None:
        """Background task to continuously receive messages from the WebSocket."""
        try:
            while self._is_running and self._websocket:
                message = await self._websocket.recv()
                if isinstance(message, str):
                    data = json.loads(message)
                    await self._incoming_queue.put(data)
                elif isinstance(message, bytes):
                    # If binary data is received, handle or log it
                    pass
        except ConnectionClosed:
            logger.info("WebSocket connection closed by server.")
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.exception("Error in WebSocket receive loop.")

    async def _ping_loop(self) -> None:
        """Background task to send periodic keep-alive pings."""
        try:
            while self._is_running and self._websocket:
                await asyncio.sleep(15.0)
                try:
                    await self._websocket.ping()
                except Exception:
                    logger.warning("Failed to send WebSocket ping.")
                    break
        except asyncio.CancelledError:
            pass

    async def send_media_chunk(self, data: bytes, mime_type: str) -> None:
        """Send a media chunk (audio or video) to the Gemini Live session.

        Args:
            data: Raw bytes of the media chunk.
            mime_type: MIME type of the media (e.g., "audio/pcm;rate=16000").
        """
        if not self._websocket:
            raise RuntimeError("WebSocket is not connected.")

        encoded_data = base64.b64encode(data).decode("utf-8")
        
        payload = {
            "realtimeInput": {
                "mediaChunks": [
                    {
                        "mimeType": mime_type,
                        "data": encoded_data
                    }
                ]
            }
        }
        await self._websocket.send(json.dumps(payload))

    async def send_text(self, text: str) -> None:
        """Send a text message to the Gemini Live session.

        Args:
            text: Text content to send.
        """
        if not self._websocket:
            raise RuntimeError("WebSocket is not connected.")

        payload = {
            "clientContent": {
                "turns": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": text
                            }
                        ]
                    }
                ],
                "turnComplete": True
            }
        }
        await self._websocket.send(json.dumps(payload))

    async def receive(self) -> Dict[str, Any]:
        """Retrieve the next message from the incoming queue.

        Returns:
            Parsed JSON message dictionary.
        """
        return await self._incoming_queue.get()

    async def get_responses(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Async generator yielding incoming messages from the queue."""
        while self._is_running or not self._incoming_queue.empty():
            try:
                msg = await asyncio.wait_for(self._incoming_queue.get(), timeout=0.5)
                yield msg
            except asyncio.TimeoutError:
                continue
