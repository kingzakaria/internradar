"""Small text helpers shared by the pipeline."""

from __future__ import annotations

import re
from html.parser import HTMLParser

# Tags that start a new block: a space is inserted so words never glue together.
# Inline tags (<strong>, <em>, <span>, <a>...) add nothing: "<b>Atlas</b> Tech" stays "Atlas Tech".
BLOCK_TAGS = {
    "p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6",
    "tr", "td", "th", "table", "section", "article",
}
SKIP_TAGS = {"script", "style"}  # their content is code, not text


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)  # &#x27; -> ', &nbsp; -> non-breaking space
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in SKIP_TAGS:
            self._skip += 1
        elif tag in BLOCK_TAGS:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP_TAGS:
            self._skip = max(0, self._skip - 1)
        elif tag in BLOCK_TAGS:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.parts.append(data)

def clean(text: str | None) -> str | None:
    """Strip and collapse whitespace; empty text becomes None."""
    if text is None:
        return None
    text = re.sub(r"\s+", " ", text).strip()
    return text or None

def html_to_text(html: str | None) -> str:
    """Strip tags, decode entities, collapse every run of whitespace into one space."""
    if not html:
        return ""
    parser = _TextExtractor()
    parser.feed(html)
    parser.close()
    return re.sub(r"\s+", " ", "".join(parser.parts)).strip()