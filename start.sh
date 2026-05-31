#!/bin/bash
# 关系动力学全息 - 启动脚本
set -e

echo "🚀 正在启动关系动力学全息系统..."

# 始终从脚本所在的项目根目录运行，避免中文路径和 backend 子目录导致的 import/venv 问题。
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# 创建数据目录
mkdir -p data

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
API_BASE="http://127.0.0.1:${BACKEND_PORT}"
FRONTEND_BASE="http://127.0.0.1:${FRONTEND_PORT}"

stop_project_port() {
    local port="$1"
    local label="$2"
    local pids
    pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
    if [ -z "$pids" ]; then
        return 0
    fi

    local kept=0
    for pid in $pids; do
        local command
        command="$(ps -p "$pid" -o command= 2>/dev/null || true)"
        if echo "$command" | grep -E "backend.main:app|vite|${PROJECT_ROOT}" >/dev/null 2>&1; then
            echo "♻️  关闭旧${label}进程 PID=$pid"
            kill "$pid" 2>/dev/null || true
        else
            kept=1
            echo "⚠️  端口 $port 已被非本项目进程占用：$command"
        fi
    done

    sleep 1
    if [ "$kept" = "1" ] && lsof -tiTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
        echo "❌ 端口 $port 仍被其他程序占用，请先关闭后再运行。"
        exit 1
    fi
}

wait_for_url() {
    local url="$1"
    local label="$2"
    local attempts="${3:-40}"
    for _ in $(seq 1 "$attempts"); do
        if curl -fsS "$url" >/dev/null 2>&1; then
            echo "✅ ${label} 就绪：$url"
            return 0
        fi
        sleep 0.5
    done
    echo "❌ ${label} 启动超时：$url"
    return 1
}

echo "🧹 清理本项目旧服务..."
stop_project_port "$BACKEND_PORT" "后端"
stop_project_port "$FRONTEND_PORT" "前端"

# 安装后端依赖
echo "📦 安装后端依赖..."
if [ -z "${PYTHON_BIN:-}" ]; then
    if command -v python3.11 >/dev/null 2>&1; then
        PYTHON_BIN="python3.11"
    else
        PYTHON_BIN="python3"
    fi
fi
if [ -d ".venv" ] && [ -x ".venv/bin/python" ]; then
    VENV_VERSION="$(.venv/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    if [ "$VENV_VERSION" != "3.11" ]; then
        echo "⚠️ 检测到 .venv 使用 Python $VENV_VERSION，当前依赖建议 Python 3.11，正在重建虚拟环境..."
        rm -rf .venv
    fi
fi
if [ ! -d ".venv" ]; then
    "$PYTHON_BIN" -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q

# 初始化数据库
echo "🗄️ 初始化数据库..."
python -c "from backend.database.seed import seed_all; seed_all()"

# 启动后端（后台运行）
echo "🌐 启动后端服务..."
if [ "${BACKEND_RELOAD:-0}" = "1" ]; then
    uvicorn backend.main:app --host 127.0.0.1 --port "$BACKEND_PORT" --reload &
else
    uvicorn backend.main:app --host 127.0.0.1 --port "$BACKEND_PORT" &
fi
BACKEND_PID=$!
wait_for_url "${API_BASE}/health" "后端健康检查"
wait_for_url "${API_BASE}/api/analytics/center?limit=20" "关键 API"

# 切换到前端目录
cd frontend

# 安装前端依赖
echo "📦 安装前端依赖..."
npm install --silent 2>/dev/null

# 启动前端
echo "🖥️ 启动前端服务..."
VITE_API_PROXY_TARGET="$API_BASE" npm run dev -- --host 127.0.0.1 --port "$FRONTEND_PORT" --strictPort &
FRONTEND_PID=$!
wait_for_url "$FRONTEND_BASE" "前端页面"

echo ""
echo "✅ 系统启动完成！"
echo "   后端API: ${API_BASE}"
echo "   API文档: ${API_BASE}/docs"
echo "   旧版手册: ${API_BASE}/manual"
echo "   前端界面: ${FRONTEND_BASE}"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待中断信号
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

wait
