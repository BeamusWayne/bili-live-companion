# Bili Live Companion Linux 服务器版

服务器版在 Linux 上无图形界面运行，不需要 Windows、Chrome 或桌面钥匙串。它支持多个账号、
终端扫码登录、房间观看心跳、直连任务识别、进度查询和自动领奖。服务始终以固定低并发运行；
任务领奖完成后仍会继续观看，直到停止服务。请遵守 Bilibili 平台规则。

## Docker Compose 部署

服务器需要 Docker Engine 和 Compose 插件，出站 HTTPS 网络可访问 Bilibili。无需开放入站
端口。先在仓库目录准备配置，并编辑 `server.json` 的账号名和房间号：

```sh
cp server.example.json server.json
docker compose build
docker compose run --rm bilidrop --config /etc/bilidrop/server.json --data-dir /data login main
```

最后一条命令会在 SSH 终端显示二维码和扫码地址。用手机 Bilibili App 扫码并确认后，Cookie
保存在 Docker 命名数据卷的 `main.cookie` 中。每增加一个账号，先在 `server.json` 增加一项，
再用该账号名分别运行一次 `login`。真实 Cookie 不会出现在命令参数、镜像或仓库文件中。

登录完成后检查配置并启动：

```sh
docker compose run --rm bilidrop --config /etc/bilidrop/server.json --data-dir /data check
docker compose up -d
docker compose logs -f --tail=100 bilidrop
```

常用维护命令：

```sh
docker compose ps
docker compose restart bilidrop
docker compose down
docker compose up -d --build
```

Cookie 失效后重复运行 `login main`，然后重启服务。可选通知地址用
`docker compose run --rm bilidrop --config /etc/bilidrop/server.json --data-dir /data set-notify main`
交互式输入，目前支持 Telegram、Gotify、Server 酱和企业微信内置通知格式。输入内容不会显示
在终端，也不会写入 `server.json`。

## 配置和数据

`server.json` 只包含非凭据配置，已被 Git 忽略。每个账号的 `rooms` 可填房间号或直播间 URL；
`threads` 默认 2，建议云服务器保持低并发。`auto_discover` 默认在没有手动 `task_ids` 时开启。
服务每隔 `discovery_interval_seconds` 从直播间页面直连识别当前任务；识别到 ID 后，现有任务
监控器会查询进度并自动领取。页面直连没有任务时仍会发送观看心跳，但不能自动查询/领奖。
此时可在 `server.json` 填入 `task_ids` 并将 `auto_discover` 设为 `false`，然后重启。

Cookie 和通知地址放在命名卷 `/data`，文件权限为 `0600`，目录权限为 `0700`。这不是加密存储：
拥有 Docker 管理权限或服务器 root 权限的人仍能读取。备份数据卷时应按账号凭据处理。
服务进程使用非 root 用户，根文件系统只读，不开放 HTTP 管理端口。

## 不使用 Docker

在 Linux 主机上安装 Python 3.11 或更新版本后，可用独立用户直接运行：

```sh
python3 -m venv .venv-server
.venv-server/bin/python -m pip install -r requirements-server.txt
.venv-server/bin/python bilibili_server.py --config server.json --data-dir ./server-data login main
.venv-server/bin/python bilibili_server.py --config server.json --data-dir ./server-data run
```

用 `SIGTERM` 或 Ctrl+C 停止服务时，程序会通知各账号的心跳和任务轮询退出。长期运行建议由
systemd 管理，工作目录设为此仓库，`ExecStart` 使用最后一条 `run` 命令，并让专用用户拥有
数据目录。

## 验证边界

配置、凭据权限、进程退出和容器配置可离线验证。真实扫码、直播计时和领奖结果依赖用户账号
与当前活动，部署后请用服务日志核对。Linux 无浏览器兜底识别，平台调整页面结构时可能需要
手动提供任务 ID。
