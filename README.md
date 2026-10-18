# dabao — 纪录片/历史视频多平台发布运营项目

> 一句话：**AutoUP/AutoYY 产出的纪录片解说成片，统一由本项目发布到 Instagram / X / Facebook / Telegram（+ TikTok / YouTube 暂停中），并负责互动值班、数据日报、失败补发。**
>
> 项目根：`D:\@kaifa\dabao`　真相源（技能本体）：`C:\Users\20200\AppData\Local\hermes\skills\dabao`（junction 视图 `.\skill`）

---

## 1. 项目边界

| 环节 | 归谁 | 位置 |
|---|---|---|
| 选题 → 下载 → 文案 → 配音 → 剪辑 → 封面 | AutoUP（前身 AutoYY） | 成品进 `D:\自动剪辑\纪录片解说待发\<编号-片名>\` |
| **发布 / 互动 / 日报 / 补发** | **本项目 dabao** | `D:\@kaifa\dabao` + Hermes cron |
| 发布通道 | MCP server `upload-post`（Upload-Post 云服务，profile `xiangge`） | 配置见 [`mcp/upload-post/`](mcp/upload-post/) |

**只做发布运营，不做视频生产。** 片源不进本仓库，素材库路径见下。

---

## 2. 目录地图

```
D:\@kaifa\dabao\
├─ README.md                     本文件：总览 + 快速开始 + 运营班表
├─ docs\
│  ├─ 01-架构与真相源.md          谁管理谁、为什么用 junction 而不复制
│  ├─ 02-平台账号矩阵.md          六平台账号/参数/版本分工/暂停状态
│  ├─ 03-发布SOP.md              单条片子从扫描到归档的完整步骤
│  ├─ 04-运营班表与cron.md        6 条 cron 的 id/时间/职责/改法
│  └─ 05-故障排查.md              高频坑位与判据（MCP parked、429、代理、token）
├─ mcp\upload-post\              MCP server 资产：定义/注册/健康检查
│  ├─ server.json                 server 定义（url + oauth），注册真相源
│  ├─ register.ps1                幂等注册到 Hermes（config.yaml mcp 段）
│  ├─ health.py                   只用标准库的健康检查（token + 账号）
│  └─ README.md                   MCP 生命周期、token 位置、parked 自救
├─ tools\                        6 个薄壳，转发到 HERMES_HOME\scripts 的真相源
├─ cron\                         6 条 dabao cron 的快照 + prompt 全文
├─ skill\                        junction → Hermes skills\dabao（SKILL.md 10 万字坑位库）
├─ scripts\status.py             一键体检：通道/素材库存/最近发布/日报
└─ state\                        运行时状态（不入库）
```

---

## 3. 快速开始

```bash
# ① 体检（只读，不发帖）
"C:/Users/20200/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe" D:/@kaifa/dabao/scripts/status.py

# ② 只验发布通道（upload-post MCP 账号信息）
"C:/Users/20200/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe" D:/@kaifa/dabao/mcp/upload-post/health.py

# ③ 查看/重建 MCP 注册
powershell -NoProfile -ExecutionPolicy Bypass -File D:/@kaifa/dabao/mcp/upload-post/register.ps1

