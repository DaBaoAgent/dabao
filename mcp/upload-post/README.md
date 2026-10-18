# upload-post MCP（dabao 的发布通道）

| 项 | 值 |
|---|---|
| Server | `upload-post` · `https://mcp.upload-post.com/mcp` |
| 鉴权 | OAuth（`hermes mcp login upload-post`，交互式） |
| Hermes 配置键 | `mcp.servers.upload-post`（真源 `HERMES_HOME\config.yaml`） |
| profile | `xiangge` |
| 套餐 | Basic $24/月 · 5 profiles |
| 直连调用器 | `HERMES_HOME\scripts\uploadpost_mcp.py`（本项目 `tools\uploadpost.py` 薄壳） |
| token | `HERMES_HOME\mcp-tokens\upload-post.json` / `.client.json` / `.meta.json` |
| IG 独立 token | `HERMES_HOME\cache\dabao_duty\conv.json`（正则 `access_token=(IG…)`） |

## 生命周期

```bash
# ⚠️ hermes 不在用户 PATH：一律用全路径（或在 git-bash 里跑）
HERMES="C:/Users/20200/AppData/Local/hermes/hermes-agent/venv/Scripts/hermes.exe"

# 注册（幂等，从 server.json 读 url）
powershell -NoProfile -ExecutionPolicy Bypass -File D:/@kaifa/dabao/mcp/upload-post/register.ps1

# 授权（仅人工，必须 pty 前台；cron 内必失败且会先删 token）
"$HERMES" mcp login upload-post --flow browser    # 成功标志：✓ Authenticated — 73 tool(s) available

# 健康检查（只读）
python D:/@kaifa/dabao/mcp/upload-post/health.py

# 直连调任意工具（MCP parked 时的唯一活路）
python D:/@kaifa/dabao/tools/uploadpost.py get_account_info '{}'
python D:/@kaifa/dabao/tools/uploadpost.py --list
```

## 两种通道

| 通道 | 何时用 | 限制 |
|---|---|---|
| Hermes MCP 工具 `mcp__upload_post__*` | 会话工具目录里有这些工具时 | server parked 时整批消失，本会话不会自动恢复 |
| 直连调用器 `uploadpost_mcp.py` | MCP parked / 单工具瞬态失败 / 后台脚本 | 需磁盘 token 可刷新；token 彻底失效时两者都不可用 |

## 编排到项目里的方式

- **不复制服务端代码**：upload-post 是云 MCP 服务，本地只有「注册声明 + token + 调用器」三样，全部纳入本项目 `mcp/upload-post/` 管理。
- 其它机器接入：`register.ps1` 读同一份 `server.json` 重建；token 需各自交互授权一次。
- 平台账号连接关系（IG/X/FB/TG…）在 Upload-Post 云端账号里，不随本地文件迁移。

## 常见故障

| 症状 | 判据 | 处置 |
|---|---|---|
| 57 个工具全部缺席 | `grep -i parking logs/mcp-stderr.log` | 改走直连调用器 |
| refresh 回 `invalid_grant` | token 文件 expires 已过 + 直连 401 | 交互式 `hermes mcp login upload-post`；**不要**删 token 文件 |
| `get_analytics` Connection closed | 返回体大 | 走直连调用器（`platforms` 必填，FB 加 pageId） |
| 429 Too many active staging uploads | staging 池上限 10 | 逐平台串行 + 发完 delete；封面走 GitHub raw |

详见 [../../docs/05-故障排查.md](../../docs/05-故障排查.md)。
