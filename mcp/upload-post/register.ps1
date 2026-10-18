<#
.SYNOPSIS
  把 upload-post MCP server 幂等注册到本机 Hermes（config.yaml 的 mcp.servers.upload-post）。

.DESCRIPTION
  server.json 是声明真相源；本脚本只负责写入 Hermes 配置，不碰 token。
  - 已注册：只打印现状，不改（要改先 hermes mcp remove upload-post）。
  - 未注册：hermes mcp add upload-post --url <url> --auth oauth，随后需交互式授权。
  授权（必须宝哥本人操作，cron 内会 callback 超时）：
      hermes mcp login upload-post
#>
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$cfg  = Get-Content -Raw (Join-Path $here "server.json") | ConvertFrom-Json
$name = $cfg.name

Write-Host "== upload-post MCP 注册检查 =="
$list = ""
try { $list = (& hermes mcp list 2>&1 | Out-String) } catch { $list = "" }

if ($list -match [regex]::Escape($name)) {
    Write-Host "[OK] 已注册：$name"
} else {
    Write-Host "[..] 未注册，正在添加：$name -> $($cfg.url)"
    & hermes mcp add $name --url $cfg.url --auth oauth
    Write-Host "[OK] 已写入配置，下一步交互式授权：hermes mcp login $name"
}

Write-Host ""
Write-Host "== 健康检查（只读） =="
$py = "C:/Users/20200/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe"
& $py (Join-Path $here "health.py")
