# Local LLM Node

A lightweight, self-hosted LLM node that turns your local AI models into a secure, configurable API for your applications and microservices.

## What is Local LLM Node?

Local LLM Node is a small self-hosted service designed to make running local Large Language Models easier.

The idea is simple:

1. Install the service.
2. Point it to your local models.
3. Configure the node from a minimal admin interface.
4. Expose a clean API.
5. Let your applications and microservices use local AI without knowing how the underlying model is served.

The project is intentionally lightweight.

It does not try to implement an LLM inference engine from scratch. Instead, it acts as a small control and API layer on top of inference backends such as Ollama, with support for additional runtimes planned in the future.

## Architecture

```text
                         Applications
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
        Microservice A  Microservice B  Microservice C
              │               │               │
              └───────────────┼───────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │  Local LLM Node   │
                    │                   │
                    │     FastAPI       │
                    │                   │
                    │  - REST API       │
                    │  - Admin API      │
                    │  - Authentication │
                    │  - Model registry │
                    │  - Audit          │
                    │  - Health checks  │
                    │  - Benchmarks     │
                    └─────────┬─────────┘
                              │
                    Inference Backend
                              │
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
              Ollama        vLLM       llama.cpp
                 │
                 ▼
           Local LLM Models
                 │
                 ▼
              CPU / GPU
```

The client application only talks to Local LLM Node.

It does not need to know:

* where the model is stored;
* which inference engine is being used;
* how the model is loaded;
* which GPU is available;
* how much VRAM the model requires.

That complexity stays inside the node.

## Goals

Local LLM Node aims to provide a simple way to turn a local machine into a reusable private AI service.

The main goals are:

* Easy Docker deployment
* Local and private inference
* Simple model management
* Clean APIs for applications and microservices
* Hardware discovery
* Model compatibility checks
* Basic benchmarking
* Auditability
* Replaceable inference backends
* Minimal configuration

## Planned Features

### Model management

Local LLM Node will be able to scan a configured model directory and expose the available models through the API and admin interface.

```text
/models
├── qwen3-8b.gguf
├── qwen3-14b.gguf
└── another-model.gguf
```

Example status:

```text
Qwen3 8B
Status: Ready
Size: 5.2 GB
Backend: Ollama

Qwen3 14B
Status: Available
Size: 9.8 GB
Backend: Ollama
```

### Hardware discovery

The node should automatically detect the hardware available on the host.

For example:

```text
CPU
AMD Ryzen 9

RAM
64 GB

GPU
NVIDIA RTX 4090

VRAM
24 GB

CUDA
Available
```

### Model compatibility

One of the goals of the project is to provide an easy answer to a very common question:

> Can this model run on this machine?

The node should combine model metadata and hardware information to provide an initial compatibility estimation.

```text
Model              Status

Qwen3 8B Q4        ✓ Recommended
Qwen3 14B Q4       ✓ Compatible
Qwen3 30B Q4       ⚠ Limited
Llama 70B Q4       ✗ Insufficient resources
```

Future versions may also verify compatibility by actually loading and benchmarking the model.

### Benchmarking

The node should be able to run lightweight local benchmarks and collect information such as:

```text
Model load time
Time to first token
Tokens per second
Peak VRAM usage
Memory usage
Context size
Concurrent requests
```

This makes it easier to understand which model is appropriate for the available hardware.

## API

Local LLM Node is API-first.

Applications should be able to use the node without depending directly on a specific inference engine.

Example:

```http
POST /v1/chat/completions
```

```json
{
  "model": "qwen3-14b",
  "messages": [
    {
      "role": "user",
      "content": "Explain quantum computing in simple terms."
    }
  ]
}
```

The node internally routes the request to the configured inference backend.

Other planned endpoints include:

```text
GET  /v1/models
GET  /health

GET  /api/system
GET  /api/hardware
GET  /api/models

POST /api/models/{model}/test
POST /api/models/{model}/benchmark
```

## Admin Interface

A minimal admin interface will provide access to the main configuration options.

Planned sections:

```text
Dashboard
Models
Hardware
Inference Engines
API Keys
Benchmarks
Audit
Settings
```

The admin interface is intentionally meant to stay simple.

Local LLM Node is infrastructure first, not another ChatGPT frontend.

## Inference Backends

Inference is delegated to specialized runtimes.

The first supported backend will be:

```text
Ollama
```

The architecture will use a common abstraction so additional backends can be added later.

```python
class InferenceBackend:

    async def list_models(self):
        ...

    async def chat(self, request):
        ...

    async def health(self):
        ...

    async def load_model(self, model):
        ...

    async def unload_model(self, model):
        ...
```

Possible future implementations:

```text
OllamaBackend
VLLMBackend
LlamaCppBackend
```

This keeps the API independent from the inference runtime.

## Docker

The project is designed to run as a containerized service.

A typical deployment may look like:

```text
Docker Compose

├── local-llm-node
│
└── ollama
      │
      └── GPU
```

Example:

```yaml
services:

  local-llm-node:
    image: local-llm-node
    ports:
      - "8000:8000"
    environment:
      OLLAMA_URL: http://ollama:11434
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama
    volumes:
      - ./models:/models
      - ollama_data:/root/.ollama

volumes:
  ollama_data:
```

Only Local LLM Node needs to be exposed to the rest of the infrastructure.

The underlying inference backend can remain on the internal Docker network.

```text
Applications
     │
     ▼
Local LLM Node :8000
     │
     ▼
Ollama :11434
     │
     ▼
GPU
```

## Audit

Local LLM Node will provide basic audit information for inference requests.

For example:

```json
{
  "request_id": "req_01",
  "timestamp": "2026-08-23T12:00:00Z",
  "model": "qwen3-14b",
  "backend": "ollama",
  "latency_ms": 742,
  "status": "success"
}
```

Logging of prompt and response contents should be optional.

This makes it possible to use the node in environments where requests may contain sensitive information without automatically storing their contents.

## Security

The long-term goal is to make the node suitable for private infrastructure.

Planned features include:

* API keys
* Service accounts
* Configurable audit logging
* Internal-only inference backends
* Rate limiting
* Model allowlists
* Secure defaults

The inference runtime should normally not be directly reachable by client applications.

```text
GOOD

Application
    │
    ▼
Local LLM Node
    │
    ▼
Ollama


NOT RECOMMENDED

Application
    │
    ▼
Ollama directly
```

## Initial Roadmap

### v0.1

* FastAPI service
* Docker image
* Ollama backend
* OpenAI-compatible chat endpoint
* Model listing
* Basic admin interface
* CPU/RAM/GPU discovery
* Health checks

### v0.2

* API keys
* Audit logging
* Model compatibility estimation
* Local benchmark suite
* VRAM monitoring
* Model load/unload controls

### v0.3

* vLLM backend
* llama.cpp backend
* Prometheus metrics
* Rate limiting
* Model provenance and hashing
* Extended hardware qualification

## Philosophy

Local LLM Node should remain simple.

The project is not trying to replace:

* Ollama
* vLLM
* llama.cpp
* LocalAI

Those projects focus primarily on inference and model serving.

Local LLM Node focuses on providing a lightweight layer between inference engines and the applications that need to consume them.

```text
Models + Hardware
       │
       ▼
Inference Engine
       │
       ▼
Local LLM Node
       │
       ▼
Your Infrastructure
```

Install it.

Point it to your models.

Expose the API.

Use local AI from anywhere inside your infrastructure.

## License

Licensed under the Apache License, Version 2.0.
