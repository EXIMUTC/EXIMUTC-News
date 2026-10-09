import pathlib
import unittest
from html.parser import HTMLParser
from urllib.parse import urlparse

PAGE = pathlib.Path(__file__).resolve().parents[1] / "docs" / "links" / "index.html"
REQUIRED = {
    "https://eximutc.com/",
    "https://www.instagram.com/eximutcgems/",
    "https://t.me/eximutc",
    "https://whatsapp.com/channel/0029Vb8SvzRCsU9VRLDFf01P",
    "https://ig.me/m/eximutcgems",
}


class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = set()

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.add(dict(attrs).get("href"))


class ContactLinksTest(unittest.TestCase):
    def test_five_real_external_html_anchors_exist(self):
        text = PAGE.read_text(encoding="utf-8")
        parser = AnchorParser()
        parser.feed(text)
        self.assertEqual(parser.links, REQUIRED)
        self.assertTrue(all(urlparse(u).scheme == "https" for u in parser.links))
        self.assertIn('href="https://news.eximutc.com/links/"', text)

    def test_not_an_instagram_native_sticker(self):
        self.assertNotIn('native_sticker_verified', PAGE.read_text(encoding="utf-8"))
