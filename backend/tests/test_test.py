import pytest

from common.text import html_to_text


@pytest.mark.parametrize(
    ("html", "expected"),
    [
        ("<p>Hello</p><p>world</p>", "Hello world"),  # blocks never glue words together
        ("<strong>Atlas</strong> Tech", "Atlas Tech"),  # inline tags add no space
        ("L&#x27;équipe", "L'équipe"),  # entities are decoded
        ("a<br>&nbsp;b", "a b"),  # <br> and non-breaking space
        ("  \n   text \n  ", "text"),  # stray whitespace
        ("<ul><li>Python</li><li>SQL</li></ul>", "Python SQL"),
        ("ok<script>alert(1)</script>", "ok"),  # script content is not text
        ("", ""),
        (None, ""),
    ],
)
def test_html_to_text(html, expected):
    assert html_to_text(html) == expected