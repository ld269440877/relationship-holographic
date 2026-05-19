#!/bin/bash
# 关系动力学全息 - 启动脚本

echo "🚀 正在启动关系动力学全息系统..."

# 创建数据目录
mkdir -p data

# 安装后端依赖
echo "📦 安装后端依赖..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r ../requirements.txt -q

# 初始化数据库
echo "🗄️ 初始化数据库..."
cd ..
python3 -c "from backend.database.seed import seed_all; seed_all()"

# 启动后端（后台运行）
echo "🌐 启动后端服务..."
source venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 切换到前端目录
cd frontend

# 安装前端依赖
echo "📦 安装前端依赖..."
npm install --silent 2>/dev/null

# 启动前端
echo "🖥️ 启动前端服务..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ 系统启动完成！"
echo "   后端API: http://localhost:8000"
echo "   前端界面: http://localhost:3000"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待中断信号
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

wait