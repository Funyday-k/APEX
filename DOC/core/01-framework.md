# 主框架规格（§1–17）

> 分册说明：完整指导书 §1–17。索引见 [DOC/README.md](../README.md)。

> **项目代号**：SciPlot-Extractor
> **目标**：跨平台、易部署的本地 Web 应用，结合传统 CV 与大模型视觉（VLM），从任意科研图表中精确提取结构化数据。
> **核心原则**：数值由 CV 精确提取，VLM 仅负责语义理解与辅助标定，人机协同保证最终准确性。

---

## 目录

1. [总体架构](#1-总体架构)
2. [技术栈与项目结构](#2-技术栈与项目结构)
3. [部署方案](#3-部署方案)
4. [后端核心骨架](#4-后端核心骨架)
5. [模块一：图像预处理](#5-模块一图像预处理)
6. [模块二：图类型分类](#6-模块二图类型分类)
7. [模块三：坐标系标定](#7-模块三坐标系标定)
8. [模块四：CV 数据提取引擎](#8-模块四cv-数据提取引擎)
9. [模块五：OCR 文本提取](#9-模块五ocr-文本提取)
10. [模块六：VLM 抽象层与 Prompt](#10-模块六vlm-抽象层与-prompt)
11. [模块七：交叉验证与置信度](#11-模块七交叉验证与置信度)
12. [模块八：输出与导出](#12-模块八输出与导出)
13. [模块九：前端交互画布](#13-模块九前端交互画布)
14. [模块十：人机协同校正](#14-模块十人机协同校正)
15. [数据库与存储](#15-数据库与存储)
16. [API 设计](#16-api-设计)
17. [测试与精度评估](#17-测试与精度评估)
18. [开发路线图](#18-开发路线图)

---

## 1. 总体架构

```
┌──────────────────────────────────────────────────────────────┐
│                       前端 (Web UI)                            │
│   React + TS + Konva 交互画布 + ECharts 重建预览               │
└───────────────────────────┬──────────────────────────────────┘
                            │ REST + WebSocket
┌───────────────────────────▼──────────────────────────────────┐
│                     后端 API (FastAPI)                         │
│                                                                │
│  ┌──────────────────── Orchestrator 调度器 ─────────────────┐ │
│  │  1.预处理 → 2.类型识别 → 3.标定 → 4.提取 → 5.验证 → 6.导出│ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┬────────┐ │
│  │预处理   │类型分类 │坐标标定 │CV引擎   │OCR      │VLM层   │ │
│  └─────────┴─────────┴─────────┴─────────┴─────────┴────────┘ │
│  ┌──────────────── 交叉验证 & 置信度 ──────────────────────┐  │
│  └──────────────────────────────────────────────────────────┘ │
└───────────┬───────────────────────────────────┬──────────────┘
            │                                    │
   ┌────────▼────────┐              ┌────────────▼───────────┐
   │ 存储层          │              │ VLM Provider           │
   │ SQLite+文件系统 │              │ 云端API / 本地Qwen-VL  │
   └─────────────────┘              └────────────────────────┘
```

**数据流（处理管线）**：

\[
\text{原图} \to \text{预处理} \to \text{类型识别} \to \text{坐标标定} \to \text{CV提取} \xrightarrow{\text{融合}} \text{VLM语义} \to \text{交叉验证} \to \text{人工校正} \to \text{导出}
\]

---

## 2. 技术栈与项目结构

### 2.1 技术选型

| 层 | 技术 | 理由 |
|----|------|------|
| 前端框架 | React 18 + TypeScript + Vite | 生态成熟、类型安全 |
| 交互画布 | Konva.js (react-konva) | 高性能图层叠加、可拖拽标注 |
| 图表预览 | ECharts | 重建图对比 |
| 状态管理 | Zustand | 轻量 |
| 后端框架 | FastAPI + Uvicorn | 异步、自动文档、Python AI 生态 |
| CV | OpenCV, scikit-image, NumPy, SciPy | 数值精确提取 |
| OCR | PaddleOCR | 中英文识别强 |
| VLM | OpenAI/Anthropic API + Qwen2-VL(本地) | 语义辅助 |
| 任务队列 | Celery + Redis（可选） | 大图异步处理 |
| 存储 | SQLite + 本地文件 | 零配置易部署 |
| 部署 | Docker Compose | 一键启动 |

### 2.2 完整目录结构

```
sciplot-extractor/
├── docker-compose.yml
├── .env.example
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                      # FastAPI 入口
│   ├── config.py                    # 全局配置
│   │
│   ├── core/
│   │   ├── orchestrator.py          # 调度器：串联所有模块
│   │   ├── schemas.py               # Pydantic 数据模型
│   │   └── exceptions.py
│   │
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   ├── loader.py                # 图像加载/格式归一化
│   │   ├── enhance.py               # 去噪/锐化/对比度
│   │   └── plot_area.py             # 绘图区域检测
│   │
│   ├── classification/
│   │   ├── classifier.py            # 图类型分类
│   │   └── rules.py                 # 规则辅助判断
│   │
│   ├── calibration/
│   │   ├── axis_detector.py         # 坐标轴检测
│   │   ├── tick_detector.py         # 刻度检测
│   │   ├── calibrator.py            # 像素↔数据映射
│   │   └── transforms.py            # 线性/对数/时间变换
│   │
│   ├── extractors/
│   │   ├── base.py                  # 提取器基类
│   │   ├── line_chart.py
│   │   ├── scatter.py
│   │   ├── bar_chart.py
│   │   ├── heatmap.py
│   │   ├── box_plot.py
│   │   └── color_segmentation.py    # 颜色分割工具
│   │
│   ├── ocr/
│   │   ├── ocr_engine.py
│   │   └── postprocess.py           # 数字/单位解析
│   │
│   ├── vlm/
│   │   ├── provider.py              # 抽象基类
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   ├── local_qwen.py
│   │   ├── prompts.py               # Prompt 模板
│   │   └── parser.py                # 结构化输出解析
│   │
│   ├── validation/
│   │   ├── cross_validator.py
│   │   └── confidence.py
│   │
│   ├── export/
│   │   ├── exporters.py             # CSV/JSON/Excel
│   │   └── report.py                # PDF 报告
│   │
│   ├── storage/
│   │   ├── database.py              # SQLAlchemy
│   │   └── models.py
│   │
│   └── api/
│       ├── routes_project.py
│       ├── routes_extract.py
│       ├── routes_calibrate.py
│       └── routes_export.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── store/                   # Zustand
│       ├── services/api.ts
│       ├── components/
│       │   ├── Canvas/              # Konva 交互画布
│       │   │   ├── ImageCanvas.tsx
│       │   │   ├── CalibrationLayer.tsx
│       │   │   ├── DataPointLayer.tsx
│       │   │   └── AxisLayer.tsx
│       │   ├── Sidebar/
│       │   ├── Preview/             # ECharts 重建
│       │   └── ExportPanel/
│       └── types/
│
└── models/                          # 本地VLM权重(可选)
    └── qwen2-vl/
```

---

## 3. 部署方案

### 3.1 docker-compose.yml

```yaml
version: "3.9"

services:
  backend:
    build: ./backend
    container_name: sciplot-backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data          # 持久化上传图与结果
      - ./models:/app/models      # 本地VLM权重
    environment:
      - VLM_PROVIDER=${VLM_PROVIDER:-openai}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=sqlite:///./data/sciplot.db
    restart: unless-stopped

  frontend:
    build: ./frontend
    container_name: sciplot-frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

  # 可选：本地 Redis 用于异步任务
  redis:
    image: redis:7-alpine
    container_name: sciplot-redis
    profiles: ["async"]
```

### 3.2 一键启动

```bash
cp .env.example .env      # 填入 API Key（可选）
docker compose up -d
# 访问 http://localhost:3000
```

### 3.3 backend/Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 系统依赖（OpenCV / PaddleOCR 需要）
RUN apt-get update && apt-get install -y \
    libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.4 requirements.txt

```text
fastapi==0.110.0
uvicorn[standard]==0.29.0
python-multipart==0.0.9
pydantic==2.6.0
numpy==1.26.4
opencv-python-headless==4.9.0.80
scikit-image==0.22.0
scipy==1.12.0
pandas==2.2.0
paddleocr==2.7.0
paddlepaddle==2.6.0
openai==1.14.0
anthropic==0.21.0
sqlalchemy==2.0.27
openpyxl==3.1.2
reportlab==4.1.0
pillow==10.2.0
```

---

## 4. 后端核心骨架

### 4.1 数据模型 `core/schemas.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class ChartType(str, Enum):
    LINE = "line"
    SCATTER = "scatter"
    BAR = "bar"
    HEATMAP = "heatmap"
    BOX = "box"
    PIE = "pie"
    CONTOUR = "contour"
    MICROSCOPY = "microscopy"
    UNKNOWN = "unknown"


class AxisScale(str, Enum):
    LINEAR = "linear"
    LOG = "log"
    TIME = "time"


class Point(BaseModel):
    x: float
    y: float


class CalibrationPoint(BaseModel):
    """一个标定参考点：像素坐标 + 对应数据坐标"""
    pixel: Point
    data: Point


class AxisCalibration(BaseModel):
    scale: AxisScale = AxisScale.LINEAR
    # 两个参考点确定一维线性/对数映射
    ref1: CalibrationPoint
    ref2: CalibrationPoint
    label: Optional[str] = None
    unit: Optional[str] = None


class CalibrationConfig(BaseModel):
    x_axis: AxisCalibration
    y_axis: AxisCalibration


class DataSeries(BaseModel):
    name: str
    color_hex: Optional[str] = None
    points: list[Point]
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class ExtractionResult(BaseModel):
    chart_type: ChartType
    series: list[DataSeries]
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    legend: list[str] = []
    metadata: dict = {}
    overall_confidence: float = 1.0
    low_confidence_flags: list[str] = []
```

### 4.2 调度器 `core/orchestrator.py`

```python
import numpy as np
from core.schemas import ExtractionResult, ChartType, CalibrationConfig
from preprocessing.loader import load_image
from preprocessing.enhance import enhance
from preprocessing.plot_area import detect_plot_area
from classification.classifier import classify_chart
from calibration.calibrator import Calibrator
from extractors import get_extractor
from ocr.ocr_engine import OCREngine
from vlm.provider import get_vlm_provider
from validation.cross_validator import CrossValidator


class Orchestrator:
    """串联整个处理管线的核心调度器"""

    def __init__(self):
        self.ocr = OCREngine()
        self.vlm = get_vlm_provider()
        self.validator = CrossValidator()

    async def auto_analyze(self, image_bytes: bytes) -> dict:
        """
        第一阶段：自动分析（不含数值提取）
        返回类型、检测到的坐标轴、刻度、图例 —— 供前端展示并让用户确认
        """
        img = load_image(image_bytes)
        img = enhance(img)

        # 1. 检测绘图区域
        plot_area = detect_plot_area(img)

        # 2. 图类型识别（VLM + 规则）
        chart_type = await classify_chart(img, self.vlm)

        # 3. OCR 提取所有文本（轴标签、刻度、标题、图例）
        ocr_results = self.ocr.extract(img)

        # 4. VLM 语义理解（图例、标题、轴含义）
        semantics = await self.vlm.analyze_semantics(image_bytes)

        # 5. 自动标定建议（坐标轴+刻度）
        from calibration.axis_detector import detect_axes
        from calibration.tick_detector import detect_ticks
        axes = detect_axes(img, plot_area)
        ticks = detect_ticks(img, axes, ocr_results)

        return {
            "chart_type": chart_type,
            "plot_area": plot_area,
            "ocr": ocr_results,
            "semantics": semantics,
            "suggested_calibration": ticks,
        }

    async def extract(
        self,
        image_bytes: bytes,
        chart_type: ChartType,
        calibration: CalibrationConfig,
        series_colors: list[str] | None = None,
    ) -> ExtractionResult:
        """
        第二阶段：精确数值提取（标定确认后执行）
        """
        img = load_image(image_bytes)
        img = enhance(img)

        # 1. 选择对应类型提取器
        extractor = get_extractor(chart_type)
        calibrator = Calibrator(calibration)

        # 2. CV 引擎提取像素级数据点
        cv_result = extractor.extract(img, calibrator, series_colors)

        # 3. VLM 提取语义（图例名、单位等）
        semantics = await self.vlm.analyze_semantics(image_bytes)

        # 4. 交叉验证 + 置信度评估
        result = self.validator.validate(cv_result, semantics, img)

        return result
```

---

## 5. 模块一：图像预处理

### 5.1 图像加载 `preprocessing/loader.py`

```python
import cv2
import numpy as np
from PIL import Image
import io


def load_image(image_bytes: bytes) -> np.ndarray:
    """
    统一加载为 RGB ndarray。
    支持 PNG/JPG/TIFF/BMP/WebP，处理 EXIF 旋转、透明通道。
    """
    pil = Image.open(io.BytesIO(image_bytes))

    # 处理透明背景：贴白底
    if pil.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", pil.size, (255, 255, 255))
        pil = pil.convert("RGBA")
        background.paste(pil, mask=pil.split()[-1])
        pil = background
    else:
        pil = pil.convert("RGB")

    # 修正 EXIF 方向
    pil = _apply_exif_orientation(pil)

    return np.array(pil)


def _apply_exif_orientation(pil: Image.Image) -> Image.Image:
    try:
        from PIL import ImageOps
        return ImageOps.exif_transpose(pil)
    except Exception:
        return pil
```

### 5.2 图像增强 `preprocessing/enhance.py`

```python
import cv2
import numpy as np


def enhance(img: np.ndarray) -> np.ndarray:
    """
    针对科研图的轻量增强：
    - 不破坏原始数据点位置
    - 仅做去噪与对比度归一化
    """
    # 高分辨率图保持原样，避免插值引入误差
    h, w = img.shape[:2]

    # 轻度双边滤波去噪（保边）
    denoised = cv2.bilateralFilter(img, d=5, sigmaColor=30, sigmaSpace=30)

    return denoised


def upscale_if_small(img: np.ndarray, min_dim: int = 800) -> np.ndarray:
    """小图放大以提高检测精度（仅用于检测，不用于最终数值）"""
    h, w = img.shape[:2]
    scale = max(1.0, min_dim / min(h, w))
    if scale > 1.0:
        return cv2.resize(img, None, fx=scale, fy=scale,
                          interpolation=cv2.INTER_CUBIC)
    return img
```

### 5.3 绘图区域检测 `preprocessing/plot_area.py`

绘图区域（plot area）即坐标轴围成的矩形数据区，是后续所有提取的基础。

```python
import cv2
import numpy as np


def detect_plot_area(img: np.ndarray) -> dict:
    """
    检测绘图区域边界框。
    策略：检测最长的水平线(x轴)与垂直线(y轴)，
    它们的交点定义绘图区左下角，结合外接框确定范围。
    返回 {x0, y0, x1, y1}（像素坐标）。
    """
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)

    # 检测直线
    lines = cv2.HoughLinesP(
        edges, rho=1, theta=np.pi / 180,
        threshold=100, minLineLength=min(img.shape[:2]) // 3,
        maxLineGap=10,
    )

    h_lines, v_lines = [], []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.degrees(np.arctan2(abs(y2 - y1), abs(x2 - x1)))
            if angle < 5:        # 水平线
                h_lines.append((x1, y1, x2, y2))
            elif angle > 85:     # 垂直线
                v_lines.append((x1, y1, x2, y2))

    # x轴：最靠下的长水平线；y轴：最靠左的长垂直线
    if h_lines and v_lines:
        x_axis = max(h_lines, key=lambda l: l[1])      # y 最大
        y_axis = min(v_lines, key=lambda l: l[0])      # x 最小
        x0 = min(y_axis[0], y_axis[2])
        y1 = max(x_axis[1], x_axis[3])
        x1 = max(x_axis[0], x_axis[2])
        y0 = min(y_axis[1], y_axis[3])
        return {"x0": int(x0), "y0": int(y0),
                "x1": int(x1), "y1": int(y1),
                "detected": True}

    # 回退：使用整图边距
    h, w = img.shape[:2]
    return {"x0": int(w * 0.1), "y0": int(h * 0.1),
            "x1": int(w * 0.95), "y1": int(h * 0.9),
            "detected": False}
```

---

## 6. 模块二：图类型分类

采用 **VLM 主判 + 规则校验** 的混合策略，兼顾准确与鲁棒。

### 6.1 `classification/classifier.py`

```python
from core.schemas import ChartType
from classification.rules import rule_based_hint
import numpy as np


async def classify_chart(img: np.ndarray, vlm) -> ChartType:
    """
    混合分类：
    1. VLM 给出主判断（语义强）
    2. 规则给出辅助提示（颜色/形状统计）
    3. 不一致时以 VLM 为主，但记录冲突
    """
    # 规则提示
    rule_hint = rule_based_hint(img)

    # VLM 判断
    vlm_type = await vlm.classify_chart_type(img)

    # 融合：若规则明确且与 VLM 冲突，信任 VLM 但保留日志
    if rule_hint and rule_hint != vlm_type:
        # 可记录到 metadata 供人工复核
        pass

    return vlm_type or rule_hint or ChartType.UNKNOWN
```

### 6.2 规则辅助 `classification/rules.py`

```python
import cv2
import numpy as np
from core.schemas import ChartType


def rule_based_hint(img: np.ndarray) -> ChartType | None:
    """
    基于图像统计特征的快速规则判断（作为 VLM 的交叉验证）。
    """
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # 1. 大面积连续色块 → 热图
    if _has_large_color_gradient(img):
        return ChartType.HEATMAP

    # 2. 检测大量矩形 → 柱状图
    if _count_rectangles(gray) >= 3:
        return ChartType.BAR

    # 3. 检测离散点簇 → 散点图
    blob_count = _count_blobs(gray)
    if blob_count > 20:
        return ChartType.SCATTER

    # 4. 检测连续长曲线 → 折线图
    if _has_continuous_curves(gray):
        return ChartType.LINE

    return None


def _has_large_color_gradient(img: np.ndarray) -> bool:
    """热图特征：大面积平滑渐变色"""
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    sat = hsv[:, :, 1]
    # 高饱和度像素占比高且空间连续
    high_sat_ratio = np.mean(sat > 80)
    return high_sat_ratio > 0.4


def _count_rectangles(gray: np.ndarray) -> int:
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    count = 0
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)
        if len(approx) == 4 and cv2.contourArea(c) > 500:
            count += 1
    return count


def _count_blobs(gray: np.ndarray) -> int:
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = 10
    params.maxArea = 500
    detector = cv2.SimpleBlobDetector_create(params)
    keypoints = detector.detect(gray)
    return len(keypoints)


def _has_continuous_curves(gray: np.ndarray) -> bool:
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST,
                                   cv2.CHAIN_APPROX_NONE)
    for c in contours:
        if cv2.arcLength(c, False) > gray.shape[1] * 0.5:
            return True
    return False
```

---

## 7. 模块三：坐标系标定

**这是保证数值准确性的核心模块。**

### 7.1 坐标变换数学

线性轴的像素→数据映射（已在前文给出），对数轴：

\[
x_{data} = 10^{\,\log_{10} x_1 + (p_x - p_{x1})\cdot \dfrac{\log_{10} x_2 - \log_{10} x_1}{p_{x2} - p_{x1}}}
\]

其中 \((p_{x1}, x_1)\) 与 \((p_{x2}, x_2)\) 是两个标定参考点。

### 7.2 变换实现 `calibration/transforms.py`

```python
import numpy as np
from core.schemas import AxisScale, AxisCalibration


class AxisTransform:
    """单轴像素↔数据双向变换"""

    def __init__(self, cal: AxisCalibration, is_x: bool = True):
        self.scale = cal.scale
        self.is_x = is_x

        # 提取参考点（x 轴用 .x，y 轴用 .y）
        if is_x:
            self.p1, self.p2 = cal.ref1.pixel.x, cal.ref2.pixel.x
            self.d1, self.d2 = cal.ref1.data.x, cal.ref2.data.x
        else:
            self.p1, self.p2 = cal.ref1.pixel.y, cal.ref2.pixel.y
            self.d1, self.d2 = cal.ref1.data.y, cal.ref2.data.y

        # 对数轴预转换
        if self.scale == AxisScale.LOG:
            self.d1 = np.log10(self.d1)
            self.d2 = np.log10(self.d2)

        # 防止除零
        if self.p2 == self.p1:
            raise ValueError("两个标定点像素坐标不能相同")

        self.slope = (self.d2 - self.d1) / (self.p2 - self.p1)

    def pixel_to_data(self, p: float) -> float:
        d = self.d1 + (p - self.p1) * self.slope
        if self.scale == AxisScale.LOG:
            return float(10 ** d)
        return float(d)

    def data_to_pixel(self, d: float) -> float:
        if self.scale == AxisScale.LOG:
            d = np.log10(d)
        return float(self.p1 + (d - self.d1) / self.slope)
```

### 7.3 标定器 `calibration/calibrator.py`

```python
import numpy as np
from core.schemas import CalibrationConfig, Point
from calibration.transforms import AxisTransform


class Calibrator:
    """二维坐标标定：像素 (px, py) ↔ 数据 (x, y)"""

    def __init__(self, config: CalibrationConfig):
        self.x_transform = AxisTransform(config.x_axis, is_x=True)
        self.y_transform = AxisTransform(config.y_axis, is_x=False)

    def pixel_to_data(self, px: float, py: float) -> Point:
        return Point(
            x=self.x_transform.pixel_to_data(px),
            y=self.y_transform.pixel_to_data(py),
        )

    def data_to_pixel(self, x: float, y: float) -> Point:
        return Point(
            x=self.x_transform.data_to_pixel(x),
            y=self.y_transform.data_to_pixel(y),
        )

    def batch_pixel_to_data(self, pixels: np.ndarray) -> np.ndarray:
        """pixels: (N,2) → data: (N,2)，向量化加速"""
        out = np.empty_like(pixels, dtype=float)
        for i, (px, py) in enumerate(pixels):
            p = self.pixel_to_data(px, py)
            out[i] = [p.x, p.y]
        return out
```

### 7.4 坐标轴检测 `calibration/axis_detector.py`

```python
import cv2
import numpy as np


def detect_axes(img: np.ndarray, plot_area: dict) -> dict:
    """
    在绘图区域内精确定位 x/y 轴线。
    返回轴线像素坐标，供刻度检测使用。
    """
    x0, y0 = plot_area["x0"], plot_area["y0"]
    x1, y1 = plot_area["x1"], plot_area["y1"]

    return {
        "x_axis": {"y_pixel": y1, "x_start": x0, "x_end": x1},
        "y_axis": {"x_pixel": x0, "y_start": y0, "y_end": y1},
    }
```

### 7.5 刻度检测 `calibration/tick_detector.py`

自动识别刻度位置与对应的数字标签，生成**标定建议**。

```python
import cv2
import numpy as np


def detect_ticks(img: np.ndarray, axes: dict, ocr_results: list) -> dict:
    """
    检测坐标轴刻度线 + 关联 OCR 数字 → 自动标定建议。

    步骤：
    1. 沿轴线寻找垂直于轴的短刻度线（tick marks）
    2. 用 OCR 结果中靠近刻度的数字作为该刻度的数据值
    3. 至少匹配 2 个刻度即可生成标定
    """
    x_ticks = _detect_x_ticks(img, axes["x_axis"], ocr_results)
    y_ticks = _detect_y_ticks(img, axes["y_axis"], ocr_results)

    return {
        "x_ticks": x_ticks,   # [{pixel: px, value: float}, ...]
        "y_ticks": y_ticks,
    }


def _detect_x_ticks(img, x_axis, ocr_results):
    """检测 x 轴刻度线"""
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    y_axis_px = x_axis["y_pixel"]
    ticks = []

    # 在轴线下方 1~12 像素范围寻找短竖线
    band = gray[y_axis_px + 1: y_axis_px + 12,
                x_axis["x_start"]: x_axis["x_end"]]
    col_darkness = np.mean(255 - band, axis=0)
    # 局部峰值即刻度位置
    peaks = _find_peaks(col_darkness, min_distance=15)

    for p in peaks:
        px = x_axis["x_start"] + p
        # 关联最近的 OCR 数字（位于刻度正下方）
        value = _match_label(ocr_results, px, y_axis_px, axis="x")
        if value is not None:
            ticks.append({"pixel": float(px), "value": value})

    return ticks


def _detect_y_ticks(img, y_axis, ocr_results):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    x_axis_px = y_axis["x_pixel"]
    ticks = []

    band = gray[y_axis["y_start"]: y_axis["y_end"],
                max(0, x_axis_px - 12): x_axis_px - 1]
    row_darkness = np.mean(255 - band, axis=1)
    peaks = _find_peaks(row_darkness, min_distance=15)

    for p in peaks:
        py = y_axis["y_start"] + p
        value = _match_label(ocr_results, x_axis_px, py, axis="y")
        if value is not None:
            ticks.append({"pixel": float(py), "value": value})

    return ticks


def _find_peaks(signal: np.ndarray, min_distance: int) -> list[int]:
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(signal, distance=min_distance,
                          height=np.mean(signal) + np.std(signal))
    return peaks.tolist()


def _match_label(ocr_results, px, py, axis, max_dist=40):
    """寻找最接近刻度位置的 OCR 数字标签"""
    best, best_dist = None, max_dist
    for item in ocr_results:
        text, (cx, cy) = item["text"], item["center"]
        num = _parse_number(text)
        if num is None:
            continue
        if axis == "x":
            dist = abs(cx - px) + 0.3 * abs(cy - py)
        else:
            dist = abs(cy - py) + 0.3 * abs(cx - px)
        if dist < best_dist:
            best, best_dist = num, dist
    return best


def _parse_number(text: str):
    import re
    text = text.replace(",", "").replace("−", "-")
    m = re.match(r"^-?\d+\.?\d*(?:[eE][-+]?\d+)?$", text.strip())
    return float(m.group()) if m else None
```

---

## 8. 模块四：CV 数据提取引擎

### 8.1 提取器基类 `extractors/base.py`

```python
from abc import ABC, abstractmethod
import numpy as np
from core.schemas import DataSeries
from calibration.calibrator import Calibrator


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, img: np.ndarray, calibrator: Calibrator,
                series_colors: list[str] | None = None) -> list[DataSeries]:
        ...
```

### 8.2 工厂 `extractors/__init__.py`

```python
from core.schemas import ChartType
from extractors.line_chart import LineChartExtractor
from extractors.scatter import ScatterExtractor
from extractors.bar_chart import BarChartExtractor
from extractors.heatmap import HeatmapExtractor
from extractors.box_plot import BoxPlotExtractor


_REGISTRY = {
    ChartType.LINE: LineChartExtractor,
    ChartType.SCATTER: ScatterExtractor,
    ChartType.BAR: BarChartExtractor,
    ChartType.HEATMAP: HeatmapExtractor,
    ChartType.BOX: BoxPlotExtractor,
}


def get_extractor(chart_type: ChartType):
    cls = _REGISTRY.get(chart_type, LineChartExtractor)
    return cls()
```

### 8.3 颜色分割工具 `extractors/color_segmentation.py`

多系列图的关键：按颜色分离不同曲线/数据系列。

```python
import cv2
import numpy as np
from sklearn.cluster import KMeans


def segment_by_color(img: np.ndarray, plot_mask: np.ndarray,
                     n_colors: int | None = None,
                     given_colors: list[str] | None = None) -> dict:
    """
    将绘图区域内的数据像素按颜色聚类分组。

    返回 {color_hex: binary_mask}
    """
    if given_colors:
        return _segment_by_given_colors(img, plot_mask, given_colors)

    # 自动发现主要颜色（排除黑白灰背景）
    ys, xs = np.where(plot_mask > 0)
    pixels = img[ys, xs].astype(float)

    # 过滤接近灰度的像素（坐标轴、网格、文字）
    sat = _saturation(pixels)
    colored = pixels[sat > 30]
    if len(colored) < 50:
        # 单色黑线图
        return {"#000000": _black_line_mask(img, plot_mask)}

    # KMeans 聚类找主色
    k = n_colors or _estimate_color_count(colored)
    km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(colored)
    centers = km.cluster_centers_.astype(int)

    masks = {}
    for c in centers:
        hexc = "#%02x%02x%02x" % tuple(c)
        masks[hexc] = _color_mask(img, plot_mask, c, tol=35)
    return masks


def _saturation(rgb: np.ndarray) -> np.ndarray:
    mx = rgb.max(axis=1)
    mn = rgb.min(axis=1)
    return np.where(mx > 0, (mx - mn) / mx * 255, 0)


def _color_mask(img, plot_mask, color, tol=35):
    diff = np.linalg.norm(img.astype(float) - color, axis=2)
    mask = ((diff < tol) & (plot_mask > 0)).astype(np.uint8) * 255
    return mask


def _black_line_mask(img, plot_mask):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    mask = ((gray < 80) & (plot_mask > 0)).astype(np.uint8) * 255
    return mask


def _estimate_color_count(colored: np.ndarray, max_k=6) -> int:
    """用肘部法估计颜色数（简化：固定上限+方差阈值）"""
    from sklearn.cluster import KMeans
    best_k, prev_inertia = 1, None
    for k in range(1, max_k + 1):
        km = KMeans(n_clusters=k, n_init=5, random_state=0).fit(colored)
        if prev_inertia and prev_inertia - km.inertia_ < prev_inertia * 0.1:
            break
        prev_inertia, best_k = km.inertia_, k
    return best_k


def _segment_by_given_colors(img, plot_mask, hex_colors):
    masks = {}
    for hexc in hex_colors:
        c = np.array([int(hexc[i:i+2], 16) for i in (1, 3, 5)])
        masks[hexc] = _color_mask(img, plot_mask, c, tol=40)
    return masks
```

### 8.4 折线图提取 `extractors/line_chart.py`

```python
import cv2
import numpy as np
from extractors.base import BaseExtractor
from extractors.color_segmentation import segment_by_color
from core.schemas import DataSeries, Point
from calibration.calibrator import Calibrator


class LineChartExtractor(BaseExtractor):
    """
    折线图提取：
    对每个颜色系列，沿 x 轴逐列扫描，取该列数据像素的 y 中位数。
    """

    def extract(self, img, calibrator, series_colors=None):
        plot_mask = self._build_plot_mask(img, calibrator)
        color_masks = segment_by_color(img, plot_mask,
                                       given_colors=series_colors)

        series_list = []
        for color_hex, mask in color_masks.items():
            points = self._trace_line(mask, calibrator)
            if len(points) >= 2:
                series_list.append(DataSeries(
                    name=f"series_{color_hex}",
                    color_hex=color_hex,
                    points=points,
                    confidence=self._estimate_confidence(mask, points),
                ))
        return series_list

    def _build_plot_mask(self, img, calibrator) -> np.ndarray:
        """构造绘图区域掩码（基于标定的轴范围）"""
        h, w = img.shape[:2]
        mask = np.zeros((h, w), np.uint8)
        # 用标定点确定矩形区域
        xt, yt = calibrator.x_transform, calibrator.y_transform
        x0 = int(min(xt.p1, xt.p2))
        x1 = int(max(xt.p1, xt.p2))
        y0 = int(min(yt.p1, yt.p2))
        y1 = int(max(yt.p1, yt.p2))
        # 适度外扩
        pad = 5
        mask[max(0, y0 - pad):min(h, y1 + pad),
             max(0, x0 - pad):min(w, x1 + pad)] = 255
        return mask

    def _trace_line(self, mask: np.ndarray, calibrator) -> list[Point]:
        """逐列扫描，每列取数据像素的 y 中位数"""
        points = []
        h, w = mask.shape
        for px in range(w):
            ys = np.where(mask[:, px] > 0)[0]
            if len(ys) == 0:
                continue
            # 若一列有多段（曲线折返），取最大连通段的中位数
            py = self._robust_y(ys)
            data_pt = calibrator.pixel_to_data(px, py)
            points.append(data_pt)

        # 按 x 排序并去抖动（移动中值滤波）
        points = self._smooth(points)
        return points

    def _robust_y(self, ys: np.ndarray) -> float:
        """处理一列多个像素：聚类取主段中位数"""
        if len(ys) <= 3:
            return float(np.median(ys))
        # 分割连续段
        gaps = np.where(np.diff(ys) > 3)[0]
        segments = np.split(ys, gaps + 1)
        largest = max(segments, key=len)
        return float(np.median(largest))

    def _smooth(self, points: list[Point], window=3) -> list[Point]:
        if len(points) < window:
            return points
        ys = np.array([p.y for p in points])
        from scipy.signal import medfilt
        ys_smooth = medfilt(ys, kernel_size=window)
        return [Point(x=p.x, y=float(ys_smooth[i]))
                for i, p in enumerate(points)]

    def _estimate_confidence(self, mask, points) -> float:
        """覆盖率越高、断点越少 → 置信度越高"""
        coverage = len(points) / max(1, mask.shape[1])
        return float(min(1.0, 0.5 + coverage))
```

### 8.5 散点图提取 `extractors/scatter.py`

```python
import cv2
import numpy as np
from extractors.base import BaseExtractor
from extractors.color_segmentation import segment_by_color
from core.schemas import DataSeries, Point


class ScatterExtractor(BaseExtractor):
    """
    散点图提取：用斑点检测（blob detection）定位每个数据点中心。
    """

    def extract(self, img, calibrator, series_colors=None):
        plot_mask = self._build_plot_mask(img, calibrator)
        color_masks = segment_by_color(img, plot_mask,
                                       given_colors=series_colors)

        series_list = []
        for color_hex, mask in color_masks.items():
            centers = self._detect_points(mask)
            points = [calibrator.pixel_to_data(cx, cy)
                      for cx, cy in centers]
            if points:
                series_list.append(DataSeries(
                    name=f"series_{color_hex}",
                    color_hex=color_hex,
                    points=points,
                    confidence=0.9,
                ))
        return series_list

    def _detect_points(self, mask: np.ndarray) -> list[tuple]:
        """连通域分析定位散点中心"""
        n, labels, stats, centroids = cv2.connectedComponentsWithStats(
            mask, connectivity=8)
        centers = []
        for i in range(1, n):  # 跳过背景
            area = stats[i, cv2.CC_STAT_AREA]
            if 5 <= area <= 2000:   # 过滤噪点与大色块
                cx, cy = centroids[i]
                centers.append((float(cx), float(cy)))
        return centers

    def _build_plot_mask(self, img, calibrator):
        # 同 LineChartExtractor，复用逻辑（实际可抽到 base）
        from extractors.line_chart import LineChartExtractor
        return LineChartExtractor()._build_plot_mask(img, calibrator)
```

### 8.6 柱状图提取 `extractors/bar_chart.py`

```python
import cv2
import numpy as np
from extractors.base import BaseExtractor
from core.schemas import DataSeries, Point


class BarChartExtractor(BaseExtractor):
    """
    柱状图提取：检测矩形柱，柱顶像素 → 数据值。
    """

    def extract(self, img, calibrator, series_colors=None):
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        _, binary = cv2.threshold(gray, 0, 255,
                                  cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        baseline_py = calibrator.y_transform.p1  # y轴起点像素(通常y=0处)

        bars = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if self._is_bar(w, h, c):
                # 柱顶中心
                top_px = x + w / 2
                top_py = y
                # 柱中心 x 用于横轴类别定位
                data_top = calibrator.pixel_to_data(top_px, top_py)
                bars.append((top_px, data_top))

        bars.sort(key=lambda b: b[0])  # 按 x 排序
        points = [b[1] for b in bars]

        return [DataSeries(name="bars", points=points, confidence=0.9)]

    def _is_bar(self, w, h, contour) -> bool:
        area = cv2.contourArea(contour)
        rect_area = w * h
        # 矩形度高、有一定高度
        return (rect_area > 200 and area / rect_area > 0.8
                and h > w * 0.3)
```

### 8.7 热图提取 `extractors/heatmap.py`

热图核心：建立 **颜色 → 数值** 的 colorbar 映射。

```python
import cv2
import numpy as np
from extractors.base import BaseExtractor
from core.schemas import DataSeries, Point


class HeatmapExtractor(BaseExtractor):
    """
    热图提取：
    1. 定位 colorbar，建立 颜色↔数值 查找表(LUT)
    2. 对绘图区每个网格单元取颜色 → 反查数值
    """

    def extract(self, img, calibrator, series_colors=None,
                colorbar_box=None, value_range=None, grid=None):
        # colorbar_box: {x0,y0,x1,y1}; value_range: (vmin,vmax)
        if colorbar_box is None or value_range is None:
            raise ValueError("热图需提供 colorbar 区域与数值范围")

        lut = self._build_colorbar_lut(img, colorbar_box, value_range)
        matrix = self._sample_grid(img, calibrator, lut, grid)

        # 以矩阵形式存入 metadata，points 存 (col,row,value)
        points = []
        rows, cols = matrix.shape
        for r in range(rows):
            for c in range(cols):
                points.append(Point(x=float(c), y=float(matrix[r, c])))

        series = DataSeries(name="heatmap", points=points, confidence=0.85)
        return [series]

    def _build_colorbar_lut(self, img, box, value_range):
        """沿 colorbar 长轴采样，建立 RGB→value 映射表"""
        x0, y0, x1, y1 = box["x0"], box["y0"], box["x1"], box["y1"]
        vmin, vmax = value_range
        vertical = (y1 - y0) > (x1 - x0)

        samples = []
        if vertical:
            for py in range(y0, y1):
                color = img[py, (x0 + x1) // 2].astype(float)
                t = (py - y0) / (y1 - y0)
                value = vmax - t * (vmax - vmin)  # 顶部=max
                samples.append((color, value))
        else:
            for px in range(x0, x1):
                color = img[(y0 + y1) // 2, px].astype(float)
                t = (px - x0) / (x1 - x0)
                value = vmin + t * (vmax - vmin)
                samples.append((color, value))
        return samples

    def _color_to_value(self, color, lut):
        """最近邻反查"""
        best_v, best_d = None, 1e9
        for c, v in lut:
            d = np.linalg.norm(color - c)
            if d < best_d:
                best_d, best_v = d, v
        return best_v

    def _sample_grid(self, img, calibrator, lut, grid):
        """对网格单元采样中心颜色"""
        xt, yt = calibrator.x_transform, calibrator.y_transform
        x0, x1 = int(min(xt.p1, xt.p2)), int(max(xt.p1, xt.p2))
        y0, y1 = int(min(yt.p1, yt.p2)), int(max(yt.p1, yt.p2))

        rows, cols = grid if grid else (10, 10)
        matrix = np.zeros((rows, cols))
        cell_w = (x1 - x0) / cols
        cell_h = (y1 - y0) / rows

        for r in range(rows):
            for c in range(cols):
                cx = int(x0 + (c + 0.5) * cell_w)
                cy = int(y0 + (r + 0.5) * cell_h)
                color = img[cy, cx].astype(float)
                matrix[r, c] = self._color_to_value(color, lut)
        return matrix
```

### 8.8 箱线图提取 `extractors/box_plot.py`

```python
import cv2
import numpy as np
from extractors.base import BaseExtractor
from core.schemas import DataSeries, Point


class BoxPlotExtractor(BaseExtractor):
    """
    箱线图提取每个箱体的五数概括：
    最小值、Q1、中位数、Q3、最大值。
    """

    def extract(self, img, calibrator, series_colors=None):
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        _, binary = cv2.threshold(gray, 0, 255,
                                  cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)

        boxes = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if self._is_box(w, h):
                # 箱体上下边界 = Q3, Q1
                q3 = calibrator.pixel_to_data(x + w/2, y).y
                q1 = calibrator.pixel_to_data(x + w/2, y + h).y
                # 中位数线：箱内最显著的水平线
                median = self._find_median_line(binary, x, y, w, h, calibrator)
                # 须线：向上下延伸的竖线端点
                whisker_hi, whisker_lo = self._find_whiskers(
                    binary, x, y, w, h, calibrator)
                boxes.append({
                    "x_pixel": x + w / 2,
                    "q1": q1, "q3": q3, "median": median,
                    "whisker_low": whisker_lo, "whisker_high": whisker_hi,
                })

        boxes.sort(key=lambda b: b["x_pixel"])
        # 以 metadata 形式表达五数概括
        points = []
        for b in boxes:
            points.extend([
                Point(x=b["x_pixel"], y=b["whisker_low"]),
                Point(x=b["x_pixel"], y=b["q1"]),
                Point(x=b["x_pixel"], y=b["median"]),
                Point(x=b["x_pixel"], y=b["q3"]),
                Point(x=b["x_pixel"], y=b["whisker_high"]),
            ])
        return [DataSeries(name="boxplot", points=points, confidence=0.8)]

    def _is_box(self, w, h):
        return 15 < w < 200 and 15 < h < 600

    def _find_median_line(self, binary, x, y, w, h, calibrator):
        region = binary[y:y+h, x:x+w]
        row_sum = region.sum(axis=1)
        median_row = int(np.argmax(row_sum))
        return calibrator.pixel_to_data(x + w/2, y + median_row).y

    def _find_whiskers(self, binary, x, y, w, h, calibrator):
        cx = x + w // 2
        col = binary[:, cx]
        ys = np.where(col > 0)[0]
        if len(ys) == 0:
            return (calibrator.pixel_to_data(cx, y).y,
                    calibrator.pixel_to_data(cx, y + h).y)
        hi = calibrator.pixel_to_data(cx, ys.min()).y
        lo = calibrator.pixel_to_data(cx, ys.max()).y
        return hi, lo
```

---

## 9. 模块五：OCR 文本提取

### 9.1 `ocr/ocr_engine.py`

```python
import numpy as np
from paddleocr import PaddleOCR


class OCREngine:
    """封装 PaddleOCR，提取所有文本及其位置"""

    def __init__(self, lang="ch"):
        # ch 模型同时支持中英文
        self.ocr = PaddleOCR(use_angle_cls=True, lang=lang,
                             show_log=False)

    def extract(self, img: np.ndarray) -> list[dict]:
        """
        返回 [{text, center:(x,y), bbox, confidence}, ...]
        """
        result = self.ocr.ocr(img, cls=True)
        items = []
        if not result or not result[0]:
            return items
        for line in result[0]:
            bbox, (text, conf) = line
            cx = float(np.mean([p[0] for p in bbox]))
            cy = float(np.mean([p[1] for p in bbox]))
            items.append({
                "text": text,
                "center": (cx, cy),
                "bbox": bbox,
                "confidence": float(conf),
            })
        return items
```

### 9.2 文本后处理 `ocr/postprocess.py`

```python
import re


def parse_number(text: str) -> float | None:
    """解析各种科研数字格式：1.2e3, 1,234, ×10⁵ 等"""
    text = text.strip().replace(",", "").replace("−", "-").replace(" ", "")
    # 科学计数法 ×10^n
    m = re.match(r"^(-?\d+\.?\d*)[×x*]10\^?(-?\d+)$", text)
    if m:
        return float(m.group(1)) * 10 ** int(m.group(2))
    m = re.match(r"^-?\d+\.?\d*(?:[eE][-+]?\d+)?$", text)
    return float(m.group()) if m else None


def extract_unit(text: str) -> str | None:
    """从轴标签提取单位，如 'Time (s)' → 's'"""
    m = re.search(r"[\(\[]([^\)\]]+)[\)\]]", text)
    return m.group(1) if m else None
```

---

## 10. 模块六：VLM 抽象层与 Prompt

### 10.1 抽象基类 `vlm/provider.py`

```python
from abc import ABC, abstractmethod
import os
import numpy as np
from core.schemas import ChartType


class VLMProvider(ABC):
    @abstractmethod
    async def classify_chart_type(self, img: np.ndarray) -> ChartType: ...

    @abstractmethod
    async def analyze_semantics(self, image_bytes: bytes) -> dict: ...


def get_vlm_provider() -> VLMProvider:
    """根据环境变量选择 Provider"""
    provider = os.getenv("VLM_PROVIDER", "openai").lower()
    if provider == "openai":
        from vlm.openai_provider import OpenAIProvider
        return OpenAIProvider()
    elif provider == "anthropic":
        from vlm.anthropic_provider import AnthropicProvider
        return AnthropicProvider()
    elif provider == "local":
        from vlm.local_qwen import LocalQwenProvider
        return LocalQwenProvider()
    raise ValueError(f"未知的 VLM_PROVIDER: {provider}")
```

### 10.2 Prompt 模板 `vlm/prompts.py`

```python
CLASSIFY_PROMPT = """你是科研图表分析专家。请判断这张图表的类型。
只能从以下选项中选择一个，仅输出类型的英文单词，不要任何解释：
line, scatter, bar, heatmap, box, pie, contour, microscopy, unknown

类型说明：
- line: 折线图
- scatter: 散点图
- bar: 柱状图/条形图
- heatmap: 热图/矩阵图
- box: 箱线图
- pie: 饼图
- contour: 等高线图
- microscopy: 显微镜图像/实验照片
- unknown: 无法归类

只输出一个单词："""


SEMANTICS_PROMPT = """你是科研图表分析专家。请仔细观察这张图表，
提取以下语义信息，以严格的 JSON 格式输出（不要 markdown 代码块标记）：

{
  "title": "图表标题，无则 null",
  "x_label": "X轴标签（含单位），无则 null",
  "y_label": "Y轴标签（含单位），无则 null",
  "x_unit": "X轴单位，无则 null",
  "y_unit": "Y轴单位，无则 null",
  "x_scale": "linear 或 log",
  "y_scale": "linear 或 log",
  "legend": ["图例项1", "图例项2"],
  "series_colors": {"图例项1": "#hex颜色", ...},
  "data_range_hint": {
    "x_min": 数值或null, "x_max": 数值或null,
    "y_min": 数值或null, "y_max": 数值或null
  },
  "notes": "其他重要观察，如误差棒、拟合线、特殊标注"
}

【重要约束】：
- 你只负责理解语义和文字，绝对不要臆测或编造具体数据点的数值坐标。
- 数据点的精确数值将由专门的算法提取，不需要你给出。
- 只描述你能清晰看到的文字和图例信息。

直接输出 JSON："""


CALIBRATION_ASSIST_PROMPT = """请识别这张科研图表坐标轴上的刻度数值。
按从左到右（X轴）和从下到上（Y轴）的顺序，
以 JSON 输出每个可见刻度标签的数值：

{
  "x_ticks": [刻度数值列表，按位置顺序],
  "y_ticks": [刻度数值列表，按位置顺序],
  "x_scale": "linear 或 log",
  "y_scale": "linear 或 log"
}

只输出 JSON，不要编造看不清的刻度："""
```

### 10.3 OpenAI Provider `vlm/openai_provider.py`

```python
import os
import json
import base64
import cv2
import numpy as np
from openai import AsyncOpenAI
from vlm.provider import VLMProvider
from vlm.prompts import CLASSIFY_PROMPT, SEMANTICS_PROMPT
from vlm.parser import parse_json_response
from core.schemas import ChartType


class OpenAIProvider(VLMProvider):
    def __init__(self, model="gpt-4o"):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def _encode(self, image_bytes: bytes) -> str:
        b64 = base64.b64encode(image_bytes).decode()
        return f"data:image/png;base64,{b64}"

    def _encode_ndarray(self, img: np.ndarray) -> str:
        _, buf = cv2.imencode(".png", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        return self._encode(buf.tobytes())

    async def _ask(self, image_url: str, prompt: str) -> str:
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url",
                     "image_url": {"url": image_url, "detail": "high"}},
                ],
            }],
            temperature=0,   # 确定性输出
            max_tokens=1000,
        )
        return resp.choices[0].message.content

    async def classify_chart_type(self, img: np.ndarray) -> ChartType:
        url = self._encode_ndarray(img)
        text = (await self._ask(url, CLASSIFY_PROMPT)).strip().lower()
        try:
            return ChartType(text)
        except ValueError:
            return ChartType.UNKNOWN

    async def analyze_semantics(self, image_bytes: bytes) -> dict:
        url = self._encode(image_bytes)
        text = await self._ask(url, SEMANTICS_PROMPT)
        return parse_json_response(text)
```

### 10.4 本地 Qwen Provider `vlm/local_qwen.py`

```python
import json
import numpy as np
from PIL import Image
import io
from vlm.provider import VLMProvider
from vlm.prompts import CLASSIFY_PROMPT, SEMANTICS_PROMPT
from vlm.parser import parse_json_response
from core.schemas import ChartType


class LocalQwenProvider(VLMProvider):
    """本地 Qwen2-VL，隐私敏感场景使用，无需联网"""

    def __init__(self, model_path="/app/models/qwen2-vl"):
        from transformers import (Qwen2VLForConditionalGeneration,
                                  AutoProcessor)
        import torch
        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            model_path, torch_dtype=torch.float16, device_map="auto")
        self.processor = AutoProcessor.from_pretrained(model_path)

    def _run(self, image: Image.Image, prompt: str) -> str:
        messages = [{
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": prompt},
            ],
        }]
        text = self.processor.apply_chat_template(
            messages, add_generation_prompt=True)
        inputs = self.processor(text=[text], images=[image],
                               return_tensors="pt").to(self.model.device)
        out = self.model.generate(**inputs, max_new_tokens=1000,
                                  do_sample=False)
        result = self.processor.batch_decode(
            out[:, inputs.input_ids.shape[1]:],
            skip_special_tokens=True)[0]
        return result

    async def classify_chart_type(self, img: np.ndarray) -> ChartType:
        pil = Image.fromarray(img)
        text = self._run(pil, CLASSIFY_PROMPT).strip().lower()
        try:
            return ChartType(text)
        except ValueError:
            return ChartType.UNKNOWN

    async def analyze_semantics(self, image_bytes: bytes) -> dict:
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        text = self._run(pil, SEMANTICS_PROMPT)
        return parse_json_response(text)
```

### 10.5 输出解析 `vlm/parser.py`

```python
import json
import re


def parse_json_response(text: str) -> dict:
    """鲁棒解析 VLM 返回的 JSON（处理 markdown 包裹、多余文本）"""
    text = text.strip()
    # 去除 markdown 代码块
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    # 提取第一个 {...}
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        text = m.group()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"_parse_error": True, "_raw": text}
```

---

## 11. 模块七：交叉验证与置信度

### 11.1 置信度计算 `validation/confidence.py`

数据系列置信度综合多个因素：

\[
C = w_1 \cdot C_{coverage} + w_2 \cdot C_{smooth} + w_3 \cdot C_{agreement}
\]

其中各项分别为覆盖率、平滑度、双引擎一致性。

```python
import numpy as np
from core.schemas import DataSeries


def coverage_score(series: DataSeries, expected_range: tuple) -> float:
    """数据点覆盖 x 范围的程度"""
    if not series.points:
        return 0.0
    xs = [p.x for p in series.points]
    x_min, x_max = expected_range
    if x_max == x_min:
        return 1.0
    covered = (max(xs) - min(xs)) / (x_max - x_min)
    return float(min(1.0, covered))


def smoothness_score(series: DataSeries) -> float:
    """折线平滑度：二阶差分越小越平滑（噪声越少）"""
    if len(series.points) < 3:
        return 0.8
    ys = np.array([p.y for p in series.points])
    second_diff = np.abs(np.diff(ys, 2))
    norm = np.std(ys) + 1e-9
    noise_ratio = np.mean(second_diff) / norm
    return float(np.clip(1.0 - noise_ratio, 0.0, 1.0))


def agreement_score(cv_count: int, vlm_legend_count: int) -> float:
    """CV 系列数与 VLM 识别图例数的一致性"""
    if vlm_legend_count == 0:
        return 0.7
    diff = abs(cv_count - vlm_legend_count)
    return float(max(0.0, 1.0 - diff / max(cv_count, vlm_legend_count)))
```

### 11.2 交叉验证器 `validation/cross_validator.py`

```python
import numpy as np
from core.schemas import (ExtractionResult, DataSeries, ChartType)
from validation.confidence import (smoothness_score, agreement_score)


class CrossValidator:
    """融合 CV 提取结果与 VLM 语义，给出置信度与复核标记"""

    W_SMOOTH = 0.5
    W_AGREE = 0.5
    LOW_THRESHOLD = 0.6

    def validate(self, cv_series: list[DataSeries],
                 semantics: dict, img) -> ExtractionResult:
        flags = []

        legend = semantics.get("legend", []) or []
        agree = agreement_score(len(cv_series), len(legend))

        if agree < 0.7:
            flags.append(
                f"CV检测到 {len(cv_series)} 条系列，"
                f"VLM识别 {len(legend)} 个图例，请人工确认系列数量")

        # 用 VLM 图例名替换 CV 默认命名
        named_series = self._assign_names(cv_series, semantics)

        # 逐系列置信度
        for s in named_series:
            smooth = smoothness_score(s)
            s.confidence = float(
                self.W_SMOOTH * smooth + self.W_AGREE * agree)
            if s.confidence < self.LOW_THRESHOLD:
                flags.append(f"系列 '{s.name}' 置信度偏低，建议人工校正")

        overall = (float(np.mean([s.confidence for s in named_series]))
                   if named_series else 0.0)

        # 检查 VLM 提示的数据范围是否与提取一致
        self._check_range_consistency(named_series, semantics, flags)

        return ExtractionResult(
            chart_type=ChartType(semantics.get("_chart_type", "line"))
                if semantics.get("_chart_type") else ChartType.LINE,
            series=named_series,
            title=semantics.get("title"),
            x_label=semantics.get("x_label"),
            y_label=semantics.get("y_label"),
            legend=legend,
            metadata={"semantics": semantics},
            overall_confidence=overall,
            low_confidence_flags=flags,
        )

    def _assign_names(self, cv_series, semantics):
        """按颜色匹配 VLM 图例名"""
        color_map = semantics.get("series_colors", {}) or {}
        # 反转：hex → name
        hex_to_name = {v.lower(): k for k, v in color_map.items()
                       if isinstance(v, str)}
        for s in cv_series:
            if s.color_hex and s.color_hex.lower() in hex_to_name:
                s.name = hex_to_name[s.color_hex.lower()]
        return cv_series

    def _check_range_consistency(self, series, semantics, flags):
        hint = semantics.get("data_range_hint", {}) or {}
        if not series:
            return
        all_y = [p.y for s in series for p in s.points]
        if not all_y:
            return
        y_min, y_max = min(all_y), max(all_y)
        hint_min = hint.get("y_min")
        hint_max = hint.get("y_max")
        if hint_max is not None and hint_max != 0:
            if abs(y_max - hint_max) / abs(hint_max) > 0.3:
                flags.append(
                    f"提取的Y最大值({y_max:.2f})与VLM估计"
                    f"({hint_max})差异较大，请检查标定")
```

---

## 12. 模块八：输出与导出

### 12.1 多格式导出 `export/exporters.py`

```python
import pandas as pd
import json
import io
from core.schemas import ExtractionResult


def to_dataframe(result: ExtractionResult) -> pd.DataFrame:
    """转为长表格式"""
    rows = []
    for s in result.series:
        for p in s.points:
            rows.append({
                "series": s.name,
                "x": p.x, "y": p.y,
                "confidence": s.confidence,
            })
    return pd.DataFrame(rows)


def export_csv(result: ExtractionResult) -> bytes:
    return to_dataframe(result).to_csv(index=False).encode("utf-8-sig")


def export_excel(result: ExtractionResult) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        # 每个系列一个 sheet
        for s in result.series:
            df = pd.DataFrame([{"x": p.x, "y": p.y} for p in s.points])
            sheet = s.name[:31] or "series"
            df.to_excel(writer, sheet_name=sheet, index=False)
        # 元数据 sheet
        meta = pd.DataFrame([{
            "title": result.title,
            "x_label": result.x_label,
            "y_label": result.y_label,
            "chart_type": result.chart_type.value,
            "overall_confidence": result.overall_confidence,
        }])
        meta.to_excel(writer, sheet_name="metadata", index=False)
    return buf.getvalue()


def export_json(result: ExtractionResult) -> bytes:
    return result.model_dump_json(indent=2).encode("utf-8")
```

### 12.2 PDF 报告 `export/report.py`

```python
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Table,
                                TableStyle, Spacer, Image as RLImage)
from reportlab.lib.styles import getSampleStyleSheet
from core.schemas import ExtractionResult


def generate_report(result: ExtractionResult,
                    original_img_bytes: bytes) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("科研图表提取报告", styles["Title"]))
    elements.append(Spacer(1, 12))

    # 元信息
    meta = [
        ["图表类型", result.chart_type.value],
        ["标题", result.title or "-"],
        ["X轴", result.x_label or "-"],
        ["Y轴", result.y_label or "-"],
        ["整体置信度", f"{result.overall_confidence:.2%}"],
        ["系列数量", str(len(result.series))],
    ]
    t = Table(meta, colWidths=[120, 350])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 12))

    # 原图
    elements.append(Paragraph("原始图表", styles["Heading2"]))
    elements.append(RLImage(io.BytesIO(original_img_bytes),
                            width=400, height=300))
    elements.append(Spacer(1, 12))

    # 低置信度警告
    if result.low_confidence_flags:
        elements.append(Paragraph("⚠ 需人工复核项", styles["Heading2"]))
        for flag in result.low_confidence_flags:
            elements.append(Paragraph(f"• {flag}", styles["Normal"]))

    doc.build(elements)
    return buf.getvalue()
```

---

## 13. 模块九：前端交互画布

### 13.1 状态管理 `frontend/src/store/useStore.ts`

```typescript
import { create } from 'zustand';

export type CalibPoint = {
  pixel: { x: number; y: number };
  data: { x: number; y: number };
};

export type ExtractionState = {
  imageUrl: string | null;
  imageId: string | null;
  chartType: string;
  // 标定的四个参考点（x轴2个，y轴2个）
  xRefs: CalibPoint[];
  yRefs: CalibPoint[];
  xScale: 'linear' | 'log';
  yScale: 'linear' | 'log';
  series: any[];
  flags: string[];
  mode: 'idle' | 'calibrating' | 'extracted';

  setImage: (url: string, id: string) => void;
  addXRef: (p: CalibPoint) => void;
  addYRef: (p: CalibPoint) => void;
  setSeries: (s: any[]) => void;
  setMode: (m: ExtractionState['mode']) => void;
};

export const useStore = create<ExtractionState>((set) => ({
  imageUrl: null,
  imageId: null,
  chartType: 'line',
  xRefs: [],
  yRefs: [],
  xScale: 'linear',
  yScale: 'linear',
  series: [],
  flags: [],
  mode: 'idle',

  setImage: (url, id) => set({ imageUrl: url, imageId: id, mode: 'idle' }),
  addXRef: (p) => set((s) => ({ xRefs: [...s.xRefs, p].slice(-2) })),
  addYRef: (p) => set((s) => ({ yRefs: [...s.yRefs, p].slice(-2) })),
  setSeries: (series) => set({ series, mode: 'extracted' }),
  setMode: (mode) => set({ mode }),
}));
```

### 13.2 主画布 `frontend/src/components/Canvas/ImageCanvas.tsx`

```tsx
import React, { useRef, useState } from 'react';
import { Stage, Layer, Image as KonvaImage } from 'react-konva';
import useImage from 'use-image';
import { useStore } from '../../store/useStore';
import { CalibrationLayer } from './CalibrationLayer';
import { DataPointLayer } from './DataPointLayer';

export const ImageCanvas: React.FC = () => {
  const { imageUrl, mode } = useStore();
  const [image] = useImage(imageUrl || '');
  const [scale, setScale] = useState(1);
  const stageRef = useRef<any>(null);

  // 鼠标滚轮缩放
  const handleWheel = (e: any) => {
    e.evt.preventDefault();
    const scaleBy = 1.1;
    const stage = stageRef.current;
    const oldScale = stage.scaleX();
    const pointer = stage.getPointerPosition();
    const newScale =
      e.evt.deltaY > 0 ? oldScale / scaleBy : oldScale * scaleBy;
    setScale(newScale);
  };

  if (!image) return <div>请上传图片</div>;

  return (
    <Stage
      ref={stageRef}
      width={900}
      height={650}
      scaleX={scale}
      scaleY={scale}
      onWheel={handleWheel}
      draggable
    >
      <Layer>
        <KonvaImage image={image} />
      </Layer>

      {/* 标定层：用户点击设置参考点 */}
      {mode === 'calibrating' && <CalibrationLayer />}

      {/* 数据点层：显示提取结果，可拖拽校正 */}
      {mode === 'extracted' && <DataPointLayer />}
    </Stage>
  );
};
```

### 13.3 标定层 `frontend/src/components/Canvas/CalibrationLayer.tsx`

```tsx
import React, { useState } from 'react';
import { Layer, Circle, Text, Line } from 'react-konva';
import { useStore } from '../../store/useStore';

export const CalibrationLayer: React.FC = () => {
  const { xRefs, yRefs, addXRef, addYRef } = useStore();
  const [pendingAxis, setPendingAxis] = useState<'x' | 'y'>('x');

  const handleClick = (e: any) => {
    const pos = e.target.getStage().getRelativePointerPosition();
    // 弹出输入框让用户输入该点对应的数据值
    const value = prompt(
      `请输入此点在 ${pendingAxis.toUpperCase()} 轴上的数据值：`
    );
    if (value === null) return;

    const point = {
      pixel: { x: pos.x, y: pos.y },
      data:
        pendingAxis === 'x'
          ? { x: parseFloat(value), y: 0 }
          : { x: 0, y: parseFloat(value) },
    };
    if (pendingAxis === 'x') {
      addXRef(point);
      if (xRefs.length >= 1) setPendingAxis('y');
    } else {
      addYRef(point);
    }
  };

  return (
    <Layer onClick={handleClick}>
      {/* 渲染已设置的 X 标定点（红色）*/}
      {xRefs.map((r, i) => (
        <React.Fragment key={`x${i}`}>
          <Circle x={r.pixel.x} y={r.pixel.y} radius={6} fill="red" />
          <Text
            x={r.pixel.x + 8}
            y={r.pixel.y}
            text={`X=${r.data.x}`}
            fontSize={14}
            fill="red"
          />
        </React.Fragment>
      ))}
      {/* 渲染 Y 标定点（蓝色）*/}
      {yRefs.map((r, i) => (
        <React.Fragment key={`y${i}`}>
          <Circle x={r.pixel.x} y={r.pixel.y} radius={6} fill="blue" />
          <Text
            x={r.pixel.x + 8}
            y={r.pixel.y}
            text={`Y=${r.data.y}`}
            fontSize={14}
            fill="blue"
          />
        </React.Fragment>
      ))}
    </Layer>
  );
};
```

### 13.4 数据点层（可拖拽校正）`frontend/src/components/Canvas/DataPointLayer.tsx`

```tsx
import React from 'react';
import { Layer, Circle, Line } from 'react-konva';
import { useStore } from '../../store/useStore';

export const DataPointLayer: React.FC = () => {
  const { series } = useStore();

  return (
    <Layer>
      {series.map((s: any, si: number) => (
        <React.Fragment key={si}>
          {/* 折线连接 */}
          <Line
            points={s.pixelPoints.flatMap((p: any) => [p.x, p.y])}
            stroke={s.color_hex || '#000'}
            strokeWidth={1.5}
          />
          {/* 可拖拽的数据点 */}
          {s.pixelPoints.map((p: any, pi: number) => (
            <Circle
              key={pi}
              x={p.x}
              y={p.y}
              radius={3}
              fill={s.color_hex || '#000'}
              draggable
              onDragEnd={(e) => {
                // 拖拽后重新计算数据坐标（调用后端或本地变换）
                const newPos = e.target.position();
                console.log('校正点', si, pi, newPos);
                // → 触发重算
              }}
            />
          ))}
        </React.Fragment>
      ))}
    </Layer>
  );
};
```

### 13.5 API 服务 `frontend/src/services/api.ts`

```typescript
const BASE = 'http://localhost:8000/api';

export async function uploadImage(file: File) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE}/projects/upload`, {
    method: 'POST',
    body: form,
  });
  return res.json();
}

export async function autoAnalyze(imageId: string) {
  const res = await fetch(`${BASE}/extract/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image_id: imageId }),
  });
  return res.json();
}

