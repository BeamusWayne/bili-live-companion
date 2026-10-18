from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QFocusEvent,
    QFont,
    QIntValidator,
    QPainter,
    QPaintEvent,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from bilibili_drops_miner.config import (
    DEFAULT_SESSIONS_PER_ROOM,
    MAX_RECONNECT_DELAY_SECONDS,
    MAX_SESSIONS_PER_ROOM,
    MAX_TASK_QUERY_INTERVAL_SECONDS,
    MIN_RECONNECT_DELAY_SECONDS,
    MIN_TASK_QUERY_INTERVAL_SECONDS,
)
from bilibili_drops_miner.gui_parts.styles import (
    BUTTON_STYLES,
    CARD_STYLE,
    DISABLED_BUTTON_STYLE,
)


@dataclass(slots=True)
class MainWindowCallbacks:
    auto_fetch_cookie: Callable[..., None]
    auto_fetch_room_id: Callable[..., None]
    auto_fetch_task_ids: Callable[..., None]
    auto_fetch_overwatch_esports: Callable[..., None]
    toggle_run: Callable[..., None]
    boost_concurrency: Callable[..., None]
    load_config: Callable[..., None]
    save_config: Callable[..., None]
    select_cookie_profile: Callable[..., None]
    save_cookie_profile: Callable[..., None]
    delete_cookie_profile: Callable[..., None]
    clear_logs: Callable[..., None]
    claim_rewards: Callable[..., None]
    refresh_tasks: Callable[..., None]
    open_settings_log: Callable[..., None]
    toggle_cookie_visibility: Callable[..., None]
    toggle_notify_visibility: Callable[..., None]
    test_notification: Callable[..., None]
    export_diagnostics: Callable[..., None]


@dataclass(slots=True)
class MainWindowWidgets:
    cookie_edit: QLineEdit
    rooms_edit: QLineEdit
    task_ids_edit: QLineEdit
    notify_urls_edit: QLineEdit
    cookie_profile_combo: QComboBox
    cookie_remark_edit: QLineEdit
    threads_spin: NumericLineEdit
    reconnect_spin: NumericLineEdit
    task_interval_spin: NumericLineEdit
    verbose_check: QCheckBox
    disable_task_notify_check: QCheckBox
    progress_bar: QProgressBar
    task_table: QTableWidget
    log_text: QPlainTextEdit
    settings_dialog: QDialog
    settings_tabs: QTabWidget
    settings_button: QPushButton
    claim_rewards_btn: QPushButton
    start_btn: QPushButton
    boost_concurrency_btn: QPushButton
    apply_all_switch: ToggleSwitch
    concurrency_mode_combo: QComboBox
    minimize_to_tray_check: QCheckBox
    close_to_tray_check: QCheckBox
    auto_check_updates_check: QCheckBox
    discover_btn: QPushButton
    overwatch_esports_btn: QPushButton
    cookie_reveal_btn: QPushButton
    save_cookie_profile_btn: QPushButton
    delete_cookie_profile_btn: QPushButton
    notify_reveal_btn: QPushButton
    runtime_state_label: QLabel
    runtime_detail_label: QLabel
    discovery_status_label: QLabel
    watch_time_label: QLabel


class NumericLineEdit(QLineEdit):
    """A bounded integer field with no steppers or wheel-based changes."""

    def __init__(self, minimum: int, maximum: int, value: int) -> None:
        super().__init__()
        self._minimum = minimum
        self._maximum = maximum
        self.setValidator(QIntValidator(minimum, maximum, self))
        self.setInputMethodHints(Qt.ImhDigitsOnly)
        self.setValue(value)

    def value(self) -> int:
        try:
            value = int(self.text().strip())
        except ValueError:
            value = self._minimum
        return max(self._minimum, min(self._maximum, value))

    def setValue(self, value: int) -> None:
        bounded = max(self._minimum, min(self._maximum, int(value)))
        self.setText(str(bounded))

    def wheelEvent(self, event: QWheelEvent) -> None:
        event.ignore()

    def focusOutEvent(self, event: QFocusEvent) -> None:
        self.setValue(self.value())
        super().focusOutEvent(event)


