# -*- coding: utf-8 -*-
"""封面转 GitHub raw URL（YouTube 缩略图用，R2 签名 URL 必 403）。

薄壳：不复制逻辑，转发到真相源 HERMES_HOME/scripts/dabao_gh_cover.py
用法：python gh_cover.py <args...>   （等价于直接跑真相源）
"""
import os
import subprocess
import sys

HERMES_HOME = os.environ.get("HERMES_HOME") or (
    os.environ.get("LOCALAPPDATA", r"C:\Users\20200\AppData\Local") + r"\hermes"
)
REAL = os.path.join(HERMES_HOME, "scripts", "dabao_gh_cover.py")

if not os.path.exists(REAL):
    sys.exit("真相源缺失: " + REAL + "（检查 HERMES_HOME 或重新部署 Hermes 脚本目录）")

if __name__ == "__main__":
    sys.exit(subprocess.call([sys.executable, REAL] + sys.argv[1:]))
