# -*- coding: utf-8 -*-
"""直连调用 upload-post MCP 工具（MCP parked 时的活路）。例：python uploadpost.py get_account_info '{}'

薄壳：不复制逻辑，转发到真相源 HERMES_HOME/scripts/uploadpost_mcp.py
用法：python uploadpost.py <args...>   （等价于直接跑真相源）
"""
import os
import subprocess
import sys

HERMES_HOME = os.environ.get("HERMES_HOME") or (
    os.environ.get("LOCALAPPDATA", r"C:\Users\20200\AppData\Local") + r"\hermes"
)
REAL = os.path.join(HERMES_HOME, "scripts", "uploadpost_mcp.py")

if not os.path.exists(REAL):
    sys.exit("真相源缺失: " + REAL + "（检查 HERMES_HOME 或重新部署 Hermes 脚本目录）")

if __name__ == "__main__":
    sys.exit(subprocess.call([sys.executable, REAL] + sys.argv[1:]))