export async function extractData(payload: any) {
  const res = await fetch(`${BASE}/extract/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function exportResult(
  imageId: string,
  format: 'csv' | 'excel' | 'json' | 'pdf'
) {
  const res = await fetch(`${BASE}/export/${imageId}?format=${format}`);
  return res.blob();
}
```

### 13.6 重建预览 `frontend/src/components/Preview/RebuiltChart.tsx`

```tsx
import React from 'react';
import ReactECharts from 'echarts-for-react';
import { useStore } from '../../store/useStore';

export const RebuiltChart: React.FC = () => {
  const { series, chartType } = useStore();

  const option = {
    title: { text: '重建图（对比验证）' },
    tooltip: { trigger: 'axis' },
    legend: { data: series.map((s: any) => s.name) },
    xAxis: { type: 'value' },
    yAxis: { type: 'value' },
    series: series.map((s: any) => ({
      name: s.name,
      type: chartType === 'scatter' ? 'scatter' : 'line',
      data: s.points.map((p: any) => [p.x, p.y]),
      itemStyle: { color: s.color_hex },
    })),
  };

  return <ReactECharts option={option} style={{ height: 400 }} />;
};
```

---

## 14. 模块十：人机协同校正

人机协同是**保证准确性的最终保障**。流程如下：

```
自动提取 → 重建图与原图叠加对比 → 用户发现偏差
   → 拖拽修正数据点 / 调整标定点 / 增删系列
   → 实时重算数据坐标 → 确认导出
```

### 14.1 校正重算接口（后端）`api/routes_calibrate.py`

```python
from fastapi import APIRouter
from pydantic import BaseModel
from calibration.calibrator import Calibrator
from core.schemas import CalibrationConfig

router = APIRouter(prefix="/api/calibrate", tags=["calibrate"])


class RecomputeRequest(BaseModel):
    calibration: CalibrationConfig
    pixel_points: list[dict]  # [{series_idx, point_idx, px, py}]


@router.post("/recompute")
async def recompute(req: RecomputeRequest):
    """用户拖拽数据点后，重算其数据坐标"""
    calibrator = Calibrator(req.calibration)
    results = []
    for item in req.pixel_points:
        data_pt = calibrator.pixel_to_data(item["px"], item["py"])
        results.append({
            "series_idx": item["series_idx"],
            "point_idx": item["point_idx"],
            "x": data_pt.x,
            "y": data_pt.y,
        })
    return {"points": results}
```

### 14.2 前端校正逻辑（拖拽 → 重算）

```typescript
// 在 DataPointLayer 的 onDragEnd 中
async function handleDragEnd(seriesIdx: number, pointIdx: number, pos: {x:number,y:number}) {
  const { calibration } = useStore.getState();
  const res = await fetch(`${BASE}/calibrate/recompute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      calibration,
      pixel_points: [{ series_idx: seriesIdx, point_idx: pointIdx,
                       px: pos.x, py: pos.y }],
    }),
  });
  const data = await res.json();
  // 更新 store 中该点的数据坐标 → 重建图自动刷新
  updatePointData(seriesIdx, pointIdx, data.points[0]);
}
```

### 14.3 校正工具栏功能清单

| 功能 | 实现 |
|------|------|
| 拖拽数据点 | Konva `draggable` + 重算接口 |
| 增加数据点 | 双击空白处插入点 |
| 删除数据点 | 选中后按 Delete |
| 调整标定点 | 拖拽标定参考点 → 全部数据重算 |
| 增删系列 | 颜色掩码手动重选 |
| 撤销/重做 | 前端状态历史栈 |
| 网格吸附 | 检测到的刻度线吸附 |

---

## 15. 数据库与存储

### 15.1 数据模型 `storage/models.py`

```python
from sqlalchemy import (Column, String, Float, JSON, DateTime,
                        Integer, LargeBinary)
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True,
                default=lambda: str(uuid.uuid4()))
    name = Column(String)
    image_path = Column(String)
    chart_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class ExtractionRecord(Base):
    __tablename__ = "extractions"
    id = Column(String, primary_key=True,
                default=lambda: str(uuid.uuid4()))
    project_id = Column(String)
    calibration = Column(JSON)
    result = Column(JSON)         # ExtractionResult 序列化
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 15.2 数据库连接 `storage/database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from storage.models import Base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/sciplot.db")

engine = create_engine(DATABASE_URL,
                       connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 16. API 设计

### 16.1 主入口 `main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import (routes_project, routes_extract,
                 routes_calibrate, routes_export)
