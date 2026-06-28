from gmap_collector.parsers.website_info_parser import extract_website_info


def test_extract_website_info_collects_contacts_social_links_and_keywords():
    """官网解析器应从 HTML 中提取联系方式、社媒渠道和 SEO Keywords。"""
    html = """
    <html>
      <head>
        <meta name="keywords" content="car wrap, ppf, window tint">
      </head>
      <body>
        <a href="mailto:sales@example-wrap.de">sales@example-wrap.de</a>
        <p>Backup email: info@example-wrap.de</p>
        <p>Call us: +49 30 1234 5678</p>
        <a href="tel:+493012345678">+49 30 1234 5678</a>
        <a href="https://www.instagram.com/examplewrap/">Instagram</a>
        <a href="https://www.tiktok.com/@examplewrap">TikTok</a>
        <a href="https://x.com/examplewrap">X</a>
        <a href="https://www.facebook.com/examplewrap">Facebook</a>
        <a href="https://www.linkedin.com/company/example-wrap/">LinkedIn</a>
        <a href="https://www.youtube.com/@examplewrap">YouTube</a>
        <a href="https://wa.me/493012345678">WhatsApp</a>
      </body>
    </html>
    """

    result = extract_website_info(html, base_url="https://example-wrap.de")

    assert result.emails == ["sales@example-wrap.de", "info@example-wrap.de"]
    assert result.phones == ["+49 30 1234 5678", "+493012345678"]
    assert result.instagram == ["https://www.instagram.com/examplewrap/"]
    assert result.tiktok == ["https://www.tiktok.com/@examplewrap"]
    assert result.twitter_x == ["https://x.com/examplewrap"]
    assert result.facebook == ["https://www.facebook.com/examplewrap"]
    assert result.linkedin == ["https://www.linkedin.com/company/example-wrap/"]
    assert result.youtube == ["https://www.youtube.com/@examplewrap"]
    assert result.whatsapp == ["https://wa.me/493012345678"]
    assert result.seo_keywords == ["car wrap", "ppf", "window tint"]


def test_extract_website_info_filters_common_noise_and_deduplicates():
    """官网解析器应过滤示例邮箱、图片资源伪邮箱和重复社媒链接。"""
    html = """
    <html>
      <head>
        <meta name="Keywords" content=" wrap , wrap, detailing ">
      </head>
      <body>
        <p>support@example.com demo@test.com real@shop.co.uk real@shop.co.uk</p>
        <img src="/assets/icon@email.png">
        <a href="https://instagram.com/shop">Instagram</a>
        <a href="https://instagram.com/shop?utm_source=site">Instagram duplicate</a>
        <a href="/contact">Contact</a>
      </body>
    </html>
    """

    result = extract_website_info(html, base_url="https://shop.co.uk")

    assert result.emails == ["real@shop.co.uk"]
    assert result.instagram == ["https://instagram.com/shop"]
    assert result.seo_keywords == ["wrap", "detailing"]


def test_extract_website_info_returns_empty_lists_for_blank_html():
    """空 HTML 不应抛异常，应返回空结果。"""
    result = extract_website_info("", base_url="https://example.com")

    assert result.emails == []
    assert result.phones == []
    assert result.all_social_links() == []
    assert result.seo_keywords == []
