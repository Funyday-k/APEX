"""本地 VLM 设备与量化配置（需 torch）。"""
from dataclasses import dataclass


@dataclass
class DeviceConfig:
    device: str
    dtype: str
    quantization: str | None
    max_memory: dict | None


def auto_detect_config(prefer_quantization: bool = True) -> DeviceConfig:
    try:
        import torch
    except ImportError:
        return DeviceConfig(device="cpu", dtype="float32", quantization=None, max_memory=None)

    if torch.cuda.is_available():
        total_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
        if total_mem >= 16:
            return DeviceConfig("cuda", "float16", None, None)
        if total_mem >= 6:
            q = "4bit" if prefer_quantization else "8bit"
            return DeviceConfig("cuda", "float16", q, {0: f"{int(total_mem - 1)}GB"})
        return _cpu_config()

    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return DeviceConfig("mps", "float16", None, None)

    return _cpu_config()


def _cpu_config() -> DeviceConfig:
    return DeviceConfig(device="cpu", dtype="float32", quantization=None, max_memory=None)
