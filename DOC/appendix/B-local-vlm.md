# 附录 B：本地 VLM 部署（Qwen2-VL）

> 分册说明：进阶模块 B。GPU/CPU 与量化配置。

## B.1 模型选型对比

| 模型 | 参数量 | 最低显存(FP16) | 量化后(4bit) | 中文 | 推荐场景 |
|------|--------|---------------|--------------|------|----------|
| Qwen2-VL-2B | 2B | ~6 GB | ~3 GB | 强 | 轻量/CPU |
| Qwen2-VL-7B | 7B | ~16 GB | ~6 GB | 强 | **推荐** |
| InternVL2-8B | 8B | ~18 GB | ~7 GB | 强 | 高精度 |
| MiniCPM-V-2.6 | 8B | ~17 GB | ~7 GB | 强 | 边缘设备 |

**推荐**：默认 Qwen2-VL-7B（4bit 量化），显存 6GB 即可运行；无 GPU 时回退 Qwen2-VL-2B CPU。

## B.2 模型下载脚本 `scripts/download_model.py`

```python
"""
本地 VLM 模型下载脚本。
支持从 HuggingFace 或 ModelScope（国内更快）下载。
"""
import os
import argparse


def download_from_modelscope(model_id: str, local_dir: str):
    """国内推荐：ModelScope"""
    from modelscope import snapshot_download
    snapshot_download(model_id, local_dir=local_dir)
    print(f"✓ 模型已下载到 {local_dir}")


def download_from_hf(model_id: str, local_dir: str):
    from huggingface_hub import snapshot_download
    snapshot_download(repo_id=model_id, local_dir=local_dir)
    print(f"✓ 模型已下载到 {local_dir}")


MODEL_MAP = {
    "qwen2-vl-7b": {
        "ms": "qwen/Qwen2-VL-7B-Instruct",
        "hf": "Qwen/Qwen2-VL-7B-Instruct",
    },
    "qwen2-vl-2b": {
        "ms": "qwen/Qwen2-VL-2B-Instruct",
        "hf": "Qwen/Qwen2-VL-2B-Instruct",
    },
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2-vl-7b",
                        choices=list(MODEL_MAP.keys()))
    parser.add_argument("--source", default="ms",
                        choices=["ms", "hf"])
    parser.add_argument("--output", default="./models")
    args = parser.parse_args()

    model_ids = MODEL_MAP[args.model]
    local_dir = os.path.join(args.output, args.model)

    if args.source == "ms":
        download_from_modelscope(model_ids["ms"], local_dir)
    else:
        download_from_hf(model_ids["hf"], local_dir)
```

```bash
# 国内下载（ModelScope）
python scripts/download_model.py --model qwen2-vl-7b --source ms
```

## B.3 设备与量化自动配置 `vlm/local_config.py`

```python
import torch
from dataclasses import dataclass


@dataclass
class DeviceConfig:
    device: str           # cuda / cpu / mps
    dtype: torch.dtype
    quantization: str | None  # 4bit / 8bit / None
    max_memory: dict | None


def auto_detect_config(prefer_quantization: bool = True) -> DeviceConfig:
    """
    自动检测硬件并返回最优配置。
    优先级：CUDA(量化) > Apple MPS > CPU
    """
    # 1. NVIDIA GPU
    if torch.cuda.is_available():
        total_mem = (torch.cuda.get_device_properties(0)
                     .total_memory / 1e9)  # GB
        print(f"检测到 CUDA GPU，显存 {total_mem:.1f} GB")

        if total_mem >= 16:
            # 充足显存，FP16 全精度
            return DeviceConfig(
                device="cuda",
                dtype=torch.float16,
                quantization=None,
                max_memory=None,
            )
        elif total_mem >= 6:
            # 中等显存，4bit 量化
            return DeviceConfig(
                device="cuda",
                dtype=torch.float16,
                quantization="4bit" if prefer_quantization else "8bit",
                max_memory={0: f"{int(total_mem - 1)}GB"},
            )
        else:
            print("⚠ 显存不足，回退 CPU")
            return _cpu_config()

    # 2. Apple Silicon (MPS)
    if torch.backends.mps.is_available():
        print("检测到 Apple Silicon MPS")
        return DeviceConfig(
            device="mps",
            dtype=torch.float16,
            quantization=None,
            max_memory=None,
        )

    # 3. CPU 回退
    return _cpu_config()


def _cpu_config() -> DeviceConfig:
    print("使用 CPU 推理（建议使用 2B 模型）")
    return DeviceConfig(
        device="cpu",
        dtype=torch.float32,
        quantization=None,
        max_memory=None,
    )
```

## B.4 完整本地 Provider `vlm/local_qwen.py`（生产级）

