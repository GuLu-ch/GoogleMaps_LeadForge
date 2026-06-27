from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, CaptionLabel, FluentIcon, PushSettingCard, SimpleCardWidget, SpinBox, StrongBodyLabel


class NoWheelSpinBox(SpinBox):
    """忽略鼠标滚轮的数字输入框。

    PySide 的数字输入框默认会响应鼠标滚轮。设置页和任务参数页通常放在滚动区域里，
    如果用户只是想滚动页面，就可能误改停留时间、滚动次数等关键参数。这个控件统一
    屏蔽滚轮修改，只允许通过点击箭头、键盘输入或选中文本后输入来改变数值。
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """忽略滚轮事件，并把滚动交还给外层滚动区域。"""
        event.ignore()


class MetricCard(SimpleCardWidget):
    """任务执行页使用的轻量统计卡片。"""

    def __init__(self, title: str, value: str = "-", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("metricCard")
        self.title_label = CaptionLabel(title)
        self.value_label = StrongBodyLabel(value)
        self.value_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        self.setMinimumHeight(78)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def setValue(self, value: str) -> None:
        """更新统计值文本。"""
        self.value_label.setText(value)


def create_section_card(title: str, subtitle: str | None = None) -> tuple[SimpleCardWidget, QVBoxLayout]:
    """创建页面通用内容卡片。

    返回卡片和内部纵向布局，调用方只需要继续往布局中添加业务控件。卡片内边距和标题
    间距在这里集中处理，避免各个页面重复写不一致的布局参数。
    """
    card = SimpleCardWidget()
    card.setObjectName("sectionCard")
    card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 16, 18, 16)
    layout.setSpacing(10)
    layout.addWidget(StrongBodyLabel(title))
    if subtitle:
        subtitle_label = CaptionLabel(subtitle)
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)
    return card, layout


def create_button_row(*buttons: QWidget) -> QWidget:
    """创建按钮行，让短按钮按内容自然显示。"""
    row_widget = QWidget()
    row_layout = QHBoxLayout(row_widget)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(8)
    for button in buttons:
        row_layout.addWidget(button)
    row_layout.addStretch(1)
    return row_widget


def create_labeled_spin(label: str, minimum: int, maximum: int, value: int) -> tuple[QWidget, NoWheelSpinBox]:
    """创建紧凑的“标签 + 数字输入框”参数行。"""
    row_widget = QWidget()
    row_layout = QHBoxLayout(row_widget)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(12)

    label_widget = BodyLabel(label)
    label_widget.setWordWrap(True)
    label_widget.setMinimumWidth(130)
    spin_box = NoWheelSpinBox()
    spin_box.setRange(minimum, maximum)
    spin_box.setValue(value)
    spin_box.setFixedWidth(108)

    row_layout.addWidget(label_widget, 1)
    row_layout.addWidget(spin_box, 0, Qt.AlignRight)
    return row_widget, spin_box


def create_path_card(title: str, path: str | Path, text: str = "打开位置") -> PushSettingCard:
    """创建只读路径展示卡片。

    路径不再使用输入框展示，因为这里不是可编辑内容；使用设置卡片可以明确表达
    “这是一个路径信息，并且右侧按钮用于打开位置”。
    """
    return PushSettingCard(
        text,
        FluentIcon.FOLDER,
        title,
        str(path),
    )


def create_text_pair(title: str, value: str = "-") -> tuple[QWidget, QLabel]:
    """创建状态详情里的“名称 + 值”文本行。"""
    row_widget = QWidget()
    row_layout = QHBoxLayout(row_widget)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(10)

    title_label = CaptionLabel(title)
    title_label.setFixedWidth(92)
    value_label = BodyLabel(value)
    value_label.setWordWrap(True)

    row_layout.addWidget(title_label)
    row_layout.addWidget(value_label, 1)
    return row_widget, value_label
