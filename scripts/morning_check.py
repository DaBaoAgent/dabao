# -*- coding: utf-8 -*-
"""dabao 晨检：确认 05:00 自动发布班是否真的接手并发出片。

用法：
    python morning_check.py            # 人读简报（<2000 字，适合 QQ 推送）
    python morning_check.py --json

判定（全部用事实，不猜）：
    1. 05 点班最近一次 execution：status / started_at / error
    2. 素材库待发数量、@已发 最新目录
    3. Instagram 最新帖时间（live，get_media）——今天 05:00 CST 之后有帖 = 真发出去了
    4. MCP token 是否仍有效（离线读文件）
退出码：0 一切正常；2 有异常（cron 失败 / 无新帖 / token 缺失）。
"""
import glob
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding="utf-8")

HERMES_HOME = os.environ.get("HERMES_HOME") or (
    os.environ.get("LOCALAPPDATA", r"C:\Users\20200\AppData\Local") + r"\hermes"
)
EXEC_DB = os.path.join(HERMES_HOME, "cron", "executions.db")
TOKEN = os.path.join(HERMES_HOME, "mcp-tokens", "upload-post.json")
MATERIAL = r"D:\自动剪辑\纪录片解说待发"
ARCHIVE = os.path.join(MATERIAL, "@已发")
JOB_05 = "222636e84bbd"
VARIANT_PREFIXES = ("2分钟版", "TT版", "TG版", "X-裁剪")


def latest_exec(job_id):
    if not os.path.exists(EXEC_DB):
        return None
    con = sqlite3.connect(EXEC_DB)
    con.row_factory = sqlite3.Row
    row = con.execute(
        "SELECT status, started_at, finished_at, error FROM executions WHERE job_id=? ORDER BY rowid DESC LIMIT 1",
        (job_id,),
    ).fetchone()
    con.close()
    return dict(row) if row else None


def pending_count():
    n = 0
    if os.path.isdir(MATERIAL):
        for name in os.listdir(MATERIAL):
            d = os.path.join(MATERIAL, name)
            if not os.path.isdir(d) or name.startswith(("@", "_")):
                continue
            if os.path.exists(os.path.join(d, "已发记录.md")):
                continue
            if [f for f in glob.glob(os.path.join(d, "*.mp4"))
                    if not os.path.basename(f).startswith(VARIANT_PREFIXES)]:
                n += 1
    return n


def newest_archive():
    if not os.path.isdir(ARCHIVE):
        return None
    dirs = [d for d in glob.glob(os.path.join(ARCHIVE, "【已发】*")) if os.path.isdir(d)]
    if not dirs:
        return None
    d = max(dirs, key=os.path.getmtime)
    return {"name": os.path.basename(d), "mtime": time.strftime("%m-%d %H:%M", time.localtime(os.path.getmtime(d)))}


def ig_latest():
    """live 读 IG 最新 1 帖（走直连调用器）。失败返回 {'error': ...}。"""
    try:
        sys.path.insert(0, os.path.join(HERMES_HOME, "scripts"))
        from uploadpost_mcp import call  # noqa: E402

        resp = call("get_media", {"user": "xiangge", "platform": "instagram", "limit": 1})
        res = (resp.get("result") or {})
        sc = res.get("structuredContent")
        data = sc.get("result") if isinstance(sc, dict) else None
        if data is None:
            for it in res.get("content") or []:
                if it.get("type") == "text":
                    data = json.loads(it["text"])
                    break
        items = (data or {}).get("media") or (data or {}).get("data") or []
        if not items:
            return {"error": "get_media 返回空"}
        m = items[0]
        return {"timestamp": m.get("timestamp"), "caption": (m.get("caption") or "")[:40],
                "permalink": m.get("permalink")}
    except BaseException as e:  # SystemExit 也算
        return {"error": "%s: %s" % (type(e).__name__, e)}


def token_left():
    if not os.path.exists(TOKEN):
        return None
    try:
        t = json.load(open(TOKEN, encoding="utf-8"))
        return int(float(t.get("expires_at") or 0) - time.time())
    except Exception:  # noqa: BLE001
        return None


def main():
    now = datetime.now().astimezone()  # 必须 aware：executions.started_at 与 IG timestamp 都带时区
    # 今天 05:00 CST 作为「本班应发」的基线
    baseline = now.replace(hour=5, minute=0, second=0, microsecond=0)
    if now < baseline:
        baseline -= timedelta(days=1)

    ex = latest_exec(JOB_05)
    pend = pending_count()
    arch = newest_archive()
    ig = ig_latest()
    tleft = token_left()

    ok_cron = bool(ex) and ex.get("status") == "completed"
    started_today = False
    if ex and ex.get("started_at"):
        try:
            started_today = datetime.fromisoformat(ex["started_at"]) >= baseline
        except Exception:  # noqa: BLE001
            started_today = False

    ig_ts, ig_fresh = None, False
    if ig.get("timestamp"):
        try:
            ig_ts = datetime.strptime(ig["timestamp"], "%Y-%m-%dT%H:%M:%S%z").astimezone()
            ig_fresh = ig_ts >= baseline
        except Exception:  # noqa: BLE001
            pass

    problems = []
    if not ok_cron:
        problems.append("05点班最近一次不是 completed（%s）" % (ex or {}).get("status"))
    if not started_today:
        problems.append("05点班今天没有按时运行（最近 started_at=%s）" % (ex or {}).get("started_at"))
    if ig.get("error"):
        problems.append("IG 读数失败：%s" % ig["error"])
    elif not ig_fresh:
        problems.append("IG 今天 05:00 后无新帖（最新 %s）" % (ig.get("timestamp") or "?"))
    if tleft is not None and tleft < 0:
        problems.append("upload-post token 已过期")

    report = {
        "checked_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "job05": ex, "job05_started_today": started_today,
        "pending": pend, "archive_latest": arch,
        "ig_latest": ig, "ig_fresh_today": ig_fresh,
        "token_expires_in_s": tleft, "problems": problems,
    }

    if "--json" in sys.argv:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if not problems else 2

    lines = ["📋 dabao 晨检 %s" % report["checked_at"], ""]
    lines.append("发布班：%s（今天已跑=%s）" % (ex.get("status") if ex else "无记录", "是" if started_today else "否"))
    if ex and ex.get("error"):
        lines.append("  错误：%s" % ex["error"][:160])
    lines.append("IG 最新：%s %s" % (ig.get("timestamp") or "读不到", "（今天已发）" if ig_fresh else "（今天未发）"))
    if ig.get("permalink"):
        lines.append("  %s" % ig["permalink"])
    lines.append("归档最新：%s" % ((arch or {}).get("name") or "-"))
    lines.append("待发库存：%d 条（约 %.1f 天）" % (pend, pend / 2))
    lines.append("MCP token：%s" % (("剩余 %dh" % (tleft // 3600)) if isinstance(tleft, int) else "缺失"))
    if problems:
        lines += ["", "⚠️ 需要处理："] + ["- " + p for p in problems]
        lines += ["", "下一步：查 D:/@kaifa/dabao/docs/05-故障排查.md 对应条目"]
    else:
        lines += ["", "✅ 自动班正常接手"]
    print("\n".join(lines))
    return 0 if not problems else 2


if __name__ == "__main__":
    sys.exit(main())
