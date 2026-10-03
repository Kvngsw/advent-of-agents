"""Closed-loop orchestration pipeline connecting live stream inputs to AST evaluation, sandbox execution, and telemetry feedback loops."""

import asyncio
import logging
import time
from typing import Any, Dict, Optional

from src.governance.ast_policy import validate_code_safety
from src.governance.schemas import ExecutionRequest, TelemetryFrame
from src.governance.token_signer import TokenSigner, hash_code_payload
from src.sandbox.cloud_run_client import CloudRunSandboxClient
from src.streaming.bidi_client import GeminiLiveClient
from src.streaming.response_parser import GeminiResponseParser
from src.utils.memory_monitor import get_rss_memory_mb

logger = logging.getLogger(__name__)


class HarnessPipeline:
    """Orchestrates the closed-loop agent execution harness."""

    def __init__(
        self,
        api_key: str,
        sandbox_url: str,
        secret_key: str,
        session_id: str = "default-session",
        enable_telemetry: bool = True,
    ) -> None:
        """Initialize the Harness Pipeline.

        Args:
            api_key: Gemini API key.
            sandbox_url: Base URL of the Cloud Run sandbox service.
            secret_key: Secret key for HMAC token generation.
            session_id: Unique session identifier.
            enable_telemetry: Whether to emit telemetry frames.
        """
        self.api_key = api_key
        self.sandbox_url = sandbox_url
        self.secret_key = secret_key
        self.session_id = session_id
        self.enable_telemetry = enable_telemetry
        self.signer = TokenSigner(secret_key=self.secret_key)
        self.parser = GeminiResponseParser()

    async def run(self) -> None:
        """Run the closed-loop orchestration pipeline."""
        logger.info("Starting Harness Pipeline...")
        
        async with GeminiLiveClient(api_key=self.api_key) as bidi_client:
            async with CloudRunSandboxClient(
                endpoint_url=self.sandbox_url, secret_key=self.secret_key
            ) as sandbox_client:
                
                logger.info("Pipeline connected and ready.")
                
                async for message in bidi_client.get_responses():
                    start_time = time.perf_counter()
                    
                    # Parse incoming message
                    text, audio, func_call = self.parser.parse_message(message)
                    
                    if text:
                        logger.info(f"Received text from Gemini: {text}")
                    
                    if func_call:
                        logger.info(f"Received code execution proposal: {func_call}")
                        
                        # Extract code from function call
                        code = func_call.get("args", {}).get("code", "")
                        if not code:
                            logger.warning("Empty code block in proposal.")
                            continue
                        
                        # 1. Pre-flight AST Safety Check
                        is_safe, violations = validate_code_safety(code)
                        
                        if not is_safe:
                            logger.warning(f"AST Safety Check Failed: {violations}")
                            # Send failure response back to Gemini
                            await bidi_client.send_text(
                                f"AST Security Check Failed: {'; '.join(violations)}"
                            )
                            continue
                        
                        # 2. Generate Capability Token
                        payload_hash = hash_code_payload(code)
                        token = self.signer.create_capability_token(payload_hash=payload_hash)
                        
                        # 3. Execute in Sandbox
                        req = ExecutionRequest(code=code, capability_token=token)
                        logger.info("Dispatching execution request to sandbox...")
                        result = await sandbox_client.execute(req)
                        
                        # 4. Send execution result back to Gemini context
                        logger.info(f"Execution completed. Success: {result.success}")
                        response_payload = {
                            "success": result.success,
                            "exit_code": result.exit_code,
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "execution_time_ms": result.execution_time_ms,
                        }
                        await bidi_client.send_text(
                            f"Execution Result: {response_payload}"
                        )
                        
                        # 5. Emit Telemetry Frame
                        if self.enable_telemetry:
                            latency = (time.perf_counter() - start_time) * 1000.0
                            rss_mem = get_rss_memory_mb()
                            telemetry = TelemetryFrame(
                                session_id=self.session_id,
                                timestamp=time.time(),
                                rss_memory_mb=rss_mem,
                                latency_ms=latency,
                                event_type="execution",
                                details={
                                    "success": result.success,
                                    "exit_code": result.exit_code,
                                    "execution_time_ms": result.execution_time_ms,
                                },
                            )
                            logger.info(f"Telemetry Frame: {telemetry.model_dump_json()}")
