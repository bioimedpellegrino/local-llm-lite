"""Discover hardware resources visible to the service."""

import os
import platform
import shutil
import subprocess
from pathlib import Path

from local_llm_node.schemas import (
    CpuInfo,
    GpuInfo,
    MachineInfoResponse,
    MemoryInfo,
)

MEBIBYTE_IN_BYTES = 1024 * 1024


def discover_machine_info() -> MachineInfoResponse:
    """Return operating system, CPU, memory and NVIDIA GPU information."""
    return MachineInfoResponse(
        operating_system=platform.system(),
        kernel_version=platform.release(),
        cpu=_discover_cpu_info(),
        memory=_discover_memory_info(),
        gpus=_discover_nvidia_gpus(),
    )


def _discover_cpu_info() -> CpuInfo:
    """Return CPU details visible to the current process."""
    return CpuInfo(
        model=_read_cpu_model(),
        architecture=platform.machine(),
        logical_cores=os.cpu_count() or 1,
    )


def _read_cpu_model() -> str:
    """Read the CPU model from procfs when it is available."""
    cpuinfo_path = Path("/proc/cpuinfo")
    try:
        for line in cpuinfo_path.read_text(encoding="utf-8").splitlines():
            if line.lower().startswith(("model name", "hardware")):
                return line.split(":", maxsplit=1)[1].strip()
    except (OSError, IndexError):
        pass

    return platform.processor() or "unknown"


def _discover_memory_info() -> MemoryInfo:
    """Return total and currently available memory from procfs."""
    values: dict[str, int] = {}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            key, raw_value = line.split(":", maxsplit=1)
            if key in {"MemTotal", "MemAvailable"}:
                values[key] = int(raw_value.strip().split()[0]) * 1024
    except (OSError, ValueError, IndexError):
        pass

    return MemoryInfo(
        total_bytes=values.get("MemTotal", 0),
        available_bytes=values.get("MemAvailable", 0),
    )


def _discover_nvidia_gpus() -> list[GpuInfo]:
    """Return NVIDIA GPUs reported by nvidia-smi, when available."""
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi is None:
        return []

    try:
        result = subprocess.run(
            [
                nvidia_smi,
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return []

    gpus = []
    for line in result.stdout.splitlines():
        fields = [field.strip() for field in line.split(",")]
        if len(fields) != 3:
            continue
        name, memory_mib, driver_version = fields
        try:
            total_vram_bytes = int(memory_mib) * MEBIBYTE_IN_BYTES
        except ValueError:
            continue
        gpus.append(
            GpuInfo(
                name=name,
                vendor="NVIDIA",
                total_vram_bytes=total_vram_bytes,
                driver_version=driver_version,
            )
        )
    return gpus
