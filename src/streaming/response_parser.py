"""Stateful response stream parser for Gemini Live WebSocket messages."""

import base64
from typing import Any, Dict, Optional, Tuple


class GeminiResponseParser:
    """Parses incoming Gemini Live WebSocket messages to extract text, audio, and tool calls."""

    def __init__(self) -> None:
        """Initialize the stateful response parser."""
        pass

    def parse_message(self, message: Dict[str, Any]) -> Tuple[Optional[str], Optional[bytes], Optional[Dict[str, Any]]]:
        """Parse a single WebSocket message from Gemini Live.

        Args:
            message: Parsed JSON message dictionary.

        Returns:
            Tuple of (text_chunk, audio_chunk, function_call).
        """
        text_chunk: Optional[str] = None
        audio_chunk: Optional[bytes] = None
        function_call: Optional[Dict[str, Any]] = None

        server_content = message.get("serverContent", {})
        model_turn = server_content.get("modelTurn", {})
        parts = model_turn.get("parts", [])

        for part in parts:
            # Extract text
            if "text" in part:
                text_chunk = part["text"]

            # Extract audio
            if "inlineData" in part:
                inline_data = part["inlineData"]
                mime_type = inline_data.get("mimeType", "")
                if "audio" in mime_type:
                    data_b64 = inline_data.get("data", "")
                    if data_b64:
                        audio_chunk = base64.b64decode(data_b64)

            # Extract function/tool calls (code execution proposals)
            if "functionCall" in part:
                function_call = part["functionCall"]

        return text_chunk, audio_chunk, function_call