from storage.database import init_db

app = FastAPI(title="SciPlot Extractor API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # 生产环境应限制
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_project.router)
app.include_router(routes_extract.router)
app.include_router(routes_calibrate.router)
app.include_router(routes_export.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}
```

### 16.2 提取路由 `api/routes_extract.py`

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.orchestrator import Orchestrator
from core.schemas import ChartType, CalibrationConfig
import os

router = APIRouter(prefix="/api/extract", tags=["extract"])
orchestrator = Orchestrator()


class AnalyzeRequest(BaseModel):
    image_id: str


class ExtractRequest(BaseModel):
    image_id: str
    chart_type: ChartType
    calibration: CalibrationConfig
    series_colors: list[str] | None = None


def _load_bytes(image_id: str) -> bytes:
    path = f"./data/uploads/{image_id}"
    if not os.path.exists(path):
        raise HTTPException(404, "图片不存在")
    with open(path, "rb") as f:
        return f.read()


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    """第一阶段：自动分析，返回类型/标定建议/语义"""
    image_bytes = _load_bytes(req.image_id)
    return await orchestrator.auto_analyze(image_bytes)


@router.post("/run")
async def run_extraction(req: ExtractRequest):
    """第二阶段：精确提取"""
    image_bytes = _load_bytes(req.image_id)
    result = await orchestrator.extract(
        image_bytes, req.chart_type,
        req.calibration, req.series_colors)
    # 持久化结果（略）
    return result.model_dump()
```

