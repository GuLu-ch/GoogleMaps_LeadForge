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
    assert result.phones == ["+49 30 1234 5678"]
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


def test_extract_website_info_filters_noisy_phone_candidates_from_real_pages():
    """官网电话提取应保留真实号码，并过滤日期、编号、坐标、时间戳和价格表噪声。"""
    html = """
    <html>
      <body>
        <p>Phone: +358 18 32990</p>
        <p>Switchboard 018-32990</p>
        <p>Mobile +358 (18) 25 426 or 0457 530 1435</p>
        <a href="tel:3584573500596">Call mobile</a>
        <p>
          Noise:
          253084009781696, 19881205, 31.12.2027, 2004 2004,
          2023-02-21 1, 1976-2026, 20260628143942,
          26 0000000000 65535, 0000001367 00000,
          0652281-1, 68-4082-8, 08.00-18.0,
          20.23809523809, 595.32 841.9, 523 523 523 523,
          +1/400.331886, 14 155 150 120 115 185/6
        </p>
      </body>
    </html>
    """

    result = extract_website_info(html, base_url="https://example.ax")

    assert result.phones == [
        "+358 18 32990",
        "+358 (18) 25 426",
        "0457 530 1435",
        "3584573500596",
    ]


def test_extract_website_info_filters_script_and_short_random_email_noise():
    """官网邮箱提取应过滤脚本随机片段和一位本地名伪邮箱。"""
    html = """
    <html>
      <body>
        <p>Emails: info@hawe.ax Bil@hawe.ax BIL@HAWE.AX robin@bobil.ax</p>
        <p>Generated tokens: J@Pi.Kg d@K.YL 2@Ar.HU e@A.ZR F@Hn.zHqnN</p>
        <script>
          window.__noise = "Ò@z.OuMvT, another J@Pi.Kg, phone 1707907897577";
        </script>
      </body>
    </html>
    """

    result = extract_website_info(html, base_url="https://example.ax")

    assert result.emails == ["info@hawe.ax", "Bil@hawe.ax", "robin@bobil.ax"]
    assert result.phones == []


def test_extract_website_info_does_not_match_numbers_from_generic_links():
    """普通链接中的路径、查询参数或资源编号不应被当作官网电话。"""
    html = """
    <html>
      <body>
        <a href="/assets/31536000000/0000001367-00000.js">Asset</a>
        <a href="/calendar/2026-01-01">Calendar</a>
        <a href="https://example.com/page?y_source=394666980590841740">Tracking</a>
        <a href="tel:+493012345678">Call</a>
        <a href="mailto:sales@example-wrap.de?subject=Hello">Mail</a>
      </body>
    </html>
    """

    result = extract_website_info(html, base_url="https://example.com")

    assert result.phones == ["+493012345678"]
    assert result.emails == ["sales@example-wrap.de"]


def test_extract_website_info_deduplicates_international_and_local_phone_variants():
    """同一号码的国际写法、可选本地 0 写法和本地写法应只保留首次出现项。"""
    html = """
    <html>
      <body>
        <p>Tel +358 (0)18 25000</p>
        <p>Same number +3581825000</p>
        <p>Same local number 018 25000</p>
        <p>Mobile +358 457 350 0596</p>
        <p>Same mobile local 0457 350 0596</p>
      </body>
    </html>
    """

    result = extract_website_info(html, base_url="https://example.ax")

    assert result.phones == ["+358 (0)18 25000", "+358 457 350 0596"]
