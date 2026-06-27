import re
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from urllib.parse import unquote, urljoin

from gmap_collector.common.models import BusinessRecord


GOOGLE_MAPS_BASE_URL = "https://www.google.com"
GOOGLE_MAPS_LINK_MARKERS = ("/maps/place/", "google.com/maps/place", "maps.google.")
WEBSITE_EXCLUDED_HOST_MARKERS = ("google.", "gstatic.", "googleusercontent.")


@dataclass
class _HtmlNode:
    """轻量 HTML 节点。

    解析器只需要读取标签名、属性、文本和子节点，使用标准库即可满足当前 DOM 兜底需求。
    """

    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list["_HtmlNode"] = field(default_factory=list)
    text_chunks: list[str] = field(default_factory=list)

    def text(self) -> str:
        """递归返回节点可见文本。"""
        parts = [*self.text_chunks]
        for child in self.children:
            child_text = child.text()
            if child_text:
                parts.append(child_text)
        return _clean_text(" ".join(parts))


class _DomParser(HTMLParser):
    """把 HTML 解析成当前模块够用的轻量树。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _HtmlNode("document")
        self._stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _HtmlNode(tag=tag, attrs={name: value or "" for name, value in attrs})
        self._stack[-1].children.append(node)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self._stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == tag:
                del self._stack[index:]
                return

    def handle_data(self, data: str) -> None:
        text = _clean_text(data)
        if text:
            self._stack[-1].text_chunks.append(text)


def parse_maps_list_results(html: str, source_keyword: str) -> list[BusinessRecord]:
    """解析 Google Maps 搜索结果列表。

    解析策略分两层：

    1. 优先解析 `role="article"` 的结果卡片。
    2. 如果页面结构变化导致没有卡片节点，则按 Google Maps 商家链接向上取可用节点兜底。

    某个字段在卡片中不存在时保留空字符串，不丢弃整条商家记录。
    """
    if not html.strip():
        return []

    parser = _DomParser()
    parser.feed(html)
    cards = _find_result_cards(parser.root)

    records: list[BusinessRecord] = []
    seen_urls: set[str] = set()
    for card in cards:
        record = _parse_card(card, source_keyword)
        if not record.google_maps_url or record.google_maps_url in seen_urls:
            continue
        seen_urls.add(record.google_maps_url)
        records.append(record)

    return records


def _find_result_cards(root: _HtmlNode) -> list[_HtmlNode]:
    """查找 Google Maps 搜索结果卡片。"""
    article_nodes = [node for node in _walk(root) if node.attrs.get("role") == "article"]
    if article_nodes:
        return article_nodes

    # 兜底：如果 Google 改掉 `role=article`，至少保留包含商家链接的父级节点。
    cards: list[_HtmlNode] = []
    for node in _walk(root):
        if node.tag == "a" and _is_google_maps_business_url(node.attrs.get("href", "")):
            cards.append(node)
    return cards


def _parse_card(card: _HtmlNode, source_keyword: str) -> BusinessRecord:
    """从单个结果卡片中解析商家字段。"""
    links = [node for node in _walk(card) if node.tag == "a" and node.attrs.get("href")]
    maps_link = _first_link(links, _is_google_maps_business_url)
    website_link = _first_link(links, _is_external_website_url)
    phone_link = _first_link(links, lambda href: href.startswith("tel:"))

    google_maps_url = _normalize_url(maps_link.attrs.get("href", "")) if maps_link else ""
    text_lines = _dedupe_keep_order(_collect_text_lines(card))
    aria_labels = _dedupe_keep_order(
        _clean_text(node.attrs.get("aria-label", ""))
        for node in _walk(card)
        if node.attrs.get("aria-label")
    )

    name = _extract_name(card, maps_link, google_maps_url)
    rating = _extract_rating(text_lines, aria_labels)
    review_count = _extract_review_count(text_lines, aria_labels)
    phone = _extract_phone(phone_link, text_lines)
    website = _normalize_url(website_link.attrs.get("href", "")) if website_link else ""
    category = _extract_category(text_lines, name)
    address = _extract_address(text_lines, name, category, rating, review_count, phone)

    return BusinessRecord(
        name=name,
        address=address,
        phone=phone,
        website=website,
        rating=rating,
        review_count=review_count,
        category=category,
        google_maps_url=google_maps_url,
        source_keyword=source_keyword,
    )


def _extract_name(card: _HtmlNode, maps_link: _HtmlNode | None, google_maps_url: str) -> str:
    """提取商家名称。"""
    if maps_link:
        link_text = maps_link.text()
        if link_text:
            return link_text

    for node in _walk(card):
        aria_label = _clean_text(node.attrs.get("aria-label", ""))
        if aria_label and not _looks_like_rating(aria_label) and not _looks_like_review_count(aria_label):
            return aria_label

    if "/maps/place/" in google_maps_url:
        raw_name = google_maps_url.split("/maps/place/", 1)[1].split("/", 1)[0]
        return _clean_text(unquote(raw_name.replace("+", " ")))

    return ""


def _extract_rating(text_lines: list[str], aria_labels: list[str]) -> str:
    """提取评分。"""
    for text in [*aria_labels, *text_lines]:
        match = re.search(r"([0-5](?:[.,]\d)?)\s*(?:stars?|星)", text, re.IGNORECASE)
        if match:
            return match.group(1).replace(",", ".")
    for text in text_lines:
        if re.fullmatch(r"[0-5](?:[.,]\d)?", text):
            return text.replace(",", ".")
    return ""


def _extract_review_count(text_lines: list[str], aria_labels: list[str]) -> str:
    """提取评论数量。"""
    for text in [*aria_labels, *text_lines]:
        match = re.search(r"([\d,.]+)\s*(?:reviews?|条评价|则评价|篇评价|Rezensionen)", text, re.IGNORECASE)
        if match:
            return _digits_only(match.group(1))
    for text in text_lines:
        match = re.fullmatch(r"\(?([\d,.]+)\)?", text)
        if match:
            return _digits_only(match.group(1))
    return ""


def _extract_phone(phone_link: _HtmlNode | None, text_lines: list[str]) -> str:
    """提取电话号码。"""
    if phone_link is not None:
        phone_text = phone_link.text()
        if phone_text:
            return phone_text
        return phone_link.attrs.get("href", "").removeprefix("tel:")

    for text in text_lines:
        if re.search(r"(?:\+\d{1,3}[\s-]?)?(?:\(?\d{2,5}\)?[\s/-]?){2,}\d", text):
            return text
    return ""


def _extract_category(text_lines: list[str], name: str) -> str:
    """提取商家分类。"""
    ignored = {name, "Website", "Directions", "Call", "Save", "Share"}
    for text in text_lines:
        if not text or text in ignored:
            continue
        if _looks_like_address(text) or _looks_like_phone(text) or _looks_like_rating(text) or _looks_like_review_count(text):
            continue
        if len(text) <= 80:
            return text
    return ""


def _extract_address(
    text_lines: list[str],
    name: str,
    category: str,
    rating: str,
    review_count: str,
    phone: str,
) -> str:
    """提取地址。"""
    ignored = {name, category, rating, review_count, phone, "Website", "Directions", "Call", "Save", "Share"}
    for text in text_lines:
        if text in ignored:
            continue
        if _looks_like_address(text):
            return text
    return ""


def _collect_text_lines(node: _HtmlNode) -> list[str]:
    """按节点粒度收集文本片段。"""
    lines: list[str] = []
    for current in _walk(node):
        # 这里只取当前节点的直接文本，避免把整张卡片的聚合文本误判为地址或分类。
        direct_text = _clean_text(" ".join(current.text_chunks))
        if direct_text:
            lines.append(direct_text)
    return lines


def _walk(node: _HtmlNode):
    """深度优先遍历节点。"""
    yield node
    for child in node.children:
        yield from _walk(child)


def _first_link(links: list[_HtmlNode], predicate) -> _HtmlNode | None:
    """返回第一个满足条件的链接节点。"""
    for link in links:
        href = link.attrs.get("href", "")
        if predicate(href):
            return link
    return None


def _is_google_maps_business_url(url: str) -> bool:
    """判断链接是否像 Google Maps 商家链接。"""
    return any(marker in url for marker in GOOGLE_MAPS_LINK_MARKERS)


def _is_external_website_url(url: str) -> bool:
    """判断链接是否像商家官网。"""
    if not url.startswith(("http://", "https://")):
        return False
    return not any(marker in url for marker in WEBSITE_EXCLUDED_HOST_MARKERS)


def _normalize_url(url: str) -> str:
    """规范化相对链接和 HTML 实体。"""
    return urljoin(GOOGLE_MAPS_BASE_URL, unescape(url))


def _clean_text(text: str) -> str:
    """清洗文本空白。"""
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _dedupe_keep_order(values) -> list[str]:
    """按出现顺序去重。"""
    result: list[str] = []
    for value in values:
        cleaned = _clean_text(str(value))
        if cleaned and cleaned not in result:
            result.append(cleaned)
    return result


def _digits_only(text: str) -> str:
    """只保留数字。"""
    return re.sub(r"\D", "", text)


def _looks_like_rating(text: str) -> bool:
    """判断文本是否像评分。"""
    return bool(re.search(r"[0-5](?:[.,]\d)?\s*(?:stars?|星)", text, re.IGNORECASE) or re.fullmatch(r"[0-5](?:[.,]\d)?", text))


def _looks_like_review_count(text: str) -> bool:
    """判断文本是否像评论数量。"""
    return bool(re.search(r"[\d,.]+\s*(?:reviews?|条评价|则评价|篇评价|Rezensionen)", text, re.IGNORECASE) or re.fullmatch(r"\(?[\d,.]+\)?", text))


def _looks_like_phone(text: str) -> bool:
    """判断文本是否像电话号码。"""
    return bool(re.search(r"(?:\+\d{1,3}[\s-]?)?(?:\(?\d{2,5}\)?[\s/-]?){2,}\d", text))


def _looks_like_address(text: str) -> bool:
    """判断文本是否像地址。"""
    address_markers = (
        "strasse",
        "straße",
        "street",
        "road",
        "avenue",
        "platz",
        "weg",
        "allee",
        "germany",
        "deutschland",
        ",",
    )
    lower_text = text.lower()
    return any(marker in lower_text for marker in address_markers) and bool(re.search(r"\d", text))
