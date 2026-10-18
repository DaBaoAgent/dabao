# tools — 薄壳（转发到真相源）

这里**不放逻辑**，每个 `.py` 都是 8 行转发器：把参数原样交给 `HERMES_HOME\scripts\<real>.py`。

| 薄壳 | 真相源 | 用途 |
|---|---|---|
| `uploadpost.py` | `uploadpost_mcp.py` | 直连调 MCP 工具（`get_account_info`、`get_media`、`upload_video`…） |
| `stage_upload.py` | `dabao_stage_upload.py` | 文件 staging：create→PUT（线路轮换）→complete |
| `pub_one.py` | `_pub_one_0924.py` | 单平台发布器（spec.json 驱动，见 docs/03） |
| `publish_retry.py` | `dabao_publish_retry.py` | 补发 watchdog（`--dry` 只看不动） |
| `gh_cover.py` | `dabao_gh_cover.py` | 封面转 GitHub raw URL |
| `detach_run.py` | `_detach_run.py` | 脱离式后台启动长任务 |

## 为什么是薄壳而不是 junction

- Windows 的**目录** junction 可跨卷，但**文件**做不到硬链接（C: 与 D: 不同卷）→ 直接复制就是双真相源；
- cron 只从 `HERMES_HOME\scripts\` 执行脚本（调度器有路径穿越校验），真相源必须留在那里；
- 薄壳保证「项目里点哪个都能跑」，但改逻辑永远只改一处。

## 判据

跑 `python tools\publish_retry.py --dry` 若报 `真相源缺失` → HERMES_HOME 路径不对或脚本被移走，先修环境再做发布。
