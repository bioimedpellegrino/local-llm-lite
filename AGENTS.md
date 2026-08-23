# AGENTS.md

## Project philosophy

This project must remain simple, understandable and maintainable.

Prefer straightforward solutions over clever ones.

The goal is not to demonstrate how many patterns, abstractions or libraries can be used. The goal is to solve each problem with the smallest clean solution that remains correct, extensible and easy to understand.

Always optimize first for:

1. correctness;
2. readability;
3. simplicity;
4. maintainability;
5. testability;
6. performance, when performance actually matters.

Do not introduce complexity without a concrete reason.

---

## Coding style

Follow the existing coding style of the repository.

When adding new code:

* write minimal and readable code;
* use descriptive and meaningful variable names;
* prefer explicit code over clever shortcuts;
* keep functions and methods focused on one responsibility;
* avoid deeply nested logic;
* avoid unnecessary abstractions;
* avoid premature generalization;
* avoid duplicated logic when a simple reusable abstraction clearly improves the code;
* prefer composition over complicated inheritance hierarchies;
* use Python typing where it improves clarity;
* follow standard Python and OSS best practices;
* follow PEP 8;
* keep imports clean and organized;
* remove unused code;
* do not leave commented-out code;
* do not introduce dependencies when the same result can reasonably be achieved with the standard library or an existing dependency.

A new abstraction should exist because it solves a real architectural problem, not because it might theoretically be useful later.

---

## Naming

Names must explain what the code does.

Prefer:

```python
available_gpu_memory
model_path
inference_backend
model_metadata
benchmark_result
```

over:

```python
mem
p
backend_obj
data
res
```

Avoid generic names such as:

```python
data
info
obj
manager
helper
utils
thing
temp
```

unless their meaning is immediately obvious from the local context.

Boolean variables should read naturally:

```python
is_available
is_compatible
has_enough_memory
should_load_model
```

---

## Functions and methods

Functions and methods should be small and focused.

A function should normally do one conceptual thing.

Prefer:

```text
discover hardware
        ↓
extract model metadata
        ↓
check compatibility
        ↓
return result
```

instead of one large function that performs the entire process internally.

Do not split code into tiny functions merely for the sake of having more functions. Split when doing so makes the problem easier to understand, test or reuse.

---

## Docstrings

Every method must have a docstring.

Functions that contain application logic should also have a docstring.

Docstrings should be short, useful and concrete.

Prefer:

```python
def get_available_vram() -> int:
    """Return the currently available GPU memory in bytes."""
```

Do not write verbose docstrings that simply repeat the implementation.

For more complex methods, document:

* what the method does;
* important arguments;
* return value;
* relevant exceptions or side effects.

Example:

```python
async def load_model(model_name: str) -> ModelStatus:
    """Load a model into the configured inference backend.

    Args:
        model_name: Name of the registered model to load.

    Returns:
        Current status of the loaded model.

    Raises:
        ModelNotFoundError: If the model is not registered.
        BackendUnavailableError: If the inference backend is unavailable.
    """
```

---

## Problem-solving style

Before implementing a change, understand the actual problem.

Do not immediately start coding.

Reason in this order:

```text
What is the actual problem?
        ↓
What are the inputs and outputs?
        ↓
What component should own this responsibility?
        ↓
What is the simplest correct solution?
        ↓
What edge cases matter?
        ↓
Implement
        ↓
Test
        ↓
Refactor only if necessary
```

Break larger problems into independent smaller problems.

Prefer reasoning from concrete cases before introducing generalized solutions.

When several solutions are possible:

1. identify the simplest viable approach;
2. compare meaningful trade-offs;
3. choose the solution with the least unnecessary complexity;
4. preserve the possibility of extending it later when reasonably possible.

Do not design infrastructure for hypothetical future requirements.

---

## Architecture

Keep responsibilities clearly separated.

The intended high-level architecture is:

```text
Applications / Microservices
            │
            ▼
         FastAPI
            │
            ▼
     Application layer
            │
            ▼
   InferenceBackend interface
            │
      ┌─────┴─────┐
      ▼           ▼
   Ollama        vLLM
  initially      later
```

FastAPI is the API and control layer.

Inference engines are responsible for actually running models.

Do not load LLMs directly inside FastAPI workers.

Do not couple API routes directly to Ollama.

Use an inference backend abstraction so that Ollama can later be replaced or complemented by other runtimes.

For example:

```python
class InferenceBackend(ABC):
    """Define the interface implemented by inference backends."""

    @abstractmethod
    async def list_models(self) -> list[Model]:
        """Return the models available through this backend."""

    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Generate a chat completion."""

    @abstractmethod
    async def health(self) -> BackendHealth:
        """Return the current backend health status."""
```

The first implementation should remain simple:

```text
InferenceBackend
      │
      ▼
OllamaBackend
```

Do not implement additional backends until needed.

---

## API design

The project is API-first.

APIs should be:

* predictable;
* typed;
* versioned where appropriate;
* easy to consume from other microservices;
* consistent in error handling;
* explicit about inputs and outputs.

