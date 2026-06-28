from collections import deque
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from gmap_collector.parsers.website_info_parser import WebsiteInfo, extract_website_info


@dataclass(frozen=True)
class WebsiteCrawlRequest:
    """官网静态抓取请求。"""

    start_url: str
    max_depth: int
    max_pages: int = 30
    timeout_seconds: int = 15


@dataclass(frozen=True)
class WebsiteCrawlResult:
    """官网静态抓取结果。"""

    info: WebsiteInfo
    visited_urls: list[str]
    failed_urls: dict[str, str] = field(default_factory=dict)


class _LinkParser(HTMLParser):
    """从 HTML 中提取站内链接。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """收集 a 标签 href。"""
        if tag.lower() != "a":
            return
        for name, value in attrs:
            if name.lower() == "href" and value:
                self.hrefs.append(unescape(value).strip())


def crawl_website(
    request: WebsiteCrawlRequest,
    fetch_html=None,
) -> WebsiteCrawlResult:
    """按深度静态抓取官网页面，并合并联系方式与社媒信息。

    抓取范围限制在起始 URL 的主域名及其二级域名内。外部网站只作为社媒链接记录，
    不会继续递归访问，避免越界采集。
    """
    fetch = fetch_html or (lambda url: fetch_url_html(url, request.timeout_seconds))
    start_url = _normalize_page_url(request.start_url, request.start_url)
    root_domain = _registered_domain(urlsplit(start_url).netloc)
    queue = deque([(start_url, 0)])
    queued_urls = {start_url}
    visited_urls: list[str] = []
    failed_urls: dict[str, str] = {}
    collected_infos: list[WebsiteInfo] = []

    while queue and len(visited_urls) < request.max_pages:
        current_url, depth = queue.popleft()
        try:
            html = _fetch_with_timeout(fetch, current_url, request.timeout_seconds)
        except Exception as error:
            failed_urls[current_url] = str(error)
            continue

        visited_urls.append(current_url)
        collected_infos.append(extract_website_info(html, base_url=current_url))

        if depth >= request.max_depth:
            continue

        for href in _extract_links(html):
            next_url = _normalize_page_url(href, current_url)
            if not next_url or next_url in queued_urls:
                continue
            if _registered_domain(urlsplit(next_url).netloc) != root_domain:
                continue
            queued_urls.add(next_url)
            queue.append((next_url, depth + 1))

    return WebsiteCrawlResult(
        info=_merge_website_infos(collected_infos),
        visited_urls=visited_urls,
        failed_urls=failed_urls,
    )


def fetch_url_html(url: str, timeout_seconds: int) -> str:
    """使用标准库请求网页 HTML。

    当前函数作为静态抓取默认实现。后续如果需要更强的编码识别、重试或代理配置，
    可以在不影响解析器的情况下替换这一层。
    """
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
            )
        },
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        raw_content = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
    return raw_content.decode(charset, errors="replace")


def _fetch_with_timeout(fetch_html, url: str, timeout_seconds: int) -> str:
    """调用抓取函数，并兼容旧的单参数测试替身。"""
    try:
        return fetch_html(url, timeout_seconds)
    except TypeError as error:
        if _looks_like_arity_error(error):
            return fetch_html(url)
        raise


def _extract_links(html: str) -> list[str]:
    """提取页面中的链接。"""
    parser = _LinkParser()
    parser.feed(html)
    return parser.hrefs


def _looks_like_arity_error(error: TypeError) -> bool:
    """判断 TypeError 是否来自函数参数数量不匹配。"""
    message = str(error)
    return "positional argument" in message or "required positional" in message


def _normalize_page_url(href: str, base_url: str) -> str:
    """规范化待抓取页面 URL。"""
    href = unescape(href).strip()
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return ""
    absolute_url = urljoin(base_url, href)
    absolute_url = urldefrag(absolute_url).url
    parts = urlsplit(absolute_url)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return ""
    path = parts.path or "/"
    return urlunsplit((parts.scheme, parts.netloc.lower(), path, parts.query, ""))


def _registered_domain(host: str) -> str:
    """提取用于同主域判断的简化主域名。

    当前不引入额外依赖，采用最后两段域名作为主域名。对 `co.uk` 这类公共后缀并不完美，
    但能覆盖第一阶段的大部分商家官网；如果后续测试发现不足，再引入 `tldextract`。
    """
    host = host.lower().split(":", 1)[0].strip(".")
    parts = [part for part in host.split(".") if part]
    if len(parts) <= 2:
        return host
    return ".".join(parts[-2:])


def _merge_website_infos(infos: list[WebsiteInfo]) -> WebsiteInfo:
    """合并多个页面的官网提取结果。"""
    return WebsiteInfo(
        phones=_merge_lists(info.phones for info in infos),
        emails=_merge_lists(info.emails for info in infos),
        instagram=_merge_lists(info.instagram for info in infos),
        tiktok=_merge_lists(info.tiktok for info in infos),
        twitter_x=_merge_lists(info.twitter_x for info in infos),
        facebook=_merge_lists(info.facebook for info in infos),
        linkedin=_merge_lists(info.linkedin for info in infos),
        youtube=_merge_lists(info.youtube for info in infos),
        whatsapp=_merge_lists(info.whatsapp for info in infos),
        seo_keywords=_merge_lists(info.seo_keywords for info in infos),
    )


def _merge_lists(groups) -> list[str]:
    """按顺序合并多个列表并去重。"""
    merged: list[str] = []
    for values in groups:
        for value in values:
            if value and value not in merged:
                merged.append(value)
    return merged
