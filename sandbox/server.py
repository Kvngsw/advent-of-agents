import os
import sys
import time
import json
import hmac
import hashlib
import subprocess
import tempfile
from typing import Any, Dict, Optional, Tuple
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(title="Cloud Run Sandbox Execution Service")

# Secret key for HMAC verification
SECRET_KEY = os.environ.get("SANDBOX_SECRET_KEY", "super-secret-governance-key-12345")

class ExecutionRequest(BaseModel):
    code: str
    capability_token: Optional[str] = None
    timeout_seconds: float = 15.0
    environment_vars: Dict[str, str] = Field(default_factory=dict)

class ExecutionResult(BaseModel):
    success: bool
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: float
    error_code: Optional[str] = None
    error_message: Optional[str] = None

def verify_token(token_str: str, expected_payload_hash: str) -> Tuple[bool, Optional[str]]:
    try:
        parsed = json.loads(token_str)
        token_data = parsed["data"]
        signature = parsed["sig"]
    except Exception:
        return False, "INVALID_TOKEN_FORMAT"

    raw_json = json.dumps(token_data, sort_keys=True).encode("utf-8")
    expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), raw_json, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature, expected_sig):
        return False, "INVALID_SIGNATURE"

    if time.time() > token_data.get("exp", 0):
        return False, "TOKEN_EXPIRED"

    if not hmac.compare_digest(token_data.get("digest", ""), expected_payload_hash):
        return False, "PAYLOAD_MISMATCH"

    return True, None

@app.post("/api/v1/sandbox/execute", response_model=ExecutionResult)
async def execute_code(request: ExecutionRequest) -> ExecutionResult:
    # 1. Verify capability token
    if not request.capability_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing capability token."
        )

    payload_hash = hashlib.sha256(request.code.encode("utf-8")).hexdigest()
    is_valid, error_reason = verify_token(request.capability_token, payload_hash)
    if not is_valid:
        return ExecutionResult(
            success=False,
            exit_code=-1,
            execution_time_ms=0.0,
            error_code="SECURITY_POLICY_VIOLATION",
            error_message=f"Capability token verification failed: {error_reason}"
        )

    # 2. Execute code in a subprocess with restricted environment
    start_time = time.perf_counter()
    try:
        with tempfile.NamedTemporaryFile(suffix=".py", dir="/tmp", delete=False) as temp_file:
            temp_file.write(request.code.encode("utf-8"))
            temp_file_path = temp_file.name

        # Prepare clean environment
        clean_env = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "PYTHONPATH": "/app",
        }
        # Add allowed environment variables
        clean_env.update(request.environment_vars)

        # Run the subprocess
        proc = subprocess.run(
            [sys.executable, temp_file_path],
            capture_output=True,
            text=True,
            env=clean_env,
            timeout=request.timeout_seconds,
        )
        execution_time = (time.perf_counter() - start_time) * 1000.0

        # Clean up the temp file
        try:
            os.remove(temp_file_path)
        except Exception:
            pass

        return ExecutionResult(
            success=(proc.returncode == 0),
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            execution_time_ms=execution_time,
        )

    except subprocess.TimeoutExpired as err:
        execution_time = (time.perf_counter() - start_time) * 1000.0
        try:
            os.remove(temp_file_path)
        except Exception:
            pass
        return ExecutionResult(
            success=False,
            exit_code=-9,
            stdout=err.stdout or "",
            stderr=err.stderr or "Execution timed out.",
            execution_time_ms=execution_time,
            error_code="TIMEOUT",
            error_message=f"Execution exceeded timeout of {request.timeout_seconds} seconds."
        )
    except Exception as err:
        execution_time = (time.perf_counter() - start_time) * 1000.0
        return ExecutionResult(
            success=False,
            exit_code=-1,
            execution_time_ms=execution_time,
            error_code="EXECUTION_ERROR",
            error_message=str(err)
        )
