"""Typed API and backend schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class BackendHealth(BaseModel):
    """Describe the current state of an inference backend."""

    name: str
    status: Literal["available", "unavailable"]
    version: str | None = None


class HealthResponse(BaseModel):
    """Describe the health of the API and its inference backend."""

    status: Literal["ok", "degraded"]
    service: str
    version: str
    backend: BackendHealth


class ModelDetails(BaseModel):
    """Describe the format and size class of an Ollama model."""

    format: str | None = None
    family: str | None = None
    families: list[str] = Field(default_factory=list)
    parameter_size: str | None = None
    quantization_level: str | None = None


class Model(BaseModel):
    """Describe a model made available by an inference backend."""

    name: str
    model: str
    modified_at: datetime
    size_bytes: int = Field(ge=0)
    digest: str
    details: ModelDetails


class ModelListResponse(BaseModel):
    """Return the models currently available to the node."""

    models: list[Model]
    count: int = Field(ge=0)


class CpuInfo(BaseModel):
    """Describe the CPU resources visible to the service."""

    model: str
    architecture: str
    logical_cores: int = Field(ge=1)


class MemoryInfo(BaseModel):
    """Describe the memory resources visible to the service."""

    total_bytes: int = Field(ge=0)
    available_bytes: int = Field(ge=0)


class GpuInfo(BaseModel):
    """Describe an NVIDIA GPU visible to the service."""

    name: str
    vendor: str
    total_vram_bytes: int = Field(ge=0)
    driver_version: str


class MachineInfoResponse(BaseModel):
    """Describe the hardware and operating system visible to the service."""

    operating_system: str
    kernel_version: str
    cpu: CpuInfo
    memory: MemoryInfo
    gpus: list[GpuInfo]