### 16.3 上传路由 `api/routes_project.py`

```python
from fastapi import APIRouter, UploadFile, File
import uuid
import os

router = APIRouter(prefix="/api/projects", tags=["projects"])
UPLOAD_DIR = "./data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    image_id = f"{uuid.uuid4()}_{file.filename}"
    path = os.path.join(UPLOAD_DIR, image_id)
    with open(path, "wb") as f:
        f.write(await file.read())
    return {"image_id": image_id,
            "url": f"/api/projects/image/{image_id}"}


@router.get("/image/{image_id}")
async def get_image(image_id: str):
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(UPLOAD_DIR, image_id))
```

### 16.4 导出路由 `api/routes_export.py`

```python
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
import io
from export.exporters import export_csv, export_excel, export_json
from export.report import generate_report
# 假设从存储加载结果（此处简化）

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/{image_id}")
async def export(image_id: str,
                 format: str = Query("csv")):
    result = _load_result(image_id)  # 从 DB 加载 ExtractionResult

    if format == "csv":
        data, mime, fn = export_csv(result), "text/csv", "data.csv"
    elif format == "excel":
        data = export_excel(result)
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        fn = "data.xlsx"
    elif format == "json":
        data, mime, fn = export_json(result), "application/json", "data.json"
    elif format == "pdf":
        img = _load_image_bytes(image_id)
        data, mime, fn = generate_report(result, img), "application/pdf", "report.pdf"
    else:
        return {"error": "不支持的格式"}

    return StreamingResponse(
        io.BytesIO(data), media_type=mime,
        headers={"Content-Disposition": f"attachment; filename={fn}"})
```

