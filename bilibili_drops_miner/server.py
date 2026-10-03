from __future__ import annotations

import argparse
import getpass
import json
import logging
import os
import re
import signal
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import qrcode

from bilibili_drops_miner.automatic_mining import select_scheduled_task_group
from bilibili_drops_miner.config import MinerConfig
from bilibili_drops_miner.domain import DiscoveryStatus, TaskSnapshot
from bilibili_drops_miner.logging_utils import redact_sensitive_text, setup_logging
from bilibili_drops_miner.miner import BilibiliWatchTimeMiner
from bilibili_drops_miner.qr_login import BilibiliQrLoginService, QrLoginState
from bilibili_drops_miner.task_discovery import TaskDiscoveryService
from bilibili_drops_miner.utils import (
    parse_cookie,
    parse_notification_urls,
    parse_room_ids,
    parse_task_ids,
)

LOGGER = logging.getLogger(__name__)
ACCOUNT_NAME_RE = re.compile(r"[A-Za-z0-9_-]{1,40}\Z")
DEFAULT_DATA_DIR = Path.home() / ".local" / "share" / "bilidrop-server"


@dataclass(frozen=True, slots=True)
class ServerAccount:
    name: str
    rooms: tuple[int, ...]
    threads: int = 2
    task_ids: tuple[str, ...] = ()
    auto_discover: bool = True
    discovery_interval_seconds: int = 900
    task_query_interval_seconds: int = 900
    reconnect_delay_seconds: int = 8


def _integer_setting(data: dict, key: str, default: int) -> int:
    value = data.get(key, default)
    if type(value) is not int:
        raise ValueError(f"{key} 必须是整数")
    return value


def load_server_config(path: Path) -> tuple[ServerAccount, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(payload, dict)
        or type(payload.get("version")) is not int
        or payload["version"] != 1
    ):
        raise ValueError("服务配置必须是 version=1 的 JSON 对象")
    if set(payload) - {"version", "accounts"}:
        raise ValueError("服务配置包含未知字段")
    raw_accounts = payload.get("accounts")
    if not isinstance(raw_accounts, list) or not raw_accounts:
        raise ValueError("accounts 必须是非空列表")

    accounts: list[ServerAccount] = []
    names: set[str] = set()
    allowed = {
        "name", "rooms", "threads", "task_ids", "auto_discover",
        "discovery_interval_seconds", "task_query_interval_seconds",
        "reconnect_delay_seconds",
    }
    for raw in raw_accounts:
        if not isinstance(raw, dict) or set(raw) - allowed:
            raise ValueError("账号配置格式错误或包含未知字段")
        name = raw.get("name")
        if not isinstance(name, str) or not ACCOUNT_NAME_RE.fullmatch(name):
            raise ValueError("账号名只能使用 1-40 位字母、数字、下划线或连字符")
        if name in names:
            raise ValueError(f"账号名重复: {name}")
        names.add(name)
        rooms_raw = raw.get("rooms")
        if not isinstance(rooms_raw, list):
            raise ValueError(f"{name}: rooms 必须是列表")
        rooms = tuple(parse_room_ids(",".join(str(room) for room in rooms_raw)))
        task_ids_raw = raw.get("task_ids", [])
        if not isinstance(task_ids_raw, list) or any(
            not isinstance(item, str) for item in task_ids_raw
        ):
            raise ValueError(f"{name}: task_ids 必须是字符串列表")
        task_ids = tuple(parse_task_ids(",".join(task_ids_raw)))
        auto_discover = raw.get("auto_discover", not task_ids)
        if type(auto_discover) is not bool:
            raise ValueError(f"{name}: auto_discover 必须是布尔值")
        account = ServerAccount(
            name=name,
            rooms=rooms,
            threads=_integer_setting(raw, "threads", 2),
            task_ids=task_ids,
            auto_discover=auto_discover,
            discovery_interval_seconds=_integer_setting(
                raw, "discovery_interval_seconds", 900
            ),
            task_query_interval_seconds=_integer_setting(
                raw, "task_query_interval_seconds", 900
            ),
            reconnect_delay_seconds=_integer_setting(
                raw, "reconnect_delay_seconds", 8
            ),
        )
        if not 60 <= account.discovery_interval_seconds <= 3600:
            raise ValueError(f"{name}: discovery_interval_seconds 必须在 60-3600 之间")
        MinerConfig(
            cookie="validation-only",
            room_ids=list(account.rooms),
            thread_count=account.threads,
            reconnect_delay_seconds=account.reconnect_delay_seconds,
            task_query_interval_seconds=account.task_query_interval_seconds,
        ).validate()
        accounts.append(account)
    return tuple(accounts)


