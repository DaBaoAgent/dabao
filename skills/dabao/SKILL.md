---
name: dabao
description: Use for AutoYY social publishing and comment/DM handling.
version: 1.0.0
author: Dabao
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [upload-post, tiktok, youtube, instagram, autopost, autodm, autoyy]
---

# Dabao — AutoYY 推广发布与互动流程

用 Upload-Post MCP（服务器名 `upload-post`，58 个 `mcp__upload_post__*` 工具）完成 AutoYY 纪录片解说开源项目的社媒发布与互动转化。

## 账号资产（2026-09-06 现状）

| 项 | 值 |
|---|---|
| Upload-Post 套餐 | Basic $24/月，5 profiles，已用 1 |
| profile | `xiangge` |
| TikTok | 艾伦和艾薇 `@alanandlvy`（capabilities 全开：draft/music/cover/comments/location） |
| YouTube | AIGC徐黑蛋 `@xuheidan` |
| Instagram | `@lvy99229`（专业账户，唯一支持 AutoDM/私信的平台） |
| Telegram | bot `@Dabaoagentbot` → 群组 AutoYY001 `@Dabaoagent`（Chat ID 填群组用户名，不是 bot；实测发帖通过 t.me/Dabaoagent/3） |
| X/Twitter | 走独立工作流，不经 Upload-Post |
| 推广项目 | AutoYY https://github.com/DaBaoAgent/AutoYY （开源免费，纪录片解说全自动 Codex 技能） |
| 付费陪跑 | 99 元人民币 或 $15，手把手教会为止（agent/部署/VPN 不熟的用户） |
| 转化漏斗 | 短视频引流 → 评论引导 → IG AutoDM 发 GitHub 链接 → 私信聊 → 微信/电报成交 |

## 发布流程

### 视频（TikTok + YouTube + Instagram 三平台）

调用 `mcp__upload_post__upload_video`：

```
user: "xiangge"
platforms: ["tiktok","youtube","instagram"]   # 多平台一次调用全发
videoPathOrUrl: 本地绝对路径（如 D:\\自动剪辑\\xx\\成片.mp4）或公网 URL
title: 文案（YouTube 用作标题，25 字内钩子式，参考 AutoYY 爆款钩子模式）
description: YouTube 详细描述（放 GitHub 链接 + 项目简介 + 标签）
firstComment: 置顶评论（IG/TikTok/YouTube 支持，放 GitHub 链接引流）
platformOptions:
  tiktokPostMode: MEDIA_UPLOAD    # 草稿箱模式（默认推荐，App 内手动发布保自然流量）
  # DIRECT_POST = 直接发布；tiktokPrivacyLevel: PUBLIC_TO_EVERYONE
  youtubePrivacyStatus: public    # public / unlisted / private
asyncUpload: true（默认，返回 request_id）
```

发布后：
1. `mcp__upload_post__get_status(request_id=...)` 轮询到 success；
2. `get_media(platform=...)` 拿各平台 permalink/postId；
3. YouTube/IG 帖子链接出来后，启动 IG AutoDM（下节）；
4. TikTok 草稿需用户在 TikTok App 手动发布，发布后把链接补进来。

### 照片/纯文字

- `mcp__upload_post__upload_photos`：IG 轮播图、TikTok 图文。
- `mcp__upload_post__upload_text`：X/Threads/Telegram 等（profile 未连的平台需先连）。

### 连接新平台（新账号）

1. `mcp__upload_post__generate_jwt(username="xiangge", platforms=["<platform>"])` 拿 access_url（48h 有效）；
2. **系统浏览器打开**（`powershell -NoProfile -Command "Start-Process '<url>'"`），不要用预览面板——内嵌浏览器拦弹窗；
3. 国内直连 IG/TikTok 不通，先确认用户浏览器代理正常；IG OAuth 若被风控，先在浏览器登录 instagram.com 主站再重试授权。

## IG AutoDM（关键词自动私信）

绑定到具体帖子，监控评论触发私信：

```
mcp__upload_post__manage_autodms(action="start",
  profile_username="xiangge",
  post_url="<IG 帖子 permalink>",
  trigger_keywords=["教程","99","deploy","部署","怎么用","GitHub"],
  reply_message="看到你想要教程啦 😄 AutoYY 是我做的开源项目，GitHub 上直接能克隆：完整流程是后台数据提炼选题→核验长视频源→下载素材字幕→口播稿强制去 AI 味→封面标题标签一键生成。部署上有任何卡壳的地方随时问我～",
  buttons=[{"title":"GitHub 开源仓库","url":"https://github.com/DaBaoAgent/AutoYY"}],
  monitoring_interval=15)
```

- 每个帖子一个 monitor；`action="status"` 查看全部，`logs` 看触发记录，`pause/resume/stop/delete` 管理。
- 新发推广视频后必须重新 start 一个 monitor 绑新帖。

## 评论/私信互动（人性化回复规范）

值班 cron（每 30 分钟）已建：job_id `46362220bc47`。手动处理时按同一规范：

