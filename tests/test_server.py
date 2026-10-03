import json
import stat
import threading

import pytest

from bilibili_drops_miner.domain import (
    DiscoveredTaskGroup,
    DiscoveryStatus,
    TaskDiscoveryResult,
)
from bilibili_drops_miner.qr_login import QrLoginPollResult, QrLoginSession, QrLoginState
from bilibili_drops_miner.server import (
    AccountRunner,
    AccountSecrets,
    ServerAccount,
    load_server_config,
    login_account,
    supervise,
)


def test_server_config_supports_multiple_accounts_and_rejects_unknown_fields(tmp_path) -> None:
    path = tmp_path / "server.json"
    path.write_text(
        json.dumps({
            "version": 1,
            "accounts": [
                {"name": "main", "rooms": [23612045]},
                {"name": "second", "rooms": ["https://live.bilibili.com/12345"],
                 "task_ids": ["a", "b"]},
            ],
        }),
        encoding="utf-8",
    )

    accounts = load_server_config(path)

    assert [account.name for account in accounts] == ["main", "second"]
    assert accounts[0].rooms == (23612045,)
    assert accounts[0].auto_discover is True
    assert accounts[1].rooms == (12345,)
    assert accounts[1].auto_discover is False
    assert accounts[1].task_ids == ("a", "b")

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["accounts"][0]["cookie"] = "must-not-be-accepted"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="未知字段"):
        load_server_config(path)


def test_account_secrets_are_private_and_names_cannot_escape_directory(tmp_path) -> None:
    store = AccountSecrets(tmp_path / "data")
    store.save_cookie("main", "SESSDATA=fixture; DedeUserID=1")
    store.save_notifications("main", ["tgram://fixture/chat"])

    cookie_path = tmp_path / "data" / "main.cookie"
    assert store.read_cookie("main") == "SESSDATA=fixture; DedeUserID=1"
    assert store.read_notifications("main") == ["tgram://fixture/chat"]
    assert stat.S_IMODE(cookie_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(cookie_path.parent.stat().st_mode) == 0o700
    with pytest.raises(ValueError, match="无效账号名"):
        store.save_cookie("../other", "SESSDATA=fixture")

    cookie_path.chmod(0o644)
    with pytest.raises(OSError, match="0600"):
        store.read_cookie("main")


def test_terminal_login_saves_cookie_without_printing_it(tmp_path, capsys) -> None:
    class FakeLogin:
        def create_session(self):
            return QrLoginSession("https://example.invalid/qr", "fixture-key")

        def poll(self, _session):
            return QrLoginPollResult(
                QrLoginState.SUCCESS,
                "扫码登录成功",
                "SESSDATA=secret-fixture; DedeUserID=1",
            )

    store = AccountSecrets(tmp_path / "data")
    assert login_account("main", store, service=FakeLogin()) == 0

    assert store.read_cookie("main").startswith("SESSDATA=secret-fixture")
    assert "secret-fixture" not in capsys.readouterr().out


class FakeMiner:
    def __init__(self, config, *, on_task_snapshot) -> None:
        del on_task_snapshot
        self.config = config
        self.stopped = threading.Event()
        self.started = threading.Event()

    def run(self) -> None:
        self.started.set()
        self.stopped.wait(5)

    def stop(self) -> None:
        self.stopped.set()

    def update_task_ids(self, task_ids: list[str]) -> bool:
        self.config.task_ids = list(task_ids)
        return True


def test_runner_discovers_tasks_and_stops_cleanly(tmp_path) -> None:
    class FakeDiscovery:
        def discover(self, room_id, **_kwargs):
            group = DiscoveredTaskGroup("today", ("task-one", "task-two"), active=True)
            return TaskDiscoveryResult(
                room_id=room_id,
                status=DiscoveryStatus.SUCCESS,
                groups=(group,),
                selected_group=group,
            )

    secrets = AccountSecrets(tmp_path / "data")
    secrets.save_cookie("main", "SESSDATA=fixture; DedeUserID=1")
    stop_event = threading.Event()
    runner = AccountRunner(
        ServerAccount("main", (23612045,)),
        secrets,
        stop_event,
        miner_factory=FakeMiner,
        discovery_service=FakeDiscovery(),
    )
    runner.start()
    assert runner.miner.started.wait(2)
    assert runner.miner.config.task_ids == ["task-one", "task-two"]

    stop_event.set()
    runner.stop()
    assert runner.join(2)


def test_supervisor_stops_all_accounts_on_signal(tmp_path) -> None:
    secrets = AccountSecrets(tmp_path / "data")
    secrets.save_cookie("main", "SESSDATA=fixture; DedeUserID=1")
    stop_event = threading.Event()
    runner = AccountRunner(
        ServerAccount("main", (23612045,), auto_discover=False),
        secrets,
        stop_event,
        miner_factory=FakeMiner,
    )
    stopper = threading.Thread(
        target=lambda: (runner.miner.started.wait(2), stop_event.set()),
        daemon=True,
    )
    stopper.start()

    assert supervise([runner], stop_event) == 0
    assert not runner.is_alive
    stopper.join(2)
