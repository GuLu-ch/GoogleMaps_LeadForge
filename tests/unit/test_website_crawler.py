from gmap_collector.services.website_crawler import WebsiteCrawlRequest, crawl_website


def test_crawl_website_respects_depth_and_same_domain_scope():
    """官网抓取应按深度遍历同域页面，并忽略外部链接。"""
    pages = {
        "https://example.com/": """
            <html>
              <head><meta name="keywords" content="wrap, ppf"></head>
              <body>
                <a href="/contact">Contact</a>
                <a href="https://external.com/contact">External</a>
                <a href="mailto:info@example.com">noise@example.com</a>
              </body>
            </html>
        """,
        "https://example.com/contact": """
            <html>
              <body>
                <p>Email: sales@example-wrap.de</p>
                <a href="https://www.instagram.com/examplewrap">Instagram</a>
                <a href="/deep">Deep</a>
              </body>
            </html>
        """,
        "https://example.com/deep": """
            <html><body><p>Deep phone +49 30 9999 0000</p></body></html>
        """,
    }
    fetched_urls: list[str] = []

    def fake_fetch(url: str) -> str:
        fetched_urls.append(url)
        return pages[url]

    result = crawl_website(
        WebsiteCrawlRequest(start_url="https://example.com", max_depth=1, max_pages=10),
        fetch_html=fake_fetch,
    )

    assert fetched_urls == ["https://example.com/", "https://example.com/contact"]
    assert result.visited_urls == ["https://example.com/", "https://example.com/contact"]
    assert result.info.emails == ["sales@example-wrap.de"]
    assert result.info.instagram == ["https://www.instagram.com/examplewrap"]
    assert result.info.phones == []
    assert result.info.seo_keywords == ["wrap", "ppf"]


def test_crawl_website_allows_subdomains_and_merges_page_results():
    """官网抓取应允许同主域名的二级域名，并合并多页提取结果。"""
    pages = {
        "https://example.com/": """
            <html>
              <body>
                <p>Main phone +49 30 1234 5678</p>
                <a href="https://contact.example.com/team">Team</a>
              </body>
            </html>
        """,
        "https://contact.example.com/team": """
            <html>
              <body>
                <p>team@example-wrap.de</p>
                <a href="https://www.linkedin.com/company/example-wrap">LinkedIn</a>
                <a href="https://www.youtube.com/@examplewrap">YouTube</a>
                <a href="https://wa.me/493012345678">WhatsApp</a>
              </body>
            </html>
        """,
    }

    result = crawl_website(
        WebsiteCrawlRequest(start_url="https://example.com", max_depth=2, max_pages=10),
        fetch_html=lambda url: pages[url],
    )

    assert result.visited_urls == ["https://example.com/", "https://contact.example.com/team"]
    assert result.info.phones == ["+49 30 1234 5678"]
    assert result.info.emails == ["team@example-wrap.de"]
    assert result.info.linkedin == ["https://www.linkedin.com/company/example-wrap"]
    assert result.info.youtube == ["https://www.youtube.com/@examplewrap"]
    assert result.info.whatsapp == ["https://wa.me/493012345678"]


def test_crawl_website_records_fetch_failures_and_continues_other_pages():
    """单个页面请求失败时，应记录失败并继续处理其它已发现页面。"""
    pages = {
        "https://example.com/": """
            <html>
              <body>
                <a href="/broken">Broken</a>
                <a href="/ok">OK</a>
              </body>
            </html>
        """,
        "https://example.com/ok": "<html><body>ok@example-wrap.de</body></html>",
    }

    def fake_fetch(url: str) -> str:
        if url.endswith("/broken"):
            raise TimeoutError("请求超时")
        return pages[url]

    result = crawl_website(
        WebsiteCrawlRequest(start_url="https://example.com", max_depth=1, max_pages=10),
        fetch_html=fake_fetch,
    )

    assert result.visited_urls == ["https://example.com/", "https://example.com/ok"]
    assert result.failed_urls == {"https://example.com/broken": "请求超时"}
    assert result.info.emails == ["ok@example-wrap.de"]


def test_crawl_website_passes_timeout_to_fetch_function():
    """官网抓取应把请求超时配置传递给实际请求函数。"""
    received_timeouts: list[int] = []

    def fake_fetch(url: str, timeout_seconds: int) -> str:
        received_timeouts.append(timeout_seconds)
        return "<html><body>sales@example-wrap.de</body></html>"

    result = crawl_website(
        WebsiteCrawlRequest(start_url="https://example.com", max_depth=0, max_pages=1, timeout_seconds=4),
        fetch_html=fake_fetch,
    )

    assert received_timeouts == [4]
    assert result.info.emails == ["sales@example-wrap.de"]
