# 03 — 单条片子发布 SOP

> 执行者：发布班 cron（05:00 / 19:00）。人工补发按同一顺序，但**先读第 0 步守卫**。

## 第 0 步：守卫（先做，省一整班）

1. `tool_search` 查 `mcp__upload_post__`。查不到 = MCP parked → **只输出一行原因并结束**，别硬跑 14 次调用。
2. 看素材库根有没有 `_补发进行中_<job_id>.txt`：有则逐平台比对最近 3 条已发标题，**标题一致的平台跳过**（防重复帖）。

## 第 1 步：选片

```bash
ls "D:/自动剪辑/纪录片解说待发"
```

- 按 `ls` 的 locale 名称序，取第一个「含成片 mp4 且无 `已发记录.md`」的目录；
- 跳过 `@已发`、`__pycache__`、无 mp4 的空壳；
- 成片判据：排除 `2分钟版-*.mp4`、`TT版-*.mp4`、`TG版-*.mp4`、`X-裁剪*.mp4` 后剩下的 mp4（文件名可能是日期，不一定带「压缩版」）。

**已发与否的权威判定**（本地归档丢了才用）：`get_history` 逐页拉全量（`limit` 只能 20，页数 = total/20 上取整）→ 用成片 mp4 的**字节数**与历史行 `media_size_bytes` **精确相等**比对。零命中 = 未发。**不要用标题文字匹配、不要用容差。**

## 第 2 步：备料

| 文件 | 缺失时 |
|---|---|
| `发布文案-多平台.txt` | 读 `发布信息.txt`（第1行标题/第2行5标签）现场生成，GitHub 链接一律 `https://github.com/DaBaoAgent/AutoUP` |
| `封面-3_4.jpg` | 宽 >1080 先 `scale=1080:1440` 存副本（TikTok 会静默忽略超宽封面） |
| `封面-4_3.jpg` | YT 缩略图需转 GitHub raw（R2 签名 URL 必 403） |
| `X-裁剪.mp4` | 从压缩版流拷贝前 2 分钟；HEVC 或 >50MB 先转 H.264（`-c:v libx264 -preset veryfast -b:v 1600k`） |
| `TG版-480p.mp4` | 720p crf28 压 ≤10MB（>10MB 报 Request Entity Too Large） |
| 压缩版 ≤500MB | 超限先两遍定码率重压（`-b:v 900k -pass 1/2`，留 4% 余量） |

ffmpeg 在 `C:\Users\20200\ffmpeg\ffmpeg-8.1.1-essentials_build\bin\`，**路径用 `D:/...` 正斜杠原生形式**（MSYS 中文路径必报 Illegal byte sequence）。

## 第 3 步：staging（本地文件必走）

```bash
python D:/@kaifa/dabao/tools/stage_upload.py "<本地绝对路径>" <ASCII名> video
```

脚本内部：`create_media_upload` → PUT（线路轮换：直连 / http 代理 / socks5h，每次重试重新 create）→ `complete_media_upload` → 返回 `media_url`。

**口诀：`media_url` 与封面 URL 一律整段复制 `complete_media_upload` 的返回，一个字符都不要改。**（`create` 的 `upload_url` 是 PUT 签名 `Expires=900`，当封面/视频 URL 用必 403。）

## 第 4 步：按平台单发

每个平台单独一次 `upload_video`，成功即 `delete_media_upload` 释放槽位（staging 池上限 10，含 PUT 失败孤儿，24h 才释放）。

```bash
python D:/@kaifa/dabao/tools/pub_one.py <spec.json>
```

`spec.json` 字段：`user`(xiangge)、`platforms`、`videoPathOrUrl`(media_url)、`title`、`description`、`platformOptions`、`firstComment`、`media_url`、`upload_id`、`cleanup`。

顺序建议（IG 最快起量，先发）：IG → X → FB → TG。

## 第 5 步：核验（缺一不可）

| 平台 | 核验方式 | 通过判据 |
|---|---|---|
| 全部 | `get_status(request_id)` | `success:true` 且 `media_size_bytes` = 本地字节 |
| IG | `get_media(platform="instagram", limit=3)` | caption 含标题行（不是只剩标签） |
| X | fxtwitter `api.fxtwitter.com/AlanandLvy/status/<id>` | `author.screen_name==AlanandLvy`、`bio_ok=True`、`has_link=False` |
| FB | `curl -x http://127.0.0.1:15715 -o /dev/null -w "%{http_code}" <permalink>` | 200（`get_media` 列表对新帖有延迟，别用它判落地） |
| TG | `curl -x socks5h://127.0.0.1:15715 "https://t.me/Dabaoagent/<号>?embed=1"` | 含 `tgme_widget_message_text`；空体重试 2–3 次 |

## 第 6 步：归档

全平台绿 → 目录加 `【已发】` 前缀 + 写 `已发记录.md`（各平台链接/request_id/时间）→ 整体 move 进 `D:\自动剪辑\纪录片解说待发\@已发\`。

有失败 → **不归档**：`retry_post`（仅对 failed 生效）或用 `_补发进行中_<job_id>.txt` 交下一班按平台跳过补发。

## 第 7 步：汇报

中文简报表：本班发了哪条、各平台链接、失败项与下一步。附「素材库剩余 N 条 ≈ N/2 天」。
