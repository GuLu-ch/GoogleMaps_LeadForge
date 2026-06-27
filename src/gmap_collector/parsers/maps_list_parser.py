from gmap_collector.common.models import BusinessRecord


def parse_maps_list_results(html: str, source_keyword: str) -> list[BusinessRecord]:
    """解析 Google Maps 搜索结果列表。

    当前阶段不写死任何 DOM 选择器。后续打开实际 Google Maps 页面后，如果自动定位不稳定，
    需要按用户要求暂停并请用户协助确认元素。
    """
    if not html.strip():
        return []

    return []
