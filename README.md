# Bili Live Companion

[简体中文](#简体中文) | [English](#english)

## 简体中文

面向 Bilibili 直播任务的非官方跨平台助手。提供 macOS 桌面版和适合云服务器的 Linux 无界面服务，支持扫码登录、多账号与直播间管理、任务进度查询，并在奖励节点达标后尝试自动领取。任务状态和奖励结果以平台实际返回为准。

### macOS 桌面版

需要 macOS、Python 3.11 或更新版本，以及可访问 Bilibili 的网络。下载源码后，在仓库目录运行：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python bilibili_gui.py
```

在应用中扫码登录，填写直播间号或 URL，然后识别任务并开始观看。保存的账号凭据在本机加密，密钥保存在 macOS 钥匙串。构建 `.app`、凭据迁移及浏览器兜底识别的说明见 [macOS 文档](docs/macos.md)。

本项目不提供已签名或公证的 macOS 安装包。请遵守平台规则，避免使用过高并发。

### Linux 云服务器版

服务器版通过 SSH 终端输出字符二维码和扫码地址，登录凭据保存在 Docker 数据卷中。服务无需图形桌面或入站端口，支持多账号常驻运行。准备 Docker Engine 和 Compose 插件后：

```sh
cp server.example.json server.json
# 编辑 server.json 中的账号名和直播间号
docker compose build
docker compose run --rm bilidrop --config /etc/bilidrop/server.json --data-dir /data login main
docker compose run --rm bilidrop --config /etc/bilidrop/server.json --data-dir /data check
docker compose up -d
```

`main` 是示例账号名；每个账号需分别扫码。运行状态可用 `docker compose logs -f bilidrop` 查看。任务自动识别依赖直播间页面结构；无法识别时可在配置中填写任务 ID。配置字段、通知地址、数据权限和非 Docker 运行方式见 [Linux 部署文档](docs/linux-server.md)。

### 许可

代码采用 [MIT License](LICENSE)。原有版权声明保留在许可证中。

## English

An unofficial cross-platform companion for Bilibili live tasks. It provides a macOS desktop app and a headless Linux service for cloud servers. Both support QR-code sign-in, multiple accounts and live rooms, task progress tracking, and automatic reward claim attempts when milestones are reached. Task and reward status depend on the platform's responses.

### macOS desktop app

Requires macOS, Python 3.11 or newer, and network access to Bilibili. From the repository directory, run:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python bilibili_gui.py
```

Sign in with the in-app QR code, enter a room ID or URL, discover tasks, and start watching. Saved account credentials are encrypted locally, with the key held in the macOS Keychain. See the [macOS guide](docs/macos.md) for `.app` builds, credential migration, and browser fallback details.

No signed or notarized macOS package is provided. Follow the platform's rules and keep concurrency modest.

### Linux cloud server

The server edition prints a text QR code and sign-in URL in your SSH terminal. Credentials are stored in a Docker volume. It needs neither a graphical desktop nor inbound ports and can run continuously for multiple accounts. With Docker Engine and the Compose plugin installed:

```sh
cp server.example.json server.json
# Edit account names and live room IDs in server.json
docker compose build
docker compose run --rm bilidrop --config /etc/bilidrop/server.json --data-dir /data login main
docker compose run --rm bilidrop --config /etc/bilidrop/server.json --data-dir /data check
docker compose up -d
```

`main` is the example account name; sign in separately for each account. Follow service output with `docker compose logs -f bilidrop`. Automatic task discovery depends on the live-room page structure; you can provide task IDs in the configuration if discovery fails. See the [Linux deployment guide](docs/linux-server.md) for settings, notifications, data permissions, and installation without Docker.

### License

Licensed under the [MIT License](LICENSE). Existing copyright notices are preserved in the license file.
