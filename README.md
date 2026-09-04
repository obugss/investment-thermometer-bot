# Investment Thermometer Bot

每天从有知有行公开页面读取全市场温度和股债现金配置，并通过 GitHub Actions 推送到 Telegram。当前方案是定时任务，不需要长期运行的云主机。

## 推送内容

```text
投资温度计 | 2026-09-03 20:00

全市场温度：51°（中估）

资产配置：
股票 56%
债券 24%
现金 20%

数据来源：有知有行
```

## Telegram 配置

1. 在 Telegram 中联系 `@BotFather`，发送 `/newbot` 并保存 Bot Token。
2. 打开新 Bot，发送 `/start`。
3. 在本机 PowerShell 临时设置 Token 并查询 Chat ID：

   ```powershell
   $env:TELEGRAM_BOT_TOKEN = Read-Host "Bot Token"
   python -m investment_thermometer.chat_id
   Remove-Item Env:TELEGRAM_BOT_TOKEN
   ```

`Read-Host` 的输入不会写入项目文件。不要把 Token、Chat ID 或 `.env` 文件提交到仓库。

## GitHub Secrets

在 GitHub 仓库的 `Settings` > `Secrets and variables` > `Actions` 中添加：

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

工作流每天 UTC 12:30，即北京时间 20:30 触发。GitHub 的定时任务可能有数分钟延迟，也可从 Actions 页面手动运行 `Daily investment thermometer`。

## 本地验证

项目仅使用 Python 标准库，要求 Python 3.11 或更高版本：

```powershell
python -m unittest discover -s tests -v
```

本地发送真实消息前，需要在当前终端临时设置两个环境变量：

```powershell
$env:TELEGRAM_BOT_TOKEN = Read-Host "Bot Token"
$env:TELEGRAM_CHAT_ID = Read-Host "Chat ID"
python -m investment_thermometer
Remove-Item Env:TELEGRAM_BOT_TOKEN, Env:TELEGRAM_CHAT_ID
```

## 数据与风险

数据来自有知有行公开页面内嵌的结构化 JSON。解析器会校验温度范围、更新时间、资产比例范围及比例总和；页面结构变化时任务会失败，并尝试发送抓取失败通知。此项目只做信息转发，不构成投资建议。