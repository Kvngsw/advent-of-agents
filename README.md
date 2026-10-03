# Gemini Live Multimodal Governance & Execution Sandbox                                                                                                            
                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
A production-grade, low-latency agent orchestration and execution governance system built for real-time bidirectional multimodal interaction with Gemini Live      
(`gemini-2.0-flash-exp`) alongside secure, capability-gated code execution sandboxing.                                                                             
                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
---                                                                                                                                                                
                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
## Architecture Overview                                                                                                                                           
                                                                                                                                                                   

                                                                                                                                                                   
                              +------------------------------------+                                                                                               
                                                                                                                                                                   
                              |         Operator CLI / User        |                                                                                               
                                                                                                                                                                   
                              +-----------------+------------------+                                                                                               
                                                                                                                                                                   
                                                |                                                                                                                  
                                                                                                                                                                   
                                                v                                                                                                                  
                                                                                                                                                                   

+-----------------------------+        +------------+-------------+                                                                                                

|   Gemini Live API (BiDi)    |<======>| HarnessPipeline / Client |                                                                                                

| (Audio / Video / Text / TC) |  gRPC/ | (Low-RAM, Streaming Pipel.)|                                                                                              

+-----------------------------+   WS   +------------+-------------+                                                                                                

                                                                                                                                                                   
                                                |                                                                                                                  
                                                                                                                                                                   
                                                | Tool Execution Intent                                                                                            
                                                                                                                                                                   
                                                v                                                                                                                  
                                                                                                                                                                   
                                   +------------+-------------+                                                                                                    
                                                                                                                                                                   
                                   | AST Governance Inspector |                                                                                                    
                                                                                                                                                                   
                                   |  - Module Blacklisting   |                                                                                                    
                                                                                                                                                                   
                                   |  - Obfuscation Defense   |                                                                                                    
                                                                                                                                                                   
                                   +------------+-------------+                                                                                                    
                                                                                                                                                                   
                                                |                                                                                                                  
                                                                                                                                                                   
                                                | Validated Safe AST                                                                                               
                                                                                                                                                                   
                                                v                                                                                                                  
                                                                                                                                                                   
                                   +------------+-------------+                                                                                                    
                                                                                                                                                                   
                                   | TokenSigner (HMAC-SHA256)|                                                                                                    
                                                                                                                                                                   
                                   |  - Payload Hash Binding  |                                                                                                    
                                                                                                                                                                   
                                   |  - Enforced TTL (e.g 30s)|                                                                                                    
                                                                                                                                                                   
                                   +------------+-------------+                                                                                                    
                                                                                                                                                                   
                                                |                                                                                                                  
                                                                                                                                                                   
                                                | Authorized Request                                                                                               
                                                                                                                                                                   
                                                v                                                                                                                  
                                                                                                                                                                   
                                   +------------+-------------+                                                                                                    
                                                                                                                                                                   
                                   |  Cloud Run Sandbox Exec  |                                                                                                    
                                                                                                                                                                   
                                   |  - Ephemeral Isolation   |                                                                                                    
                                                                                                                                                                   
                                   |  - Low Memory Footprint  |                                                                                                    
                                                                                                                                                                   
                                   +--------------------------+                                                                                                    
                                                                                                                                                                   

                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
---                                                                                                                                                                
                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
## Key Subsystems                                                                                                                                                  
                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
### 1. Bidirectional Multimodal Streaming (`src/streaming/`)                                                                                                       
                                                                                                                                                                   
- **`GeminiLiveClient` (`bidi_client.py`)**: Asynchronous full-duplex WebSocket connection to `generativelanguage.googleapis.com` supporting concurrent upstream   
streaming (PCM audio, video frames, text) and downstream real-time chunks.                                                                                         
                                                                                                                                                                   
- **`GeminiResponseParser` (`response_parser.py`)**: Zero-copy parser handling server turns, text generation fragments, inline PCM audio payloads, and tool call   
requests (`execute_code`).                                                                                                                                         
                                                                                                                                                                   
- **`media_chunker.py`**: Memory-efficient generator utilities for streaming raw PCM audio frames (chunks of 640 bytes / 20ms) and throttled video frames.         
                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
### 2. Static AST Governance & Token Signing (`src/governance/`)                                                                                                   
                                                                                                                                                                   
- **`ASTGovernancePolicy` (`ast_policy.py`)**: Strict Python AST inspection engine that blocks:                                                                    
                                                                                                                                                                   
  - Unauthorized imports (`os`, `sys`, `subprocess`, `socket`, `shutil`, `ctypes`, etc.).                                                                          
                                                                                                                                                                   
  - Obfuscation and dynamic execution primitives (`eval`, `exec`, `__import__`, `globals`, `locals`, `compile`).                                                   
                                                                                                                                                                   
  - Introspection and sandbox escape vectors (`__subclasses__`, `__bases__`, `__mro__`, `__builtins__`).                                                           
                                                                                                                                                                   
- **`TokenSigner` (`token_signer.py`)**: Generates cryptographically secure, timestamped HMAC-SHA256 capability tokens bound to the SHA-256 hash of the sanitized  
code payload with strict expiration limits (TTL).                                                                                                                  
                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
### 3. Isolated Execution Sandbox (`sandbox/` & `src/sandbox/`)                                                                                                    
                                                                                                                                                                   
- **FastAPI Sandbox Server (`sandbox/server.py`)**: Containerized execution endpoint enforcing token authenticity and payload integrity before executing Python    
scripts in an isolated process with strict resource limits and timeouts.                                                                                           
                                                                                                                                                                   
- **`CloudRunSandboxClient` (`src/sandbox/cloud_run_client.py`)**: Asynchronous HTTP client configured with defensive timeout, retry, and connection-pooling       
semantics.                                                                                                                                                         
                                                                                                                                                                   