class AccountSecrets:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir.expanduser().resolve()

    def _path(self, account: str, kind: str) -> Path:
        if not ACCOUNT_NAME_RE.fullmatch(account):
            raise ValueError("无效账号名")
        return self.data_dir / f"{account}.{kind}"

    def _write(self, path: Path, value: str) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.data_dir, 0o700)
        fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=self.data_dir)
        temporary = Path(temporary_name)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(value)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def _read(self, path: Path) -> str:
        if not path.exists():
            return ""
        if path.stat().st_mode & 0o077:
            raise OSError(f"凭据文件权限过宽，应为 0600: {path}")
        return path.read_text(encoding="utf-8").strip()

    def save_cookie(self, account: str, cookie: str) -> None:
        if not parse_cookie(cookie).get("SESSDATA"):
            raise ValueError("Cookie 缺少 SESSDATA")
        self._write(self._path(account, "cookie"), cookie.strip() + "\n")

    def read_cookie(self, account: str) -> str:
        cookie = self._read(self._path(account, "cookie"))
        if not parse_cookie(cookie).get("SESSDATA"):
            raise ValueError(f"{account}: 缺少已保存的登录 Cookie，请先运行 login")
        return cookie

    def save_notifications(self, account: str, urls: list[str]) -> None:
        self._write(self._path(account, "notify"), "\n".join(urls) + "\n")

    def read_notifications(self, account: str) -> list[str]:
        return parse_notification_urls(self._read(self._path(account, "notify")))


def login_account(account: str, secrets: AccountSecrets, *, service=None) -> int:
    service = service or BilibiliQrLoginService()
    session = service.create_session()
    print("请用 Bilibili App 扫描二维码并在手机上确认：")
    if sys.stdout.isatty():
        code = qrcode.QRCode(border=2)
        code.add_data(session.url)
        code.make(fit=True)
        code.print_ascii(invert=True)
    print(f"扫码地址：{session.url}")
    deadline = time.monotonic() + 180
    last_state = None
    while time.monotonic() < deadline:
        result = service.poll(session)
        if result.state != last_state:
            print(result.message)
            last_state = result.state
        if result.state == QrLoginState.SUCCESS:
            secrets.save_cookie(account, result.cookie)
            print(f"账号 {account} 登录凭据已保存，请重启服务。")
            return 0
        if result.state in {QrLoginState.EXPIRED, QrLoginState.ERROR}:
            return 1
        time.sleep(2)
    print("二维码已超时，请重新运行 login。", file=sys.stderr)
    return 1


def set_notifications(account: str, secrets: AccountSecrets) -> None:
    if not sys.stdin.isatty():
        raise ValueError("请在交互式终端中设置通知地址")
    print("逐条输入通知地址，直接回车结束；输入不会显示在终端。")
    urls = []
    while True:
        value = getpass.getpass("通知地址：").strip()
        if not value:
            break
        urls.append(value)
    secrets.save_notifications(account, parse_notification_urls("\n".join(urls)))
    print(f"账号 {account} 的通知地址已保存，请重启服务。")


