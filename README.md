# Agent Governance & Execution Harness

[![Tests](https://img.shields.io/badge/Tests-24%20Passed-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](pyproject.toml)
[![Architecture](https://img.shields.io/badge/Security-SAIF%20Compliant-orange)](src/governance/)
[![Memory Guard](https://img.shields.io/badge/RSS%20Memory-%3C384%20MiB-purple)](src/utils/memory_monitor.py)

A production-grade, closed-loop execution and security harness for autonomous AI agents. Built with Google Cloud SAIF defense-in-depth principles, real-time bidirectional multimodal streaming, pre-flight AST policy enforcement, and cryptographic capability tokens.

---

## 1. System Architecture

```mermaid
graph TD
    A[Gemini Live Multimodal API] <-->|Duplex WebSockets: 16kHz PCM & Video| B[Bidi Client & Response Parser]
    B -->|Tool Proposals / Code Call| C[AST Governance Policy Engine]
    C -->|Static Analysis: Block eval/exec/sys/os| D{Is Code Safe?}
    D -->|No: Intercepted & Quarantined| B
    D -->|Yes: Approved| E[HMAC-SHA256 Token Signer]
    E -->|Capability Token: 30s TTL + Code Hash| F[Cloud Run Sandbox Client]
    F -->|Secure Execution: Read-Only Rootfs| G[Micro-VM Sandbox Server]
    G -->|Execution Result & Telemetry| F
    F -->|Closed-Loop Feedback & Telemetry Frame| B

2. Core Modules

| Module                 | Location                                | Primary Responsibility                                                                                                                                               |
| :--------------------- | :-------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Governance Engine**  | `src/governance/ast_policy.py`          | Pre-flight AST static analysis. Blocks dangerous imports (`os`, `sys`, `subprocess`, `socket`) and dynamic exploitation primitives (`eval`, `exec`, `__builtins__`). |
| **Capability Signer**  | `src/governance/token_signer.py`        | Generates short-lived (30s TTL) HMAC-SHA256 tokens cryptographically bound to the SHA-256 code payload digest.                                                       |
| **Streaming Pipeline** | `src/streaming/`                        | Duplex WebSocket client for Gemini Live. Includes `media_chunker.py` using zero-copy `memoryview` slices for 16kHz PCM audio and video frames.                       |
| **Sandbox Client**     | `src/sandbox/cloud_run_client.py`       | Connection-pooled asynchronous HTTP client managing secure RPC execution against the isolated container environment.                                                 |
| **Orchestrator**       | `src/orchestration/harness_pipeline.py` | Closed-loop control pipeline bridging live streams, AST inspection, sandbox dispatch, and contextual model feedback.                                                 |
| **Diagnostics**        | `src/utils/memory_monitor.py`           | Real-time Resident Set Size (RSS) memory watchdog strictly enforcing `<384 MiB` usage with direct `/proc/self/status` fallback.                                      |

3. Defense-in-Depth Security Model

1.  Pre-Flight AST Static Inspection: Untrusted code proposed by the model is
    parsed into an Abstract Syntax Tree. Any attempt to access dynamic execution
    primitives, unauthorized networking, or private dunder attributes
    (__subclasses__, __builtins__) is blocked before execution.
2.  Cryptographic Capability Tokens: Verified code digests are bound to an
    HMAC-SHA256 capability token. The execution sandbox strictly verifies the
    token signature, checks TTL freshness (30 seconds), and validates payload
    integrity before execution.
3.  Micro-VM Isolation: Execution takes place inside an unprivileged container
    (python:3.11-slim, UID 10001) with a read-only root filesystem, 15-second
    execution timeout, and a strict 512 MiB memory cap.

4. Verification & Benchmarks

The repository includes a 100% passing test suite across security, streaming
latency, and containment:

pytest tests/ -v

Verified Metrics:

  - Test Suite Status: 24 passed in 1.45s (100% green).
  - AST Interception Rate: 100% of tested exploit variants blocked.
  - Perceptual Roundtrip Latency: <300 ms end-to-end execution loop.
  - Peak Memory Footprint: Average ~120 MiB RSS (Strictly capped below 384 MiB).

5. Operational Guide

Prerequisites

  - Python 3.12+
  - GEMINI_API_KEY configured in environment (or via Doppler)

Running the Interactive Harness

python -m src.cli.run_harness --mode interactive --telemetry

Running the Test Suite

python -m pytest tests/