# ④ 手动补发判定（只看不动）
"C:/Users/20200/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe" D:/@kaifa/dabao/tools/publish_retry.py --dry
```

发布本身由 cron 自动跑（05:00 / 19:00），**不要**用 `hermes cron run` 前台手动跑发布班（会把 job 判成 unknown，见 docs/05）。

---

## 4. 六平台矩阵（当前生效）

| 平台 | 账号 | 版本 | 状态 |
|---|---|---|---|
| Instagram | `@lvy99229` | 2分钟版 Reels + 3:4 封面 + `firstComment` 引流主页简介 | ✅ |
| X | `@AlanandLvy` | X-裁剪 2 分钟（H.264 ≤50MB），正文不带链接、CTA「主页简介」 | ✅ |
| Facebook | Page「Autoyy纪录片解说工厂」`1368682286321514` | 完整版 VIDEO | ✅ |
| Telegram | 群 `@Dabaoagent` / bot `@Dabaoagentbot` | 2分钟版 ≤10MB（480p） | ✅ |
| TikTok | `@alanandlvy` | — | ⛔ 2026-09-15 起暂停（账号注销中） |
| YouTube | `DabaoAgent` / `@xuheidan` | — | ⛔ 2026-09-18 起暂停（老板令） |

恢复任一平台：改 `skill\SKILL.md` 顶部暂停声明 + 两条发布班 prompt 的 platforms，再改本表。详见 [docs/02](docs/02-平台账号矩阵.md)。

---

## 5. 运营班表

| 时间 | job id | 职责 |
|---|---|---|
| 每天 05:00 / 19:00 | `222636e84bbd` / `b1ac6266c95b` | 发下一条待发片（按目录名序），全平台成功才归档 |
| 每 30 分钟 | `da63e3511e89` | 发布班失败自动补发（no_agent 脚本，QQ 通知） |
| 每小时 07–23 点 | `4c3c057a96db` | 评论/私信互动值班（IG 为主，AutoDM 绑新帖） |
| 每天 20:00 | `e40385ea577f` | 六平台数据日报 → HTML 邮件 + QQ 简讯 |
| 每周一 01:30 | `51af456349b4` | 爆款文案库学习/扩充 |

快照与 prompt 全文在 [`cron/`](cron/)；新增/改动 cron 后请重跑 `scripts/status.py --refresh-cron` 更新快照。

---

## 6. 真相源约定（重要）

| 资产 | 真相源 | 本项目的角色 |
|---|---|---|
| 技能流程 / 坑位库 | `HERMES_HOME\skills\dabao\SKILL.md` | `skill\` 是 **junction**，不要在本项目里另存副本 |
| 工具链脚本 | `HERMES_HOME\scripts\{uploadpost_mcp,dabao_stage_upload,_pub_one_0924,dabao_publish_retry,dabao_gh_cover,_detach_run}.py` | `tools\` 只放薄壳转发 |
| cron 定义 | `HERMES_HOME\cron\jobs.json` | `cron\` 是只读快照，改 cron 走 `hermes cron edit` |
| MCP 注册 | `HERMES_HOME\config.yaml` 的 `mcp.servers.upload-post` | `mcp\upload-post\server.json` 是声明，`register.ps1` 写入 |
| 凭证 | `HERMES_HOME\mcp-tokens\upload-post.json`（OAuth）+ `cache\dabao_duty\conv.json`（IG token） | **永不入库**，只记录位置 |

理由：cron 与 Hermes 技能加载只认 HERMES_HOME 下的路径；复制一份到项目会造成双真相源漂移（历史上 `D:\@kaifa\dabao文案库` 被删就吃过一次亏）。

---

## 7. 素材与产出路径

| 用途 | 路径 |
|---|---|
| 待发片（每条一个目录：成片 mp4 + `发布信息.txt` + 3:4/4:3 封面 + `发布文案-多平台.txt`） | `D:\自动剪辑\纪录片解说待发\` |
| 已发归档（`【已发】` 前缀 + `已发记录.md`） | `D:\自动剪辑\纪录片解说待发\@已发\` |
| 日报看板 | `D:\@kaifa\dabao日报\日报-YYYY-MM-DD.html` |
| 邮件收件人 | `120112121@qq.com` |

---

## 8. 验收标准（一条片子算「发完」）

1. 每个启用平台 `get_status` 回 `success:true`，`media_size_bytes` 与本地文件字节**精确相等**；
2. 外部回读：IG 有 permalink 且 caption 含标题行；X fxtwitter 读到 `author=AlanandLvy` 且 `bio_ok=True, has_link=False`；TG `t.me/Dabaoagent/<号>?embed=1` 有消息体；FB permalink 200；
3. 目录加 `【已发】` 前缀 + 写 `已发记录.md`（含各平台链接/request_id）；
4. 任一平台失败 → **不归档**，交补发 watchdog 或下一班按「已上线平台跳过」。

---

## 9. 关联项目

- 视频生产：`D:\@kaifa\AutoYY`（技能 `autoyy`）、GitHub `DaBaoAgent/AutoUP`
- 发布通道：MCP `upload-post`（https://mcp.upload-post.com/mcp，OAuth）
- 日报/知识沉淀：OpenViking（`viking://` 下 dabao 相关 events/patterns）

---

_维护：改动发布流程请同时更新 `skill\SKILL.md`（坑位库）+ 本 README 的班表/矩阵，两者不一致时以 SKILL.md 的实测记录为准。_
