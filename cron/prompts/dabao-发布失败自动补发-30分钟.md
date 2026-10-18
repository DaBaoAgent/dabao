<!-- job_id: da63e3511e89 | schedule: {'kind': 'interval', 'minutes': 30, 'display': 'every 30m'} | enabled: True -->

dabao 发布班次失败后自动补发一次（失败 30 分钟后重试）。no_agent 脚本：%LOCALAPPDATA%\hermes\scripts\dabao_publish_retry.py（真相源 skills/dabao/scripts/publish_retry_watchdog.py）。无补发动作时脚本 stdout 为空 → 不推送；有补发动作才推送一行中文说明。