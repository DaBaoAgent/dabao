# 04 — 运营班表与 cron

快照：`cron/jobs.snapshot.json`｜prompt 全文：`cron/prompts/*.md`

| job id | 名称 | 时间 | 类型 | 职责 |
|---|---|---|---|---|
| `222636e84bbd` | dabao-自动发布-05点 | `0 5 * * *` | agent | 发下一条待发片（六平台分组） |
| `b1ac6266c95b` | dabao-自动发布-19点 | `0 19 * * *` | agent | 同上 |
| `da63e3511e89` | dabao-发布失败自动补发-30分钟 | `every 30m` | no_agent 脚本 | 失败后 25min–6h 自动重试一次，同日上限 2 次，QQ 通知 |
| `4c3c057a96db` | dabao-互动值班-每小时(7-23点) | `0 7-23 * * *` | agent | 评论/私信，IG 为主；AutoDM 绑新帖 |
| `e40385ea577f` | dabao-每日数据日报-20点 | `0 20 * * *` | agent | 六平台数据 → HTML 看板 + 邮件 + QQ 简讯 |
| `51af456349b4` | dabao-爆款文案库每周学习 | `30 1 * * 1` | agent | 扩充 X 引流模板池 / 话术库 |

> 2026-09-15 老板拍板：原 11 点 / 23 点发布班已删除。发布节奏 2 条/天。

## 改 cron 的正确姿势

```bash
# 查看
hermes cron list | grep dabao

# 改 prompt（不要在 shell 里拼中文 + 反引号，易被吞）
python -c "import subprocess;subprocess.run(['hermes','cron','edit','222636e84bbd','--prompt',open('D:/@kaifa/dabao/cron/prompts/dabao-自动发布-05点.md',encoding='utf-8').read().split('-->',1)[1].strip()])"

# 触发补发（进程内，交给 gateway ticker；绝不用 hermes cron run 前台跑）
python -c "from cron import jobs as j; j.trigger_job('222636e84bbd')"
```

改完跑一次 `python D:/@kaifa/dabao/scripts/status.py --refresh-cron` 更新快照。

## 发布班 prompt 的硬结构（v10）

1. **第 0 步守卫**：`tool_search` 查 `mcp__upload_post__`，查不到就结束（省 token）；
2. 选片 → 备料 → staging → 分平台发布 → 核验 → 归档 → 中文简报；
3. 平台暂停声明写进 prompt（TikTok/YouTube 当前跳过）。

## 为什么不能用 `hermes cron run`

CLI 那条路会同步跑完整个 job（10–30min），被父进程超时杀掉后 gateway 把它标成 `unknown` 并可能清掉进程树 → 出现过「压缩版已生成、一个平台都没发」的事故。补发一律进程内 `trigger_job`。

## 补发 watchdog 判定（四条同时满足）

1. job 名匹配 `dabao-自动发布*` 且 enabled；
2. 最近一次执行 `status ∈ {failed,error,timeout,unknown}`；
3. 该次 `started_at` 落在计划点 +0~20min（防级联总闸）；
4. 距失败 25min–6h，且同一次失败未补过、当日补发 <2 次。

排障先看 `publish_retry_watchdog.py` 的 `latest_execution()` 是否用 `ORDER BY rowid DESC`（用 `id DESC` 会读到随机 UUID 的旧行，watchdog 静默失效，2026-10-02 已修）。
