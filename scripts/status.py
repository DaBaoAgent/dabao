# -*- coding: utf-8 -*-
"""dabao 项目一键体检（只读，不联网、不发帖）。

用法：
    python scripts/status.py                # 人读表格
    python scripts/status.py --json         # 机器读
    python scripts/status.py --refresh-cron # 先刷新 cron 快照再体检

检查项：
    1. 真相源：技能 SKILL.md、junction、HERMES_HOME 脚本
    2. cron：6 条 dabao job 的 enabled / 下次运行（快照与实时对比）
    3. 素材库：待发目录、已发归档、最早待发片
    4. 日报：最新看板文件
    5. MCP：token 文件与剩余有效期（不联网；连通性用 mcp/upload-post/health.py）
"""
import glob
import json
import os
import re
import shutil
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

HERMES_HOME = os.environ.get("HERMES_HOME") or (
    os.environ.get("LOCALAPPDATA", r"C:\Users\20200\AppData\Local") + r"\hermes"
)
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATERIAL = r"D:\自动剪辑\纪录片解说待发"
ARCHIVE = os.path.join(MATERIAL, "@已发")
REPORTS = r"D:\@kaifa\dabao日报"
TOKEN = os.path.join(HERMES_HOME, "mcp-tokens", "upload-post.json")
JOBS = os.path.join(HERMES_HOME, "cron", "jobs.json")
SNAPSHOT = os.path.join(PROJECT, "cron", "jobs.snapshot.json")
SKILL = os.path.join(HERMES_HOME, "skills", "dabao", "SKILL.md")
VARIANT_PREFIXES = ("2分钟版", "TT版", "TG版", "X-裁剪")


def fmt_ts(v):
    if isinstance(v, (int, float)) and v > 1e9:
        return time.strftime("%m-%d %H:%M", time.localtime(v))
    return str(v) if v else "-"


def load_jobs():
    if not os.path.exists(JOBS):
        return []
    d = json.load(open(JOBS, encoding="utf-8"))
    jobs = d if isinstance(d, list) else d.get("jobs", d)
    return [j for j in jobs if isinstance(j, dict) and "dabao" in (j.get("name") or "")]


