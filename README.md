# Bili Live Companion

[简体中文](#简体中文) | [English](#english)

## 简体中文

面向 Bilibili 直播任务的非官方跨平台助手。macOS 桌面版可扫码登录、管理多个账号与直播间、查看任务进度，并在奖励节点达标后尝试自动领取。任务状态和奖励结果以平台实际返回为准。

### macOS 桌面版

需要 macOS、Python 3.11 或更新版本，以及可访问 Bilibili 的网络。下载源码后，在仓库目录运行：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python bilibili_gui.py
```

在应用中扫码登录，填写直播间号或 URL，然后识别任务并开始观看。保存的账号凭据在本机加密，密钥保存在 macOS 钥匙串。构建 `.app`、凭据迁移及浏览器兜底识别的说明见 [macOS 文档](docs/macos.md)。

本项目不提供已签名或公证的 macOS 安装包。请遵守平台规则，避免使用过高并发。

### 许可

代码采用 [MIT License](LICENSE)。原有版权声明保留在许可证中。

## English

An unofficial cross-platform companion for Bilibili live tasks. The macOS desktop app supports QR-code sign-in, multiple accounts and live rooms, task progress tracking, and automatic reward claim attempts when milestones are reached. Task and reward status depend on the platform's responses.

### macOS desktop app

Requires macOS, Python 3.11 or newer, and network access to Bilibili. From the repository directory, run:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python bilibili_gui.py
```

Sign in with the in-app QR code, enter a room ID or URL, discover tasks, and start watching. Saved account credentials are encrypted locally, with the key held in the macOS Keychain. See the [macOS guide](docs/macos.md) for `.app` builds, credential migration, and browser fallback details.

No signed or notarized macOS package is provided. Follow the platform's rules and keep concurrency modest.

### License

Licensed under the [MIT License](LICENSE). Existing copyright notices are preserved in the license file.