class AccountRunner:
    def __init__(
        self,
        account: ServerAccount,
        secrets: AccountSecrets,
        stop_event: threading.Event,
        *,
        miner_factory=BilibiliWatchTimeMiner,
        discovery_service: TaskDiscoveryService | None = None,
    ) -> None:
        self.account = account
        self.stop_event = stop_event
        self.cookie = secrets.read_cookie(account.name)
        config = MinerConfig(
            cookie=self.cookie,
            room_ids=list(account.rooms),
            thread_count=account.threads,
            reconnect_delay_seconds=account.reconnect_delay_seconds,
            task_ids=list(account.task_ids),
            task_query_interval_seconds=account.task_query_interval_seconds,
            notify_urls=secrets.read_notifications(account.name),
        )
        config.validate()
        self.miner = miner_factory(config, on_task_snapshot=self._on_snapshot)
        self.discovery = discovery_service or TaskDiscoveryService(
            cache_ttl_seconds=0,
            browser_provider=lambda _preferred: (),
        )
        self.error = ""
        self._last_snapshot = None
        self._initial_discovery_delay = account.discovery_interval_seconds
        self._miner_thread = threading.Thread(
            target=self._run_miner, name=f"miner-{account.name}", daemon=True
        )
        self._discovery_thread = threading.Thread(
            target=self._discovery_loop,
            name=f"discovery-{account.name}",
            daemon=True,
        )

    @property
    def is_alive(self) -> bool:
        return self._miner_thread.is_alive()

    def start(self) -> None:
        if self.account.auto_discover and not self.stop_event.is_set():
            self._initial_discovery_delay = self._discover_once()
        if self.stop_event.is_set():
            return
        self._miner_thread.start()
        if self.account.auto_discover:
            self._discovery_thread.start()

    def stop(self) -> None:
        if self._miner_thread.is_alive():
            self.miner.stop()

    def join(self, timeout: float = 20) -> bool:
        if self._miner_thread.ident is not None:
            deadline = time.monotonic() + timeout
            while self._miner_thread.is_alive() and time.monotonic() < deadline:
                self.miner.stop()
                self._miner_thread.join(
                    max(0.0, min(0.5, deadline - time.monotonic()))
                )
        if self._discovery_thread.ident is not None:
            self._discovery_thread.join(min(12, timeout))
        return not self._miner_thread.is_alive() and not self._discovery_thread.is_alive()

    def _run_miner(self) -> None:
        try:
            self.miner.run()
        except Exception as exc:
            self.error = redact_sensitive_text(str(exc)) or type(exc).__name__
            LOGGER.error("账号 %s 运行失败: %s", self.account.name, self.error)
            self.stop_event.set()

    def _on_snapshot(self, snapshot: TaskSnapshot) -> None:
        signature = (
            snapshot.error,
            tuple(
                (
                    task.task_id, task.cur_value, task.limit_value,
                    tuple(
                        (point.sid, point.cur_value, point.limit_value, point.status)
                        for point in task.check_points
                    ),
                )
                for task in snapshot.progresses
            ),
        )
        if signature == self._last_snapshot:
            return
        self._last_snapshot = signature
        if snapshot.error:
            LOGGER.warning(
                "账号 %s 任务状态异常: %s",
                self.account.name, redact_sensitive_text(snapshot.error),
            )
        elif snapshot.progresses:
            LOGGER.info(
                "账号 %s 任务进度已更新：%s 个任务，%s 个奖励节点已完成",
                self.account.name,
                len(snapshot.progresses),
                snapshot.completed_count,
            )

    def _discovery_loop(self) -> None:
        delay = self._initial_discovery_delay
        while not self.stop_event.wait(delay):
            delay = self._discover_once()

    def _discover_once(self) -> int:
        task_ids: list[str] = []
        complete = True
        next_delay = self.account.discovery_interval_seconds
        for room_id in self.account.rooms:
            if self.stop_event.is_set():
                break
            try:
                result = self.discovery.discover(
                    room_id,
                    cookie=self.cookie,
                    timeout_seconds=8,
                    force_refresh=True,
                )
                if not result.succeeded:
                    complete = False
                    reason = (
                        "直连页面没有可识别的任务"
                        if result.status == DiscoveryStatus.NO_BROWSER
                        else result.message
                    )
                    LOGGER.info(
                        "账号 %s 房间 %s 暂未识别任务: %s",
                        self.account.name, room_id, reason,
                    )
                    continue
                selection = select_scheduled_task_group(
                    result.groups,
                    now=datetime.now(ZoneInfo("Asia/Shanghai")),
                )
                next_delay = min(next_delay, selection.next_check_seconds)
                if selection.phase == "current" and selection.group is not None:
                    task_ids.extend(selection.group.task_ids)
                elif selection.phase not in {"future", "expired"}:
                    complete = False
            except Exception as exc:
                complete = False
                LOGGER.warning(
                    "账号 %s 房间 %s 任务识别失败: %s",
                    self.account.name, room_id, type(exc).__name__,
                )
        if complete and not self.stop_event.is_set():
            normalized = list(dict.fromkeys(task_ids))
            if normalized != self.miner.config.task_ids:
                self.miner.update_task_ids(normalized)
                LOGGER.info(
                    "账号 %s 已更新任务：%s 个 ID",
                    self.account.name, len(normalized),
                )
        return max(60, next_delay)


