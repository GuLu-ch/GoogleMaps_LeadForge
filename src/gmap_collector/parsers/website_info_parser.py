import re
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from urllib.parse import parse_qsl, unquote, urlencode, urljoin, urlsplit, urlunsplit


EMAIL_PATTERN = re.compile(
    r"(?<![A-Za-z0-9.!#$%&'*+/=?^_`{|}~-])"
    r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,24}"
    r"(?![A-Za-z0-9.-])",
    re.ASCII,
)
INTERNATIONAL_PHONE_PATTERN = re.compile(r"(?<![\w@])(?:\+|00)\s*\d{1,3}(?:[\s().-]*\d){5,14}(?![\w@])")
LOCAL_TRUNK_PHONE_PATTERN = re.compile(r"(?<![\w@])0\d{1,4}(?:[\s().-]*\d){5,10}(?![\w@])")
GROUPED_LOCAL_PHONE_PATTERN = re.compile(r"(?<![\w@])\d{2,4}[\s-]\d{3,6}(?:[\s-]\d{2,5}){0,2}(?![\w@])")
BARE_CONTEXT_PHONE_PATTERN = re.compile(r"(?<![\w@])\d{7,10}(?![\w@])")
NOISE_EMAIL_DOMAINS = {"example.com", "test.com", "example.org", "example.net", "domain.com", "yourdomain.com"}
NOISE_EMAIL_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js"}
IGNORED_TEXT_TAGS = {"script", "style", "noscript", "svg", "canvas"}
PHONE_CONTEXT_WORDS = (
    "phone",
    "tel",
    "telephone",
    "mobile",
    "call",
    "fax",
    "contact",
    "kontakt",
    "telefon",
    "puhelin",
    "puh",
    "gsm",
    "mob",
    "växel",
    "vaxel",
    "ring",
    "kundservice",
    "asiakaspalvelu",
    "whatsapp",
)
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
    mailto_hrefs: list[str] = field(default_factory=list)
    tel_hrefs: list[str] = field(default_factory=list)
    meta_keywords: list[str] = field(default_factory=list)