1. 读评论：`get_post_comments(user="xiangge", platform=<ig|youtube|tiktok>, postId=...)`（TikTok 必须用 postId，不接受 URL；TikTok 评论只能读不能回）。
2. 读私信：`list_dm_conversations(user="xiangge", platform="instagram")`；回私信 `send_dm(recipient_id=...)`。
3. 回复规则：
   - 先判意图：夸赞/闲聊/提问/求教程/抱怨/广告。
   - 夸赞→真诚感谢+一句有信息量的延伸；提问→基于 AutoYY 真实功能答，不懂不编。
   - 求教程/链接→给 GitHub 链接，强调开源免费可自己克隆；IG 可用 `reply_to_comment`（带 GitHub 按钮）或 `public_reply_to_comment`。
   - 对方明确说部署难/不熟 agent/问带教/问价→才提 99 元或 $15 陪跑，语气自然（"自己折腾费劲的话我这边可以手把手带，教会为止"），绝不硬推、绝不第一句谈钱。
   - 广告/引流评论→不回复。
   - 口语化中文（对方用英文则回英文），1-3 句，不用"您好""亲"。
4. YouTube 评论回复：`create_comment(platform="youtube", ...)`。

## AutoYY 项目卖点（回复素材，勿编造）

- 抖音/快手/B站后台截图 → 自动汇总分析，提炼可复制选题（70% 验证过 / 20% 相邻扩展 / 10% 实验，25 分制打分）。
- YouTube 30 分钟+ 长视频源核验（时长/清晰度/授权/匹配度分级），CSV 清单断点续传，aria2 多连接加速。
- FunASR/faster-whisper 本地字幕兜底（无需 GPU，国内走 hf-mirror）。
- 口播稿 4500-5500 字轻快科普风，强制 Humanizer 去 AI 味 + 事实复检。
- 爆款钩子模式库自学习（数字冲击/对比反差/信息缺口设问/后果威胁/身份反转/反常识/悬念事件/情感共鸣），按历史表现自动进化。
- 封面（3:4 + 4:3，金色毛笔字排版）、25 字内标题、5 标签批量生成；成品目录一键验收。

## Telegram 连接与发帖

- Bot 建：@BotFather → /newbot → 名字随意，用户名必须 bot 结尾（@Dabaoagentbot）。
- **bot 被拉群前必须开权限**：BotFather → /mybots → 选 bot → Bot Settings → Groups → Turn on（默认其实已 enabled，但拉群搜索不到时从 bot 资料页「添加到群组或频道」入口最稳）。
- bot 入群后设为**管理员**（发布消息权限）。
- Upload-Post 连接页 Chat ID 填**群组/频道的用户名**（如 `@Dabaoagent`），不是 bot 自己的 @xxxbot——填错报 "Forbidden: the bot can't send messages to the bot"。
- 测试：upload_text(platforms=["telegram"]) 成功返回 post_id + t.me 链接。
- token 安全：截图泄露过的话用 /revoke 换新，换后重填 Upload-Post Telegram 连接。

## 新机接入清单（clone 技能后一次性）

技能本体零配置，但底层凭据不随 git 走，新电脑按序接一次：

1. **Upload-Post OAuth**（必做，~1 分钟）：`hermes mcp add upload-post --url https://mcp.upload-post.com/mcp --auth oauth` → 系统浏览器完成授权。同一账号多台设备授权互不冲突，平台连接/额度都在账号云端，无需重连各平台。
2. **代理**：国内访问 IG/TikTok/授权页需要；机器已有梯子则无事。
3. **edge-tts / ffmpeg**：仅发新视频需配音/剪辑时装（互动回复不需要）。
4. **互动值班 cron 不随技能走**：需按本技能「评论/私信互动」规范在新机重建。⚠️ 多台机器同时开值班 cron 会重复回复同一条评论——只允许一台主力机开。
5. 验证接入成功：`mcp__upload_post__get_account_info` 返回邮箱即通；`list_users` 能看到 xiangge 与四平台。

## 坑位备忘

- 工具层 TTS 对长中文文本会静默截断（edge 后端 5.6s 就断）；需要配音时直接 `python -c` 调 `edge_tts`（本机已装 7.2.7）。
- ffmpeg 在 `D:\\@佳康顺矩阵\\@工具\\ffmpeg\\`（系统 PATH 没有）。
- Upload-Post 免费版不能发 TikTok（已升级 Basic 无此限制）。
- 各平台上传都是异步的，`get_status` 确认成功后再拿链接。
- IG 评论私信回复窗口 7 天（Meta 限制），过窗的回复会失败。
- `get_post_comments` TikTok 的 limit 上限是 30，传 50 会报 `TikTok API error 40002: max_count: number must be most 30`。
- YouTube 个别视频评论区被禁用（如 xiangge 频道的占位视频 j8Y4wVNFm1Y / NdFGeYKZ3cg / 6_jGPe9jyNo / RHWOxDN2xCM），`get_post_comments` 会返回 403 "has disabled comments"，且连发 3-4 次会触发 MCP 熔断（unreachable ~50s）。这是永久状态，值班清单里标记过的直接跳过，不要重试。
- execute_code 在 cron 下被禁（审批机制），等待熔断冷却用 terminal 跑 `sleep 50` 再重试。
