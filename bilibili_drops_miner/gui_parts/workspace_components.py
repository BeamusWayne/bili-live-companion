"""Small Qt-native components for the desktop workspace; no web runtime."""
from __future__ import annotations

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem, QTableWidget


PATHS = {
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    "users": '<circle cx="9" cy="8" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6m2 3a5 5 0 0 1 3 5v2"/>',
    "settings": '<path d="M4 6h16M4 12h16M4 18h16"/><circle cx="9" cy="6" r="2" fill="white"/><circle cx="15" cy="12" r="2" fill="white"/><circle cx="9" cy="18" r="2" fill="white"/>',
    "log": '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/>',
    "refresh": '<path d="M20 7v5h-5M4 17v-5h5M6.1 6.1A8 8 0 0 1 20 12M4 12a8 8 0 0 0 13.9 5.9"/>',
    "gift": '<path d="M3 11h18v-5H3v5Zm2 0v10h14V11M12 6v15M12 6H8a2.5 2.5 0 1 1 2.5-2.5L12 6Zm0 0h4a2.5 2.5 0 1 0-2.5-2.5L12 6Z"/>',
    "qr": '<path d="M3 9V3h6m6 0h6v6M3 15v6h6m6 0h6v-6M7 7h1m8 0h1M7 16h1m4-5v3h5m-3 3v1"/>',
    "play": '<path d="m8 5 11 7-11 7V5Z"/>',
    "bolt": '<path d="m13 2-9 12h7l-1 8 10-13h-8l1-7Z"/>',
    "link": '<path d="m10 14 4-4M8 16l-1 1a4 4 0 0 1-6-6l5-5a4 4 0 0 1 6 0m4 2 1-1a4 4 0 0 1 6 6l-5 5a4 4 0 0 1-6 0"/>',
}


def line_icon(name: str, color: str = "#747a81", size: int = 18) -> QIcon:
    body = PATHS[name]
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    QSvgRenderer(QByteArray(svg.encode())).render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return QIcon(pixmap)


class RewardTable(QTableWidget):
    """Render a useful empty state while preserving the accessible table model."""

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.rowCount() and not (self.rowCount() == 1 and self.columnSpan(0, 0) == self.columnCount()):
            return
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.viewport().rect(), QColor("#ffffff"))
        center_x = self.viewport().width() / 2
        center_y = max(65, self.viewport().height() / 2 - 20)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#fff0f5"))
        painter.drawRoundedRect(QRectF(center_x - 25, center_y - 40, 50, 50), 14, 14)
        line_icon("gift", "#d64873", 25).paint(painter, int(center_x - 13), int(center_y - 28), 26, 26)
        painter.setPen(QColor("#61666d"))
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        item = self.item(0, 0)
        message = item.text() if item else "暂无任务，请先识别当前任务"
        font.setBold(False)
        font.setPixelSize(14)
        painter.setFont(font)
        painter.drawText(QRectF(24, center_y + 23, self.viewport().width() - 48, 70), Qt.AlignHCenter | Qt.TextWordWrap, message)


class RewardDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        percent = index.data(Qt.UserRole)
        if index.column() == 1 and percent is not None:
            painter.save()
            selected = bool(option.state & QStyle.State_Selected)
            painter.fillRect(option.rect, QColor("#fff2f6" if selected else "#ffffff"))
            rect = QRectF(option.rect).adjusted(15, 12, -15, -12)
            painter.setPen(QColor("#61666d"))
            painter.drawText(rect.adjusted(0, 0, 0, -8), Qt.AlignLeft | Qt.AlignVCenter, str(index.data()))
            track = QRectF(rect.left(), rect.bottom() - 3, rect.width(), 4)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#edeef0"))
            painter.drawRoundedRect(track, 2, 2)
            painter.setBrush(QColor("#fb7299"))
            if percent:
                painter.drawRoundedRect(QRectF(track.left(), track.top(), track.width() * percent / 100, 4), 2, 2)
            painter.restore()
            return
        if index.column() == 2:
            painter.save()
            painter.fillRect(option.rect, QColor("#fff2f6" if option.state & QStyle.State_Selected else "#ffffff"))
            text = str(index.data() or "")
            foreground, background = ("#397258", "#eaf5ec") if text in {"已完成", "已领取"} else ("#087ea4", "#e9f7fc")
            width = painter.fontMetrics().horizontalAdvance(text) + 20
            rect = QRectF(option.rect.center().x() - width / 2, option.rect.center().y() - 12, width, 24)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(background))
            painter.drawRoundedRect(rect, 6, 6)
            painter.setPen(QColor(foreground))
            painter.drawText(rect, Qt.AlignCenter, text)
            painter.restore()
            return
        super().paint(painter, option, index)
