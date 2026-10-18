# 06 — MCP 授权与恢复记录

## 2026-10-18 23:00 · upload-post 重新授权（成功）

背景：`mcp-tokens/upload-post.json` 自 2026-10-07 06:31 起被删（当时一次 cron 内 `hermes mcp login --flow browser` 授权超时，脚本先删 token），此后 12 天：
- 05/19 点发布班全部走「parked 守卫」直接跳过（executions 记为 completed，实际零发布）；
- IG 最后一条帖子停在 2026-10-06（`43 统一之谜`）；
- 素材库积压 15 条待发。

### 操作步骤（可复用）

```bash
HERMES="C:/Users/20200/AppData/Local/hermes/hermes-agent/venv/Scripts/hermes.exe"

# 1) 必须先杀掉还在跑的旧 login（否则端口/client 冲突）
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object {\$_.CommandLine -like '*mcp login upload-post*'} | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }"

# 2) 用 pty 跑 browser flow（pty 才看得到实时输出）
"$HERMES" mcp login upload-post --flow browser

# 3) 浏览器自动打开授权页 → 登录 Upload-Post → 点授权
#    成功标志：终端打印  ✓ Authenticated — 73 tool(s) available
```

### 关键坑位

| 现象 | 原因 | 处置 |
|---|---|---|
| PowerShell 报「无法将 hermes 项识别为 cmdlet」 | `hermes` 不在用户 PATH | 用全路径 `C:\Users\20200\AppData\Local\hermes\hermes-agent\venv\Scripts\hermes.exe`，或在 git-bash 里跑 |
| `--flow device` 立即失败：`Server does not advertise device authorization` | 该服务端不支持 RFC 8628 | 只能用 `--flow browser` |
| 浏览器已跳到 `127.0.0.1:13687/callback?code=…` 但 token 没落盘 | 非 pty 运行时 stdout 块缓冲 + 回调交换未完成 | 结束进程，改 **pty** 重跑；每次 login 都会重新注册 client（client_id 会变） |
| `get_account_info` 回 `Token is valid` 但发布仍失败 | token 只证明鉴权通 | 再跑一次只读 `get_media`，能返回帖子才算链路通 |

### 本次结果

- token 有效期 ≈ 7 天（604,771s），自动刷新可用；
- 账号 `xxx139139@gmail.com`，plan `Basic`；
- profiles：`xiangge`（TikTok 显示名「艾伦和艾薇」/ YouTube「AIGC徐黑蛋」等连接均 `reauth_required:false`）；
- 工具数 **73**（不是旧文档写的 58）；
- 只读验证：`get_media(instagram, limit=3)` 返回 10-06 三条 Reel，链路真实可用。

### 待办（恢复运营）

- [x] **补发第 1 条已完成（2026-10-18 23:37–23:52）**：`44 美索不达米亚：被遗忘的文明` 发到 FB / IG / TG / X 四平台，全部 `success` 且字节数精确相等，目录已归档到 `@已发\【已发】44 …`。
  - IG https://www.instagram.com/reel/DepBebck0uB/
  - FB https://www.facebook.com/1368682286321514/videos/1084028797775761
  - TG https://t.me/Dabaoagent/86
  - X https://x.com/AlanandLvy/status/2111844842338673017
  - ⚠️ 本班踩坑：`_pub_one_0924.py` 的 PUT 线路轮换原先把 http 代理排第一 → 142MB 被限速 ~99KB/s、600s 超时；**已改为 `--noproxy '*'` 直连优先**（4.18MB/s / 34s）。
- [ ] 观察 24h 数据：日报 20:00 班应恢复四平台数字；
- [ ] 素材库剩余 14 条（约 7 天），按 2 条/天自动跑。
