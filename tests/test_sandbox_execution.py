"""Integration and unit tests for Cloud Run Sandbox Execution."""

import pytest
from fastapi.testclient import TestClient
from sandbox.server import app, ExecutionRequest, ExecutionResult
from src.governance.token_signer import TokenSigner, hash_code_payload
from src.sandbox.cloud_run_client import CloudRunSandboxClient

# Test client for synchronous/direct testing of the FastAPI app
client = TestClient(app)


def test_sandbox_execute_without_token() -> None:
    """Verify that requests without a capability token are rejected."""
    response = client.post(
        "/api/v1/sandbox/execute",
        json={"code": "print('hello')"},
    )
    assert response.status_code == 403
    assert "Missing capability token" in response.json()["detail"]


def test_sandbox_execute_with_invalid_token() -> None:
    """Verify that requests with an invalid capability token are rejected."""
    response = client.post(
        "/api/v1/sandbox/execute",
        json={
            "code": "print('hello')",
            "capability_token": "invalid-token-format",
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is False
    assert result["error_code"] == "SECURITY_POLICY_VIOLATION"


def test_sandbox_execute_success() -> None:
    """Verify successful execution of safe code with a valid token."""
    secret = "super-secret-governance-key-12345"
    signer = TokenSigner(secret_key=secret)
    code = "print('Hello from Sandbox!')"
    payload_hash = hash_code_payload(code)
    token = signer.create_capability_token(payload_hash=payload_hash)

    response = client.post(
        "/api/v1/sandbox/execute",
        json={
            "code": code,
            "capability_token": token,
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["exit_code"] == 0
    assert "Hello from Sandbox!" in result["stdout"]


def test_sandbox_execute_timeout() -> None:
    """Verify that execution times out correctly."""
    secret = "super-secret-governance-key-12345"
    signer = TokenSigner(secret_key=secret)
    code = "import time\ntime.sleep(2)"
    payload_hash = hash_code_payload(code)
    token = signer.create_capability_token(payload_hash=payload_hash)

    response = client.post(
        "/api/v1/sandbox/execute",
        json={
            "code": code,
            "capability_token": token,
            "timeout_seconds": 0.5,
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is False
    assert result["error_code"] == "TIMEOUT"


@pytest.mark.asyncio
async def test_async_sandbox_client() -> None:
    """Verify that the CloudRunSandboxClient works correctly with the FastAPI app."""
    secret = "super-secret-governance-key-12345"
    signer = TokenSigner(secret_key=secret)
    code = "print('Async Client Test')"
    payload_hash = hash_code_payload(code)
    token = signer.create_capability_token(payload_hash=payload_hash)

    from src.governance.schemas import ExecutionRequest as SchemaRequest

    req = SchemaRequest(code=code, capability_token=token)

    # Initialize client with the app transport for in-memory testing
    async with CloudRunSandboxClient(endpoint_url="http://testserver", secret_key=secret) as sandbox_client:
        import httpx
        sandbox_client._client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")
        
        result = await sandbox_client.execute(req)
        assert result.success is True
        assert "Async Client Test" in result.stdout
