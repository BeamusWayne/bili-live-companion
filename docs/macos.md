# Bili Live Companion macOS 版

macOS 版提供 Python 心跳、任务识别、多账号和 Qt 界面，不需要 Windows 虚拟机。
请遵守 Bilibili 平台规则；并发和任务结果以平台实际接口为准。

## 从源码运行

需要 macOS、Python 3.11 或更新版本，以及能访问 Bilibili 的网络。任务直接识别不需要
浏览器；页面兜底识别需要安装 Google Chrome 或 Microsoft Edge。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python bilibili_gui.py
```

扫码登录后输入直播间号或 URL，点击“识别当前任务”查看奖励节点，再点击“开始”。
任务识别不是观看心跳的前置条件。CLI 也可用 `.venv/bin/python bilibili.py --help` 查看参数。

## 构建应用

必须在 macOS 上构建 macOS 应用，不能直接使用 Windows EXE。运行：

```sh
.venv/bin/python -m pip install -r requirements-build.txt
.venv/bin/python build.py --target gui --clean
```

输出位于 `dist/bilibili-drops-miner-gui.app`。这是本地构建的应用，未做 Apple Developer
签名或公证。此版本将自动更新检查设为开发通道，在发布独立安装包前不会提示下载其他平台的版本。

## 凭据与迁移

保存的 Cookie、通知地址和设置正文写入
`~/Library/Application Support/BiliDrop/credentials.json`，内容使用 Fernet 加密；
加密主密钥保存在当前 macOS 用户的系统钥匙串。临时账号只在进程内保留。钥匙串不可用时，
保存操作会失败，不会写入明文，也不会覆盖已有档案。仅复制 JSON 文件到另一台 Mac
无法解密；跨设备使用时请重新扫码登录。原 Windows DPAPI 凭据也无法直接在 Mac 解密。
需要隔离本地数据时，可在启动前设置 `BILIDROP_DATA_DIR` 为绝对目录；它会覆盖默认路径。

早期非 Windows 源码版本如果写过未加密的 `credentials.json`，读取该条目时会将其重新加密。
旧位置 `~/.config/bilidrop/credentials.json` 不会自动移动。如果要迁移，先退出程序，
将旧文件复制到上述 Application Support 路径，再启动本版本；确认账号可读取后再处理旧文件。

## 验证范围

本地自动化可覆盖凭据存储、GUI 启动和打包。真实账号登录、直播计时、任务领取和通知发送
需要用户自己的账号与活动，未在自动化测试中代替用户执行。
