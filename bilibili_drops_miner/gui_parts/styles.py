from __future__ import annotations

DISABLED_BUTTON_STYLE = "QPushButton:disabled{background:#f1f2f3;color:#9499a0;border:1px solid #e3e5e7;}"
PRIMARY = (
    "QPushButton{background:#fb7299;color:#4c2031;border:1px solid #fb7299;"
    "border-radius:7px;padding:8px 18px;min-height:18px;font-weight:600;}"
    "QPushButton:hover{background:#ff8fb0;border-color:#e45d88;}"
    "QPushButton:pressed{background:#f25d8e;}"
    "QPushButton:focus{border:1px solid #a92d56;}"
)
SECONDARY = (
    "QPushButton{background:#ffffff;color:#61666d;border:1px solid #e3e5e7;"
    "border-radius:7px;padding:8px 14px;min-height:18px;font-weight:500;}"
    "QPushButton:hover{background:#f8f9fa;border-color:#c9ccd0;}"
    "QPushButton:pressed{background:#edeef0;}"
    "QPushButton:focus{border-color:#a92d56;}"
)
DANGER = (
    "QPushButton{background:#fff0f3;color:#b92d4a;border:1px solid #f1bcc8;"
    "border-radius:7px;padding:8px 18px;min-height:18px;font-weight:600;}"
    "QPushButton:hover{background:#ffe3ea;}"
    "QPushButton:focus{border-color:#b92d4a;}"
)
# Aliases preserve the existing run controller's start/stop transitions.
BUTTON_STYLES = {"green": PRIMARY, "blue": PRIMARY, "purple": PRIMARY, "red": DANGER, "gray": SECONDARY, "": SECONDARY}
CARD_STYLE = "QFrame#card{background:#ffffff;border:1px solid #e3e5e7;border-radius:12px;}"
