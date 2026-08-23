# Local LLM Node

A lightweight, self-hosted LLM node that turns your local AI models into a secure, configurable API for your applications and microservices.

## v0.1 quick start

The first runnable version provides a FastAPI service, an internal Ollama
backend and three typed endpoints:

```text
GET /health
GET /model_list
GET /machine_info
POST /generate
```

Prepare the project and start the CPU-compatible base stack:

```bash
./install.sh
./run.sh
```

Run it in the background by passing the usual Compose option:

```bash
./run.sh -d
```

The API is then available at `http://localhost:8088`, with interactive OpenAPI
documentation at `http://localhost:8088/docs`. Ollama is intentionally reachable
only from the internal Compose network. FastAPI is bound to `127.0.0.1` by
default because v0.1 does not provide authentication yet.

To use NVIDIA GPUs, install the NVIDIA Container Toolkit and apply the included
override (Docker Compose 2.30 or newer):

```bash
./run.sh --nvidia
```

No model is downloaded automatically. This keeps the initial setup small and
leaves model choice explicit:

```bash
docker compose exec ollama ollama pull llama3.2:1b
curl http://localhost:8088/model_list
```

The host port can be changed without editing the Compose file:

```bash
LOCAL_LLM_NODE_PORT=8181 ./run.sh
```

To make the API reachable from other machines on a trusted network, explicitly
change the bind address. Do not expose this unauthenticated version directly to
the internet:

```bash
LOCAL_LLM_NODE_HOST=0.0.0.0 ./run.sh
```

At the start of v0.1, the following easy-to-remember ports were verified as
available on the development machine: `8000`, `8080`, `8088`, `8181`, `8888`
and `11434`. Port availability can change whenever another service starts;
`8088` is the project default because it is memorable and less commonly used
than `8000` or `8080`.

### API responses

`GET /health` always describes both layers. It returns `ok` when Ollama is
available and `degraded` when FastAPI is running but Ollama cannot be reached:

```json
{
  "status": "ok",
  "service": "local-llm-node",
  "version": "0.1.0",
  "backend": {
    "name": "ollama",
    "status": "available",
    "version": "0.12.6"
  }
}
```

`GET /model_list` returns the models registered in Ollama and responds with
HTTP `503` if the backend is unavailable:

```json
{
  "models": [],
  "count": 0
}
```

`POST /generate` sends one prompt to a model listed by `/model_list`. It is
non-streaming and deliberately keeps the request small:

```json
{
  "model_name": "gemma3:1b",
  "prompt": "Spiega la fotosintesi in due frasi.",
  "thinking": false
}
```

`thinking` defaults to `false`. When the selected model supports it, setting it
to `true` enables backend reasoning but does not expose its trace in the API
response:

```json
{
  "answer": "La fotosintesi converte luce, acqua e anidride carbonica in glucosio e ossigeno. Le piante usano il glucosio come fonte di energia.",
  "time_elapsed_ms": 245
}
```

`time_elapsed_ms` is the total model execution time reported by Ollama, in
milliseconds; it includes any model loading needed for the request.

`GET /machine_info` returns the operating system, CPU, RAM and the NVIDIA GPUs
visible to the API process. GPU discovery uses `nvidia-smi`; the base CPU stack
therefore returns an empty `gpus` list. The NVIDIA override makes GPUs visible
to both FastAPI and Ollama.

### Local development

Install the project and development tools, then run the checks:

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
```

Start FastAPI outside Docker with:

```bash
OLLAMA_URL=http://localhost:11434 uv run uvicorn local_llm_node.main:app --reload
```

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

The included Compose stack has two services:

```text
Docker Compose

├── local-llm-node
│
└── ollama
      │
      └── GPU
```

Only Local LLM Node needs to be exposed to the rest of the infrastructure.

The underlying inference backend can remain on the internal Docker network.

```text
Applications
     │
     ▼
Local LLM Node :8088
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

* FastAPI service and Docker image
* Docker Compose stack with an internal Ollama backend
* Typed health, model-list and machine-info endpoints
* CPU/RAM and optional NVIDIA GPU discovery

### v0.2

* OpenAI-compatible chat endpoint
* Basic admin interface
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
