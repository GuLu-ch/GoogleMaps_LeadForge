import re
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit


EMAIL_PATTERN = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")
PHONE_PATTERN = re.compile(r"(?:\+\d{1,3}[\s()./-]?)?(?:\(?\d{2,5}\)?[\s()./-]?){2,}\d")
NOISE_EMAIL_DOMAINS = {"example.com", "test.com", "example.org", "example.net", "domain.com", "yourdomain.com"}
NOISE_EMAIL_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js"}
TRACKING_QUERY_PREFIXES = ("utm_",)
TRACKING_QUERY_NAMES = {"fbclid", "gclid", "mc_cid", "mc_eid"}


@dataclass(frozen=True)
class WebsiteInfo:
    """官网信息提取结果。

    所有字段都使用列表保存，便于保留同一网站中出现的多个邮箱、电话或社媒账号。
    后续写入 SQLite 时再按项目规则合并为逗号分隔字符串。
    """

    phones: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    instagram: list[str] = field(default_factory=list)
    tiktok: list[str] = field(default_factory=list)
    twitter_x: list[str] = field(default_factory=list)
    facebook: list[str] = field(default_factory=list)
    linkedin: list[str] = field(default_factory=list)
    youtube: list[str] = field(default_factory=list)
    whatsapp: list[str] = field(default_factory=list)
    seo_keywords: list[str] = field(default_factory=list)

    def all_social_links(self) -> list[str]:
        """返回全部社媒链接，保持字段顺序。"""
        return [
            *self.instagram,
            *self.tiktok,
            *self.twitter_x,
            *self.facebook,
            *self.linkedin,
            *self.youtube,
            *self.whatsapp,
        ]


@dataclass
class _HtmlScanResult:
    """HTML 扫描阶段收集到的结构化信息。"""

    text_chunks: list[str] = field(default_factory=list)
    hrefs: list[str] = field(default_factory=list)
    meta_keywords: list[str] = field(default_factory=list)


