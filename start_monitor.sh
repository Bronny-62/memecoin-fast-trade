#!/bin/bash
echo "--- MemeCoin Fast Trade 1.0 一键启动脚本 ---"
echo "============================================="
echo "实时监控WebSocket推送，基于关键词自动买币"

# Check for Python 3
if ! command -v python3 &> /dev/null
then
    echo "Error: Python 3 is not installed or not in PATH. Please install Python 3."
    exit 1
fi
echo "Python 3 check passed."

# --- Virtual Environment Setup ---
VENV_DIR=".venv"
CREATED_VENV=0
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found, creating..."
    python3 -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment. Please check your Python 3 installation."
        echo "You may need to install python3-venv package:"
        echo "  On Ubuntu/Debian: sudo apt install python3-venv"
        echo "  On macOS: python3 should have venv built-in"
        exit 1
    fi
    echo "Virtual environment created successfully."
    CREATED_VENV=1
    
    # Ensure pip is available in the new virtual environment
    echo "Ensuring pip is available in virtual environment..."
    source $VENV_DIR/bin/activate
    python -m ensurepip --upgrade 2>/dev/null || echo "ensurepip not available, pip should already be installed"
    deactivate
fi

echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Verify virtual environment activation
if [ "$VIRTUAL_ENV" != "" ]; then
    echo "Virtual environment activated: $VIRTUAL_ENV"
else
    echo "Warning: Virtual environment may not be properly activated"
fi

# --- Install Dependencies ---
echo "Installing Python dependencies..."
# Use the virtual environment's pip with full path to ensure we're using the right one
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

if [ -f "$VENV_PIP" ]; then
    if [ "$CREATED_VENV" -eq 1 ]; then
        echo "Using virtual environment pip: $VENV_PIP"
        $VENV_PIP install --disable-pip-version-check -r requirements.txt
    else
        $VENV_PIP install --disable-pip-version-check -q -r requirements.txt >/dev/null
    fi
elif [ -f "$VENV_PYTHON" ]; then
    if [ "$CREATED_VENV" -eq 1 ]; then
        echo "Using virtual environment python with -m pip"
        $VENV_PYTHON -m pip install --disable-pip-version-check -r requirements.txt
    else
        $VENV_PYTHON -m pip install --disable-pip-version-check -q -r requirements.txt >/dev/null
    fi
else
    echo "Error: Virtual environment python/pip not found"
    echo "Virtual environment may not be properly created"
    deactivate
    exit 1
fi

if [ $? -ne 0 ]; then
    echo "Error: Dependency installation failed."
    deactivate
    exit 1
fi
if [ "$CREATED_VENV" -eq 1 ]; then
    echo "Dependencies installed successfully."
else
    echo "Dependencies check passed."
fi

export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

echo ""
echo "=== 平台兼容性检查 ==="
$VENV_PYTHON -m monitoring_service.tools.platform_check
if [ $? -ne 0 ]; then
    echo "[ERROR] 平台兼容性检查失败。"
    deactivate
    exit 1
fi

# --- Telegram Authorization & Bot Connection ---
echo ""
echo "=== Telegram 授权与机器人连接检查 ==="
echo "[SETUP] 每次启动都会检查 Telegram 会话与机器人联通性。"
echo "[SETUP] 如果当前未授权，将自动进入手机号和验证码验证流程。"
echo ""

$VENV_PYTHON -m monitoring_service.tools.telegram_auth
if [ $? -ne 0 ]; then
    echo "[ERROR] Telegram 授权或联通性检查失败，请检查配置后重试。"
    deactivate
    exit 1
fi
echo ""

# --- Start Service ---
echo ""
echo "=== 启动监控服务 ==="
echo ""
echo "MemeCoin Fast Trade 1.0 使用说明"
echo "======================================"
echo ""
echo "系统功能:"
echo "   - 实时监控WebSocket推送的推文内容"
echo "   - 支持Twitter和Binance Square平台"
echo "   - 基于关键词匹配自动发送代币地址到Telegram Bot"
echo "   - BSC 双层权限控制(BSC_T0, BSC_T1)"
echo "   - XLayer 双层权限控制(XLAYER_T0, XLAYER_T1)"
echo ""
echo "配置说明:"
echo "   - WebSocket URL: config/config.ini 中的 [Source] ws_url"
echo "   - 关键词映射: config/token_mapping.json"
echo "   - 监控用户: config/monitored_users.json"
echo ""
echo "权限层级:"
echo "   - SigmaBot_T0_Users: 可触发 SigmaBot_T0_KEYS 和 SigmaBot_T1_KEYS"
echo "   - SigmaBot_T1_Users: 仅触发 SigmaBot_T1_KEYS"
echo "   - BasedBot_T0_Users: 可触发 BasedBot_T0_KEYS 和 BasedBot_T1_KEYS"
echo "   - BasedBot_T1_Users: 仅触发 BasedBot_T1_KEYS"
echo ""

# Clean up existing processes on port 8051 ONLY (do not affect port 8050)
echo "Checking for existing services on port 8051..."
EXISTING_PID=$(lsof -ti:8051 2>/dev/null)
if [ ! -z "$EXISTING_PID" ]; then
  echo "Warning: Port 8051 is occupied by PID: $EXISTING_PID"
  echo "Attempting to terminate the existing process..."
  kill $EXISTING_PID 2>/dev/null || sudo kill $EXISTING_PID 2>/dev/null
  sleep 2
  echo "Process terminated."
  echo "Note: Other systems (e.g., cook_v5 on port 8050) are NOT affected."
fi

function cleanup() {
    echo "Deactivating virtual environment..."
    deactivate
    echo "Service stopped."
}

trap cleanup EXIT

# Launch the server
echo "正在启动监控服务 (MemeCoin Fast Trade 1.0)..."
echo "服务地址: http://localhost:8051"
echo "WebSocket: ws://localhost:8051/ws"
echo ""
echo "GMGN 插件连接说明:"
echo "   - 在 gmgn.ai 页面打开 GMGN Monitor 插件"
echo "   - 点击连接按钮连接到本系统 (ws://localhost:8051/ws)"
echo "   - 或连接到 cook_v5 系统 (ws://localhost:8050/ws)"
echo ""
echo "按 Ctrl+C 停止服务"
echo "========================================="

$VENV_PYTHON -m monitoring_service
