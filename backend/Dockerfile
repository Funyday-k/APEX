FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-ocr.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-ocr.txt || true

COPY . .

ENV DATA_DIR=/app/data
RUN mkdir -p /app/data/uploads /app/data/results

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
