<div align="center">

# 🎁 Bili Live Companion

### Bilibili Live Drops auto-watching and reward-claiming helper

**You scan once. It keeps watch.**

![Windows Desktop](https://img.shields.io/badge/Windows-Desktop-FB7299)
![macOS Desktop](https://img.shields.io/badge/macOS-Desktop-111111?logo=apple&logoColor=white)
![Linux Headless](https://img.shields.io/badge/Linux-Headless-FCC624?logo=linux&logoColor=black)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
[![License: MIT](https://img.shields.io/badge/License-MIT-2ea44f)](LICENSE)

QR sign-in · Multiple accounts · Task progress · Reward claims

Current version: **v0.1.0-alpha.1 development preview**. No stable release has been published.

[Features](#features) · [Quick Start](#quick-start) · [Support](#support-the-project) · [中文](README.md)

</div>

---

## Features

| Feature | What it does |
| --- | --- |
| 📱 **QR sign-in** | Scan inside the Windows / macOS app, or use the text QR code and URL printed in your SSH terminal |
| 👥 **Multiple accounts** | Keep credentials, live rooms, and task state separate for each account |
| 📺 **Watch heartbeats** | Connect to configured live rooms and retry after disconnections |
| 🎯 **Task tracking** | Discover current tasks, query reward milestones, and attempt to claim completed rewards |
| 🔔 **Notifications** | Configure Telegram, Gotify, ServerChan, or WeCom notifications |

Task and reward results depend on Bilibili's responses. Changes to the live-room page may affect automatic discovery; watching can continue, and Linux users can provide task IDs manually.

## Choose your setup

| | Windows desktop | macOS desktop | Linux cloud server |
| --- | --- | --- | --- |
| Interface | Pink and white Qt desktop app | The same Qt desktop UI | Headless service managed through SSH and container logs |
| Sign-in | In-app QR code | In-app QR code | Terminal QR code, once per account |
| Credentials | Windows DPAPI encryption | Encrypted locally; key stored in macOS Keychain | Unencrypted `0600` files in a Docker volume |
| After rewards are claimed | Pauses watching while background checks continue | Pauses watching while background checks continue | Keeps watching until the service is stopped |
| Deployment | Standalone EXE or Python source | Local `.app` or Python source | Docker Compose or Python with systemd |

The Linux service needs no desktop environment or inbound ports. Each edition runs independently on its own operating system.

## Desktop interface

![Windows desktop workspace with demonstration data](docs/images/windows-workspace.png)

The UI uses Bilibili pink and the repository's TV icon, with separate account management and visual reward progress. Activities and progress in the screenshot are synthetic preview data.

## Quick Start

### Windows desktop

The desktop UI now uses a Bilibili pink and white palette with sidebar navigation, a separate account page, and visual reward progress. Windows credentials use DPAPI; tray operation and single-instance activation are supported.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe bilibili_gui.py
```

Run `.\build_windows.ps1` on Windows to test, build a standalone EXE, and validate the packaged app. A packaged EXE does not require Python. See the [Windows guide](docs/windows.md) for details (in Chinese).

The [Windows desktop workflow](https://github.com/BeamusWayne/bili-live-companion/actions/workflows/windows-desktop.yml) runs on PRs and main-branch updates. Download the EXE from **Artifacts → Bili-Companion-Windows-x64** in a successful run. No stable Release installer is published yet.

### macOS desktop

Requires macOS, Python 3.11 or newer, and network access to Bilibili:

```sh
git clone https://github.com/BeamusWayne/bili-live-companion.git
cd bili-live-companion
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python bilibili_gui.py
```

Scan the QR code in the app, enter a live-room ID or URL, discover tasks, and click Start. Task discovery is not required to send watch heartbeats. The [macOS guide](docs/macos.md) covers `.app` builds, credential migration, and browser fallback (in Chinese). No signed or notarized package is provided yet.

### Linux cloud server

Requires Docker Engine, the Compose plugin, and outbound network access to Bilibili:

```sh
git clone https://github.com/BeamusWayne/bili-live-companion.git
cd bili-live-companion
cp server.example.json server.json
# Edit account names and live room IDs in server.json
docker compose build
docker compose run --rm bilidrop --config /etc/bilidrop/server.json --data-dir /data login main
docker compose run --rm bilidrop --config /etc/bilidrop/server.json --data-dir /data check
docker compose up -d
docker compose logs -f --tail=100 bilidrop
```

`main` is the example account name. The terminal prints a text QR code and sign-in URL; after confirmation on your phone, credentials are stored in a Docker volume. Run `login` separately for additional accounts. See the [Linux deployment guide](docs/linux-server.md) for configuration, notifications, and installation without Docker (in Chinese).

## Before you run it

- Follow the platform's rules and keep concurrency modest. Task progress, watch time, and rewards are determined by the platform.
- Windows credentials use DPAPI encryption. macOS credentials are protected by the system Keychain. Linux Cookie files are not encrypted; server root and Docker administrators can read them.
- Real sign-in, watch-time credit, and reward claims depend on your account and current events. Check the UI or logs after deployment.

## Support the project

If this helper saved you time watching live streams, you can buy me a coffee via WeChat. Support is entirely optional; all features remain available to everyone.

<div align="center">
  <img src="assets/wechat-reward.jpg" alt="WeChat reward QR code" width="420">
  <br>
  <sub>Scan with WeChat · Optional support</sub>
</div>

## License

Licensed under the [MIT License](LICENSE), with existing copyright notices preserved. This is an unofficial tool and is not affiliated with Bilibili.

---

<div align="center">
  Made with ☕ by <a href="https://github.com/BeamusWayne">Beamus Wayne</a>
</div>
