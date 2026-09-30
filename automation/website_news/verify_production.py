#!/usr/bin/env python3
"""Check the latest Website News publication on its public host."""
import html
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urljoin

ROOT = Path(__file__).resolve().parents[2]
BASE = os.environ.get("WEBSITE_NEWS_BASE_URL", "https://eximutc.github.io/EXIMUTC-News/").rstrip("/") + "/"

def read(url):
    request = urllib.request.Request(url, headers={"User-Agent": "EXIMUTC-News-production-check"})
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise ValueError(f"HTTP {response.status}: {url}")
        return response.read().decode("utf-8")

def verify(article):
    slug = quote(article["slug"], safe="-")
    url = urljoin(BASE, "articles/" + slug + ".html")
    page = read(url)
    index = read(BASE)
    image = read(urljoin(BASE, "assets/gemstone-news.svg"))
    title = html.escape(article["title"], quote=True)
    body = html.escape(article.get("body") or article.get("summary") or "", quote=True).replace("\n", "</p><p>")
    view = html.escape(article.get("market_view") or "", quote=True)
    markers = [f"<h1>{title}</h1>", body, view,
               '<time datetime="' + html.escape(article["published_at"], quote=True) + '">',
               'src="../assets/gemstone-news.svg"', 'rel="canonical"',
               'name="description"', 'property="og:image"']
    if not body or not view or not all(marker in page for marker in markers):
        raise ValueError("Latest article content, date, image or metadata is missing")
    if slug + ".html" not in index or "<svg" not in image:
        raise ValueError("Latest article missing from index or illustration unavailable")
    for placeholder in ("Editorial feed is being prepared.", "{{", "TODO", "PLACEHOLDER"):
        if placeholder in page or placeholder in index:
            raise ValueError(f"Technical placeholder on production: {placeholder}")
    published = datetime.fromisoformat(article["published_at"])
    if published.tzinfo is None:
        raise ValueError("Publication date is missing a timezone")
    age = (datetime.now(timezone.utc) - published).total_seconds()
    if age < -300:
        raise ValueError("Publication date is in the future")
    if age > 12 * 3600:
        raise ValueError("No new Website News publication in more than 12 hours")
    print(f"PASS: {url}")

def main():
    history = json.loads((ROOT / "pipeline_state/website_news_history.json").read_text())
    if not history:
        raise SystemExit("No published Website News history")
    for attempt in range(20):
        try:
            verify(history[-1])
            return
        except (OSError, ValueError) as error:
            if attempt == 19:
                raise SystemExit(f"FAIL: {error}")
            print(f"Waiting for production ({attempt + 1}/20): {error}", flush=True)
            time.sleep(15)

if __name__ == "__main__":
    main()