class ToggleSwitch(QCheckBox):
    """Compact iOS-style boolean switch without the native focus rectangle."""

    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(46, 26)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)

    def sizeHint(self) -> QSize:
        return QSize(46, 26)

    def hitButton(self, pos) -> bool:
        return self.rect().contains(pos)

    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        opacity = 1.0 if self.isEnabled() else 0.45
        painter.setOpacity(opacity)
        track = QRectF(1, 3, self.width() - 2, self.height() - 6)
        painter.setPen(Qt.NoPen)
        painter.setBrush(
            QColor("#fb7299" if self.isChecked() else "#c9ccd0")
        )
        painter.drawRoundedRect(
            track,
            track.height() / 2,
            track.height() / 2,
        )
        knob_size = track.height() - 4
        knob_x = (
            track.right() - knob_size - 2
            if self.isChecked()
            else track.left() + 2
        )
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(
            QRectF(knob_x, track.top() + 2, knob_size, knob_size)
        )
        if self.hasFocus():
            from PySide6.QtGui import QPen
            painter.setPen(QPen(QColor("#a92d56"), 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1), 6, 6)


def build_main_window_layout(
    window: QMainWindow,
    callbacks: MainWindowCallbacks,
) -> MainWindowWidgets:
    from bilibili_drops_miner.gui_parts.workspace_layout import build_workspace

    workspace = build_workspace(window, callbacks)

    settings_dialog = QDialog(window)
    settings_dialog.setWindowTitle("设置与日志")
    settings_dialog.setModal(False)
    settings_dialog.resize(900, 700)
    settings_dialog.setMinimumSize(740, 580)
    settings_dialog_layout = QVBoxLayout(settings_dialog)
    settings_dialog_layout.setContentsMargins(18, 16, 18, 18)
    settings_dialog_layout.setSpacing(12)
    dialog_title = QLabel("设置与日志")
    dialog_title.setFont(_font(15, bold=True))
    settings_dialog_layout.addWidget(dialog_title)
    settings_tabs = QTabWidget()
    settings_dialog_layout.addWidget(settings_tabs, 1)

    advanced_scroll = QScrollArea()
    advanced_scroll.setWidgetResizable(True)
    advanced_scroll.setFrameShape(QFrame.NoFrame)
    advanced_page = QWidget()
    advanced_scroll.setWidget(advanced_page)
    advanced_stack = QVBoxLayout(advanced_page)
    advanced_stack.setContentsMargins(14, 14, 14, 14)
    advanced_stack.setSpacing(10)

    threads_spin = _numeric_input(
        1, MAX_SESSIONS_PER_ROOM, DEFAULT_SESSIONS_PER_ROOM
    )
    reconnect_spin = _numeric_input(
        MIN_RECONNECT_DELAY_SECONDS, MAX_RECONNECT_DELAY_SECONDS, 8
    )
    task_interval_spin = _numeric_input(
        MIN_TASK_QUERY_INTERVAL_SECONDS, MAX_TASK_QUERY_INTERVAL_SECONDS, 30
    )
    connection_group, connection_layout = _settings_group(
        "连接参数",
        "默认值适合普通使用；并发越高越容易触发平台限频。",
    )
    connection_fields = QHBoxLayout()
    connection_fields.setSpacing(12)
    for title, control in (
        ("每房间并发会话", threads_spin),
        ("断线重试等待（秒）", reconnect_spin),
        ("任务刷新间隔（秒）", task_interval_spin),
    ):
        connection_fields.addWidget(_field_widget(title, control), 1)
    connection_layout.addLayout(connection_fields)
    concurrency_mode_combo = QComboBox()
    concurrency_mode_combo.addItem(
        "自动调节（追赶 16，3 分钟检测后 2）", "automatic"
    )
    concurrency_mode_combo.addItem("固定并发", "fixed")
    concurrency_mode_combo.setToolTip(
        "自动模式先用 16 个心跳会话；3 分钟进度增量不足 16 时降为 2 个，"
        "并保持到下一组新任务。后台检测到初始进度为 0 的新任务直接使用 2 个。"
    )
    connection_layout.addWidget(
        _field_widget("并发模式", concurrency_mode_combo)
    )
    advanced_stack.addWidget(connection_group)

    task_ids_edit = _line_edit("任务 ID（自动识别，必要时手动填写）")
    task_ids_edit.setAccessibleName("任务 ID 高级设置")
    task_group, task_group_layout = _settings_group(
        "任务识别",
        "正常情况下由房间号自动识别。只有自动识别失败时，才需要手动填写任务 ID。",
    )
    task_group_layout.addWidget(task_ids_edit)
    advanced_stack.addWidget(task_group)

    notify_urls_edit = _line_edit(
        "Telegram：tgram://BotToken/ChatID；也支持 Gotify、Server 酱、企业微信"
    )
    notify_urls_edit.setEchoMode(QLineEdit.Password)
    notify_urls_edit.setAccessibleName("通知地址")
    notify_urls_edit.setToolTip(
        "Telegram 格式：tgram://BotToken/ChatID；多个通知地址用逗号分隔"
    )
    notify_reveal_btn = _button("显示", "gray", callbacks.toggle_notify_visibility)
    notification_group, notification_layout = _settings_group(
        "通知与运行行为",
        "Telegram 使用 tgram://BotToken/ChatID；通知地址会隐藏并保存在受保护凭据中。",
    )
    notification_row = QHBoxLayout()
    notification_row.setSpacing(8)
    notification_row.addWidget(notify_urls_edit, 1)
    notification_row.addWidget(notify_reveal_btn)
    notification_row.addWidget(_button("测试通知", "gray", callbacks.test_notification))
    notification_layout.addLayout(notification_row)

    verbose_check = QCheckBox("输出详细运行日志")
    disable_task_notify_check = QCheckBox("不发送任务完成通知")
    option_row = QHBoxLayout()
    option_row.setSpacing(20)
    option_row.addWidget(verbose_check)
    option_row.addWidget(disable_task_notify_check)
    option_row.addStretch(1)
    notification_layout.addLayout(option_row)
    advanced_stack.addWidget(notification_group)

    desktop_group, desktop_layout = _settings_group(
        "桌面运行",
        "默认最小化和关闭主窗口后继续驻留托盘；可在这里恢复普通窗口行为。",
    )
    minimize_to_tray_check = QCheckBox("最小化到托盘")
    minimize_to_tray_check.setChecked(True)
    close_to_tray_check = QCheckBox("关闭到托盘")
    close_to_tray_check.setChecked(True)
    auto_check_updates_check = QCheckBox("启动时检查更新")
    auto_check_updates_check.setChecked(True)
    auto_check_updates_check.setToolTip(
        "只检查 GitHub Release；发现新版本后询问是否打开发布页，不自动下载或安装"
    )
    desktop_options = QHBoxLayout()
    desktop_options.setSpacing(20)
    desktop_options.addWidget(minimize_to_tray_check)
    desktop_options.addWidget(close_to_tray_check)
    desktop_options.addWidget(auto_check_updates_check)
    desktop_options.addStretch(1)
    desktop_layout.addLayout(desktop_options)
    advanced_stack.addWidget(desktop_group)

    settings_actions = QHBoxLayout()
    settings_actions.setSpacing(8)
    settings_actions.addWidget(_button("导出诊断", "gray", callbacks.export_diagnostics))
    settings_actions.addStretch(1)
    settings_actions.addWidget(_button("加载设置", "gray", callbacks.load_config))
    settings_actions.addWidget(_button("保存设置", "blue", callbacks.save_config))
    advanced_stack.addLayout(settings_actions)
    advanced_stack.addStretch(1)
    settings_tabs.addTab(advanced_scroll, "高级设置")

    log_page = QWidget()
    log_layout = QVBoxLayout(log_page)
    log_layout.setContentsMargins(14, 14, 14, 14)
    log_layout.setSpacing(10)
    log_head = QHBoxLayout()
    log_title = QLabel("实时运行日志")
    log_title.setFont(_font(11, bold=True))
    log_head.addWidget(log_title)
    log_head.addStretch(1)
    log_head.addWidget(_button("清空", "gray", callbacks.clear_logs))
    log_layout.addLayout(log_head)
    log_text = QPlainTextEdit()
    log_text.setReadOnly(True)
    log_text.setFont(QFont("Consolas", 10))
    log_text.setMaximumBlockCount(5000)
    log_text.setMinimumHeight(420)
    log_layout.addWidget(log_text, 1)
    settings_tabs.addTab(log_page, "运行日志")

    return MainWindowWidgets(
        **workspace,
        task_ids_edit=task_ids_edit,
        notify_urls_edit=notify_urls_edit,
        threads_spin=threads_spin,
        reconnect_spin=reconnect_spin,
        task_interval_spin=task_interval_spin,
        verbose_check=verbose_check,
        disable_task_notify_check=disable_task_notify_check,
        log_text=log_text,
        settings_dialog=settings_dialog,
        settings_tabs=settings_tabs,
        concurrency_mode_combo=concurrency_mode_combo,
        minimize_to_tray_check=minimize_to_tray_check,
        close_to_tray_check=close_to_tray_check,
        auto_check_updates_check=auto_check_updates_check,
        notify_reveal_btn=notify_reveal_btn,
    )


