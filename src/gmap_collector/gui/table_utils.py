from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget


def apply_mixed_table_resize(
    table: QTableWidget,
    stretch_columns: set[int],
    column_widths: dict[int, int] | None = None,
    default_width: int = 120,
) -> None:
    """应用可拖拽列宽和拉伸列混合的表格宽度策略。

    常规字段给出合理默认宽度并允许用户手动拖拽，长文本字段使用拉伸列吃掉剩余空间。
    当表格内容超过可视区域时，水平和垂直滚动条会自动出现，方便后续查看大量数据。
    """
    column_widths = column_widths or {}
    header = table.horizontalHeader()
    header.setSectionsMovable(False)
    header.setStretchLastSection(False)
    header.setDefaultSectionSize(default_width)

    for column_index in range(table.columnCount()):
        if column_index in stretch_columns:
            header.setSectionResizeMode(column_index, QHeaderView.Stretch)
        else:
            header.setSectionResizeMode(column_index, QHeaderView.Interactive)
            table.setColumnWidth(column_index, column_widths.get(column_index, default_width))

    table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setWordWrap(False)
