"""Data schemas for harness governance, execution requests, and telemetry streaming."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ExecutionRequest(BaseModel):
    """Payload representing an untrusted code execution request."""

    code: str = Field(..., description="Python source code snippet proposed for execution.")
    capability_token: Optional[str] = Field(
        default=None, description="HMAC cryptographic token validating pre-flight AST approval."
    )
    timeout_seconds: float = Field(
        default=15.0, ge=1.0, le=30.0, description="Maximum execution timeout window in seconds."
    )
    environment_vars: Dict[str, str] = Field(
        default_factory=dict, description="Allowed ephemeral environment variables."
    )


class ExecutionResult(BaseModel):
    """Payload representing output and execution metrics returned from the sandbox."""

    success: bool = Field(..., description="Indicates whether execution completed without errors or security blocks.")
    exit_code: int = Field(..., description="Process exit status code.")
    stdout: str = Field(default="", description="Standard output captured during execution.")
    stderr: str = Field(default="", description="Standard error captured during execution.")
    execution_time_ms: float = Field(..., ge=0.0, description="Total wall-clock duration of execution in milliseconds.")
    error_code: Optional[str] = Field(
        default=None, description="Standardized error classification (e.g., SECURITY_POLICY_VIOLATION)."
    )
    error_message: Optional[str] = Field(
        default=None, description="Detailed diagnostic or policy violation message."
    )


class TelemetryFrame(BaseModel):
    """Real-time streaming telemetry packet emitted to Gemini context and operator dashboard."""

    session_id: str = Field(..., description="Active session or stream identifier.")
    timestamp: float = Field(..., description="Epoch timestamp of telemetry emission.")
    rss_memory_mb: float = Field(..., ge=0.0, description="Current process resident set size in megabytes.")
    latency_ms: float = Field(..., ge=0.0, description="Measured stream/execution round-trip latency in milliseconds.")
    event_type: str = Field(..., description="Event classification name (e.g., ast_check, execution, latency_ping).")
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary structured context and metrics."
    )