### 16.5 API 端点总览

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/projects/upload` | 上传图片 |
| GET | `/api/projects/image/{id}` | 获取图片 |
| POST | `/api/extract/analyze` | 自动分析（类型+标定建议+语义） |
| POST | `/api/extract/run` | 执行精确提取 |
| POST | `/api/calibrate/recompute` | 校正后重算坐标 |
| GET | `/api/export/{id}?format=` | 导出 CSV/Excel/JSON/PDF |
| GET | `/health` | 健康检查 |

---

## 17. 测试与精度评估

### 17.1 精度评估指标

对提取结果 \(\hat{y}_i\) 与真值 \(y_i\)，计算：

**平均绝对百分比误差**：
\[
MAPE = \frac{1}{N}\sum_{i=1}^{N}\left|\frac{y_i - \hat{y}_i}{y_i}\right| \times 100\%
\]

**均方根误差**：
\[
RMSE = \sqrt{\frac{1}{N}\sum_{i=1}^{N}(y_i - \hat{y}_i)^2}
\]

### 17.2 测试代码 `tests/test_extraction.py`

```python
import numpy as np
import pytest
from calibration.calibrator import Calibrator
from core.schemas import (CalibrationConfig, AxisCalibration,
                          CalibrationPoint, Point, AxisScale)


