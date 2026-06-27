from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget
from qfluentwidgets import ScrollArea


def build_adaptive_page(parent: QWidget) -> tuple[QVBoxLayout, QWidget, QVBoxLayout]:
    """创建带页面级滚动区域的自适应页面骨架。

    返回值依次为页面根布局、滚动内容容器、滚动内容布局。页面底部的关键操作按钮
    应继续添加到根布局中，这样窗口变矮时按钮不会被滚动内容挤出可视范围。
    """
    root_layout = QVBoxLayout(parent)
    root_layout.setContentsMargins(24, 20, 24, 18)
    root_layout.setSpacing(14)

    scroll_area = ScrollArea(parent)
    scroll_area.setObjectName("pageScrollArea")
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(ScrollArea.NoFrame)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    content_widget = QWidget()
    content_widget.setObjectName("pageScrollContent")
    content_layout = QVBoxLayout(content_widget)
    content_layout.setContentsMargins(0, 0, 0, 0)
    content_layout.setSpacing(14)
    content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)

    scroll_area.setWidget(content_widget)
    root_layout.addWidget(scroll_area, 1)

    return root_layout, content_widget, content_layout


def build_action_bar(parent_layout: QVBoxLayout) -> QHBoxLayout:
    """创建固定在页面底部的操作栏布局。"""
    action_layout = QHBoxLayout()
    action_layout.setContentsMargins(0, 0, 0, 0)
    action_layout.setSpacing(8)
    parent_layout.addLayout(action_layout)
    return action_layout
