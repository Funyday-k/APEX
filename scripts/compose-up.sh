#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "已创建 .env（可按需填入 OPENAI_API_KEY 等）"
fi

mkdir -p data/uploads data/results models

if docker compose version &>/dev/null; then
  COMPOSE=(docker compose)
elif command -v docker-compose &>/dev/null; then
  COMPOSE=(docker-compose)
else
  echo "未找到 docker compose。请先: brew install docker docker-compose colima && colima start -f"
  exit 1
fi

"${COMPOSE[@]}" up -d --build
echo ""
echo "SciPlot 已启动："
echo "  前端  http://localhost:3000"
echo "  后端  http://localhost:8000/docs"
echo "  健康  http://localhost:8000/health"
