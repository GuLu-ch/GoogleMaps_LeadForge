from dataclasses import dataclass


@dataclass(frozen=True)
class BusinessRecord:
    """解析层传给存储层的商家记录。

    `source_keyword` 是用户输入的行业关键词，不是完整搜索词。完整搜索词可能包含城市、
    地区和逗号，放进逗号分隔字段会产生歧义；完整搜索词由命中关系表保存。
    """

    name: str
    address: str
    phone: str
    website: str
    rating: str
    review_count: str
    category: str
    google_maps_url: str
    source_keyword: str