class _WebsiteHtmlParser(HTMLParser):
    """扫描官网 HTML，提取文本、链接和 meta keywords。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.result = _HtmlScanResult()
        self._ignored_text_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """收集链接和 SEO Keywords。"""
        tag_name = tag.lower()
        if tag_name in IGNORED_TEXT_TAGS:
            self._ignored_text_depth += 1
            return
        attr_map = {name.lower(): value or "" for name, value in attrs}
        if tag_name == "a" and attr_map.get("href"):
            href = unescape(attr_map["href"]).strip()
            self.result.hrefs.append(href)
            href_lower = href.lower()
            if href_lower.startswith("mailto:"):
                self.result.mailto_hrefs.append(href)
            elif href_lower.startswith("tel:"):
                self.result.tel_hrefs.append(href)
        if tag_name == "meta" and attr_map.get("name", "").lower() == "keywords":
            self.result.meta_keywords.append(unescape(attr_map.get("content", "")))

    def handle_endtag(self, tag: str) -> None:
        """离开脚本、样式等标签后恢复正文采集。"""
        if tag.lower() in IGNORED_TEXT_TAGS and self._ignored_text_depth > 0:
            self._ignored_text_depth -= 1

    def handle_data(self, data: str) -> None:
        """收集可见文本片段。"""
        if self._ignored_text_depth:
            return
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
    searchable_text = "\n".join(scan_result.text_chunks)

    emails = _extract_emails(searchable_text, scan_result.mailto_hrefs)
    phones = _extract_phones(searchable_text, scan_result.tel_hrefs)
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


def _extract_emails(text: str, mailto_hrefs: list[str] | None = None) -> list[str]:
    """提取邮箱，并过滤示例域名、静态资源和脚本压缩片段中的伪邮箱。"""
    emails: list[str] = []
    seen_emails: set[str] = set()
    search_sources = [text, *(_mailto_payload(href) for href in (mailto_hrefs or []))]
    for source_text in search_sources:
        for match in EMAIL_PATTERN.finditer(source_text):
            email = match.group(0).strip(".,;:()[]{}<>\"'")
            lower_email = email.lower()
            if lower_email in seen_emails or not _is_valid_email(email):
                continue
            seen_emails.add(lower_email)
            emails.append(email)
    return emails


def _extract_phones(text: str, tel_hrefs: list[str] | None = None) -> list[str]:
    """提取电话并按数字指纹去重。

    电话只从可见正文和 `tel:` 链接提取，普通 URL 中的资源编号、跟踪参数和社媒数字路径
    不进入电话候选，避免把脚本时间戳、坐标和构建产物编号写入官网电话字段。
    """
    phones: list[str] = []
    seen_digits: set[str] = set()

    for candidate, has_context in _iter_text_phone_candidates(text):
        _append_phone_if_valid(phones, seen_digits, candidate, source="text", has_context=has_context)

    for href in tel_hrefs or []:
        for candidate in _tel_payloads(href):
            _append_phone_if_valid(phones, seen_digits, candidate, source="tel", has_context=True)
    return phones


def _append_phone_if_valid(
    phones: list[str],
    seen_digits: set[str],
    candidate: str,
    source: str,
    has_context: bool,
) -> None:
    """校验电话候选并按数字串去重。"""
    phone = _clean_phone(candidate)
    fingerprints = _phone_fingerprints(phone)
    if not fingerprints or seen_digits.intersection(fingerprints):
        return
    if not _is_valid_phone(phone, source=source, has_context=has_context):
        return
    seen_digits.update(fingerprints)
    phones.append(phone)


def _iter_text_phone_candidates(text: str):
    """按行生成正文中的电话候选，保留候选所在行的电话上下文信号。"""
    for line in text.splitlines():
        cleaned_line = _clean_text(line)
        if not cleaned_line:
            continue
        has_context = _line_has_phone_context(cleaned_line)
        number_table = _line_looks_like_number_table(cleaned_line)
        matches: list[tuple[int, int, int, str]] = []

        for priority, pattern in ((0, INTERNATIONAL_PHONE_PATTERN), (1, LOCAL_TRUNK_PHONE_PATTERN)):
            matches.extend((match.start(), match.end(), priority, match.group(0)) for match in pattern.finditer(cleaned_line))

        if has_context or not number_table:
            matches.extend(
                (match.start(), match.end(), 2, match.group(0))
                for match in GROUPED_LOCAL_PHONE_PATTERN.finditer(cleaned_line)
            )

        if has_context:
            matches.extend(
                (match.start(), match.end(), 3, match.group(0))
                for match in BARE_CONTEXT_PHONE_PATTERN.finditer(cleaned_line)
            )

        for _, _, _, candidate in _select_non_overlapping_phone_matches(matches):
            yield candidate, has_context


def _select_non_overlapping_phone_matches(matches: list[tuple[int, int, int, str]]) -> list[tuple[int, int, int, str]]:
    """同一文本片段被多条电话正则命中时，只保留最长且优先级最高的候选。"""
    selected: list[tuple[int, int, int, str]] = []
    occupied: list[tuple[int, int]] = []
    for start, end, priority, candidate in sorted(matches, key=lambda item: (item[2], item[0], -(item[1] - item[0]))):
        if any(start < used_end and end > used_start for used_start, used_end in occupied):
            continue
        selected.append((start, end, priority, candidate))
        occupied.append((start, end))
    return sorted(selected, key=lambda item: item[0])


def _is_valid_email(email: str) -> bool:
    """校验邮箱候选，过滤随机脚本片段和明显非业务邮箱。"""
    lower_email = email.lower()
    local_part, domain = lower_email.rsplit("@", 1)
    labels = domain.split(".")
    tld = labels[-1]
    if len(local_part) < 2:
        return False
    if local_part.startswith(".") or local_part.endswith(".") or ".." in local_part:
        return False
    if domain in NOISE_EMAIL_DOMAINS:
        return False
    if any(lower_email.endswith(extension) for extension in NOISE_EMAIL_EXTENSIONS):
        return False
    if not all(label and not label.startswith("-") and not label.endswith("-") for label in labels):
        return False
    return tld.isalpha() and 2 <= len(tld) <= 24


def _is_valid_phone(phone: str, source: str, has_context: bool) -> bool:
    """校验电话候选，过滤日期、时间、编号、坐标、时间戳和数字表噪声。"""
    digits = re.sub(r"\D", "", phone)
    if not 7 <= len(digits) <= 15:
        return False
    if _looks_like_date_or_year(phone):
        return False
    if _looks_like_time_range(phone):
        return False
    if _looks_like_decimal_noise(phone):
        return False
    if _looks_like_identifier(phone, source=source, has_context=has_context):
        return False
    if _has_bad_phone_group_shape(phone):
        return False
    if re.search(r"0{6,}", digits):
        return False
    if _starts_with_emergency_code(phone):
        return False
    if source != "tel" and not _has_phone_signal(phone, has_context):
        return False
    return True


def _has_phone_signal(phone: str, has_context: bool) -> bool:
    """判断正文电话候选是否具备足够的电话形态信号。"""
    stripped = phone.strip()
    if stripped.startswith("+"):
        return True
    if stripped.startswith("00"):
        return has_context or _has_phone_separator(stripped)
    if stripped.startswith("0"):
        return has_context or _has_phone_separator(stripped)
    return _has_phone_separator(stripped)


def _phone_fingerprints(phone: str) -> set[str]:
    """生成电话去重指纹，兼容国际区号、可选本地 0 和本地写法。"""
    digits = re.sub(r"\D", "", phone)
    if not digits:
        return set()

    fingerprints = {digits}
    normalized_digits = digits
    if phone.strip().startswith("+") and normalized_digits.startswith("358"):
        local_digits = normalized_digits[3:]
        fingerprints.add(local_digits)
        fingerprints.add(f"0{local_digits}")
        if local_digits.startswith("0"):
            fingerprints.add(local_digits[1:])
    elif normalized_digits.startswith("00358"):
        local_digits = normalized_digits[5:]
        fingerprints.add(local_digits)
        fingerprints.add(f"0{local_digits}")
        if local_digits.startswith("0"):
            fingerprints.add(local_digits[1:])
    elif normalized_digits.startswith("358") and len(normalized_digits) >= 10:
        local_digits = normalized_digits[3:]
        fingerprints.add(local_digits)
        fingerprints.add(f"0{local_digits}")
        if local_digits.startswith("0"):
            fingerprints.add(local_digits[1:])
    elif normalized_digits.startswith("0"):
        fingerprints.add(normalized_digits[1:])
    return {fingerprint for fingerprint in fingerprints if fingerprint}


def _has_phone_separator(phone: str) -> bool:
    """判断候选是否包含常见电话分隔符。"""
    return bool(re.search(r"\d[\s().-]+\d", phone))


def _compact_phone_candidate(phone: str) -> str:
    """压缩电话候选内部空白，方便噪声规则做全量匹配。"""
    return re.sub(r"\s+", " ", phone).strip()


def _looks_like_date_or_year(phone: str) -> bool:
    """过滤日期、年份区间和年月日时间戳。"""
    normalized = _compact_phone_candidate(phone)
    digits = re.sub(r"\D", "", normalized)
    groups = re.findall(r"\d+", normalized)
    if re.fullmatch(r"\d{1,2}[./]\d{1,2}[./]\d{2,4}", normalized):
        return True
    if re.fullmatch(r"(?:18|19|20)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}(?:\s+\d)?", normalized):
        return True
    if re.fullmatch(r"(?:18|19|20)\d{2}\s*[-–]\s*(?:18|19|20)\d{2}", normalized):
        return True
    if len(groups) == 2 and all(re.fullmatch(r"(?:18|19|20)\d{2}", group) for group in groups):
        return True
    if len(digits) == 8 and _is_yyyymmdd(digits):
        return True
    if len(digits) == 14 and _is_yyyymmdd(digits[:8]):
        return True
    return False


def _looks_like_time_range(phone: str) -> bool:
    """过滤营业时间范围，例如 08.00-18.0。"""
    return bool(re.fullmatch(r"\d{1,2}[.:]\d{1,2}\s*[-–]\s*\d{1,2}[.:]\d{1,2}", _compact_phone_candidate(phone)))


def _looks_like_decimal_noise(phone: str) -> bool:
    """过滤坐标、小数和 CSS/脚本生成的浮点数。"""
    normalized = _compact_phone_candidate(phone)
    if re.search(r"[+-]?\d+/\d+\.\d+", normalized):
        return True
    if re.search(r"\d+\.\d{4,}", normalized):
        return True
    return bool(re.search(r"\d+\.\d+\s+\d+\.\d+", normalized))


def _looks_like_identifier(phone: str, source: str, has_context: bool) -> bool:
    """过滤工商编号、构建编号和无上下文长数字 ID。"""
    normalized = _compact_phone_candidate(phone)
    digits = re.sub(r"\D", "", normalized)
    has_prefix = normalized.startswith("+") or normalized.startswith("00")
    if re.fullmatch(r"\d{6,8}-\d", normalized):
        return True
    if re.fullmatch(r"\d{2,4}-\d{3,5}-\d", normalized):
        return True
    if source != "tel" and not has_context and not has_prefix and not _has_phone_separator(normalized):
        return True
    if source != "tel" and not has_context and normalized.startswith("00") and not _has_phone_separator(normalized):
        return True
    if source != "tel" and not has_prefix and not _has_phone_separator(normalized) and len(digits) > 10:
        return True
    return False


def _has_bad_phone_group_shape(phone: str) -> bool:
    """过滤明显不像电话号码的数字分组。"""
    normalized = _compact_phone_candidate(phone)
    groups = re.findall(r"\d+", normalized)
    if len(groups) > 5:
        return True
    if len(groups) >= 4 and len(set(groups)) == 1:
        return True
    for index, group in enumerate(groups):
        if len(group) != 1:
            continue
        is_country_code_one = index == 0 and normalized.startswith("+1")
        is_optional_trunk_zero = group == "0" and "(0)" in normalized
        if not is_country_code_one and not is_optional_trunk_zero:
            return True
    return False


def _starts_with_emergency_code(phone: str) -> bool:
    """过滤把紧急号码和后续数字拼成的伪电话。"""
    stripped = phone.strip()
    groups = re.findall(r"\d+", stripped)
    if stripped.startswith("+") or stripped.startswith("00") or not groups:
        return False
    return groups[0] in {"112", "911", "999"}


def _line_has_phone_context(line: str) -> bool:
    """判断文本行是否包含电话字段上下文。"""
    lower_line = line.lower()
    return any(word in lower_line for word in PHONE_CONTEXT_WORDS)


def _line_looks_like_number_table(line: str) -> bool:
    """判断文本行是否像尺寸、价格或脚本数字表。"""
    numeric_groups = re.findall(r"\b\d{1,4}\b", line)
    return len(numeric_groups) >= 6


def _is_yyyymmdd(digits: str) -> bool:
    """判断 8 位数字是否是年月日。"""
    try:
        year = int(digits[:4])
        month = int(digits[4:6])
        day = int(digits[6:8])
    except ValueError:
        return False
    return 1800 <= year <= 2099 and 1 <= month <= 12 and 1 <= day <= 31


def _mailto_payload(href: str) -> str:
    """提取 mailto 链接中的邮箱主体。"""
    payload = unescape(href).strip()[len("mailto:") :]
    return unquote(payload.split("?", 1)[0])


def _tel_payloads(href: str) -> list[str]:
    """提取 tel 链接中的电话主体，兼容分号参数。"""
    payload = unescape(href).strip()[len("tel:") :]
    payload = unquote(payload.split("?", 1)[0].split("#", 1)[0])
    payload = payload.split(";", 1)[0]
    return [part for part in re.split(r"\s*,\s*", payload) if part]


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
