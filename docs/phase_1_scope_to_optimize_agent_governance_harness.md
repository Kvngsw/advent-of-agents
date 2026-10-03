# Product Specification & Implementation Blueprint: Phase 1 Scope-to-Optimize Agent Governance Harness

**Document Version:** 1.0.0  
**Target Milestone:** Phase 1 (Days 7-8 Integration: Cloud Run Sandbox Execution & Gemini Live Bidirectional Streaming)  
**Author:** Principal Technical Product Manager & Systems Architect  
**Status:** Approved for Implementation  

---

## 1. Problem Statement & Target Personas

### 1.1 Problem Statement
Autonomous robotics, human-robot interaction (HRI), and dynamic automation workflows require running dynamically synthesized agent code while maintaining sub-300ms perceptual latency. Executing unverified LLM-generated code locally presents critical security hazards (host escalation, uncontrolled resource consumption, network scanning). Simultaneously, traditional request-response inference induces multi-second latency, rendering real-time teleoperation, robotic tactile correction, and natural voice interaction unusable.

### 1.2 Target Personas
1. **Robotics & Teleoperation Engineers:** Require low-latency (<300ms) perceptual feedback loops streaming audio/video frames alongside synchronized control primitives.
2. **Autonomous Systems Architects:** Require isolated, ephemeral execution sandboxes (scale-to-zero micro-VMs) with strict cgroup limits for untrusted agent-generated code.
3. **Safety & Governance Officers:** Require deterministic runtime auditing, execution quotas, telemetry traces, and immediate kill-switch mechanisms for rogue automation loops.

---

## 2. User Journey & Critical Success Metrics

### 2.1 End-to-End User Journey
1. **Perceptual Ingestion:** Teleoperation operator / physical sensor feeds sub-300ms bidirectional PCM audio chunks and WebP/JPEG video frames over a persistent WebSocket session into the Gemini Live Multimodal streaming pipeline.
2. **Cognitive Synthesis & Evaluation:** Gemini Live processes incoming multimodal streams, tracks continuous state, and proposes dynamic automation code/commands to address observed spatial changes or voice instructions.
3. **Deterministic Governance Validation:** The Governance Harness intercepts proposed actions, applies abstract syntax tree (AST) safety policies, verifies network egress whitelist limits, and issues a cryptographic capability token.
4. **Isolated Sandboxed Execution:** The code executes inside an isolated Google Cloud Run scale-to-zero micro-VM container with constrained memory (max 512MiB), strict CPU caps (0.5 vCPU), and a hard timeout (15s).
5. **Telemetry & Feedback Ingestion:** Execution stdout/stderr, latency profiles, and return values stream back to the operator console and re-enter the Gemini Live session context for real-time continuous closed-loop control.

### 2.2 Critical Success Metrics & SLAs
| Metric ID | Metric Description | Target Threshold | P99 SLA |
| :--- | :--- | :--- | :--- |
| **METRIC-01** | Bidi-Streaming Perception-to-Audio Latency | < 300 ms | < 450 ms |
| **METRIC-02** | Micro-VM Sandbox Cold-Start Latency | < 1,200 ms | < 2,000 ms |
| **METRIC-03** | Sandbox Memory Overhead (Codespace Dev) | < 384 MiB resident | < 512 MiB resident |
| **METRIC-04** | Malicious Code Containment Rate | 100.0% isolation | 100.0% isolation |
| **METRIC-05** | Stream Frame Drop Rate under Network Jitter | < 1.5% frame loss | < 3.0% frame loss |

---

## 3. Architecture & System Flow

