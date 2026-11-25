#!/usr/bin/env bash
# 一键激活本项目 Python 虚拟环境 (.venv)
# 用法 1（推荐，直接在当前终端激活）：source start_venv.sh  或  . start_venv.sh
# 用法 2（直接运行，启动一个已激活虚拟环境的终端）：./start_venv.sh

if [ -n "${BASH_SOURCE:-}" ]; then
    _START_VENV_SCRIPT="${BASH_SOURCE[0]}"
else
    _START_VENV_SCRIPT="$0"
fi

_START_VENV_DIR="$(cd "$(dirname "$_START_VENV_SCRIPT")" && pwd)"
_ACTIVATE_SCRIPT="$_START_VENV_DIR/.venv/Scripts/activate"

if [ ! -f "$_ACTIVATE_SCRIPT" ] && [ -f "$_START_VENV_DIR/.venv/bin/activate" ]; then
    _ACTIVATE_SCRIPT="$_START_VENV_DIR/.venv/bin/activate"
fi

if (return 0 2>/dev/null); then
    _IS_SOURCED=1
else
    _IS_SOURCED=0
fi

if [ ! -f "$_ACTIVATE_SCRIPT" ]; then
    echo "错误：未找到虚拟环境激活脚本：$_START_VENV_DIR/.venv" >&2
    echo "请先在项目根目录创建虚拟环境：python -m venv .venv" >&2
    unset _START_VENV_SCRIPT _START_VENV_DIR _ACTIVATE_SCRIPT
    if [ "$_IS_SOURCED" -eq 1 ]; then
        unset _IS_SOURCED
        return 1
    else
        exit 1
    fi
fi

if [ "$_IS_SOURCED" -eq 1 ]; then
    # shellcheck disable=SC1090
    source "$_ACTIVATE_SCRIPT"
    echo "虚拟环境已激活: $(which python)"
    unset _START_VENV_SCRIPT _START_VENV_DIR _ACTIVATE_SCRIPT _IS_SOURCED
else
    _TMP_RC="$(mktemp)"
    printf -v _Q_TMP_RC '%q' "$_TMP_RC"
    printf -v _Q_ACTIVATE '%q' "$_ACTIVATE_SCRIPT"
    cat > "$_TMP_RC" <<EOF
rm -f $_Q_TMP_RC
[ -f /etc/bash.bashrc ] && source /etc/bash.bashrc
[ -f "\$HOME/.bashrc" ] && source "\$HOME/.bashrc"
source $_Q_ACTIVATE
echo "虚拟环境已激活（输入 exit 可退出）: \$(which python)"
EOF
    exec bash --rcfile "$_TMP_RC" -i
fi
