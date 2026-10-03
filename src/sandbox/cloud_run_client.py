"""Async client for interacting with the Cloud Run Sandbox Execution service."""

import logging
from typing import Any, Dict, Optional
import httpx

from src.governance.schemas import ExecutionRequest, ExecutionResult

logger = logging.getLogger(__name__)


class CloudRunSandboxClient:
    """Asynchronous client for executing untrusted code in the Cloud Run Sandbox."""

    def __init__(self, endpoint_url: str, secret_key: str) -> None:
        """Initialize the Cloud Run Sandbox Client.

        Args:
            endpoint_url: The base URL of the Cloud Run sandbox service.
            secret_key: The secret key used for HMAC token generation or verification.
        """
        self.endpoint_url = endpoint_url.rstrip("/")
        self.secret_key = secret_key
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "CloudRunSandboxClient":
        """Enter the async context manager, initializing the HTTP client."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(20.0, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the async context manager, closing the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Send an execution request to the Cloud Run sandbox.

        Args:
            request: The ExecutionRequest payload containing code and capability token.

        Returns:
            ExecutionResult containing stdout, stderr, and execution metrics.
        """
        if not self._client:
            raise RuntimeError("Client is not initialized. Use 'async with' context manager.")

        url = f"{self.endpoint_url}/api/v1/sandbox/execute"
        try:
            response = await self._client.post(
                url,
                json=request.model_dump(),
                headers={"Content-Type": "application/json"},
            )
            if response.status_code == 200:
                return ExecutionResult.model_validate(response.json())
            else:
                logger.error(f"Sandbox execution failed with status {response.status_code}: {response.text}")
                return ExecutionResult(
                    success=False,
                    exit_code=-1,
                    execution_time_ms=0.0,
                    error_code="HTTP_ERROR",
                    error_message=f"Sandbox returned status code {response.status_code}: {response.text}",
                )
        except httpx.RequestError as exc:
            logger.exception("Network error occurred while connecting to Cloud Run Sandbox.")
            return ExecutionResult(
                success=False,
                exit_code=-1,
                execution_time_ms=0.0,
                error_code="CONNECTION_FAILED",
                error_message=f"Failed to connect to sandbox: {str(exc)}",
            )