def make_calibration():
    """构造一个已知的标定配置用于测试"""
    return CalibrationConfig(
        x_axis=AxisCalibration(
            scale=AxisScale.LINEAR,
            ref1=CalibrationPoint(pixel=Point(x=100, y=500),
                                  data=Point(x=0, y=0)),
            ref2=CalibrationPoint(pixel=Point(x=500, y=500),
                                  data=Point(x=10, y=0)),
        ),
        y_axis=AxisCalibration(
            scale=AxisScale.LINEAR,
            ref1=CalibrationPoint(pixel=Point(x=100, y=500),
                                  data=Point(x=0, y=0)),
            ref2=CalibrationPoint(pixel=Point(x=100, y=100),
                                  data=Point(x=0, y=100)),
        ),
    )


def test_pixel_to_data():
    cal = Calibrator(make_calibration())
    # 像素 (300, 300) 应映射到数据 (5, 50)
    pt = cal.pixel_to_data(300, 300)
    assert abs(pt.x - 5.0) < 1e-6
    assert abs(pt.y - 50.0) < 1e-6


def test_log_axis():
    """对数轴标定测试"""
    cal_config = CalibrationConfig(
        x_axis=AxisCalibration(
            scale=AxisScale.LOG,
            ref1=CalibrationPoint(pixel=Point(x=100, y=0),
                                  data=Point(x=1, y=0)),
            ref2=CalibrationPoint(pixel=Point(x=300, y=0),
                                  data=Point(x=100, y=0)),
        ),
        y_axis=AxisCalibration(
            scale=AxisScale.LINEAR,
            ref1=CalibrationPoint(pixel=Point(x=0, y=100),
                                  data=Point(x=0, y=0)),
            ref2=CalibrationPoint(pixel=Point(x=0, y=0),
                                  data=Point(x=0, y=10)),
        ),
    )
    cal = Calibrator(cal_config)
    # 像素 x=200 (中点) 应对应 10 (对数中点)
    pt = cal.pixel_to_data(200, 50)
    assert abs(pt.x - 10.0) < 0.01