def _card(title: str) -> tuple[QFrame, QVBoxLayout]:
    card = QFrame()
    card.setObjectName("card")
    card.setStyleSheet(CARD_STYLE)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 14, 18, 16)
    layout.setSpacing(10)
    if title:
        label = QLabel(title)
        label.setFont(_font(11, bold=True))
        layout.addWidget(label)
    return card, layout


def _font(size: int, *, bold: bool = False) -> QFont:
    font = QFont()
    font.setPointSize(size)
    font.setBold(bold)
    return font


def _line_edit(placeholder: str) -> QLineEdit:
    widget = QLineEdit()
    widget.setPlaceholderText(placeholder)
    return widget


def _numeric_input(minimum: int, maximum: int, value: int) -> NumericLineEdit:
    return NumericLineEdit(minimum, maximum, value)


def _button(text: str, color: str, slot: Callable[..., None]) -> QPushButton:
    button = QPushButton(text)
    button.setStyleSheet(
        BUTTON_STYLES.get(color, BUTTON_STYLES[""]) + DISABLED_BUTTON_STYLE
    )
    button.setCursor(Qt.PointingHandCursor)
    button.clicked.connect(slot)
    return button


def _buddy_label(text: str, buddy: QWidget) -> QLabel:
    label = QLabel(text)
    label.setBuddy(buddy)
    label.setStyleSheet("color:#61666d;")
    label.setMinimumWidth(76)
    return label