def refresh_cron():
    """重建 cron/jobs.snapshot.json 与 cron/prompts/*.md（只读源：jobs.json）。"""
    jobs = load_jobs()
    snap = []
    pdir = os.path.join(PROJECT, "cron", "prompts")
    os.makedirs(pdir, exist_ok=True)
    for j in jobs:
        item = {k: j.get(k) for k in ("id", "name", "schedule", "enabled", "script",
                                      "deliver", "no_agent", "model", "provider")}
        item["prompt_len"] = len(j.get("prompt") or "")
        snap.append(item)
        pr = j.get("prompt") or ""
        if pr:
            fn = re.sub(r'[\\/:*?"<>|]', "_", j.get("name") or j.get("id")) + ".md"
            with open(os.path.join(pdir, fn), "w", encoding="utf-8") as f:
                f.write("<!-- job_id: %s | schedule: %s | enabled: %s -->\n\n%s"
                        % (j.get("id"), j.get("schedule"), j.get("enabled"), pr))
    json.dump(snap, open(SNAPSHOT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return snap


def pending_dirs():
    out = []
    if not os.path.isdir(MATERIAL):
        return out
    for name in os.listdir(MATERIAL):
        d = os.path.join(MATERIAL, name)
        if not os.path.isdir(d) or name.startswith("@") or name.startswith("_"):
            continue
        if os.path.exists(os.path.join(d, "已发记录.md")):
            continue
        mp4s = [f for f in glob.glob(os.path.join(d, "*.mp4"))
                if not os.path.basename(f).startswith(VARIANT_PREFIXES)]
        if mp4s:
            out.append({"dir": name, "file": os.path.basename(mp4s[0]),
                        "mb": round(os.path.getsize(mp4s[0]) / 1048576, 1)})
    out.sort(key=lambda x: x["dir"])
    return out


def main():
    as_json = "--json" in sys.argv
    if "--refresh-cron" in sys.argv:
        refresh_cron()

    rep = {"checked_at": time.strftime("%Y-%m-%d %H:%M:%S"), "errors": [], "warns": []}

    # 1. 真相源
    skill = {"path": SKILL, "exists": os.path.exists(SKILL)}
    if skill["exists"]:
        st = os.stat(SKILL)
        chars = len(open(SKILL, encoding="utf-8", errors="replace").read())
        skill.update(size_kb=round(st.st_size / 1024, 1), chars=chars,
                     mtime=time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime)))
        if chars > 100_000:
            rep["errors"].append("SKILL.md 字符数 %d 超过 100,000 上限（逐班日志请移入 references/）" % chars)
        elif chars > 90_000:
            rep["warns"].append("SKILL.md 已 %d 字符（上限 100,000），尽快把日志迁到 references/" % chars)
    else:
        rep["errors"].append("技能真相源缺失: " + SKILL)
    junction = os.path.join(PROJECT, "skill")
    skill["junction_ok"] = os.path.isdir(junction) and os.path.exists(os.path.join(junction, "SKILL.md"))
    for real in ("uploadpost_mcp.py", "dabao_stage_upload.py", "_pub_one_0924.py",
                 "dabao_publish_retry.py", "dabao_gh_cover.py", "_detach_run.py"):
        if not os.path.exists(os.path.join(HERMES_HOME, "scripts", real)):
            rep["errors"].append("HERMES 脚本缺失: " + real)
    rep["source"] = skill

    # 2. cron
    live = {j.get("id"): j for j in load_jobs()}
    try:
        snap = {j["id"]: j for j in json.load(open(SNAPSHOT, encoding="utf-8"))}
    except Exception:  # noqa: BLE001
        snap = {}
    rows = []
    for jid, j in live.items():
        s = snap.get(jid, {})
        drift = []
        for k in ("enabled", "script"):
            if s and s.get(k) != j.get(k):
                drift.append(k)
        if j.get("enabled") is False:
            rep["warns"].append("cron 已停用: %s" % (j.get("name") or jid))
        rows.append({
            "id": jid, "name": j.get("name"),
            "schedule": (j.get("schedule") or {}).get("display") or str(j.get("schedule")),
            "enabled": j.get("enabled"),
            "next_run": fmt_ts(j.get("next_run_at")),
            "drift": drift,
        })
    if snap and set(snap) != set(live):
        rep["warns"].append("cron 快照与实时不一致（新增/删除），跑 --refresh-cron")
    rep["cron"] = sorted(rows, key=lambda r: (r["schedule"] or "", r["name"] or ""))

    # 3. 素材库
    pend = pending_dirs()
    arch = [d for d in os.listdir(ARCHIVE) if d.startswith("【已发】")] if os.path.isdir(ARCHIVE) else []
    rep["material"] = {
        "root": MATERIAL, "exists": os.path.isdir(MATERIAL),
        "pending": len(pend), "archived": len(arch),
        "days_left": round(len(pend) / 2, 1),
        "next": pend[0] if pend else None,
    }
    if len(pend) <= 4:
        rep["warns"].append("待发库存仅 %d 条（约 %.0f 天），提醒补素材" % (len(pend), len(pend) / 2))

    # 4. 日报
    reports = sorted(glob.glob(os.path.join(REPORTS, "日报-*.html")))
    rep["reports"] = {"dir": REPORTS, "count": len(reports),
                      "latest": os.path.basename(reports[-1]) if reports else None,
                      "latest_mtime": time.strftime("%Y-%m-%d %H:%M",
                                                    time.localtime(os.path.getmtime(reports[-1])))
                      if reports else None}
    if reports:
        age_h = (time.time() - os.path.getmtime(reports[-1])) / 3600
        if age_h > 30:
            rep["warns"].append("最新日报已 %.0f 小时未更新（20 点班可能失败）" % age_h)

    # 5. MCP token（离线）
    tok = {"path": TOKEN, "present": os.path.exists(TOKEN)}
    if tok["present"]:
        try:
            t = json.load(open(TOKEN, encoding="utf-8"))
            left = int(float(t.get("expires_at") or 0) - time.time())
            tok.update(expires_in_s=left, has_refresh=bool(t.get("refresh_token")))
            if left < 0:
                rep["warns"].append("upload-post access_token 已过期（%ds），需刷新或交互授权" % left)
        except Exception as e:  # noqa: BLE001
            tok["error"] = str(e)
    else:
        rep["warns"].append("upload-post token 文件缺失 → 需 hermes mcp login upload-post")
    rep["mcp_token"] = tok

    # 6. 环境
    venv = os.path.join(HERMES_HOME, "hermes-agent", "venv", "Scripts", "python.exe")
    rep["env"] = {"venv_python": venv, "venv_ok": os.path.exists(venv),
                  "ffmpeg": bool(shutil.which("ffmpeg"))}
    if not rep["env"]["venv_ok"]:
        rep["warns"].append("hermes venv python 不存在: " + venv)

    if as_json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 0 if not rep["errors"] else 1

    print("== dabao 项目体检 %s ==" % rep["checked_at"])
    s = rep["source"]
    print("[真相源] SKILL.md %s  %sKB  %s   junction=%s" % (
        "OK" if s["exists"] else "缺失", s.get("size_kb", "-"), s.get("mtime", "-"),
        "OK" if s["junction_ok"] else "失效"))
    print("[cron] %d 条" % len(rep["cron"]))
    for r in rep["cron"]:
        print("   %-18s %-16s %-22s next=%s %s" % (
            r["id"], r["name"][:18], r["schedule"], r["next_run"],
            ("DRIFT:" + ",".join(r["drift"])) if r["drift"] else ""))
    m = rep["material"]
    print("[素材库] 待发 %d 条（约 %.1f 天）| 已发归档 %d | 下一条: %s" % (
        m["pending"], m["days_left"], m["archived"],
        (m["next"]["dir"] + " / " + m["next"]["file"] + " " + str(m["next"]["mb"]) + "MB") if m["next"] else "-"))
    rp = rep["reports"]
    print("[日报] %d 份 | 最新 %s (%s)" % (rp["count"], rp["latest"], rp["latest_mtime"]))
    t = rep["mcp_token"]
    print("[MCP] token %s %s" % ("存在" if t["present"] else "缺失",
                                 ("剩余 %ss" % t["expires_in_s"]) if "expires_in_s" in t else ""))
    print("[环境] venv=%s ffmpeg=%s" % ("OK" if rep["env"]["venv_ok"] else "缺失",
                                        "OK" if rep["env"]["ffmpeg"] else "未在 PATH"))
    if rep["errors"]:
        print("\n!! 错误")
        for e in rep["errors"]:
            print("  -", e)
    if rep["warns"]:
        print("\n* 提醒")
        for w in rep["warns"]:
            print("  -", w)
    print("\n下一步: 通道连通性 → python %s" %
          os.path.join(PROJECT, "mcp", "upload-post", "health.py"))
    return 0 if not rep["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