def test_roundtrip():
    """像素→数据→像素 往返一致性"""
    cal = Calibrator(make_calibration())
    pt = cal.pixel_to_data(250, 350)
    px = cal.data_to_pixel(pt.x, pt.y)
    assert abs(px.x - 250) < 1e-6
    assert abs(px.y - 350) < 1e-6
```

### 17.3 基准测试集

建立标准测试集评估整体精度：

```
tests/benchmark/
├── line_charts/         # 已知真值的折线图
│   ├── chart_01.png
│   ├── chart_01_truth.csv
│   └── ...
├── scatter/
├── bar/
└── run_benchmark.py     # 批量评估 MAPE/RMSE
```

```python
# run_benchmark.py
import pandas as pd
import numpy as np


def evaluate(pred_csv, truth_csv) -> dict:
    pred = pd.read_csv(pred_csv)
    truth = pd.read_csv(truth_csv)
    # 按 x 对齐插值后比较 y
    merged = pd.merge_asof(
        pred.sort_values("x"), truth.sort_values("x"),
        on="x", suffixes=("_pred", "_truth"))
    err = np.abs((merged.y_truth - merged.y_pred) /
                 merged.y_truth.replace(0, np.nan))
    mape = err.mean() * 100
    rmse = np.sqrt(((merged.y_truth - merged.y_pred) ** 2).mean())
    return {"MAPE": mape, "RMSE": rmse}
```