- **Containerization (`sandbox/Dockerfile`, `scripts/deploy_sandbox.sh`)**: Minimal, low-footprint Linux runtime ready for deployment to Google Cloud Run.         
                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
### 4. Harness Pipeline & CLI (`src/orchestration/`, `src/cli/`, `src/utils/`)                                                                                     
                                                                                                                                                                   
- **`HarnessPipeline` (`harness_pipeline.py`)**: Coordinates the end-to-end loop: establishes the Gemini Live session, mediates user input, evaluates tool         
invocation against security policies, issues capability tokens, dispatches sandboxed execution, and feeds results back to Gemini.                                  
                                                                                                                                                                   
- **`run_harness.py`**: Production CLI supporting interactive text/multimodal sessions, mock modes, and live RSS telemetry tracking.                               
                                                                                                                                                                   
- **`memory_monitor.py`**: Low-overhead memory tracking verifying compliance with low-RAM deployment constraints.                                                  
                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
---                                                                                                                                                                
                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
## Directory Structure                                                                                                                                             
                                                                                                                                                                   

.                                                                                                                                                                  

├── .gitignore                                                                                                                                                     

├── README.md                                                                                                                                                      

├── docs/                                                                                                                                                          

│   ├── phase_1_optimized_execution_plan.md                                                                                                                        

│   ├── phase_1_scope_to_optimize_agent_governance_harness.md                                                                                                      

│   └── verification_report.md                                                                                                                                     

├── sandbox/                                                                                                                                                       

│   ├── Dockerfile                                                                                                                                                 

│   ├── requirements.txt                                                                                                                                           

│   └── server.py                                                                                                                                                  

├── scripts/                                                                                                                                                       

│   └── deploy_sandbox.sh                                                                                                                                          

├── src/                                                                                                                                                           

│   ├── cli/                                                                                                                                                       

│   │   └── run_harness.py                                                                                                                                         

│   ├── governance/                                                                                                                                                

│   │   ├── ast_policy.py                                                                                                                                          

│   │   ├── schemas.py                                                                                                                                             

│   │   └── token_signer.py                                                                                                                                        

│   ├── orchestration/                                                                                                                                             

│   │   └── harness_pipeline.py                                                                                                                                    

│   ├── sandbox/                                                                                                                                                   

│   │   └── cloud_run_client.py                                                                                                                                    

│   ├── streaming/                                                                                                                                                 

│   │   ├── bidi_client.py                                                                                                                                         

│   │   ├── media_chunker.py                                                                                                                                       

│   │   └── response_parser.py                                                                                                                                     

│   └── utils/                                                                                                                                                     

│       └── memory_monitor.py                                                                                                                                      

└── tests/                                                                                                                                                         

                                                                                                                                                                   
├── test_ast_governance.py                                                                                                                                         
                                                                                                                                                                   
├── test_bidi_latency.py                                                                                                                                           
                                                                                                                                                                   
└── test_sandbox_execution.py                                                                                                                                      
                                                                                                                                                                   

                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
---                                                                                                                                                                
                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
## Getting Started                                                                                                                                                 
                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
### Prerequisites                                                                                                                                                  
                                                                                                                                                                   
- Python 3.10+                                                                                                                                                     
                                                                                                                                                                   
- Active Google Gemini API Key with access to `gemini-2.0-flash-exp`                                                                                               
                                                                                                                                                                   
- Docker (optional, for local sandbox containerization)                                                                                                            
                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
### Environment Configuration                                                                                                                                      
                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
Export the required environment variables:                                                                                                                         
                                                                                                                                                                   

export GEMINI_API_KEY="your-gemini-api-key"                                                                                                                        

export SANDBOX_SECRET_KEY="your-cryptographic-signing-secret"                                                                                                      

export SANDBOX_URL="http://localhost:8080"                                                                                                                         

                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
### Installation                                                                                                                                                   
                                                                                                                                                                   

python3 -m venv .venv                                                                                                                                              

source .venv/bin/activate                                                                                                                                          

pip install -r sandbox/requirements.txt                                                                                                                            

pip install pytest pytest-asyncio                                                                                                                                  

                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
---                                                                                                                                                                
                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
## Running the Components                                                                                                                                          
                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
### 1. Launch the Sandbox Server                                                                                                                                   
                                                                                                                                                                   

uvicorn sandbox.server:app --host 0.0.0.0 --port 8080 --workers 1                                                                                                  

                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
### 2. Launch the Orchestration Harness CLI                                                                                                                        
                                                                                                                                                                   

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Interactive mode with memory telemetry enabled                                                                                                                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

python3 -m src.cli.run_harness --mode interactive --telemetry                                                                                                      

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Non-interactive / single-query execution                                                                                                                        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

python3 -m src.cli.run_harness --prompt "Calculate the first 50 fibonacci numbers"                                                                                 

                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
---                                                                                                                                                                
                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
## Testing & Verification                                                                                                                                          
                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
Run the full suite of unit and integration tests:                                                                                                                  
                                                                                                                                                                   

pytest -v tests/                                                                                                                                                   

                                                                                                                                                                   
                                                                                                                                                                   
                                                                                                                                                                   
Test coverage includes:                                                                                                                                            
                                                                                                                                                                   
- **`tests/test_ast_governance.py`**: AST module blacklisting, identifier blocking, exploit evasion, and HMAC capability token lifecycle.                          
                                                                                                                                                                   
- **`tests/test_bidi_latency.py`**: PCM chunking, video frame streaming generators, and Gemini server message parsing.                                             
                                                                                                                                                                   
- **`tests/test_sandbox_execution.py`**: HTTP sandbox authorization, timeout enforcement, output capture, and client resilience.                                   
                                                                                                                                                                   