Use Pydantic models for request and response schemas.

Avoid returning loosely structured dictionaries when a meaningful schema can be defined.

Prefer:

```python
class HardwareInfo(BaseModel):
    cpu_name: str
    total_ram_bytes: int
    gpu_name: str | None
    total_vram_bytes: int | None
```

instead of:

```python
return {
    "cpu": ...,
    "ram": ...,
    "gpu": ...
}
```

when the object is part of a stable application interface.

---

## Error handling

Errors should be explicit and useful.

Do not silently ignore failures.

Do not use broad exception handlers such as:

```python
except Exception:
    pass
```

unless there is an exceptional and documented reason.

Prefer domain-specific exceptions when they improve clarity:

```python
ModelNotFoundError
BackendUnavailableError
InsufficientMemoryError
ModelLoadError
```

Translate internal exceptions into appropriate API responses at the API boundary.

Do not mix HTTP-specific logic into the core application layer.

---

## Logging

Logs should help understand what happened without becoming noise.

Log meaningful events such as:

* backend startup;
* backend failures;
* model discovery;
* model loading and unloading;
* benchmark execution;
* hardware detection failures;
* inference errors.

Do not log secrets.

Do not log prompt or response contents by default.

Sensitive inference content must only be logged when explicitly enabled by configuration.

---

## Security

Assume the service may eventually run in environments containing sensitive data.

Therefore:

* never hardcode secrets;
* use environment variables or configuration files for secrets;
* never commit `.env` files;
* validate external input;
* do not expose inference backends directly unless explicitly configured;
* use secure defaults;
* avoid logging request contents by default;
* minimize privileges;
* keep dependencies updated and limited.

---

## Testing

Every meaningful feature must have tests.

Prefer small tests that verify behavior rather than implementation details.

Test:

* normal behavior;
* relevant edge cases;
* expected errors;
* API contracts;
* backend failures where applicable.

Mock external inference backends in unit tests.

Do not require a real GPU or running Ollama instance for the normal unit-test suite.

GPU/backend integration tests should be clearly separated and optional.

Before considering a change complete, run the project's available checks, including:

```bash
pytest
ruff check .
```

and any additional configured formatting or type-checking tools.

Do not modify tests merely to make an incorrect implementation pass.

---

## OSS quality

Treat the repository as a public open-source project.

Code should be understandable by somebody who did not write it.

When adding a feature:

* keep public interfaces clear;
* avoid project-specific hacks;
* add tests;
* update documentation when behavior changes;
* keep configuration discoverable;
* preserve backward compatibility when reasonable;
* avoid unnecessary breaking changes;
* provide useful error messages;
* keep setup simple.

A contributor should be able to understand the architecture without reading the entire repository.

---

## Dependencies

Be conservative when adding dependencies.

Before adding a package, ask:

```text
Do we actually need it?
Can the standard library do this cleanly?
Is an existing dependency already able to do it?
Does the dependency add more complexity than it removes?
```

If a small amount of straightforward code replaces a large dependency, prefer the straightforward code.

Do not reimplement complex, security-sensitive or well-solved functionality merely to avoid a dependency.

---

## Refactoring

Do not refactor unrelated code while implementing a feature.

Prefer small, focused changes.

Refactor when:

* duplication is becoming meaningful;
* a responsibility is clearly misplaced;
* the current structure makes the requested feature difficult to implement correctly;
* readability materially improves.

Do not refactor simply to introduce a preferred design pattern.

---

## Comments

Code should primarily explain itself through structure and naming.

Use comments to explain **why**, not to narrate **what** the next line does.

Good:

```python
# Keep a safety margin because the runtime needs VRAM in addition to model weights.
usable_vram = total_vram * 0.9
```

Avoid:

```python
# Calculate usable VRAM.
usable_vram = total_vram * 0.9
```

---

## Configuration

Configuration should be explicit and have sensible defaults.

Environment-specific values must not be hardcoded.

Prefer a single clear settings layer rather than reading environment variables throughout the codebase.

For example:

```python
class Settings(BaseSettings):
    """Define application configuration."""

    ollama_url: str = "http://ollama:11434"
    model_directory: Path = Path("/models")
    audit_enabled: bool = True
```

Other modules should consume the settings object rather than accessing environment variables directly.

---

## Decision rule

When uncertain between two implementations, prefer the one that is:

```text
simpler
more explicit
easier to read
easier to test
less coupled
easier to remove later
```

provided that it correctly solves the current problem.

Do not optimize for architectural elegance at the expense of understandability.

---

## Final check before completing work

Before considering a task finished, verify:

* Does the implementation solve the actual requested problem?
* Is there a simpler way to achieve the same result?
* Are variable and method names clear?
* Does every method have a useful docstring?
* Are responsibilities in the correct module?
* Did we introduce unnecessary abstractions?
* Did we introduce an unnecessary dependency?
* Are relevant edge cases handled?
* Are there tests?
* Do existing tests still pass?
* Is sensitive data kept out of logs?
* Would another developer understand this code without an explanation?

If the answer to any of these is no, fix it before considering the task complete.