class _WebsiteHtmlParser(HTMLParser):
    """扫描官网 HTML，提取文本、链接和 meta keywords。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.result = _HtmlScanResult()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """收集链接和 SEO Keywords。"""
        attr_map = {name.lower(): value or "" for name, value in attrs}
        if tag.lower() == "a" and attr_map.get("href"):
            self.result.hrefs.append(unescape(attr_map["href"]).strip())
        if tag.lower() == "meta" and attr_map.get("name", "").lower() == "keywords":
            self.result.meta_keywords.append(unescape(attr_map.get("content", "")))

    def handle_data(self, data: str) -> None:
        """收集可见文本片段。"""
        cleaned = _clean_text(data)
        if cleaned:
            self.result.text_chunks.append(cleaned)


def extract_website_info(html: str, base_url: str) -> WebsiteInfo:
    """从官网 HTML 中提取联系方式、社媒链接和 SEO Keywords。

    该函数只处理已经获取到的 HTML，不负责网络请求。这样 Requests 抓取、浏览器兜底
    和单元测试都能复用同一套解析逻辑。
    """
    if not html.strip():
        return WebsiteInfo()

    parser = _WebsiteHtmlParser()
    parser.feed(html)
    scan_result = parser.result
    searchable_text = "\n".join([*scan_result.text_chunks, *scan_result.hrefs])

    emails = _extract_emails(searchable_text)
    phones = _extract_phones(searchable_text)
    social_links = _extract_social_links(scan_result.hrefs, base_url)
    seo_keywords = _extract_seo_keywords(scan_result.meta_keywords)

    return WebsiteInfo(
        phones=phones,
        emails=emails,
        instagram=social_links["instagram"],
        tiktok=social_links["tiktok"],
        twitter_x=social_links["twitter_x"],
        facebook=social_links["facebook"],
        linkedin=social_links["linkedin"],
        youtube=social_links["youtube"],
        whatsapp=social_links["whatsapp"],
        seo_keywords=seo_keywords,
    )


def _extract_emails(text: str) -> list[str]:
    """提取邮箱，并过滤示例域名和静态资源伪邮箱。"""
    emails: list[str] = []
    for match in EMAIL_PATTERN.finditer(text):
        email = match.group(0).strip(".,;:()[]{}<>\"'")
        lower_email = email.lower()
        domain = lower_email.rsplit("@", 1)[-1]
        if domain in NOISE_EMAIL_DOMAINS:
            continue
        if any(lower_email.endswith(extension) for extension in NOISE_EMAIL_EXTENSIONS):
            continue
        if email not in emails:
            emails.append(email)
    return emails


def _extract_phones(text: str) -> list[str]:
    """提取电话并按出现顺序去重。"""
    # 社媒链接中可能包含纯数字路径，例如 `wa.me/4930...`。这些链接应归入
    # WhatsApp 字段，不应作为普通电话重复写入。
    text_without_http_links = re.sub(r"https?://\S+", " ", text)
    phones: list[str] = []
    for match in PHONE_PATTERN.finditer(text_without_http_links):
        phone = _clean_phone(match.group(0))
        digit_count = len(re.sub(r"\D", "", phone))
        if digit_count < 7:
            continue
        if phone not in phones:
            phones.append(phone)
    return phones


def _extract_social_links(hrefs: list[str], base_url: str) -> dict[str, list[str]]:
    """按社媒平台提取链接。"""
    result = {
        "instagram": [],
        "tiktok": [],
        "twitter_x": [],
        "facebook": [],
        "linkedin": [],
        "youtube": [],
        "whatsapp": [],
    }
    for href in hrefs:
        normalized_url = _normalize_url(href, base_url)
        if not normalized_url:
            continue
        host = urlsplit(normalized_url).netloc.lower()
        platform = _social_platform(host)
        if platform is None:
            continue
        if normalized_url not in result[platform]:
            result[platform].append(normalized_url)
    return result


def _extract_seo_keywords(meta_keywords: list[str]) -> list[str]:
    """提取并去重 SEO Keywords。"""
    keywords: list[str] = []
    for content in meta_keywords:
        for keyword in content.split(","):
            cleaned = _clean_text(keyword)
            if cleaned and cleaned not in keywords:
                keywords.append(cleaned)
    return keywords


def _social_platform(host: str) -> str | None:
    """根据域名判断社媒平台。"""
    if host.endswith("instagram.com"):
        return "instagram"
    if host.endswith("tiktok.com"):
        return "tiktok"
    if host.endswith("twitter.com") or host.endswith("x.com"):
        return "twitter_x"
    if host.endswith("facebook.com") or host.endswith("fb.com"):
        return "facebook"
    if host.endswith("linkedin.com"):
        return "linkedin"
    if host.endswith("youtube.com") or host.endswith("youtu.be"):
        return "youtube"
    if host.endswith("wa.me") or host.endswith("whatsapp.com"):
        return "whatsapp"
    return None


def _normalize_url(href: str, base_url: str) -> str:
    """规范化链接并移除常见跟踪参数。"""
    href = unescape(href).strip()
    if not href or href.startswith(("#", "javascript:")):
        return ""
    absolute_url = urljoin(base_url, href)
    parts = urlsplit(absolute_url)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return ""
    query_items = [
        (name, value)
        for name, value in parse_qsl(parts.query, keep_blank_values=True)
        if not name.lower().startswith(TRACKING_QUERY_PREFIXES) and name.lower() not in TRACKING_QUERY_NAMES
    ]
    query = urlencode(query_items, doseq=True)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))


def _clean_text(text: str) -> str:
    """清洗文本空白。"""
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _clean_phone(phone: str) -> str:
    """清洗电话两侧标点和空白。"""
    return re.sub(r"\s+", " ", phone).strip(" .,:;()[]{}<>\"'")