def supervise(runners: list[AccountRunner], stop_event: threading.Event) -> int:
    failed = False
    try:
        for runner in runners:
            if stop_event.is_set():
                break
            runner.start()
        while not stop_event.wait(1):
            if any(not runner.is_alive for runner in runners):
                LOGGER.error("账号服务意外退出，正在停止其他账号")
                failed = True
                break
    finally:
        stop_event.set()
        for runner in runners:
            runner.stop()
        for runner in runners:
            if not runner.join():
                LOGGER.error("账号 %s 未能在退出期限内停止", runner.account.name)
                failed = True
    return 1 if failed or any(runner.error for runner in runners) else 0


def run_service(accounts: tuple[ServerAccount, ...], secrets: AccountSecrets) -> int:
    stop_event = threading.Event()
    runners = [AccountRunner(account, secrets, stop_event) for account in accounts]

    def request_stop(_signum, _frame) -> None:
        stop_event.set()

    previous_term = signal.signal(signal.SIGTERM, request_stop)
    previous_int = signal.signal(signal.SIGINT, request_stop)
    try:
        return supervise(runners, stop_event)
    finally:
        signal.signal(signal.SIGTERM, previous_term)
        signal.signal(signal.SIGINT, previous_int)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BiliDrop Linux headless service")
    parser.add_argument("--config", type=Path, default=Path("server.json"))
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("run", help="运行后台服务")
    actions.add_parser("check", help="检查配置和已保存的 Cookie")
    actions.add_parser("login", help="在终端扫码登录").add_argument("account")
    actions.add_parser("set-notify", help="设置通知地址").add_argument("account")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    setup_logging(verbose=False, no_color=True)
    try:
        accounts = load_server_config(args.config)
        secrets = AccountSecrets(args.data_dir)
        names = {account.name for account in accounts}
        if args.action in {"login", "set-notify"} and args.account not in names:
            raise ValueError(f"配置中没有账号 {args.account}")
        if args.action == "login":
            return login_account(args.account, secrets)
        if args.action == "set-notify":
            set_notifications(args.account, secrets)
            return 0
        for account in accounts:
            secrets.read_cookie(account.name)
        if args.action == "check":
            print(f"配置有效：{len(accounts)} 个账号，登录凭据齐全。")
            return 0
        return run_service(accounts, secrets)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"服务启动失败: {redact_sensitive_text(exc)}", file=sys.stderr)
        return 1
