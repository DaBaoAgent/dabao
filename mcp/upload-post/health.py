# -*- coding: utf-8 -*-
"""upload-post MCP 通道健康检查（只读，不发帖）。

用法：
    "C:/Users/20200/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe" health.py [--json]

判据：
    OK      = token 可刷新 且 get_account_info 返回成功
    DEGRADED= token 文件缺失/过期且 refresh 失败（需交互式 hermes mcp login upload-post）
    FAIL    = 网络/服务不可达（先查代理出口，见 docs/05 第 3 节）
"""
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

HERMES_HOME = os.environ.get("HERMES_HOME") or (
    os.environ.get("LOCALAPPDATA", r"C:\Users\20200\AppData\Local") + r"\hermes"
)
TOKEN = os.path.join(HERMES_HOME, "mcp-tokens", "upload-post.json")
sys.path.insert(0, os.path.join(HERMES_HOME, "scripts"))


def payload(resp):
    """把 MCP 信封拆成业务 dict（兼容 structuredContent / content[0].text）。"""
    if not isinstance(resp, dict):
        return {}
    res = resp.get("result") or {}
    sc = res.get("structuredContent")
    if isinstance(sc, dict):
        return sc.get("result", sc)
    for item in res.get("content") or []:
        if item.get("type") == "text":
            try:
                return json.loads(item["text"])
            except Exception:  # noqa: BLE001
                return {"_raw": item["text"][:400]}
    return res


def token_state():
    if not os.path.exists(TOKEN):
        return {"present": False, "reason": "token 文件不存在（需 hermes mcp login upload-post）"}
    try:
        t = json.load(open(TOKEN, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"present": True, "reason": "读取失败: %s" % e}
    exp = float(t.get("expires_at") or 0)
    return {
        "present": True,
        "expires_in_s": int(exp - time.time()),
        "has_refresh": bool(t.get("refresh_token")),
        "access_token_len": len(t.get("access_token") or ""),
    }


def main():
    as_json = "--json" in sys.argv
    out = {"checked_at": time.strftime("%Y-%m-%d %H:%M:%S"), "token": token_state()}
    if not out["token"].get("present"):
        # 无 token 时直连调用器必然 FileNotFoundError，直接判 DEGRADED，不制造假 FAIL
        out.update(ok=False, status="DEGRADED",
                   error="token 文件不存在 → 需交互式 hermes mcp login upload-post")
        if as_json:
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return 1
        _print_human(out)
        return 1
    try:
        from uploadpost_mcp import call  # noqa: E402  （真相源：HERMES_HOME/scripts）
    except Exception as e:  # noqa: BLE001
        out.update(ok=False, status="FAIL", error="无法导入直连调用器: %s" % e)
    else:
        try:
            info = payload(call("get_account_info", {}))
            users = payload(call("list_users", {}))
            unames = []
            if isinstance(users, dict):
                for u in users.get("users") or users.get("data") or []:
                    if isinstance(u, dict):
                        unames.append(u.get("username") or u.get("user"))
            out.update(
                ok=True,
                status="OK",
                account={k: info.get(k) for k in ("email", "plan", "success", "error") if k in info},
                users=unames,
                profile_ok=("xiangge" in unames) if unames else None,
            )
        except SystemExit as e:  # call() 失败时 raise SystemExit
            out.update(ok=False, status="DEGRADED", error=str(e))
        except Exception as e:  # noqa: BLE001
            out.update(ok=False, status="FAIL", error="%s: %s" % (type(e).__name__, e))

    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        _print_human(out)
    return 0 if out["status"] == "OK" else 1


def _print_human(out):
    print("== upload-post MCP 健康检查 ==")
    print("时间:", out["checked_at"])
    ts = out["token"]
    print("token:", "存在" if ts.get("present") else "缺失",
          ("剩余 %ss" % ts["expires_in_s"]) if "expires_in_s" in ts else ts.get("reason", ""))
    print("状态:", out["status"])
    if out.get("account"):
        print("账号:", json.dumps(out["account"], ensure_ascii=False))
    if out.get("users"):
        print("profiles:", ", ".join([u for u in out["users"] if u]))
    if out.get("error"):
        print("错误:", out["error"])
    if out["status"] != "OK":
        print("处置: 见 D:/@kaifa/dabao/docs/05-故障排查.md 第 1–2 节")


if __name__ == "__main__":
    sys.exit(main())
