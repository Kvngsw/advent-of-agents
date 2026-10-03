"""CLI entrypoint for running the Agent Governance Harness."""

import argparse
import asyncio
import logging
import os
import sys

from src.orchestration.harness_pipeline import HarnessPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Parse arguments and run the interactive harness pipeline."""
    parser = argparse.ArgumentParser(description="Agent Governance Harness CLI")
    parser.add_argument(
        "--mode",
        choices=["interactive", "batch"],
        default="interactive",
        help="Execution mode (default: interactive)",
    )
    parser.add_argument(
        "--telemetry",
        action="store_true",
        default=True,
        help="Enable real-time telemetry streaming",
    )
    parser.add_argument(
        "--sandbox-url",
        default="http://localhost:8080",
        help="Base URL of the Cloud Run sandbox service",
    )
    parser.add_argument(
        "--secret-key",
        default="super-secret-governance-key-12345",
        help="Secret key for HMAC token generation",
    )
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is missing.")
        sys.exit(1)

    pipeline = HarnessPipeline(
        api_key=api_key,
        sandbox_url=args.sandbox_url,
        secret_key=args.secret_key,
        enable_telemetry=args.telemetry,
    )

    try:
        await pipeline.run()
    except KeyboardInterrupt:
        logger.info("Harness pipeline stopped by user.")
    except Exception as exc:
        logger.exception(f"Pipeline execution failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
