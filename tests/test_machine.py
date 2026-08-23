"""Hardware discovery tests."""

from subprocess import CompletedProcess

import local_llm_node.machine as machine


def test_nvidia_gpu_discovery(monkeypatch) -> None:
    """nvidia-smi output is converted to bytes and typed GPU metadata."""
    monkeypatch.setattr(machine.shutil, "which", lambda command: "/bin/nvidia-smi")
    monkeypatch.setattr(
        machine.subprocess,
        "run",
        lambda *args, **kwargs: CompletedProcess(
            args=args,
            returncode=0,
            stdout="NVIDIA RTX 4090, 24564, 580.00\n",
            stderr="",
        ),
    )

    gpus = machine._discover_nvidia_gpus()

    assert len(gpus) == 1
    assert gpus[0].name == "NVIDIA RTX 4090"
    assert gpus[0].total_vram_bytes == 24_564 * 1024 * 1024
    assert gpus[0].driver_version == "580.00"


def test_gpu_discovery_is_empty_without_nvidia_smi(monkeypatch) -> None:
    """GPU discovery returns an empty list when NVIDIA tooling is absent."""
    monkeypatch.setattr(machine.shutil, "which", lambda command: None)

    assert machine._discover_nvidia_gpus() == []