```python
import io
import json
import numpy as np
from PIL import Image
import torch

from vlm.provider import VLMProvider
from vlm.local_config import auto_detect_config
from vlm.prompts import (CLASSIFY_PROMPT, SEMANTICS_PROMPT,
                         CALIBRATION_ASSIST_PROMPT)
from vlm.parser import parse_json_response
from core.schemas import ChartType


class LocalQwenProvider(VLMProvider):
    """
    生产级本地 Qwen2-VL Provider。
    特性：自动设备检测、量化、显存管理、懒加载。
    """

    def __init__(self, model_path: str = "/app/models/qwen2-vl-7b",
                 lazy: bool = True):
        self.model_path = model_path
        self.config = auto_detect_config()
        self.model = None
        self.processor = None
        if not lazy:
            self._load_model()

    def _load_model(self):
        """懒加载：首次调用时才载入模型（节省启动内存）"""
        if self.model is not None:
            return

        from transformers import (Qwen2VLForConditionalGeneration,
                                  AutoProcessor, BitsAndBytesConfig)

        print(f"加载本地模型: {self.model_path}")
        kwargs = {
            "torch_dtype": self.config.dtype,
        }

        # 量化配置
        if self.config.quantization == "4bit":
            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
        elif self.config.quantization == "8bit":
            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_8bit=True)

        if self.config.device == "cuda":
            kwargs["device_map"] = "auto"
            if self.config.max_memory:
                kwargs["max_memory"] = self.config.max_memory

        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            self.model_path, **kwargs)

        if self.config.device in ("mps", "cpu") and \
                self.config.quantization is None:
            self.model = self.model.to(self.config.device)

        self.processor = AutoProcessor.from_pretrained(
            self.model_path,
            # 限制图像分辨率以控制显存（科研图通常够用）
            min_pixels=256 * 28 * 28,
            max_pixels=1280 * 28 * 28,
        )
        self.model.eval()
        print("✓ 模型加载完成")

    @torch.inference_mode()
    def _run(self, image: Image.Image, prompt: str,
             max_new_tokens: int = 1024) -> str:
        self._load_model()

        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt},
            ],
        }]

        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True)

        # 处理视觉输入
        from qwen_vl_utils import process_vision_info
        image_inputs, video_inputs = process_vision_info(messages)

        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )

        # 移到目标设备
        if self.config.device != "cpu":
            inputs = inputs.to(self.model.device)

        generated = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,       # 确定性输出
            temperature=1.0,
            num_beams=1,
        )

        # 截取新生成部分
        generated_trimmed = [
            out[len(inp):]
            for inp, out in zip(inputs.input_ids, generated)
        ]
        output = self.processor.batch_decode(
            generated_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]

        # 主动清理显存
        if self.config.device == "cuda":
            torch.cuda.empty_cache()

        return output.strip()

    # ---------- VLMProvider 接口实现 ----------

    async def classify_chart_type(self, img: np.ndarray) -> ChartType:
        pil = Image.fromarray(img)
        text = self._run(pil, CLASSIFY_PROMPT,
                        max_new_tokens=20).strip().lower()
        # 提取第一个匹配的类型词
        for ct in ChartType:
            if ct.value in text:
                return ct
        return ChartType.UNKNOWN

    async def analyze_semantics(self, image_bytes: bytes) -> dict:
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        text = self._run(pil, SEMANTICS_PROMPT, max_new_tokens=1024)
        return parse_json_response(text)

    async def assist_calibration(self, image_bytes: bytes) -> dict:
        """辅助识别坐标轴刻度（本地模型独有便利方法）"""
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        text = self._run(pil, CALIBRATION_ASSIST_PROMPT,
                        max_new_tokens=512)
        return parse_json_response(text)

    def unload(self):
        """显式释放模型显存"""
        if self.model is not None:
            del self.model
            self.model = None
            if self.config.device == "cuda":
                torch.cuda.empty_cache()
            print("✓ 模型已卸载")
```

## B.5 本地部署专用 Dockerfile `backend/Dockerfile.gpu`

```dockerfile
# GPU 版本：基于 NVIDIA CUDA 镜像
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3.11 python3-pip \
    libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-local.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt && \
    pip3 install --no-cache-dir -r requirements-local.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### B.5.1 本地推理依赖 `requirements-local.txt`

```text
torch==2.2.0
transformers==4.45.0
accelerate==0.30.0
bitsandbytes==0.43.0          # 量化
qwen-vl-utils==0.0.8
modelscope==1.13.0            # 国内下载
einops==0.7.0
```

## B.6 docker-compose 本地 VLM 配置

```yaml
# 在 docker-compose.yml 增加 GPU 服务
services:
  backend-gpu:
    build:
      context: ./backend
      dockerfile: Dockerfile.gpu
    profiles: ["local-vlm"]
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./models:/app/models
    environment:
      - VLM_PROVIDER=local
      - LOCAL_MODEL_PATH=/app/models/qwen2-vl-7b
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

```bash
# 启动本地 VLM 版本
docker compose --profile local-vlm up -d
```

## B.7 显存占用估算公式

模型显存占用近似为：

\[
M_{total} = M_{weights} + M_{activations} + M_{kv\_cache}
\]

其中权重部分：

\[
M_{weights} = N_{params} \times \frac{B_{bits}}{8}
\]

例如 7B 模型 4bit 量化：

\[
M_{weights} = 7 \times 10^9 \times \frac{4}{8} = 3.5 \text{ GB}
\]

加上激活与 KV 缓存，实际约需 \(5\sim6\) GB。

---

# 模块 C：前端完整页面与交互流程

完整实现单图提取的**端到端交互流程**，五步向导式 UI。

