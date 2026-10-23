# Bili Companion Windows 桌面版

新版采用 B 站粉（`#FB7299`）、白色与浅灰色，使用 Qt 原生窗口。首页展示直播间、运行状态、连接数和奖励节点；账号凭据在独立账号页管理，设置与日志由侧栏打开。

当前版本为 `v0.1.0`，应用使用仓库已有的 B 站小电视图标。

## 直接运行

从 [Releases](https://github.com/BeamusWayne/bili-live-companion/releases/tag/v0.1.0) 下载 **BiliCompanion-v0.1.0-Windows-x64.exe**，在 Windows x64 上双击运行。独立 EXE 已包含 Python、Qt、时区数据库与应用资源，不需要另外安装 Python。发布页同时提供使用说明和 `SHA256SUMS.txt` 校验文件。

1. 点击右上角「扫码登录」，用 Bilibili App 扫描并确认。
2. 在「账号管理」填写备注并「保存档案」，便于下次继续使用；临时账号关闭后删除。
3. 回到「直播工作台」，输入直播间号或 URL；也可点击「守望先锋电竞」。
4. 点击「识别当前任务」查看奖励，再点击「开始」。识别成功不是发送观看心跳的前置条件。
5. 多账号通过顶部下拉框切换。开启「应用到所有账号」后，识别与开始/停止作用于所有账号。

「停止」关闭观看线程，后台任务检测继续运行；完全退出请使用托盘菜单的「退出程序」。关闭和最小化到托盘可以在设置中关闭。

任务计时、活动进度与奖励领取以 Bilibili 返回结果为准。开发验证使用离线数据；真实扫码、计时和领奖需要自己的账号与有效活动验证。此构建尚未进行代码签名。

## 数据保存

- 默认目录：`%LOCALAPPDATA%\BiliDrop\`。
- `credentials.json` 保存账号及设置，Cookie、通知密钥由 Windows DPAPI 加密。
- 加密凭据与当前 Windows 用户关联，复制到其他用户或计算机后应重新扫码登录。
- 可用 `BILIDROP_DATA_DIR` 指定其他数据目录。应用文件可移动，个人数据不写入程序解压目录。
- 旧版凭据迁移沿用原项目逻辑，迁移前会保留备份。

扫码登录和 API 识别不依赖浏览器；浏览器兜底识别需要 Chrome 或 Edge 及联网下载匹配的驱动。无需单独安装 WebView2。

## 从源码运行

安装 Python 3.11+ x64，进入项目目录，在 PowerShell 执行：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe bilibili_gui.py
```

## 一键构建

```powershell
.\build_windows.ps1
```

脚本创建 `.venv`、安装固定版本依赖、运行 Windows 桌面测试、调用 PyInstaller，再实际启动产物做离线检查。

- 默认产物：`dist\bilibili-drops-miner-gui.exe`。
- `-OneDir`：生成目录版，分发时应保留整个目录。
- `-SkipTests`：本地已测试后跳过单元测试；仍执行产物启动检查。
- `dist\windows-smoke-result.json`：产物启动检查结果。

也可手动执行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe build.py --target gui --clean
```

Windows 版本必须在 Windows 上打包。`.github/workflows/windows-desktop.yml` 提供测试、构建、启动检查与发布流程，也可手动运行。主分支采用 `release` 更新渠道且版本号尚未发布时，会创建对应标签及 Release；已有 Release 不会被覆盖。发布附件来自同一次通过检查的构建。

## 离线验证

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe -m pytest --ignore=tests/test_server.py
.\.venv\Scripts\python.exe bilibili_gui.py --smoke-test --smoke-result smoke-result.json
```

`--smoke-test` 使用临时数据目录，验证 DPAPI、时区、窗口、导航和打包资源，不登录、不观看直播、不访问真实账号。`tests/test_server.py` 面向 Linux 服务的 POSIX 文件权限，在 Linux 中运行，Windows 桌面测试将其排除。

界面截图可离线生成：

```powershell
.\.venv\Scripts\python.exe scripts\preview_ui.py --output work\previews
```

`workspace-empty.png` 是初始界面，`workspace-preview.png` 含明确标记的演示数据；另外生成账号页和设置页截图。

本次本地验证环境：Windows 11 x64、Python 3.12、PySide6 6.11。macOS/Linux 的底层业务代码保留，其他平台的打包需在对应系统上验证。

## 联动测试版

v0.1.1-beta.1 提供「下载回放 / 视频」入口、公开视频链接确认和平台进度确认提示。测试版独立 EXE 不替换 v0.1.0 稳定版发布；仍使用同一用户数据目录。

本轮在 Windows 上通过 189 项桌面范围测试（按构建脚本排除 Linux 专用 server 测试），并完成独立 EXE 的离线 DPAPI、资源和窗口导航冒烟检查。未据此声称真实活动掉宝和领奖已完成在线验证。
