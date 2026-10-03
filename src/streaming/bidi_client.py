"""Async duplex WebSocket client for Gemini Live Bidirectional Streaming."""

import asyncio
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
                await self