def _form_row(label: str, primary: QWidget, *extras: QWidget) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(8)
    row.addWidget(_buddy_label(label, primary))
    primary.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    row.addWidget(primary, 1)
    for widget in extras:
        row.addWidget(widget)
    return row


def _settings_group(
    title: str,
    description: str,
) -> tuple[QFrame, QVBoxLayout]:
    group = QFrame()
    group.setObjectName("settingsGroup")
    group.setStyleSheet(
        "QFrame#settingsGroup{background:#ffffff;border:1px solid #e3e5e7;"
        "border-radius:8px;}"
    )
    layout = QVBoxLayout(group)
    layout.setContentsMargins(14, 12, 14, 14)
    layout.setSpacing(8)
    title_label = QLabel(title)
    title_label.setFont(_font(10, bold=True))
    layout.addWidget(title_label)
    title_label.setToolTip(description)
    return group, layout


def _field_widget(title: str, control: QWidget) -> QWidget:
    field = QWidget()
    layout = QVBoxLayout(field)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(5)
    label = _buddy_label(title, control)
    label.setMinimumWidth(0)
    layout.addWidget(label)
    control.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    layout.addWidget(control)
    return field


def _runtime_action_group(
    title: str,
    primary: QPushButton,
    secondary: QPushButton,
) -> QWidget:
    group = QFrame()
    group.setObjectName("runtimeActionGroup")
    group.setStyleSheet(
        "QFrame#runtimeActionGroup{background:#ffffff;border:1px solid #e3e5e7;"
        "border-radius:8px;}"
    )
    layout = QVBoxLayout(group)
    layout.setContentsMargins(10, 8, 10, 10)
    layout.setSpacing(7)
    label = QLabel(title)
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet("color:#61666d;font-size:9pt;")
    layout.addWidget(label)
    buttons = QHBoxLayout()
    buttons.setSpacing(6)
    buttons.addWidget(primary, 1)
    buttons.addWidget(secondary, 1)
    layout.addLayout(buttons)
    return group
